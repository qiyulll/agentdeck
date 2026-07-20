export type NodeStatus = "healthy" | "degraded" | "offline" | "demo";

export interface NodeRecord {
  id: string;
  name: string;
  base_url: string;
  status: NodeStatus;
  last_seen_at: string;
}

export interface SessionSnapshot {
  id: string;
  node_id: string;
  tmux_session: string;
  tmux_window: string;
  tmux_pane: string;
  pane_title: string;
  current_path: string;
  command: string;
  status: string;
  last_seen_at: string;
}

export interface CaptureResponse {
  session_id: string;
  output: string;
  captured_at: string;
  source: string;
}

export interface DiffResponse {
  session_id: string;
  current_path: string;
  changed_files: string[];
  diff: string;
  error?: string | null;
}

export interface AuditLog {
  id: number;
  created_at: string;
  actor: string;
  node_id: string;
  session_id: string;
  action: string;
  target: string;
  request_preview: string;
  result: string;
}

