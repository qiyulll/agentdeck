from functools import lru_cache
from os import getenv


class NodeSettings:
    node_id: str = getenv("AGENTDECK_NODE_ID", "local-node")
    node_name: str = getenv("AGENTDECK_NODE_NAME", "Local Node")
    node_base_url: str = getenv("AGENTDECK_NODE_BASE_URL", "http://127.0.0.1:8101")
    hub_url: str = getenv("AGENTDECK_HUB_URL", "http://127.0.0.1:8000")
    node_token: str = getenv("AGENTDECK_NODE_TOKEN", "dev-node-token")
    demo_mode: bool = getenv("AGENTDECK_DEMO_MODE", "true").lower() in {"1", "true", "yes"}
    report_interval_seconds: int = int(getenv("AGENTDECK_REPORT_INTERVAL_SECONDS", "5"))


@lru_cache
def get_settings() -> NodeSettings:
    return NodeSettings()

