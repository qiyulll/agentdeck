import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from agentdeck_shared.models import AuditLog, NodeHeartbeat, NodeRecord, SessionSnapshot


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


class HubStore:
    def __init__(self, path: str):
        self.path = path
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS nodes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    base_url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS session_snapshots (
                    id TEXT PRIMARY KEY,
                    node_id TEXT NOT NULL,
                    tmux_session TEXT NOT NULL,
                    tmux_window TEXT NOT NULL,
                    tmux_pane TEXT NOT NULL,
                    pane_title TEXT NOT NULL,
                    current_path TEXT NOT NULL,
                    command TEXT NOT NULL,
                    status TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    raw_metadata_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT NOT NULL,
                    request_preview TEXT NOT NULL,
                    result TEXT NOT NULL
                );
                """
            )

    def upsert_node(self, heartbeat: NodeHeartbeat) -> NodeRecord:
        now = utc_now().isoformat()
        with self.connect() as conn:
            existing = conn.execute("SELECT created_at FROM nodes WHERE id = ?", (heartbeat.id,)).fetchone()
            created_at = existing["created_at"] if existing else now
            conn.execute(
                """
                INSERT INTO nodes (id, name, base_url, status, last_seen_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    base_url = excluded.base_url,
                    status = excluded.status,
                    last_seen_at = excluded.last_seen_at,
                    updated_at = excluded.updated_at
                """,
                (heartbeat.id, heartbeat.name, heartbeat.base_url, heartbeat.status, now, created_at, now),
            )
        return self.get_node(heartbeat.id)

    def get_node(self, node_id: str) -> NodeRecord:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
        if row is None:
            raise KeyError(node_id)
        return NodeRecord(
            id=row["id"],
            name=row["name"],
            base_url=row["base_url"],
            status=row["status"],
            last_seen_at=dt(row["last_seen_at"]),
            created_at=dt(row["created_at"]),
            updated_at=dt(row["updated_at"]),
        )

    def list_nodes(self) -> list[NodeRecord]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM nodes ORDER BY name").fetchall()
        return [
            NodeRecord(
                id=row["id"],
                name=row["name"],
                base_url=row["base_url"],
                status=row["status"],
                last_seen_at=dt(row["last_seen_at"]),
                created_at=dt(row["created_at"]),
                updated_at=dt(row["updated_at"]),
            )
            for row in rows
        ]

    def upsert_sessions(self, sessions: list[SessionSnapshot]) -> None:
        with self.connect() as conn:
            for item in sessions:
                conn.execute(
                    """
                    INSERT INTO session_snapshots (
                        id, node_id, tmux_session, tmux_window, tmux_pane, pane_title,
                        current_path, command, status, last_seen_at, raw_metadata_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        node_id = excluded.node_id,
                        tmux_session = excluded.tmux_session,
                        tmux_window = excluded.tmux_window,
                        tmux_pane = excluded.tmux_pane,
                        pane_title = excluded.pane_title,
                        current_path = excluded.current_path,
                        command = excluded.command,
                        status = excluded.status,
                        last_seen_at = excluded.last_seen_at,
                        raw_metadata_json = excluded.raw_metadata_json
                    """,
                    (
                        item.id,
                        item.node_id,
                        item.tmux_session,
                        item.tmux_window,
                        item.tmux_pane,
                        item.pane_title,
                        item.current_path,
                        item.command,
                        item.status,
                        item.last_seen_at.isoformat(),
                        json.dumps(item.raw_metadata),
                    ),
                )

    def list_sessions(self, node_id: str | None = None) -> list[SessionSnapshot]:
        query = "SELECT * FROM session_snapshots"
        args: tuple[str, ...] = ()
        if node_id:
            query += " WHERE node_id = ?"
            args = (node_id,)
        query += " ORDER BY node_id, tmux_session, tmux_window, tmux_pane"
        with self.connect() as conn:
            rows = conn.execute(query, args).fetchall()
        return [self._session_from_row(row) for row in rows]

    def get_session(self, session_id: str) -> SessionSnapshot:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM session_snapshots WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            raise KeyError(session_id)
        return self._session_from_row(row)

    def _session_from_row(self, row: sqlite3.Row) -> SessionSnapshot:
        return SessionSnapshot(
            id=row["id"],
            node_id=row["node_id"],
            tmux_session=row["tmux_session"],
            tmux_window=row["tmux_window"],
            tmux_pane=row["tmux_pane"],
            pane_title=row["pane_title"],
            current_path=row["current_path"],
            command=row["command"],
            status=row["status"],
            last_seen_at=dt(row["last_seen_at"]),
            raw_metadata=json.loads(row["raw_metadata_json"] or "{}"),
        )

    def add_audit_log(
        self,
        actor: str,
        node_id: str,
        session_id: str,
        action: str,
        target: str,
        request_preview: str,
        result: str,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO audit_logs
                    (created_at, actor, node_id, session_id, action, target, request_preview, result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (utc_now().isoformat(), actor, node_id, session_id, action, target, request_preview[:240], result),
            )

    def list_audit_logs(self, limit: int = 50) -> list[AuditLog]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [
            AuditLog(
                id=row["id"],
                created_at=dt(row["created_at"]),
                actor=row["actor"],
                node_id=row["node_id"],
                session_id=row["session_id"],
                action=row["action"],
                target=row["target"],
                request_preview=row["request_preview"],
                result=row["result"],
            )
            for row in rows
        ]

