import asyncio
import json
from contextlib import asynccontextmanager
from datetime import timezone
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from agentdeck_shared.auth import dashboard_auth, node_auth
from agentdeck_shared.models import CaptureResponse, DiffResponse, NodeHeartbeat, SendRequest, SendResponse, SessionSnapshot
from hub.config import get_settings
from hub.db import HubStore, utc_now
from hub.demo import demo_capture, demo_diff, demo_send, seed_demo
from hub.node_client import NodeClient

settings = get_settings()
store = HubStore(settings.db_path)
node_client = NodeClient(settings.node_token)
events: list[asyncio.Queue[str]] = []


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.demo_mode:
        seed_demo(store)
        await publish_event("demo.seeded", {"enabled": True})
    yield


app = FastAPI(title="AgentDeck Hub", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DashboardAuth = Annotated[None, Depends(dashboard_auth(settings.dashboard_token))]
NodeAuth = Annotated[None, Depends(node_auth(settings.node_token))]


async def publish_event(event: str, payload: dict) -> None:
    message = f"event: {event}\ndata: {json.dumps(payload, default=str)}\n\n"
    stale: list[asyncio.Queue[str]] = []
    for queue in events:
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            stale.append(queue)
    for queue in stale:
        events.remove(queue)


def with_computed_status(nodes):
    now = utc_now()
    output = []
    for node in nodes:
        if node.status != "demo":
            age = (now - node.last_seen_at.astimezone(timezone.utc)).total_seconds()
            if age > settings.degraded_after_seconds:
                node.status = "degraded"
        output.append(node)
    return output


@app.get("/health")
async def health():
    return {"ok": True, "service": "hub"}


@app.get("/api/nodes")
async def list_nodes(_: DashboardAuth):
    return with_computed_status(store.list_nodes())


@app.get("/api/sessions")
async def list_sessions(_: DashboardAuth, node_id: str | None = Query(default=None)):
    return store.list_sessions(node_id=node_id)


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str, _: DashboardAuth):
    try:
        return store.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found") from None


@app.get("/api/sessions/{session_id}/capture")
async def capture_session(session_id: str, _: DashboardAuth) -> CaptureResponse:
    session = get_existing_session(session_id)
    node = store.get_node(session.node_id)
    if node.base_url.startswith("demo://"):
        return demo_capture(session_id)
    return await node_client.capture(node.base_url, session_id)


@app.post("/api/sessions/{session_id}/send")
async def send_to_session(session_id: str, payload: SendRequest, _: DashboardAuth) -> SendResponse:
    session = get_existing_session(session_id)
    node = store.get_node(session.node_id)
    if node.base_url.startswith("demo://"):
        result = demo_send(session_id)
    else:
        result = await node_client.send(node.base_url, session_id, payload)
    store.add_audit_log(
        actor="local-user",
        node_id=node.id,
        session_id=session_id,
        action="send",
        target=session.tmux_pane,
        request_preview=payload.text,
        result=result.message,
    )
    await publish_event("session.send", {"session_id": session_id, "node_id": node.id})
    return result


@app.get("/api/sessions/{session_id}/diff")
async def session_diff(session_id: str, _: DashboardAuth) -> DiffResponse:
    session = get_existing_session(session_id)
    node = store.get_node(session.node_id)
    if node.base_url.startswith("demo://"):
        return demo_diff(session_id, session.current_path)
    return await node_client.diff(node.base_url, session_id)


@app.get("/api/audit-logs")
async def audit_logs(_: DashboardAuth, limit: int = Query(default=50, ge=1, le=200)):
    return store.list_audit_logs(limit=limit)


@app.get("/api/events")
async def event_stream(token: str = Query(default="")):
    if token != settings.dashboard_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
    events.append(queue)

    async def generator():
        try:
            yield "event: ready\ndata: {\"ok\": true}\n\n"
            while True:
                yield await queue.get()
        finally:
            if queue in events:
                events.remove(queue)

    return StreamingResponse(generator(), media_type="text/event-stream")


@app.post("/api/node/heartbeat")
async def node_heartbeat(payload: NodeHeartbeat, _: NodeAuth):
    node = store.upsert_node(payload)
    await publish_event("node.heartbeat", {"node_id": node.id})
    return node


@app.post("/api/node/session-snapshots")
async def node_session_snapshots(payload: list[SessionSnapshot], _: NodeAuth):
    store.upsert_sessions(payload)
    await publish_event("sessions.updated", {"count": len(payload)})
    return {"ok": True, "count": len(payload)}


def get_existing_session(session_id: str) -> SessionSnapshot:
    try:
        return store.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found") from None
