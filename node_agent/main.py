import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from agentdeck_shared.auth import node_auth
from agentdeck_shared.models import ManagedSessionCreate, SendRequest
from node_agent.config import get_settings
from node_agent.demo_provider import DemoProvider
from node_agent.managed_provider import ManagedProvider
from node_agent.reporter import report_loop
from node_agent.tmux_provider import TmuxProvider, TmuxUnavailable

settings = get_settings()
if settings.demo_mode:
    provider = DemoProvider(settings.node_id)
elif settings.backend == "managed":
    provider = ManagedProvider(settings.node_id)
else:
    provider = TmuxProvider(settings.node_id)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(report_loop(settings, provider))
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="AgentDeck Node Agent", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


NodeAuth = Depends(node_auth(settings.node_token))


@app.get("/health")
async def health():
    return {"ok": True, "service": "node-agent", "node_id": settings.node_id}


@app.get("/sessions")
async def sessions(_: None = NodeAuth):
    try:
        return provider.sessions()
    except TmuxUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/sessions/managed")
async def create_managed_session(payload: ManagedSessionCreate, _: None = NodeAuth):
    if not hasattr(provider, "create"):
        raise HTTPException(status_code=400, detail="This node does not support managed sessions")
    try:
        return provider.create(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/sessions/{session_id}/capture")
async def capture(session_id: str, _: None = NodeAuth):
    try:
        return provider.capture(session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/sessions/{session_id}/send")
async def send(session_id: str, payload: SendRequest, _: None = NodeAuth):
    try:
        return provider.send(session_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/sessions/{session_id}/diff")
async def diff(session_id: str, _: None = NodeAuth):
    try:
        return provider.diff(session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.websocket("/sessions/{session_id}/terminal")
async def terminal(session_id: str, websocket: WebSocket):
    token = websocket.query_params.get("token", "")
    if token != settings.node_token:
        await websocket.close(code=1008)
        return
    if not hasattr(provider, "subscribe") or not hasattr(provider, "write"):
        await websocket.close(code=1011)
        return
    await websocket.accept()
    subscriber = provider.subscribe(session_id)
    initial = provider.capture(session_id).output
    if initial:
        await websocket.send_text(initial)

    async def send_output() -> None:
        while True:
            chunk = await asyncio.to_thread(subscriber.get)
            await websocket.send_text(chunk)

    output_task = asyncio.create_task(send_output())
    try:
        while True:
            data = await websocket.receive_text()
            provider.write(session_id, data)
    except WebSocketDisconnect:
        pass
    finally:
        output_task.cancel()
        provider.unsubscribe(session_id, subscriber)
