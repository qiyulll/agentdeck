from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


NodeStatus = Literal["healthy", "degraded", "offline", "demo"]
SessionStatus = Literal["running", "idle", "unknown", "demo"]


class NodeHeartbeat(BaseModel):
    id: str
    name: str
    base_url: str
    status: NodeStatus = "healthy"


class NodeRecord(NodeHeartbeat):
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime


class SessionSnapshot(BaseModel):
    id: str
    node_id: str
    tmux_session: str
    tmux_window: str = ""
    tmux_pane: str
    pane_title: str = ""
    current_path: str = ""
    command: str = ""
    status: SessionStatus = "unknown"
    last_seen_at: datetime
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class CaptureResponse(BaseModel):
    session_id: str
    output: str
    captured_at: datetime
    source: str = "tmux"


class SendRequest(BaseModel):
    text: str = Field(min_length=1)
    enter: bool = True


class SendResponse(BaseModel):
    session_id: str
    accepted: bool
    message: str


class DiffResponse(BaseModel):
    session_id: str
    current_path: str
    changed_files: list[str]
    diff: str
    error: str | None = None


class AuditLog(BaseModel):
    id: int
    created_at: datetime
    actor: str
    node_id: str
    session_id: str
    action: str
    target: str
    request_preview: str
    result: str

