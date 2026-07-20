import { Activity, FileDiff, KeyRound, Play, RefreshCw, Send, Server, TerminalSquare } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, eventUrl, getToken, setToken } from "./api";
import { TerminalView } from "./TerminalView";
import type { AuditLog, CaptureResponse, DiffResponse, NodeRecord, SessionSnapshot } from "./types";

export function App() {
  const [tokenInput, setTokenInput] = useState(getToken());
  const [nodes, setNodes] = useState<NodeRecord[]>([]);
  const [sessions, setSessions] = useState<SessionSnapshot[]>([]);
  const [selectedNode, setSelectedNode] = useState<string>("");
  const [selectedSession, setSelectedSession] = useState<string>("");
  const [capture, setCapture] = useState<CaptureResponse | null>(null);
  const [diff, setDiff] = useState<DiffResponse | null>(null);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [prompt, setPrompt] = useState("");
  const [newSessionName, setNewSessionName] = useState("Windows Codex");
  const [newSessionCwd, setNewSessionCwd] = useState("");
  const [newSessionCommand, setNewSessionCommand] = useState("codex");
  const [error, setError] = useState("");

  async function refresh() {
    try {
      setError("");
      const [nextNodes, nextSessions, nextLogs] = await Promise.all([api.nodes(), api.sessions(), api.logs()]);
      setNodes(nextNodes);
      setSessions(nextSessions);
      setLogs(nextLogs);
      if ((!selectedNode || !nextNodes.some((node) => node.id === selectedNode)) && nextNodes[0]) {
        setSelectedNode(nextNodes[0].id);
      }
      if ((!selectedSession || !nextSessions.some((session) => session.id === selectedSession)) && nextSessions[0]) {
        setSelectedSession(nextSessions[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  useEffect(() => {
    void refresh();
    const source = new EventSource(eventUrl());
    source.addEventListener("node.heartbeat", () => void refresh());
    source.addEventListener("sessions.updated", () => void refresh());
    source.addEventListener("session.send", () => void refresh());
    source.onerror = () => source.close();
    return () => source.close();
  }, []);

  useEffect(() => {
    if (!selectedSession) {
      return;
    }
    void loadSessionDetails(selectedSession);
  }, [selectedSession]);

  async function loadSessionDetails(sessionId: string) {
    try {
      setError("");
      const nextCapture = await api.capture(sessionId);
      setCapture(nextCapture);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
    try {
      const nextDiff = await api.diff(sessionId);
      setDiff(nextDiff);
    } catch (err) {
      setDiff({
        session_id: sessionId,
        current_path: activeSession?.current_path ?? "",
        changed_files: [],
        diff: "",
        error: err instanceof Error ? err.message : String(err)
      });
    }
  }

  async function sendPrompt() {
    if (!selectedSession || !prompt.trim()) {
      return;
    }
    try {
      await api.send(selectedSession, prompt.trim());
      setPrompt("");
      await loadSessionDetails(selectedSession);
      const nextLogs = await api.logs();
      setLogs(nextLogs);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function sendEnter() {
    if (!selectedSession) {
      return;
    }
    try {
      await api.send(selectedSession, "", true);
      await loadSessionDetails(selectedSession);
      const nextLogs = await api.logs();
      setLogs(nextLogs);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  async function startManagedCodex() {
    if (!selectedNode) {
      setError("请先选择一个 Windows managed 节点。");
      return;
    }
    if (!canCreateManaged) {
      setError("当前选中的是演示节点。请先选择 Windows Local 节点，再启动 Windows Codex。");
      return;
    }
    try {
      setError("");
      const session = await api.createManaged(selectedNode, {
        name: newSessionName || "Windows Codex",
        cwd: newSessionCwd,
        command: newSessionCommand.trim().split(/\s+/)
      });
      await refresh();
      setSelectedSession(session.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }

  const visibleSessions = useMemo(
    () => sessions.filter((session) => !selectedNode || session.node_id === selectedNode),
    [sessions, selectedNode]
  );
  const activeSession = sessions.find((session) => session.id === selectedSession);
  const activeNode = nodes.find((node) => node.id === selectedNode);
  const canCreateManaged = Boolean(activeNode && activeNode.status !== "demo" && !activeNode.base_url.startsWith("demo://"));
  const statusText: Record<string, string> = {
    healthy: "正常",
    degraded: "降级",
    offline: "离线",
    demo: "演示"
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>AgentDeck</h1>
          <p>面向 Codex CLI 的 tmux-first 多会话控制台</p>
        </div>
        <div className="token-box">
          <KeyRound size={16} />
          <input value={tokenInput} onChange={(event) => setTokenInput(event.target.value)} />
          <button
            onClick={() => {
              setToken(tokenInput);
              void refresh();
            }}
          >
            保存
          </button>
          <button className="icon-button" onClick={() => void refresh()} aria-label="刷新">
            <RefreshCw size={16} />
          </button>
        </div>
      </header>

      {error && <div className="error-line">{error}</div>}

      <section className="dashboard-grid">
        <aside className="panel">
          <div className="panel-title">
            <Server size={17} />
            节点
          </div>
          <div className="list">
            {nodes.map((node) => (
              <button
                className={`list-item ${node.id === selectedNode ? "active" : ""}`}
                key={node.id}
                onClick={() => {
                  setSelectedNode(node.id);
                  const firstSession = sessions.find((session) => session.node_id === node.id);
                  if (firstSession) {
                    setSelectedSession(firstSession.id);
                  } else {
                    setSelectedSession("");
                    setCapture(null);
                    setDiff(null);
                  }
                }}
              >
                <span>{node.name}</span>
                <span className={`status ${node.status}`}>{statusText[node.status] ?? node.status}</span>
              </button>
            ))}
          </div>
        </aside>

        <aside className="panel">
          <div className="panel-title">
            <Activity size={17} />
            会话
          </div>
          <div className="list">
            {visibleSessions.map((session) => (
              <button
                className={`list-item session-item ${session.id === selectedSession ? "active" : ""}`}
                key={session.id}
                onClick={() => setSelectedSession(session.id)}
              >
                <span>{session.tmux_session}</span>
                <small>{session.command || session.tmux_pane}</small>
              </button>
            ))}
          </div>
          <div className="managed-create">
            <input value={newSessionName} onChange={(event) => setNewSessionName(event.target.value)} placeholder="会话名" />
            <input value={newSessionCwd} onChange={(event) => setNewSessionCwd(event.target.value)} placeholder="工作目录，留空为项目目录" />
            <input value={newSessionCommand} onChange={(event) => setNewSessionCommand(event.target.value)} placeholder="启动命令，例如 codex" />
            <button disabled={!canCreateManaged} onClick={() => void startManagedCodex()}>
              <Play size={16} />
              {canCreateManaged ? "启动 Windows Codex" : "请选择 Windows Local"}
            </button>
          </div>
        </aside>

        <section className="detail">
          <div className="detail-header">
            <div>
              <h2>{activeSession?.tmux_session ?? "未选择会话"}</h2>
              <p>{activeSession?.current_path ?? "选择一个会话后，可以读取终端输出并查看代码变更。"}</p>
            </div>
            <button disabled={!selectedSession} onClick={() => selectedSession && void loadSessionDetails(selectedSession)}>
              <RefreshCw size={16} />
              读取输出
            </button>
          </div>

          <div className="detail-grid">
            <section className="tool-panel terminal-panel">
              <div className="panel-title">
                <TerminalSquare size={17} />
                终端输出
              </div>
              <TerminalView sessionId={selectedSession} output={capture?.output ?? ""} />
              <div className="send-row">
                <input value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="发送 prompt 到当前 Codex session" />
                <button onClick={() => void sendPrompt()} disabled={!selectedSession || !prompt.trim()}>
                  <Send size={16} />
                  发送
                </button>
                <button onClick={() => void sendEnter()} disabled={!selectedSession}>
                  Enter
                </button>
              </div>
              <div className="key-row">
                <button onClick={() => void api.send(selectedSession, "\u001b", false)} disabled={!selectedSession}>Esc</button>
                <button onClick={() => void api.send(selectedSession, "\t", false)} disabled={!selectedSession}>Tab</button>
                <button onClick={() => void api.send(selectedSession, "\u0003", false)} disabled={!selectedSession}>Ctrl+C</button>
                <button onClick={() => void api.send(selectedSession, "\u001b[A", false)} disabled={!selectedSession}>↑</button>
                <button onClick={() => void api.send(selectedSession, "\u001b[B", false)} disabled={!selectedSession}>↓</button>
              </div>
            </section>

            <section className="tool-panel diff-panel">
              <div className="panel-title">
                <FileDiff size={17} />
                变更文件
              </div>
              {diff?.error && <div className="warning">{diff.error}</div>}
              <ul className="changed-files">
                {(diff?.changed_files ?? []).map((file) => (
                  <li key={file}>{file}</li>
                ))}
              </ul>
              <pre className="diff-view">{diff?.diff || "还没有读取到 diff。"}</pre>
            </section>
          </div>

          <section className="audit-strip">
            <div className="panel-title">操作审计</div>
            {logs.slice(0, 6).map((log) => (
              <div className="audit-row" key={log.id}>
                <span>{new Date(log.created_at).toLocaleTimeString()}</span>
                <span>{log.session_id}</span>
                <span>{log.request_preview}</span>
              </div>
            ))}
          </section>
        </section>
      </section>
    </main>
  );
}
