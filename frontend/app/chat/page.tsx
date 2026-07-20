"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  AgentMeta,
  ChatResponse,
  Health,
  getAgents,
  getHealth,
  sendChat,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";

type UserMsg = { kind: "user"; text: string };
type BotMsg = { kind: "bot"; data: ChatResponse };
type Msg = UserMsg | BotMsg;

const SUGGESTIONS = [
  "I paid yesterday but Premium is still locked.",
  "How long do refunds take?",
  "AeroBook 14 or ProStation 16 for video editing?",
  "This is the worst service ever — I want a manager.",
];

/* Minimal markdown: **bold**, _italic_, > blockquote, blank-line paragraphs. */
function renderAnswer(text: string) {
  const blocks = text.split(/\n{2,}/);
  return blocks.map((block, i) => {
    if (block.trim().startsWith(">")) {
      const quote = block.replace(/^>\s?/gm, "").trim();
      return <blockquote key={i}>{inline(quote)}</blockquote>;
    }
    const clean = block.replace(/^#{1,6}\s*/gm, "");
    return <p key={i}>{inline(clean)}</p>;
  });
}
function inline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|_[^_]+_)/g);
  return parts.map((p, i) => {
    if (p.startsWith("**") && p.endsWith("**"))
      return <strong key={i}>{p.slice(2, -2)}</strong>;
    if (p.startsWith("_") && p.endsWith("_") && p.length > 2)
      return <em key={i} className="muted-note">{p.slice(1, -1)}</em>;
    return <span key={i}>{p}</span>;
  });
}

export default function Home() {
  const router = useRouter();
  const { user, loading: authLoading, logout } = useAuth();
  const [agents, setAgents] = useState<AgentMeta[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [pinging, setPinging] = useState<Set<string>>(new Set());

  const sessionId = useRef<string>("");
  const threadRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    sessionId.current =
      (typeof crypto !== "undefined" && crypto.randomUUID?.()) ||
      `s-${Date.now()}`;
    getAgents().then(setAgents).catch(() => {});
    getHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight });
  }, [messages, sending]);

  useEffect(() => {
    if (!authLoading && !user) router.replace("/sign-in");
  }, [authLoading, user, router]);

  const accentById = useMemo(() => {
    const m: Record<string, string> = {};
    agents.forEach((a) => (m[a.id] = a.accent));
    return m;
  }, [agents]);

  const activeAgents = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if (m.kind === "bot") return new Set(m.data.agents.map((a) => a.id));
    }
    return new Set<string>();
  }, [messages]);

  async function submit(text: string) {
    const q = text.trim();
    if (!q || sending) return;
    setInput("");
    if (taRef.current) taRef.current.style.height = "auto";
    setMessages((m) => [...m, { kind: "user", text: q }]);
    setSending(true);
    try {
      const data = await sendChat(sessionId.current, q);
      setMessages((m) => [...m, { kind: "bot", data }]);
      const ids = new Set(data.agents.map((a) => a.id));
      setPinging(ids);
      setTimeout(() => setPinging(new Set()), 750);
    } catch {
      setMessages((m) => [
        ...m,
        {
          kind: "bot",
          data: {
            session_id: sessionId.current,
            answer:
              "I couldn't reach the support backend. Make sure the API is running on port 8000, then try again.",
            intent: "error",
            agents: [],
            sources: [],
            escalated: false,
            latency_ms: 0,
            demo_mode: false,
          },
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  function onKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit(input);
    }
  }
  function autogrow() {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 120) + "px";
  }

  const statusText = !health
    ? "connecting…"
    : health.llm_enabled
    ? health.model || "live"
    : "demo mode · no key";
  const statusClass = !health ? "off" : health.llm_enabled ? "" : "demo";

  if (authLoading || !user) {
    return (
      <div className="app" style={{ alignItems: "center", justifyContent: "center", display: "flex" }}>
        <div className="status-pill">
          <span className="status-dot off" />
          {authLoading ? "checking your session…" : "redirecting to sign in…"}
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="topbar">
        <Link href="/" className="brand" style={{ textDecoration: "none", color: "inherit" }}>
          <div className="brand-mark" aria-hidden>
            <span /><span /><span />
            <div className="brand-core" />
          </div>
          <div className="brand-title">
            <b>Support Switchboard</b>
            <small>TechMart Electronics · multi-agent AI desk</small>
          </div>
        </Link>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div className="status-pill" title="Backend status">
            <span className={`status-dot ${statusClass}`} />
            {statusText}
          </div>
          <div className="user-chip" title={user.email}>
            <span className="user-avatar">{user.name.charAt(0).toUpperCase()}</span>
            {user.name.split(" ")[0]}
          </div>
          <button
            className="logout-btn"
            onClick={async () => {
              await logout();
              router.push("/");
            }}
          >
            Sign out
          </button>
        </div>
      </header>

      <div className="stage">
        {/* Agent rail */}
        <aside className="rail">
          <div className="rail-head">Agents on duty</div>
          <ul className="roster">
            {agents.map((a) => {
              const active = activeAgents.has(a.id);
              const ping = pinging.has(a.id);
              return (
                <li
                  key={a.id}
                  className={`agent-card${active ? " active" : ""}${
                    ping ? " pinging" : ""
                  }`}
                  style={{ ["--accent" as any]: a.accent }}
                >
                  <div className="agent-avatar">{a.emoji}</div>
                  <div className="agent-meta">
                    <b>{a.name}</b>
                    <small>{a.blurb}</small>
                  </div>
                  <span className="agent-live">● LIVE</span>
                </li>
              );
            })}
            {agents.length === 0 &&
              [0, 1, 2, 3, 4].map((i) => (
                <li key={i} className="agent-card" style={{ opacity: 0.4 }}>
                  <div className="agent-avatar">·</div>
                  <div className="agent-meta">
                    <b>Loading…</b>
                    <small>connecting to backend</small>
                  </div>
                </li>
              ))}
          </ul>
          <div className="rail-foot">
            retrieval · <span>{health?.retrieval_backend ?? "—"}</span>
            <br />
            knowledge base ·{" "}
            <span>{health ? `${health.documents_indexed} docs` : "—"}</span>
          </div>
        </aside>

        {/* Chat */}
        <main className="chat">
          <div className="thread" ref={threadRef}>
            {messages.length === 0 && (
              <div className="welcome">
                <div className="welcome-orb" aria-hidden>
                  <svg viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M12 3v3M12 18v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M3 12h3M18 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1" />
                  </svg>
                </div>
                <h1>
                  Ask once. The <em>right specialist</em> answers.
                </h1>
                <p>
                  Your question is routed to one or more expert agents — billing,
                  technical, product, complaints, or FAQ — each grounded in
                  TechMart's real documents. Watch them light up as they respond.
                </p>
              </div>
            )}

            {messages.map((m, i) =>
              m.kind === "user" ? (
                <div className="msg user" key={i}>
                  <div className="bubble-user">{m.text}</div>
                </div>
              ) : (
                <BotBubble key={i} data={m.data} accentById={accentById} />
              )
            )}

            {sending && (
              <div className="routing" aria-live="polite">
                <div className="orchestrator" aria-hidden>
                  <svg viewBox="0 0 24 24" width="16" fill="none" stroke="#fff" strokeWidth="2">
                    <path d="M4 7h16M4 12h16M4 17h10" />
                  </svg>
                </div>
                <div className="routing-text">
                  <b>Orchestrator</b> is routing to the right specialist
                  <span className="dots"><span /><span /><span /></span>
                </div>
              </div>
            )}
          </div>

          <form
            className="composer"
            onSubmit={(e) => {
              e.preventDefault();
              submit(input);
            }}
          >
            {messages.length === 0 && (
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button
                    type="button"
                    key={s}
                    className="suggestion"
                    onClick={() => submit(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
            <div className="input-row">
              <textarea
                ref={taRef}
                rows={1}
                value={input}
                placeholder="Ask about billing, a bug, a product, or a complaint…"
                onChange={(e) => {
                  setInput(e.target.value);
                  autogrow();
                }}
                onKeyDown={onKey}
                aria-label="Message"
              />
              <button
                className="send-btn"
                type="submit"
                disabled={!input.trim() || sending}
                aria-label="Send message"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 12l15-7-6 16-3-6-6-3z" />
                </svg>
              </button>
            </div>
          </form>
        </main>
      </div>
    </div>
  );
}

function BotBubble({
  data,
  accentById,
}: {
  data: ChatResponse;
  accentById: Record<string, string>;
}) {
  return (
    <div className="msg bot">
      <div className="answer">
        <div className="answer-head">
          <span className="route-arrow">routed to</span>
          {data.agents.length === 0 && (
            <span className="agent-chip">System</span>
          )}
          {data.agents.map((a) => (
            <span
              key={a.id}
              className="agent-chip"
              style={{ ["--accent" as any]: accentById[a.id] || "#6366f1" }}
              title={a.reason}
            >
              {a.name}
            </span>
          ))}
          {data.intent && <span className="intent-tag">intent: {data.intent}</span>}
        </div>

        <div className="answer-body">{renderAnswer(data.answer)}</div>

        {data.escalated && (
          <div className="escalation">
            <span>⚠</span> Flagged for human escalation — a specialist will follow up.
          </div>
        )}

        {data.sources.length > 0 && (
          <div className="sources">
            <div className="sources-label">Retrieved from knowledge base</div>
            {data.sources.map((s, i) => (
              <span className="source-chip" key={i} title={s.snippet}>
                <span className="doc-dot" />
                {s.document}
                <span className="score">{s.score.toFixed(2)}</span>
              </span>
            ))}
          </div>
        )}
      </div>
      <div className="msg-foot">
        {data.demo_mode ? "demo mode · " : ""}
        {data.latency_ms} ms
      </div>
    </div>
  );
}
