from datetime import datetime, timezone

from agentdeck_shared.models import CaptureResponse, DiffResponse, SendRequest, SendResponse, SessionSnapshot


class DemoProvider:
    def __init__(self, node_id: str):
        self.node_id = node_id

    def sessions(self) -> list[SessionSnapshot]:
        now = datetime.now(timezone.utc)
        return [
            SessionSnapshot(
                id=f"{self.node_id}:%1",
                node_id=self.node_id,
                tmux_session="Codex README 打磨",
                tmux_window="0",
                tmux_pane="%1",
                pane_title="Codex",
                current_path="/demo/agentdeck",
                command="codex",
                status="demo",
                last_seen_at=now,
                raw_metadata={"provider": "demo"},
            ),
            SessionSnapshot(
                id=f"{self.node_id}:%2",
                node_id=self.node_id,
                tmux_session="Codex UI Review",
                tmux_window="1",
                tmux_pane="%2",
                pane_title="Codex",
                current_path="/demo/web-dashboard",
                command="codex",
                status="demo",
                last_seen_at=now,
                raw_metadata={"provider": "demo"},
            ),
        ]

    def capture(self, session_id: str) -> CaptureResponse:
        return CaptureResponse(
            session_id=session_id,
            captured_at=datetime.now(timezone.utc),
            source="demo",
            output="AgentDeck 演示节点在线。\n$ tmux capture-pane -p\n正在 review 变更文件...\n",
        )

    def send(self, session_id: str, payload: SendRequest) -> SendResponse:
        return SendResponse(session_id=session_id, accepted=True, message=f"演示模式已接收：{payload.text[:40]}")

    def diff(self, session_id: str) -> DiffResponse:
        return DiffResponse(
            session_id=session_id,
            current_path="/demo/agentdeck",
            changed_files=["README.md", "hub/main.py"],
            diff="+ 增加 tmux-first 架构说明\n+ 增加审计日志接口\n",
        )
