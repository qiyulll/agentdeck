# AgentDeck MVP Specification

## Product Scope

AgentDeck MVP is a personal web dashboard for viewing and controlling tmux-backed Codex CLI sessions across several development machines.

It must be runnable locally, demonstrable without tmux through demo mode, and structured clearly enough for future expansion.

## Users

Primary user:

- A developer running multiple coding agent sessions across 2-3 machines.
- Uses tmux to keep sessions alive.
- Wants to review progress from desktop or phone.
- Wants simple control, not enterprise permissions.

## Core User Stories

1. As a user, I can open the dashboard and see all registered machines.
2. As a user, I can see whether each machine is healthy, degraded, or offline.
3. As a user, I can select a machine and view its tmux-backed agent sessions.
4. As a user, I can select a session and read recent terminal output.
5. As a user, I can send a prompt or command to a selected tmux pane.
6. As a user, I can inspect changed files and git diff for the selected session's working directory.
7. As a user, I can see an audit log of dashboard-triggered actions.
8. As a user, I can run demo mode without tmux to show the product concept.

## Functional Requirements

### Hub Service

- Expose REST APIs for nodes, sessions, captures, diffs, sending input, and audit logs.
- Receive node heartbeat and session snapshots.
- Store nodes, latest session snapshots, and audit logs in SQLite.
- Mark nodes as degraded when heartbeat is older than 30 seconds.
- Serve SSE events for dashboard updates.
- Require a dashboard token for user-facing APIs.
- Require a node shared token for Node Agent reporting and Hub-to-Node calls.

### Node Agent

- Expose HTTP APIs used by the Hub.
- Scan local tmux sessions and panes.
- Read recent pane output through `tmux capture-pane`.
- Send input through `tmux send-keys`.
- Resolve pane current working directory.
- Return git changed files and git diff from the pane working directory.
- Periodically report heartbeat and session snapshots to the Hub.
- Support demo mode with generated nodes, sessions, output, and diffs when tmux is unavailable.

### Web Dashboard

- Use Vite + React + TypeScript.
- Use xterm.js for terminal-like output presentation.
- Use a three-column layout:
  - Node list
  - Session list
  - Terminal and diff details
- Show node status: healthy, degraded, offline/demo.
- Show session metadata: node, tmux session, pane id, working directory, last seen time.
- Allow sending prompt to selected session.
- Show changed files and git diff.
- Show audit log entries for send actions.
- Subscribe to SSE updates from the Hub.
- Store personal auth token in browser localStorage.

## Data Model

### Node

- id
- name
- base_url
- status
- last_seen_at
- created_at
- updated_at

### Session Snapshot

- id
- node_id
- tmux_session
- tmux_window
- tmux_pane
- pane_title
- current_path
- command
- status
- last_seen_at
- raw_metadata_json

### Audit Log

- id
- created_at
- actor
- node_id
- session_id
- action
- target
- request_preview
- result

## API Shape

Exact routes can evolve during implementation, but MVP should include:

- `GET /api/nodes`
- `GET /api/sessions`
- `GET /api/sessions/{session_id}`
- `GET /api/sessions/{session_id}/capture`
- `POST /api/sessions/{session_id}/send`
- `GET /api/sessions/{session_id}/diff`
- `GET /api/audit-logs`
- `GET /api/events`
- `POST /api/node/heartbeat`
- `POST /api/node/session-snapshots`

Node Agent APIs should include:

- `GET /health`
- `GET /sessions`
- `GET /sessions/{session_id}/capture`
- `POST /sessions/{session_id}/send`
- `GET /sessions/{session_id}/diff`

## Security Scope

MVP uses token-based auth only:

- Dashboard token for browser to Hub.
- Shared node token for Hub to Node and Node to Hub.

No RBAC, no multi-user account model, no OAuth, no SSO.

## Reliability Scope

- tmux sessions must continue running if AgentDeck crashes.
- Hub marks stale nodes as degraded after 30 seconds.
- Errors from tmux or git should be returned clearly and shown in the UI.
- Node Agent should not kill or restart tmux sessions.

## Documentation Requirements

README must include:

- What problem AgentDeck solves.
- Architecture diagram.
- Why tmux-first.
- Why FastAPI, React, xterm.js, SQLite, Tailscale.
- How heartbeat and degraded state work.
- How demo mode works.
- Known limitations.
- Pitfalls encountered.
- Comparison with:
  - tmux-agent-status
  - Codeman
  - Agent of Empires
- Resume bullet examples with honest, measurable claims.
