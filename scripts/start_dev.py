from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
NPM = Path("D:/Programs/nodejs/npm.cmd")


def start(name: str, command: list[str], cwd: Path, stdout_name: str, stderr_name: str) -> None:
    env = os.environ.copy()
    env["AGENTDECK_DEMO_MODE"] = "true"
    env["AGENTDECK_DASHBOARD_TOKEN"] = env.get("AGENTDECK_DASHBOARD_TOKEN", "dev-dashboard-token")
    env["AGENTDECK_NODE_TOKEN"] = env.get("AGENTDECK_NODE_TOKEN", "dev-node-token")
    env["PYTHONPATH"] = str(ROOT)

    stdout = (ROOT / stdout_name).open("ab")
    stderr = (ROOT / stderr_name).open("ab")
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        creationflags=creationflags,
        close_fds=True,
    )
    print(f"{name}: pid={process.pid}")


def main() -> int:
    if not PYTHON.exists():
        print(f"Missing virtualenv Python: {PYTHON}", file=sys.stderr)
        return 1
    if not NPM.exists():
        print(f"Missing npm.cmd: {NPM}", file=sys.stderr)
        return 1

    start(
        "hub",
        [str(PYTHON), "-m", "uvicorn", "hub.main:app", "--host", "127.0.0.1", "--port", "8000"],
        ROOT,
        "hub.log",
        "hub.err.log",
    )
    start(
        "node",
        [str(PYTHON), "-m", "uvicorn", "node_agent.main:app", "--host", "127.0.0.1", "--port", "8101"],
        ROOT,
        "node.log",
        "node.err.log",
    )
    start(
        "web",
        [str(NPM), "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173"],
        WEB,
        "web.log",
        "web.err.log",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

