Set-Location "F:\work\codex\web dashboard"
$env:AGENTDECK_DEMO_MODE = "true"
& ".\.venv\Scripts\python.exe" -m uvicorn hub.main:app --host 127.0.0.1 --port 8000 *> "F:\work\codex\web dashboard\hub.log"
