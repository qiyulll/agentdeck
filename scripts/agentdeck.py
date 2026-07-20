from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import threading
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
VENV_PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def resolve_python() -> str:
    if VENV_PYTHON.exists():
        return str(VENV_PYTHON)
    return sys.executable


def resolve_npm() -> str:
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if npm:
        return npm
    fallback = Path("D:/Programs/nodejs/npm.cmd")
    if fallback.exists():
        return str(fallback)
    raise SystemExit("npm was not found on PATH")


def stream_output(name: str, process: subprocess.Popen[str]) -> None:
    assert process.stdout is not None
    for line in process.stdout:
        print(f"[{name}] {line}", end="")


def start(name: str, command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.Popen[str]:
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    threading.Thread(target=stream_output, args=(name, process), daemon=True).start()
    return process


def build_env(args: argparse.Namespace) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env["AGENTDECK_DASHBOARD_TOKEN"] = args.dashboard_token
    env["AGENTDECK_NODE_TOKEN"] = args.node_token
    env["AGENTDECK_DEMO_MODE"] = "true" if args.demo else "false"
    return env


def run_processes(processes: list[subprocess.Popen[str]]) -> int:
    def stop_all() -> None:
        for process in processes:
            if process.poll() is None:
                process.terminate()

    signal.signal(signal.SIGINT, lambda *_: stop_all())
    signal.signal(signal.SIGTERM, lambda *_: stop_all())

    try:
        while True:
            for process in processes:
                code = process.poll()
                if code is not None:
                    stop_all()
                    return code
            threading.Event().wait(0.5)
    finally:
        stop_all()


def run_local(args: argparse.Namespace) -> int:
    env = build_env(args)
    python = resolve_python()
    npm = resolve_npm()
    processes = [
        start(
            "hub",
            [python, "-m", "uvicorn", "hub.main:app", "--host", "0.0.0.0", "--port", str(args.hub_port)],
            ROOT,
            env,
        ),
        start(
            "web",
            [npm, "run", "dev", "--", "--host", "127.0.0.1", "--port", str(args.web_port)],
            WEB,
            env,
        ),
    ]
    print("")
    print(f"AgentDeck local dashboard: http://127.0.0.1:{args.web_port}")
    print(f"Hub API for server nodes: http://<THIS_MACHINE_TAILSCALE_IP>:{args.hub_port}")
    print("Keep this window open. Press Ctrl+C to stop.")
    return run_processes(processes)


def run_server_node(args: argparse.Namespace) -> int:
    env = build_env(args)
    env["AGENTDECK_NODE_ID"] = args.node_id
    env["AGENTDECK_NODE_NAME"] = args.node_name
    env["AGENTDECK_NODE_BASE_URL"] = args.node_base_url
    env["AGENTDECK_HUB_URL"] = args.hub_url
    env["AGENTDECK_DEMO_MODE"] = "false"
    python = resolve_python()
    processes = [
        start(
            "node",
            [python, "-m", "uvicorn", "node_agent.main:app", "--host", "0.0.0.0", "--port", str(args.node_port)],
            ROOT,
            env,
        )
    ]
    print("")
    print(f"AgentDeck node: {args.node_name}")
    print(f"Reporting to Hub: {args.hub_url}")
    print("Keep this window open. Press Ctrl+C to stop.")
    return run_processes(processes)


def main() -> int:
    parser = argparse.ArgumentParser(description="AgentDeck launcher")
    parser.add_argument("--dashboard-token", default="dev-dashboard-token")
    parser.add_argument("--node-token", default="dev-node-token")
    subparsers = parser.add_subparsers(dest="command", required=True)

    local = subparsers.add_parser("local", help="Run Hub + Web on this computer")
    local.add_argument("--hub-port", type=int, default=8000)
    local.add_argument("--web-port", type=int, default=5173)
    local.add_argument("--demo", action="store_true", help="Seed demo sessions")
    local.set_defaults(func=run_local)

    server = subparsers.add_parser("server-node", help="Run Node Agent on a server")
    server.add_argument("--hub-url", required=True, help="Hub URL, for example http://100.x.y.z:8000")
    server.add_argument("--node-base-url", required=True, help="This server Node URL, for example http://100.a.b.c:8101")
    server.add_argument("--node-id", default="server-1")
    server.add_argument("--node-name", default="My Server")
    server.add_argument("--node-port", type=int, default=8101)
    server.set_defaults(func=run_server_node)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

