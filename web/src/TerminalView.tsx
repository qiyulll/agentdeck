import { useEffect, useRef } from "react";
import { Terminal } from "@xterm/xterm";

interface Props {
  output: string;
}

export function TerminalView({ output }: Props) {
  const host = useRef<HTMLDivElement | null>(null);
  const terminal = useRef<Terminal | null>(null);

  useEffect(() => {
    if (!host.current || terminal.current) {
      return;
    }
    terminal.current = new Terminal({
      convertEol: true,
      cursorBlink: false,
      fontFamily: "JetBrains Mono, Consolas, monospace",
      fontSize: 13,
      theme: {
        background: "#101214",
        foreground: "#d7dde5"
      }
    });
    terminal.current.open(host.current);
  }, []);

  useEffect(() => {
    terminal.current?.clear();
    terminal.current?.write(output || "还没有读取到终端输出。");
  }, [output]);

  return <div className="terminal-host" ref={host} />;
}
