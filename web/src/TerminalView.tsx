import { useEffect, useRef } from "react";
import { Terminal } from "@xterm/xterm";
import { terminalUrl } from "./api";

interface Props {
  sessionId: string;
  output: string;
}

export function TerminalView({ sessionId, output }: Props) {
  const host = useRef<HTMLDivElement | null>(null);
  const terminal = useRef<Terminal | null>(null);
  const socket = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!host.current) return;
    host.current.innerHTML = "";
    const term = new Terminal({
      convertEol: true,
      cursorBlink: true,
      fontFamily: "JetBrains Mono, Consolas, monospace",
      fontSize: 13,
      scrollback: 1000,
      theme: { background: "#101214", foreground: "#d7dde5" }
    });
    terminal.current = term;
    term.open(host.current);
    term.write(output || "正在连接实时终端...\r\n");

    if (sessionId) {
      const ws = new WebSocket(terminalUrl(sessionId));
      socket.current = ws;
      ws.onopen = () => term.write("\r\n[AgentDeck live terminal connected]\r\n");
      ws.onmessage = (event) => term.write(String(event.data));
      ws.onerror = () => term.write("\r\n[AgentDeck live terminal error]\r\n");
      ws.onclose = () => term.write("\r\n[AgentDeck live terminal closed]\r\n");
      term.onData((data) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(data);
        }
      });
    }

    return () => {
      socket.current?.close();
      term.dispose();
      socket.current = null;
      terminal.current = null;
    };
  }, [sessionId]);

  return <div className="terminal-host" ref={host} />;
}
