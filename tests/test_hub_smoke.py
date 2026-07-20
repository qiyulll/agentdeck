from fastapi.testclient import TestClient

from hub.main import app


TOKEN = {"Authorization": "Bearer dev-dashboard-token"}


def test_demo_hub_main_flow():
    with TestClient(app) as client:
        nodes = client.get("/api/nodes", headers=TOKEN)
        assert nodes.status_code == 200
        assert len(nodes.json()) >= 2

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

