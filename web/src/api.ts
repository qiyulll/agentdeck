import type { AuditLog, CaptureResponse, DiffResponse, NodeRecord, SessionSnapshot } from "./types";

const API_BASE = import.meta.env.VITE_AGENTDECK_API_BASE ?? "http://127.0.0.1:8000";

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
  send: (sessionId: string, text: string) =>
    request(`/api/sessions/${encodeURIComponent(sessionId)}/send`, {
      method: "POST",
      body: JSON.stringify({ text, enter: true })
    })
};

export function eventUrl(): string {
  return `${API_BASE}/api/events?token=${encodeURIComponent(getToken())}`;
}
