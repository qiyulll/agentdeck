@echo off
cd /d "%~dp0"
.\.venv\Scripts\python.exe .\scripts\agentdeck.py local --web-host 0.0.0.0 --windows-node
