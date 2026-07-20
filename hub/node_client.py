import httpx
from fastapi import HTTPException

from agentdeck_shared.models import CaptureResponse, DiffResponse, ManagedSessionCreate, SendRequest, SendResponse, SessionSnapshot


class NodeClient:
    def __init__(self, token: str, timeout: float = 8.0):
        self.token = token
        self.timeout = timeout

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    async def capture(self, base_url: str, session_id: str) -> CaptureResponse:
        async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as client:
            response = await client.get(f"{base_url}/sessions/{session_id}/capture", headers=self.headers)
            self._raise_node_error(response)
            return CaptureResponse.model_validate(response.json())

    async def send(self, base_url: str, session_id: str, payload: SendRequest) -> SendResponse:
        async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as client:
            response = await client.post(
                f"{base_url}/sessions/{session_id}/send",
                headers=self.headers,
                json=payload.model_dump(),
            )
            self._raise_node_error(response)
            return SendResponse.model_validate(response.json())

    async def diff(self, base_url: str, session_id: str) -> DiffResponse:
        async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as client:
            response = await client.get(f"{base_url}/sessions/{session_id}/diff", headers=self.headers)
            self._raise_node_error(response)
            return DiffResponse.model_validate(response.json())

    async def create_managed(self, base_url: str, payload: ManagedSessionCreate) -> SessionSnapshot:
        async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as client:
            response = await client.post(
                f"{base_url}/sessions/managed",
                headers=self.headers,
                json=payload.model_dump(),
            )
            self._raise_node_error(response)
            return SessionSnapshot.model_validate(response.json())

    def _raise_node_error(self, response: httpx.Response) -> None:
        if response.status_code < 400:
            return
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        if not detail:
            detail = f"Node request failed with HTTP {response.status_code}"
        raise HTTPException(status_code=response.status_code, detail=detail)
