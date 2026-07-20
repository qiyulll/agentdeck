# AgentDeck Project Plan

## Project Goal

AgentDeck is a lightweight Agent Session Web Dashboard for personal use. It manages long-running Codex CLI sessions across 2-3 development machines, where each agent session lives inside tmux and remains the source of truth even if the web service crashes.

The project should be useful as both a daily tool and a resume-ready engineering project. The implementation should show a complete loop: real workflow pain, architecture design, technical tradeoffs, reliability thinking, and measurable productivity impact.

## Target Scenario

The user runs multiple agent sessions on several machines. Today, reviewing progress requires SSHing into each machine, attaching tmux sessions, checking output, sending prompts, and manually inspecting git diffs.

AgentDeck centralizes this workflow:

- View all nodes and tmux-backed sessions from one web dashboard.
- Read recent terminal output from each session.
- Send prompts or commands to a selected tmux pane.
- Preview changed files and git diff for the pane's current working directory.
- Detect disconnected nodes through heartbeat status.
- Keep tmux as the only ground truth for actual agent execution.

## Confirmed Decisions

- Project name: AgentDeck
- Frontend: Vite + React + TypeScript
- Backend Hub: FastAPI
- Node Agent: FastAPI
- Transport:
  - Node to Hub: HTTP status report and heartbeat
  - Web to Hub: REST API plus Server-Sent Events
  - Hub to Node: HTTP calls for capture, send, and diff actions
- Storage: SQLite
- Stored data:
  - nodes
  - session snapshots
  - audit logs
- Terminal output history is not persisted in MVP.
- Network model: Tailscale private network by default.
- Auth model: token-based personal auth, no RBAC or multi-user permission system.
- Demo mode: supported for running without tmux.
- Diff scope: current pane working directory only, using git status and git diff.
- Layout: three columns: Node list, Session list, Terminal/Diff details.

## Architecture

```text
Browser Dashboard
  |
  | REST + SSE
  v
Hub FastAPI Service
  |
  | HTTP with shared node token
  v
Node Agent FastAPI Service
  |
  | tmux list-sessions / capture-pane / send-keys
  v
tmux sessions and panes
```

## Design Principles

1. tmux-first:
   tmux sessions remain the only ground truth. AgentDeck observes and controls tmux but does not replace it.

2. Recoverable web layer:
   If the Hub, Node Agent, or Dashboard crashes, existing Codex CLI sessions continue running inside tmux.

3. Small personal control plane:
   MVP focuses on one user's 2-3 machines, not enterprise-scale orchestration.

4. Honest reliability:
   Node heartbeat and degraded status should make disconnected state visible instead of hiding failures.

5. Resume-ready documentation:
   README should explain architecture decisions, technical selection, pitfalls, and comparison with tmux-agent-status, Codeman, and Agent of Empires.

## Non-Goals For MVP

- RBAC
- OAuth or SSO
- Multi-user collaboration
- Public internet deployment
- Full terminal emulator backend
- Persistent terminal transcript database
- Complex ANSI transcript parser
- Agent task scheduling or orchestration
- Docker sandbox
- File editor
- Pull request integration

## Development Phases

### Phase 1: Planning

- Create `codex.md`
- Create `spec.md`
- Create `tasks.md`
- Create `checklist.md`

### Phase 2: Backend Skeleton

- Hub FastAPI service
- Node Agent FastAPI service
- Shared data models
- Token middleware
- SQLite schema

### Phase 3: tmux Integration

- Scan tmux sessions and panes
- Capture pane output
- Send prompt to pane
- Resolve pane current working directory
- Read git status and git diff
- Add demo provider when tmux is unavailable

### Phase 4: Web Dashboard

- Vite React TypeScript app
- Three-column dashboard layout
- Session details
- Terminal output view using xterm.js
- Prompt send form
- Diff preview
- Audit log panel

### Phase 5: Reliability And Documentation

- Heartbeat and degraded status
- SSE updates
- README architecture documentation
- Local run instructions
- Demo script
- Manual verification
