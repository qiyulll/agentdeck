from datetime import timedelta

from agentdeck_shared.models import CaptureResponse, DiffResponse, NodeHeartbeat, SendResponse, SessionSnapshot
from hub.db import HubStore, utc_now


def seed_demo(store: HubStore) -> None:
    now = utc_now()
    nodes = [
        NodeHeartbeat(id="demo-macbook", name="主力开发机", base_url="demo://macbook", status="demo"),
        NodeHeartbeat(id="demo-wsl", name="WSL 开发环境", base_url="demo://wsl", status="demo"),
        NodeHeartbeat(id="demo-lab", name="实验室工作站", base_url="demo://lab", status="healthy"),
    ]
    for node in nodes:
        store.upsert_node(node)
    with store.connect() as conn:
        stale_at = (now - timedelta(seconds=45)).isoformat()
        conn.execute(
            "UPDATE nodes SET last_seen_at = ?, updated_at = ? WHERE id = ?",
            (stale_at, stale_at, "demo-lab"),
        )
    sessions = [
        SessionSnapshot(
            id="demo-macbook:%1",
            node_id="demo-macbook",
            tmux_session="Codex API 重构",
            tmux_window="0",
            tmux_pane="%1",
            pane_title="Codex",
            current_path="/Users/dev/projects/计费服务",
            command="codex",
            status="demo",
            last_seen_at=now,
            raw_metadata={"agent": "Codex CLI"},
        ),
        SessionSnapshot(
            id="demo-macbook:%2",
            node_id="demo-macbook",
            tmux_session="Codex 移动端界面",
            tmux_window="1",
            tmux_pane="%2",
            pane_title="Codex",
            current_path="/Users/dev/projects/移动端控制台",
            command="codex",
            status="demo",
            last_seen_at=now,
            raw_metadata={"agent": "Codex CLI"},
        ),
        SessionSnapshot(
            id="demo-wsl:%3",
            node_id="demo-wsl",
            tmux_session="Codex 测试补全",
            tmux_window="0",
            tmux_pane="%3",
            pane_title="Codex",
            current_path="/home/dev/projects/agentdeck",
            command="codex",
            status="demo",
            last_seen_at=now - timedelta(seconds=8),
            raw_metadata={"agent": "Codex CLI"},
        ),
    ]
    store.upsert_sessions(sessions)


def demo_capture(session_id: str) -> CaptureResponse:
    return CaptureResponse(
        session_id=session_id,
        captured_at=utc_now(),
        source="demo",
        output=(
            "$ codex\n"
            "正在分析当前仓库...\n"
            "已发现 FastAPI Hub 和 tmux Node Agent 模块。\n"
            "下一步：把发送操作写入审计日志。\n"
            "[demo] Web 层可以崩溃，但 tmux 仍然是真实会话来源。\n"
        ),
    )


def demo_diff(session_id: str, current_path: str) -> DiffResponse:
    return DiffResponse(
        session_id=session_id,
        current_path=current_path,
        changed_files=["hub/main.py", "node_agent/tmux_provider.py", "web/src/App.tsx"],
        diff=(
            "diff --git a/hub/main.py b/hub/main.py\n"
            "+ await publish_event('session.send', {'session_id': session_id})\n"
            "diff --git a/node_agent/tmux_provider.py b/node_agent/tmux_provider.py\n"
            "+ subprocess.run(['tmux', 'send-keys', '-t', pane_id, text, 'Enter'])\n"
        ),
    )


def demo_send(session_id: str) -> SendResponse:
    return SendResponse(session_id=session_id, accepted=True, message="演示 prompt 已接收")
