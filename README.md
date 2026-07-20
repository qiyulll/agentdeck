# AgentDeck

AgentDeck 是一个轻量级 Agent Session Web Dashboard，用来统一管理多台个人开发机器上的 Codex CLI 会话。每个 Agent 会话都运行在 tmux 里，Dashboard 只负责观察和操作，不接管会话本身。

核心设计原则是 **tmux-first**：tmux session 永远是唯一事实来源。即使 Hub、Node Agent 或浏览器崩溃，真实的 Agent 任务仍然会继续在 tmux 里运行。

## 为什么做这个项目

当你在 2-3 台机器上同时跑多个 Codex CLI session 时，日常 review 进度通常要反复 SSH、attach tmux、读输出、补 prompt、看 git diff。这个流程很碎，尤其手机上更难操作。

AgentDeck 把这些操作集中到一个 Web Dashboard 里，适合个人多机器、多 Agent 并行开发场景。

## 架构设计

```text
浏览器 Dashboard
  |
  | REST + SSE
  v
Hub FastAPI 服务
  |
  | HTTP + 预共享 Node Token
  v
Node Agent FastAPI 服务
  |
  | tmux list-panes / capture-pane / send-keys
  v
tmux sessions and panes
```

### 关键决策

- Hub 只保存节点、会话快照和审计日志，不保存完整 terminal transcript。
- Web 侧展示的是 capture 结果，不把浏览器状态当成真实状态。
- Node Agent 只调用 tmux 和 git，不杀进程、不重启 session。
- Node 超过 30 秒没有 heartbeat，Hub 会将其标记为 degraded。

## 技术选型

- FastAPI：Hub 和 Node Agent 都用 FastAPI，接口清晰，异步能力够用，个人部署成本低。
- React + TypeScript + Vite：适合快速做 Dashboard，组件边界清楚，后续扩展方便。
- xterm.js：用于展示 terminal 风格输出，避免一开始就实现完整双向终端。
- SQLite：MVP 只需要保存 nodes、session snapshots 和 audit logs，用 SQLite 足够。
- Tailscale：默认假设机器之间在私有网络内互通，不把控制面直接暴露到公网。
- tmux-first：不改造 Codex CLI 会话，保留随时 `tmux attach` 回退到纯终端的能力。

## 当前 MVP 功能

- Node Agent 扫描本机 tmux panes。
- 通过 `tmux capture-pane` 读取最近输出。
- 通过 `tmux send-keys` 向指定 pane 发送 prompt。
- Node 定时向 Hub 上报 heartbeat 和 session snapshots。
- Hub 超过 30 秒未收到 heartbeat 时标记节点为 degraded。
- Web 展示节点、session、terminal 输出、changed files、git diff 和 audit log。
- 支持 demo mode，没有 tmux 也能演示页面和主流程。

## 本地启动

安装 Python 依赖：

```bash
pip install -r requirements.txt
```

启动 Hub：

```bash
uvicorn hub.main:app --reload --port 8000
```

启动 Node Agent：

```bash
uvicorn node_agent.main:app --reload --port 8101
```

启动 Web Dashboard：

```bash
cd web
npm install
npm run dev
```

最简单的本机启动方式：

```powershell
.\agentdeck.bat
```

或者直接运行：

```powershell
.\.venv\Scripts\python.exe .\scripts\agentdeck.py local --demo
```

它只启动 Hub + Web 两个服务。本机 demo 和远程服务器接入都不需要启动本机 Node Agent。

旧的三窗口启动方式仍然保留：

```powershell
.\scripts\start-dev.bat
```

等 Vite 窗口打印 `Local:` 后，打开：

```text
http://127.0.0.1:5173
```

默认开发 token：

- Dashboard token：`dev-dashboard-token`
- Node token：`dev-node-token`

连接远程服务器的步骤见：

```text
docs/connect-server.md
```

## Demo Mode

默认启用 demo mode：

```bash
AGENTDECK_DEMO_MODE=true
```

在 demo mode 下：

- Hub 会生成几台示例节点和多个 Codex 会话。
- Node Agent 可以在没有 tmux 的环境里返回模拟 session、terminal 输出和 diff。
- 发送 prompt 会写入 audit log，但不会操作真实 tmux。

## 已知限制

- 暂不支持 RBAC、OAuth、SSO 和多人协作。
- Terminal 输出按需 capture，不持久化完整 transcript。
- Web 输入是 prompt 级操作，不是完整双向 terminal。
- Git diff 只读取当前 pane 工作目录下的仓库。
- Windows 原生环境通常没有 tmux；真实 Node Agent 建议跑在 Linux、macOS 或 WSL。

## 踩坑与取舍

- tmux-first 降低了系统复杂度，但 Web UI 必须容忍快照滞后。
- SSE 足够支撑 MVP 的状态刷新；真正低延迟 streaming 后续可以换 WebSocket。
- `tmux send-keys` 简单可靠，但它只是模拟键盘输入，不理解 Agent 语义。
- `git` 和 `tmux` 在不同机器上可能不存在，所以 Node Agent 会返回明确错误，而不是静默失败。
- 浏览器原生 `EventSource` 不能设置 Authorization header，因此 SSE 事件流使用 query token。

## 与相关项目对比

- tmux-agent-status：AgentDeck 借鉴了 tmux-first 和状态追踪思路，但目标是 Hub-Node Web 控制面，不是 tmux sidebar/status 插件。
- Codeman：Codeman 是更完整的 coding agent Web UI。AgentDeck 刻意保持轻量，聚焦个人 tmux-backed 多机器控制。
- Agent of Empires：AoE 更接近完整 Agent 编排平台。AgentDeck 不做 sandbox 和任务调度，只做轻量 dashboard。

## 简历写法示例

- 设计并实现 tmux-first Agent Session Dashboard，用于统一管理多台开发机器上的 Codex CLI 会话，将手工 SSH + tmux review 流程收敛为集中式 Web 操作。
- 搭建 Hub-Node 架构，基于 FastAPI、SQLite、SSE 和 token auth 实现节点心跳、会话快照、terminal capture、prompt send 和 git diff 预览。
- 实现 degraded 节点检测、Dashboard 操作审计日志和 demo mode，使项目在没有真实 tmux 环境时也能完整演示核心工作流。
