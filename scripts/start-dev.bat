@echo off
set ROOT=F:\work\codex\web dashboard
set AGENTDECK_DEMO_MODE=true
set AGENTDECK_DASHBOARD_TOKEN=dev-dashboard-token
set AGENTDECK_NODE_TOKEN=dev-node-token

start "AgentDeck Hub :8000" cmd /k "cd /d "%ROOT%" && .venv\Scripts\python.exe -m uvicorn hub.main:app --host 127.0.0.1 --port 8000"
start "AgentDeck Node :8101" cmd /k "cd /d "%ROOT%" && .venv\Scripts\python.exe -m uvicorn node_agent.main:app --host 127.0.0.1 --port 8101"
start "AgentDeck Web :5173" cmd /k "cd /d "%ROOT%\web" && D:\Programs\nodejs\npm.cmd run dev -- --host 127.0.0.1 --port 5173"

echo AgentDeck dev servers are starting.
echo Open http://127.0.0.1:5173 after the Vite window prints "Local:".

