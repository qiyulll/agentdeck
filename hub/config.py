from functools import lru_cache
from os import getenv


class HubSettings:
    dashboard_token: str = getenv("AGENTDECK_DASHBOARD_TOKEN", "dev-dashboard-token")
    node_token: str = getenv("AGENTDECK_NODE_TOKEN", "dev-node-token")
    db_path: str = getenv("AGENTDECK_DB_PATH", "./agentdeck.db")
    demo_mode: bool = getenv("AGENTDECK_DEMO_MODE", "true").lower() in {"1", "true", "yes"}
    degraded_after_seconds: int = int(getenv("AGENTDECK_DEGRADED_AFTER_SECONDS", "30"))


@lru_cache
def get_settings() -> HubSettings:
    return HubSettings()

