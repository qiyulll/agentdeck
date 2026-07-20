# AgentDeck Task Breakdown

## 0. Project Setup

- [x] Create monorepo directory structure.
- [x] Add root README.
- [x] Add Hub Python package.
- [x] Add Node Agent Python package.
- [x] Add Web Vite React TypeScript app.
- [x] Add `.env.example` files.
- [x] Add basic development scripts.

## 1. Shared Backend Foundations

- [x] Define shared Pydantic models for nodes, sessions, capture output, diff output, and audit logs.
- [x] Add token auth helpers.
- [x] Add common timestamp/status helpers.
- [x] Add structured error response shape.

## 2. Hub Service

- [x] Create FastAPI Hub app.
- [x] Create SQLite connection and migrations/bootstrap.
- [x] Implement nodes table.
- [x] Implement session snapshots table.
- [x] Implement audit logs table.
- [x] Implement node heartbeat endpoint.
- [x] Implement session snapshot ingestion endpoint.
- [x] Implement node degraded status calculation.
- [x] Implement REST endpoints for nodes and sessions.
- [x] Implement proxy endpoint for session capture.
- [x] Implement proxy endpoint for send prompt.
- [x] Implement proxy endpoint for git diff.
- [x] Implement audit log write on send action.
- [x] Implement SSE event stream.

## 3. Node Agent

- [x] Create FastAPI Node Agent app.
- [x] Implement tmux command wrapper.
- [x] Implement tmux session and pane scanner.
- [x] Implement pane capture through `tmux capture-pane`.
- [x] Implement send input through `tmux send-keys`.
- [x] Implement pane current path resolution.
- [x] Implement git status and git diff reader.
- [x] Implement HTTP APIs for sessions, capture, send, and diff.
- [x] Implement periodic heartbeat to Hub.
- [x] Implement periodic session snapshot reporting to Hub.
- [x] Implement demo mode provider.
- [x] Add clear error handling for missing tmux, missing git repo, and invalid pane.

## 4. Web Dashboard

- [x] Create Vite + React + TypeScript app.
- [x] Add API client with token support.
- [x] Add SSE client.
- [x] Add three-column app shell.
- [x] Add node list with status indicators.
- [x] Add session list filtered by selected node.
- [x] Add session detail panel.
- [x] Add xterm.js terminal output view.
- [x] Add prompt input and send button.
- [x] Add changed files view.
- [x] Add git diff preview.
- [x] Add audit log view.
- [x] Add localStorage token handling.
- [x] Add loading, empty, degraded, and error states.
- [ ] Verify mobile layout.

## 5. Demo Mode

- [x] Add Hub demo seed or Node demo provider.
- [x] Simulate two nodes.
- [x] Simulate several Codex sessions.
- [ ] Simulate one degraded node.
- [x] Simulate terminal output.
- [x] Simulate changed files and git diff.
- [x] Document demo mode in README.

## 6. Verification

- [x] Run backend unit tests or smoke tests.
- [x] Run frontend build.
- [ ] Manually test real tmux capture if tmux is available.
- [ ] Manually test send prompt if tmux is available.
- [x] Manually test demo mode without tmux.
- [ ] Manually test heartbeat degraded state.
- [x] Manually test audit log write.
- [ ] Manually test SSE refresh.
- [ ] Capture screenshots for README if useful.

## 7. Documentation

- [x] Write README usage instructions.
- [x] Write architecture section.
- [x] Write technology selection section.
- [x] Write pitfalls section.
- [x] Write comparison with tmux-agent-status, Codeman, and Agent of Empires.
- [x] Write resume bullets.
- [x] Add local development guide.
- [x] Add limitation and future roadmap section.
