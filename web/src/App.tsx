import { Activity, FileDiff, KeyRound, RefreshCw, Send, Server, TerminalSquare } from "lucide-react";
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
  const [error, setError] = useState("");

  async function refresh() {
    try {
      setError("");
      const [nextNodes, nextSessions, nextLogs] = await Promise.all([api.nodes(), api.sessions(), api.logs()]);
      setNodes(nextNodes);
      setSessions(nextSessions);
      setLogs(nextLogs);
      if (!selectedNode && nextNodes[0]) {
        setSelectedNode(nextNodes[0].id);
      }
      if (!selectedSession && nextSessions[0]) {
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
      const [nextCapture, nextDiff] = await Promise.all([api.capture(sessionId), api.diff(sessionId)]);
      setCapture(nextCapture);
      setDiff(nextDiff);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
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

  const visibleSessions = useMemo(
    () => sessions.filter((session) => !selectedNode || session.node_id === selectedNode),
    [sessions, selectedNode]
  );
  const activeSession = sessions.find((session) => session.id === selectedSession);
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
                  if (firstSession) setSelectedSession(firstSession.id);
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
              <TerminalView output={capture?.output ?? ""} />
              <div className="send-row">
                <input value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="发送 prompt 到当前 tmux pane" />
                <button onClick={() => void sendPrompt()} disabled={!selectedSession || !prompt.trim()}>
                  <Send size={16} />
                  发送
                </button>
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
