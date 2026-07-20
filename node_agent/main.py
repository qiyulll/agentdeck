import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agentdeck_shared.auth import node_auth
from agentdeck_shared.models import SendRequest
from node_agent.config import get_settings
from node_agent.demo_provider import DemoProvider
from node_agent.reporter import report_loop
from node_agent.tmux_provider import TmuxProvider, TmuxUnavailable

settings = get_settings()
provider = DemoProvider(settings.node_id) if settings.demo_mode else TmuxProvider(settings.node_id)


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
