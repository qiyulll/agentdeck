import asyncio

import httpx

from agentdeck_shared.models import NodeHeartbeat
from node_agent.config import NodeSettings


async def report_loop(settings: NodeSettings, provider) -> None:
    headers = {"Authorization": f"Bearer {settings.node_token}"}
    async with httpx.AsyncClient(timeout=8.0) as client:
        while True:
            try:
                heartbeat = NodeHeartbeat(
                    id=settings.node_id,
                    name=settings.node_name,
                    base_url=settings.node_base_url,
                    status="demo" if settings.demo_mode else "healthy",
                )
                await client.post(f"{settings.hub_url}/api/node/heartbeat", headers=headers, json=heartbeat.model_dump())
                snapshots = [item.model_dump(mode="json") for item in provider.sessions()]
                await client.post(f"{settings.hub_url}/api/node/session-snapshots", headers=headers, json=snapshots)
            except Exception:
                pass
            await asyncio.sleep(settings.report_interval_seconds)

