@echo off
cd /d "%~dp0"
echo Close all AgentDeck server windows before running this script.
echo.
if exist agentdeck.db del agentdeck.db
if exist hub.log del hub.log
if exist hub.err.log del hub.err.log
if exist node.log del node.log
if exist node.err.log del node.err.log
if exist web.log del web.log
if exist web.err.log del web.err.log
echo AgentDeck local runtime data has been cleared.
echo Start again with: agentdeck-mobile-lan.bat

