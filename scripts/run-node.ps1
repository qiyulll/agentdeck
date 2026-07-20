Set-Location "F:\work\codex\web dashboard"
$env:AGENTDECK_DEMO_MODE = "true"
& ".\.venv\Scripts\python.exe" -m uvicorn node_agent.main:app --host 127.0.0.1 --port 8101 *> "F:\work\codex\web dashboard\node.log"
