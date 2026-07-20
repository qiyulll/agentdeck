# 将服务器接入 AgentDeck

这份文档假设：

- 当前电脑运行 AgentDeck Hub 和 Web Dashboard。
- 远程服务器上运行 tmux，并且 tmux 里有 Codex CLI session。
- 两台机器可以通过 Tailscale 或同一个私有网络互相访问。

## 1. 在当前电脑启动 Hub 和 Web

在当前电脑运行：

```powershell
F:\work\codex\web dashboard\scripts\start-hub-public.bat
```

它会启动：

- Hub API：`http://0.0.0.0:8000`
- Web Dashboard：`http://127.0.0.1:5173`

在当前电脑打开 Dashboard：

```text
http://127.0.0.1:5173
```

Dashboard token：

```text
dev-dashboard-token
```

## 2. 获取当前电脑的 Tailscale IP

在当前电脑运行：

```powershell
tailscale ip -4
```

假设输出：

```text
100.x.y.z
```

那么远程服务器需要连接的 Hub URL 是：

```text
http://100.x.y.z:8000
```

如果不用 Tailscale，就换成当前电脑的局域网 IP。

## 3. 将项目复制到服务器

在服务器上：

```bash
git clone <your-agentdeck-repo-url> agentdeck
cd agentdeck
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

如果项目还没上传 GitHub，可以用 `scp`、`rsync`、SFTP 或任意文件同步工具复制到服务器。

## 4. 在服务器启动真实 Node Agent

把下面命令里的 `100.x.y.z` 换成当前电脑的 Tailscale IP：

```bash
cd agentdeck
source .venv/bin/activate

export AGENTDECK_DEMO_MODE=false
export AGENTDECK_NODE_ID=server-1
export AGENTDECK_NODE_NAME="My Server"
export AGENTDECK_NODE_BASE_URL="http://SERVER_TAILSCALE_IP:8101"
export AGENTDECK_HUB_URL="http://100.x.y.z:8000"
export AGENTDECK_NODE_TOKEN="dev-node-token"

python -m uvicorn node_agent.main:app --host 0.0.0.0 --port 8101
```

`SERVER_TAILSCALE_IP` 指服务器自己的 Tailscale IP，可以在服务器上运行：

```bash
tailscale ip -4
```

这个终端需要保持打开。

## 5. 在服务器准备 tmux session

在服务器上创建或进入 tmux session：

```bash
tmux new -s codex-work
```

在 tmux 里运行 Agent：

```bash
codex
```

AgentDeck 扫描的是 tmux pane。如果服务器上没有 tmux session，Dashboard 就没有真实 session 可展示。

## 6. 刷新 Dashboard

回到当前电脑：

```text
http://127.0.0.1:5173
```

点击刷新。正常情况下，左侧节点列表会出现 `My Server`，中间 session 列表会出现服务器上的 tmux session。

## 常见问题

### 服务器没有出现在节点列表

先确认服务器能访问 Hub：

```bash
curl http://100.x.y.z:8000/health
```

### Capture 或 Send 不生效

确认当前电脑能访问服务器上的 Node Agent：

```powershell
Invoke-RestMethod http://SERVER_TAILSCALE_IP:8101/health
```

### 没有 session

在服务器运行：

```bash
tmux list-panes -a
```

如果这里没有输出，AgentDeck 也没有内容可扫描。

### Git diff 为空或报错

选中的 tmux pane 必须位于一个 git 仓库目录内。AgentDeck 会从 pane 的当前工作目录读取 `git status` 和 `git diff`。
