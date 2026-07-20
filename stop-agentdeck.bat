@echo off
echo Stopping AgentDeck local servers...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*scripts\agentdeck.py*local*' -or $_.CommandLine -like '*uvicorn*hub.main:app*' -or $_.CommandLine -like '*uvicorn*node_agent.main:app*' -or $_.CommandLine -like '*npm*run*dev*5173*' -or $_.CommandLine -like '*vite*--port*5173*' } | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; Write-Host ('Stopped PID ' + $_.ProcessId) } catch {} }"
echo Done.
