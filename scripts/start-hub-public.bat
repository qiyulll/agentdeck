@echo off
set ROOT=F:\work\codex\web dashboard
set AGENTDECK_DEMO_MODE=true
set AGENTDECK_DASHBOARD_TOKEN=dev-dashboard-token
set AGENTDECK_NODE_TOKEN=dev-node-token

start "AgentDeck Hub :8000" cmd /k "cd /d "%ROOT%" && .venv\Scripts\python.exe -m uvicorn hub.main:app --host 0.0.0.0 --port 8000"
start "AgentDeck Web :5173" cmd /k "cd /d "%ROOT%\web" && D:\Programs\nodejs\npm.cmd run dev -- --host 127.0.0.1 --port 5173"

echo Hub and Web are starting.
echo Hub listens on 0.0.0.0:8000 so your server can report to it.
echo Open http://127.0.0.1:5173 on this computer.

