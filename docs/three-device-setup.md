# Windows + Linux Server + Android Setup

This is the intended setup for the current project:

```text
Android phone browser
  |
  | HTTP over same Wi-Fi / ZeroTier / private network
  v
Windows computer
  - Hub
  - Web Dashboard
  - Windows managed Codex node
  |
  | HTTP
  v
Linux server
  - tmux-backed Codex node
```

## 1. Start Windows Control Plane

On Windows:

```powershell
cd "F:\work\codex\web dashboard"
.\agentdeck-mobile-lan.bat
```

This starts:

- Hub: `http://0.0.0.0:8000`
- Web: `http://0.0.0.0:5173`
- Windows managed node: `http://127.0.0.1:8101`

Open on Windows:

```text
http://127.0.0.1:5173
```

Open on Android phone using the Windows LAN IP:

```text
http://172.20.45.35:5173
```

Token:

```text
dev-dashboard-token
```

## 2. Start A Codex Session On Windows

In the Dashboard:

1. Select node `Windows Local`.
2. In the session panel, set a session name, for example `Windows Codex`.
3. Optionally set a working directory, for example:

```text
F:\work\codex\web dashboard
```

4. Click `启动 Windows Codex`.

This starts a Codex process managed by AgentDeck. You can then:

- Read output.
- Send prompt.
- Inspect git diff from the configured working directory.

Important limitation:

- AgentDeck can control Windows Codex sessions it starts itself.
- It cannot attach to an already-open PowerShell or Windows Terminal Codex process.

## 3. Connect Linux Server

Copy the project to the Linux server, then install dependencies:

```bash
cd agentdeck
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start a tmux Codex session on the server:

```bash
tmux new -s server-codex
codex
```

In another server terminal, start the Linux Node Agent:

```bash
cd agentdeck
source .venv/bin/activate

python scripts/agentdeck.py server-node \
  --hub-url "http://172.20.45.35:8000" \
  --node-base-url "http://SERVER_IP:8101" \
  --node-id "linux-server" \
  --node-name "Linux Server"
```

Replace:

- `172.20.45.35` with the Windows computer IP reachable from the server.
- `SERVER_IP` with the Linux server IP reachable from Windows.

## 4. Android Control

On Android, open:

```text
http://172.20.45.35:5173
```

You should see:

- `Windows Local`
- `Linux Server`

From the phone you can switch nodes, read Codex output, send prompts, and review diffs.

## Network Options

Use whichever network path is available:

- Same Wi-Fi LAN: easiest for phone and Windows.
- ZeroTier: useful when devices are not on the same Wi-Fi.
- WireGuard: best if you can self-host and configure it.

Do not expose the dashboard directly to the public internet without access control.

