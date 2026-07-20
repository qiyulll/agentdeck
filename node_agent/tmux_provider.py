import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from agentdeck_shared.models import CaptureResponse, DiffResponse, SendRequest, SendResponse, SessionSnapshot


class TmuxUnavailable(RuntimeError):
    pass


class TmuxProvider:
    def __init__(self, node_id: str):
        self.node_id = node_id

    def ensure_tmux(self) -> None:
        if shutil.which("tmux") is None:
            raise TmuxUnavailable("tmux is not available on PATH")

    def run(self, args: list[str], cwd: str | None = None) -> str:
        self.ensure_tmux()
        result = subprocess.run(["tmux", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=8)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "tmux command failed")
        return result.stdout

    def sessions(self) -> list[SessionSnapshot]:
        fmt = "#{session_name}\t#{window_index}\t#{pane_id}\t#{pane_title}\t#{pane_current_path}\t#{pane_current_command}"
        output = self.run(["list-panes", "-a", "-F", fmt])
        now = datetime.now(timezone.utc)
        snapshots: list[SessionSnapshot] = []
        for line in output.splitlines():
            parts = line.split("\t")
            if len(parts) < 6:
                continue
            session_name, window_index, pane_id, pane_title, current_path, command = parts[:6]
            snapshots.append(
                SessionSnapshot(
                    id=f"{self.node_id}:{pane_id}",
                    node_id=self.node_id,
                    tmux_session=session_name,
                    tmux_window=window_index,
                    tmux_pane=pane_id,
                    pane_title=pane_title,
                    current_path=current_path,
                    command=command,
                    status="running" if command else "unknown",
                    last_seen_at=now,
                    raw_metadata={"source": "tmux"},
                )
            )
        return snapshots

    def capture(self, session_id: str) -> CaptureResponse:
        pane_id = self.pane_from_session_id(session_id)
        output = self.run(["capture-pane", "-p", "-t", pane_id, "-S", "-200"])
        return CaptureResponse(
            session_id=session_id,
            output=output,
            captured_at=datetime.now(timezone.utc),
            source="tmux",
        )

    def send(self, session_id: str, payload: SendRequest) -> SendResponse:
        pane_id = self.pane_from_session_id(session_id)
        self.run(["send-keys", "-t", pane_id, payload.text])
        if payload.enter:
            self.run(["send-keys", "-t", pane_id, "Enter"])
        return SendResponse(session_id=session_id, accepted=True, message="Sent to tmux pane")

    def diff(self, session_id: str) -> DiffResponse:
        pane_id = self.pane_from_session_id(session_id)
        current_path = self.run(["display-message", "-p", "-t", pane_id, "#{pane_current_path}"]).strip()
        path = Path(current_path)
        if not path.exists():
            return DiffResponse(session_id=session_id, current_path=current_path, changed_files=[], diff="", error="Path does not exist")
        if shutil.which("git") is None:
            return DiffResponse(session_id=session_id, current_path=current_path, changed_files=[], diff="", error="git is not available on PATH")
        status = subprocess.run(["git", "status", "--short"], cwd=current_path, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=8)
        diff = subprocess.run(["git", "diff"], cwd=current_path, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=8)
        if status.returncode != 0:
            error = status.stderr.strip() or "Directory is not a git repository"
            return DiffResponse(session_id=session_id, current_path=current_path, changed_files=[], diff="", error=error)
        changed = [line[3:] if len(line) > 3 else line for line in status.stdout.splitlines()]
        return DiffResponse(session_id=session_id, current_path=current_path, changed_files=changed, diff=diff.stdout, error=None)

    def pane_from_session_id(self, session_id: str) -> str:
        if ":" not in session_id:
            raise ValueError("Session id must include node prefix and tmux pane id")
        return session_id.split(":", 1)[1]
