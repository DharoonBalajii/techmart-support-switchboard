const BASE = process.env.NEXT_PUBLIC_API_URL || "";
const TOKEN_KEY = "switchboard_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}
export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export type AgentMeta = {
  id: string;
  name: string;
  domain: string;
  accent: string;
  emoji: string;
  blurb: string;
};

export type Source = { document: string; snippet: string; score: number };
export type AgentTrace = { id: string; name: string; domain: string; reason: string };

export type ChatResponse = {
  session_id: string;
  answer: string;
  intent: string;
  agents: AgentTrace[];
  sources: Source[];
  escalated: boolean;
  latency_ms: number;
  demo_mode: boolean;
};

export type Health = {
  status: string;
  llm_enabled: boolean;
  model: string | null;
  retrieval_backend: string;
  documents_indexed: number;
  chunks_indexed: number;
};

export type User = { id: string; name: string; email: string; created_at: string };
export type AuthResponse = { token: string; user: User };

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function asJson<T>(r: Response): Promise<T> {
  if (!r.ok) {
    let detail = `request failed: ${r.status}`;
    try {
      const body = await r.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new ApiError(r.status, detail);
  }
  return r.json();
}

export async function getHealth(): Promise<Health> {
  const r = await fetch(`${BASE}/api/health`, { cache: "no-store" });
  return asJson(r);
}

export async function getAgents(): Promise<AgentMeta[]> {
  const r = await fetch(`${BASE}/api/agents`, { cache: "no-store" });
  return (await asJson<{ agents: AgentMeta[] }>(r)).agents;
}

export async function register(name: string, email: string, password: string): Promise<AuthResponse> {
  const r = await fetch(`${BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });
  return asJson(r);
}



export async function login(email: string, password: string): Promise<AuthResponse> {
  const r = await fetch(`${BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return asJson(r);
}

export async function logout(): Promise<void> {
  await fetch(`${BASE}/api/auth/logout`, {
    method: "POST",
    headers: { ...authHeaders() },
  }).catch(() => {});
}

export async function getMe(): Promise<User> {
  const r = await fetch(`${BASE}/api/auth/me`, {
    cache: "no-store",
    headers: { ...authHeaders() },
  });
  return asJson(r);
}

export async function sendChat(sessionId: string, message: string): Promise<ChatResponse> {
  const r = await fetch(`${BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  return asJson(r);
}
