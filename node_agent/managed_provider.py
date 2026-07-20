import os
import queue
import shutil
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

import pyte

from agentdeck_shared.models import CaptureResponse, DiffResponse, ManagedSessionCreate, SendRequest, SendResponse, SessionSnapshot

if sys.platform == "win32":
    import winpty


MOJIBAKE_MARKERS = ("姝", "杩", "缁", "瀹", "鎺", "鍙", "鐢", "璇", "棰", "鎴", "锛", "鈥", "�")


def repair_mojibake(text: str) -> str:
    if not any(marker in text for marker in MOJIBAKE_MARKERS):
        return text
    try:
        repaired = text.encode("gbk", errors="strict").decode("utf-8", errors="strict")
    except UnicodeError:
        return text
    if repaired.count("\ufffd") > text.count("\ufffd"):
        return text
    return repaired


class ManagedProcess:
    def __init__(self, session_id: str, name: str, cwd: str, command: list[str], process):
        self.session_id = session_id
        self.name = name
        self.cwd = cwd
        self.command = command
        self.process = process
        self.lines: queue.Queue[str] = queue.Queue(maxsize=2000)
        self.buffer: list[str] = []
        self.screen = pyte.Screen(120, 32)
        self.stream = pyte.Stream(self.screen)
        self.lock = threading.Lock()
        self.subscribers: list[queue.Queue[str]] = []
        self.created_at = datetime.now(timezone.utc)
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()

    def _read_stdout(self) -> None:
        if hasattr(self.process, "read"):
            while True:
                try:
                    chunk = self.process.read(4096)
                except Exception as exc:
                    self.buffer.append(f"\n[AgentDeck] reader stopped: {exc}\n")
                    break
                if not chunk:
                    break
                self._append_output(chunk)
            return
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self._append_output(line)

    def _append_output(self, text: str) -> None:
        text = repair_mojibake(text)
        with self.lock:
            self.buffer.append(text)
            if len(self.buffer) > 800:
                self.buffer = self.buffer[-800:]
            self.stream.feed(text)
            stale: list[queue.Queue[str]] = []
            for subscriber in self.subscribers:
                try:
                    subscriber.put_nowait(text)
                except queue.Full:
                    stale.append(subscriber)
            for subscriber in stale:
                self.subscribers.remove(subscriber)

    def screen_text(self) -> str:
        with self.lock:
            lines = []
            for line in self.screen.display:
                lines.append(line.rstrip())
            text = "\n".join(lines).rstrip()
            if text:
                return text
            return "".join(self.buffer[-80:]).strip()


class ManagedProvider:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.sessions_by_id: dict[str, ManagedProcess] = {}
        self.next_id = 1

    def create(self, payload: ManagedSessionCreate) -> SessionSnapshot:
        command = payload.command or ["codex"]
        executable = self._resolve_executable(command[0])
        if executable is None:
            raise RuntimeError(f"Command not found on PATH: {command[0]}")
        cwd = payload.cwd or os.getcwd()
        if not Path(cwd).exists():
            raise RuntimeError(f"Working directory does not exist: {cwd}")
        session_id = f"{self.node_id}:managed-{self.next_id}"
        self.next_id += 1
        process = self._spawn_process([executable, *command[1:]], cwd)
        self.sessions_by_id[session_id] = ManagedProcess(session_id, payload.name, cwd, command, process)
        return self._snapshot(self.sessions_by_id[session_id])

    def sessions(self) -> list[SessionSnapshot]:
        return [self._snapshot(item) for item in self.sessions_by_id.values()]

    def capture(self, session_id: str) -> CaptureResponse:
        item = self._get(session_id)
        output = item.screen_text()
        if not output:
            output = "Managed Codex process is running. No output captured yet."
        return CaptureResponse(session_id=session_id, output=output, captured_at=datetime.now(timezone.utc), source="managed")

    def send(self, session_id: str, payload: SendRequest) -> SendResponse:
        item = self._get(session_id)
        if not self._is_running(item.process):
            return SendResponse(session_id=session_id, accepted=False, message="Process is not running")
        if hasattr(item.process, "write"):
            item.process.write(payload.text)
            if payload.enter:
                item.process.write("\r")
            return SendResponse(session_id=session_id, accepted=True, message="Sent to managed Codex PTY")
        assert item.process.stdin is not None
        item.process.stdin.write(payload.text)
        if payload.enter:
            item.process.stdin.write("\n")
        item.process.stdin.flush()
        return SendResponse(session_id=session_id, accepted=True, message="Sent to managed Codex process")

    def write(self, session_id: str, data: str) -> None:
        item = self._get(session_id)
        if not self._is_running(item.process):
            raise RuntimeError("Process is not running")
        if hasattr(item.process, "write"):
            item.process.write(data)
            return
        assert item.process.stdin is not None
        item.process.stdin.write(data)
        item.process.stdin.flush()

    def subscribe(self, session_id: str) -> queue.Queue[str]:
        item = self._get(session_id)
        subscriber: queue.Queue[str] = queue.Queue(maxsize=200)
        with item.lock:
            item.subscribers.append(subscriber)
        return subscriber

    def unsubscribe(self, session_id: str, subscriber: queue.Queue[str]) -> None:
        item = self._get(session_id)
        with item.lock:
            if subscriber in item.subscribers:
                item.subscribers.remove(subscriber)

    def diff(self, session_id: str) -> DiffResponse:
        item = self._get(session_id)
        if shutil.which("git") is None:
            return DiffResponse(session_id=session_id, current_path=item.cwd, changed_files=[], diff="", error="git is not available on PATH")
        status = subprocess.run(
            ["git", "status", "--short"],
            cwd=item.cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
        )
        diff = subprocess.run(
            ["git", "diff"],
            cwd=item.cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
        )
        if status.returncode != 0:
            return DiffResponse(
                session_id=session_id,
                current_path=item.cwd,
                changed_files=[],
                diff="",
                error=status.stderr.strip() or "Directory is not a git repository",
            )
        changed = [line[3:] if len(line) > 3 else line for line in status.stdout.splitlines()]
        return DiffResponse(session_id=session_id, current_path=item.cwd, changed_files=changed, diff=diff.stdout)

    def _snapshot(self, item: ManagedProcess) -> SessionSnapshot:
        running = self._is_running(item.process)
        return SessionSnapshot(
            id=item.session_id,
            node_id=self.node_id,
            tmux_session=item.name,
            tmux_window="managed",
            tmux_pane=item.session_id.rsplit(":", 1)[-1],
            pane_title="Codex",
            current_path=item.cwd,
            command=" ".join(item.command),
            status="running" if running else "idle",
            last_seen_at=datetime.now(timezone.utc),
            raw_metadata={"backend": "managed", "pid": getattr(item.process, "pid", None)},
        )

    def _get(self, session_id: str) -> ManagedProcess:
        if session_id not in self.sessions_by_id:
            raise KeyError(session_id)
        return self.sessions_by_id[session_id]

    def _resolve_executable(self, command: str) -> str | None:
        if sys.platform == "win32" and not Path(command).suffix:
            for suffix in (".cmd", ".bat", ".exe"):
                resolved = shutil.which(f"{command}{suffix}")
                if resolved:
                    return resolved
        return shutil.which(command)

    def _spawn_process(self, argv: list[str], cwd: str):
        if sys.platform == "win32":
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["LANG"] = "C.UTF-8"
            env["LC_ALL"] = "C.UTF-8"
            try:
                return winpty.PtyProcess.spawn(argv, cwd=cwd, env=env, dimensions=(32, 120))
            except PermissionError as exc:
                raise RuntimeError(
                    f"Cannot start {argv[0]}: access denied. On Windows this usually means the discovered executable "
                    "is not a CLI binary that can be launched by AgentDeck."
                ) from exc
        return subprocess.Popen(
            argv,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

    def _is_running(self, process) -> bool:
        if hasattr(process, "isalive"):
            return bool(process.isalive())
        return process.poll() is None
