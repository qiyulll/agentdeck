from fastapi.testclient import TestClient

import hub.main as hub_main
from hub.db import HubStore
from hub.demo import seed_demo
from hub.main import app


TOKEN = {"Authorization": "Bearer dev-dashboard-token"}


def test_demo_hub_main_flow(tmp_path, monkeypatch):
    test_store = HubStore(str(tmp_path / "agentdeck-test.db"))
    seed_demo(test_store)
    monkeypatch.setattr(hub_main, "store", test_store)
    monkeypatch.setattr(hub_main.settings, "demo_mode", True)

    with TestClient(app) as client:
        nodes = client.get("/api/nodes", headers=TOKEN)
        assert nodes.status_code == 200
        nodes_payload = nodes.json()
        assert len(nodes_payload) >= 2
        assert any(node["status"] == "degraded" for node in nodes_payload)

        sessions = client.get("/api/sessions", headers=TOKEN)
        assert sessions.status_code == 200
        first_session = sessions.json()[0]["id"]

        capture = client.get(f"/api/sessions/{first_session}/capture", headers=TOKEN)
        assert capture.status_code == 200
        assert "tmux" in capture.json()["output"]

        sent = client.post(
            f"/api/sessions/{first_session}/send",
            headers=TOKEN,
            json={"text": "continue", "enter": True},
        )
        assert sent.status_code == 200
        assert sent.json()["accepted"] is True

        diff = client.get(f"/api/sessions/{first_session}/diff", headers=TOKEN)
        assert diff.status_code == 200
        assert diff.json()["changed_files"]

        logs = client.get("/api/audit-logs", headers=TOKEN)
        assert logs.status_code == 200
        assert logs.json()[0]["action"] == "send"
