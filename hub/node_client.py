import httpx

from agentdeck_shared.models import CaptureResponse, DiffResponse, SendRequest, SendResponse


class NodeClient:
    def __init__(self, token: str, timeout: float = 8.0):
        self.token = token
        self.timeout = timeout

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    async def capture(self, base_url: str, session_id: str) -> CaptureResponse:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{base_url}/sessions/{session_id}/capture", headers=self.headers)
            response.raise_for_status()
            return CaptureResponse.model_validate(response.json())

    async def send(self, base_url: str, session_id: str, payload: SendRequest) -> SendResponse:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{base_url}/sessions/{session_id}/send",
                headers=self.headers,
                json=payload.model_dump(),
            )
            response.raise_for_status()
            return SendResponse.model_validate(response.json())

    async def diff(self, base_url: str, session_id: str) -> DiffResponse:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{base_url}/sessions/{session_id}/diff", headers=self.headers)
            response.raise_for_status()
            return DiffResponse.model_validate(response.json())

