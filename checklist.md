# AgentDeck MVP Verification Checklist

## Planning Files

- [x] `codex.md` exists and explains goal, plan, architecture, and non-goals.
- [x] `spec.md` exists and defines the MVP scope.
- [x] `tasks.md` exists and breaks down implementation work.
- [x] `checklist.md` exists and defines done criteria.

## Hub Verification

- [x] Hub starts locally without crashing.
- [x] Hub creates or opens SQLite database.
- [ ] Hub rejects unauthenticated dashboard requests.
- [x] Hub accepts authenticated dashboard requests.
- [ ] Hub accepts authenticated node heartbeat.
- [x] Hub stores node records.
- [x] Hub stores latest session snapshots.
- [ ] Hub marks a node degraded when heartbeat is older than 30 seconds.
- [x] Hub returns nodes through REST API.
- [x] Hub returns sessions through REST API.
- [x] Hub proxies capture request to Node Agent.
- [x] Hub proxies send request to Node Agent.
- [x] Hub proxies diff request to Node Agent.
- [x] Hub writes audit log for send actions.
- [ ] Hub emits SSE update events.

## Node Agent Verification

- [x] Node Agent starts locally without crashing.
- [x] Node Agent exposes health endpoint.
- [ ] Node Agent scans tmux sessions when tmux exists.
- [ ] Node Agent reads pane output with `tmux capture-pane`.
- [ ] Node Agent sends input with `tmux send-keys`.
- [ ] Node Agent resolves pane current working directory.
- [ ] Node Agent returns git status and git diff for a git repo.
- [ ] Node Agent returns clear error for non-git directory.
- [ ] Node Agent reports heartbeat to Hub.
- [ ] Node Agent reports session snapshots to Hub.
- [x] Node Agent demo mode works without tmux.

## Web Verification

- [x] Web app builds successfully.
- [ ] Web app loads in browser.
- [ ] Token entry or localStorage auth works.
- [ ] Node list renders.
- [ ] Session list renders.
- [ ] Selecting a node filters sessions.
- [ ] Selecting a session shows details.
- [ ] Terminal output renders through xterm.js.
- [ ] Prompt send action calls Hub API.
- [ ] Changed files render.
- [ ] Git diff renders.
- [ ] Audit log renders.
- [ ] SSE updates refresh visible state.
- [ ] Degraded node state is visible.
- [ ] Empty states are understandable.
- [ ] Mobile layout is usable.

## Demo Verification

- [x] Demo mode can run without tmux installed.
- [x] Demo mode shows at least two nodes.
- [x] Demo mode shows at least three sessions.
- [ ] Demo mode includes one degraded node.
- [x] Demo mode includes terminal output.
- [x] Demo mode includes changed files and diff.
- [x] Demo mode supports sending a prompt and recording an audit log.

## Documentation Verification

- [x] README explains the real workflow pain.
- [x] README includes architecture diagram.
- [x] README explains tmux-first design.
- [x] README explains technology selection.
- [x] README explains heartbeat and degraded status.
- [x] README explains demo mode.
- [x] README documents local run commands.
- [x] README lists known limitations.
- [x] README includes pitfalls and tradeoffs.
- [x] README compares with tmux-agent-status.
- [x] README compares with Codeman.
- [x] README compares with Agent of Empires.
- [x] README includes resume-ready project bullets.
