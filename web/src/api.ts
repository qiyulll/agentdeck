import type { AuditLog, CaptureResponse, DiffResponse, ManagedSessionCreate, NodeRecord, SessionSnapshot } from "./types";

function defaultApiBase(): string {
  if (typeof window === "undefined") {
    return "http://127.0.0.1:8000";
  }
  return `${window.location.protocol}//${window.location.hostname}:8000`;
}

const API_BASE = import.meta.env.VITE_AGENTDECK_API_BASE ?? defaultApiBase();

export function getToken(): string {
  return localStorage.getItem("agentdeck_token") || "dev-dashboard-token";
}

export function setToken(token: string): void {
  localStorage.setItem("agentdeck_token", token);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
      ...(init.headers || {})
    }
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json() as Promise<T>;
}

export const api = {
  nodes: () => request<NodeRecord[]>("/api/nodes"),
  sessions: () => request<SessionSnapshot[]>("/api/sessions"),
  capture: (sessionId: string) => request<CaptureResponse>(`/api/sessions/${encodeURIComponent(sessionId)}/capture`),
  diff: (sessionId: string) => request<DiffResponse>(`/api/sessions/${encodeURIComponent(sessionId)}/diff`),
  logs: () => request<AuditLog[]>("/api/audit-logs"),
  createManaged: (nodeId: string, payload: ManagedSessionCreate) =>
    request<SessionSnapshot>(`/api/nodes/${encodeURIComponent(nodeId)}/managed-sessions`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  send: (sessionId: string, text: string, enter = true) =>
    request(`/api/sessions/${encodeURIComponent(sessionId)}/send`, {
      method: "POST",
      body: JSON.stringify({ text, enter })
    })
};

export function eventUrl(): string {
  return `${API_BASE}/api/events?token=${encodeURIComponent(getToken())}`;
}

export function terminalUrl(sessionId: string): string {
  const base = new URL(API_BASE);
  base.protocol = base.protocol === "https:" ? "wss:" : "ws:";
  base.pathname = `/api/sessions/${encodeURIComponent(sessionId)}/terminal`;
  base.search = `token=${encodeURIComponent(getToken())}`;
  return base.toString();
}
