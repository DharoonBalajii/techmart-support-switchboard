"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import "./landing.css";

const AGENTS = [
  {
    id: "billing",
    name: "Billing",
    emoji: "💳",
    accent: "#10B981",
    cx: 52,
    on: true,
    blurb: "Payments, invoices, subscriptions and refunds.",
    handles: "refunds · invoices · Premium",
  },
  {
    id: "technical",
    name: "Technical",
    emoji: "🛠️",
    accent: "#3B82F6",
    cx: 141,
    on: true,
    blurb: "Login, setup, errors, bugs and installation.",
    handles: "login · errors · setup",
  },
  {
    id: "product",
    name: "Product",
    emoji: "📦",
    accent: "#8B5CF6",
    cx: 230,
    on: false,
    blurb: "Features, pricing, comparisons and availability.",
    handles: "specs · pricing · compare",
  },
  {
    id: "complaint",
    name: "Complaint",
    emoji: "🚩",
    accent: "#F43F5E",
    cx: 319,
    on: false,
    blurb: "Frustration, escalation and dissatisfaction.",
    handles: "escalate · empathy",
  },
  {
    id: "faq",
    name: "FAQ",
    emoji: "💬",
    accent: "#06B6D4",
    cx: 408,
    on: false,
    blurb: "Policies, shipping, hours and contact info.",
    handles: "policy · shipping · contact",
  },
];

const STEPS = [
  {
    t: "Detect intent",
    d: "Reads each question and classifies it — billing, technical, product, complaint or FAQ.",
  },
  {
    t: "Route to specialist(s)",
    d: "Sends it to the right agent — or several at once when a question spans domains.",
  },
  {
    t: "Retrieve from your docs",
    d: "Each agent pulls the most relevant passages from your knowledge base via RAG.",
  },
  {
    t: "Answer, grounded & cited",
    d: "Replies in the agent's voice, cites its sources, and escalates when it can't resolve.",
  },
];

const FEATURES = [
  {
    t: "Multi-agent routing",
    d: "One message can fire several specialists at once and merge their answers into one reply.",
    icon: (
      <path d="M12 3v6m0 0L7 14m5-5l5 5M5 20h4m6 0h4" />
    ),
  },
  {
    t: "Grounded in your docs",
    d: "Every answer is retrieved from your knowledge base, with source citations attached.",
    icon: <path d="M5 4h9l5 5v11H5zM14 4v5h5M8 13h7M8 16h7" />,
  },
  {
    t: "Smart escalation",
    d: "Detects frustration or dead-ends and flags the conversation for a human specialist.",
    icon: <path d="M12 4l9 16H3zM12 10v4M12 17h.01" />,
  },
  {
    t: "Conversation memory",
    d: "Remembers the thread so follow-up questions keep all their context.",
    icon: <path d="M4 5h16v10H8l-4 4zM8 9h8M8 12h5" />,
  },
  {
    t: "Runs on a cheap model",
    d: "Powered by OpenRouter — swap models with one env var. Cents per thousand chats.",
    icon: <path d="M12 3v3M12 18v3M5 12H2M22 12h-3M6 6l-2-2M20 20l-2-2M6 18l-2 2M20 4l-2 2M12 8a4 4 0 100 8 4 4 0 000-8z" />,
  },
  {
    t: "Visible orchestration",
    d: "Watch the agents light up live — you always see who answered and why.",
    icon: <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7zM12 9a3 3 0 100 6 3 3 0 000-6z" />,
  },
];

export default function Landing() {
  const router = useRouter();
  const { user, loading, logout } = useAuth();

  return (
    <div className="lp">
      {/* Nav */}
      <nav className="lp-nav">
        <Link href="/" className="lp-brand">
          <div className="brand-mark" aria-hidden>
            <span /><span /><span />
            <div className="brand-core" />
          </div>
          <b>Support Switchboard</b>
        </Link>
        <div className="lp-navlinks">
          <a href="#how">How it works</a>
          <a href="#agents">The agents</a>
          {!loading && !user && (
            <>
              <Link href="/sign-in" className="lp-cta ghost">Sign in</Link>
              <Link href="/sign-up" className="lp-cta primary">Sign up</Link>
            </>
          )}
          {!loading && user && (
            <>
              <Link href="/chat" className="lp-cta primary">
                Launch app →
              </Link>
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
            </>
          )}
        </div>
      </nav>

      {/* Hero */}
      <header className="lp-hero">
        <div>
          <span className="eyebrow">
            <span className="pip" /> Multi-agent AI support
          </span>
          <h1>
            Every question, to the <em>right specialist</em> — instantly.
          </h1>
          <p className="lp-sub">
            One chatbot can't be an expert in everything. Support Switchboard reads
            intent, routes to the billing, technical, product, complaint or FAQ agent
            (or several at once), and grounds every answer in your real documents.
          </p>
          <div className="lp-hero-actions">
            <Link href="/chat" className="lp-cta primary">
              Open the live demo →
            </Link>
            <a href="#how" className="lp-cta ghost">
              See how it works
            </a>
          </div>
          <div className="lp-trust">
            <span><i className="tick">✓</i> Grounded in your docs</span>
            <span><i className="tick">✓</i> Cites its sources</span>
            <span><i className="tick">✓</i> Escalates when it should</span>
          </div>
        </div>

        {/* The signature: live routing constellation */}
        <div className="constellation" aria-hidden>
          <svg viewBox="0 0 460 400" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="brandGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor="#6366f1" />
                <stop offset="0.55" stopColor="#8b5cf6" />
                <stop offset="1" stopColor="#22d3ee" />
              </linearGradient>
            </defs>

            {/* customer question */}
            <rect x="132" y="14" width="196" height="46" rx="12" className="node-box" />
            <text x="230" y="35" textAnchor="middle" className="query-caption">
              &ldquo;I paid but Premium is
            </text>
            <text x="230" y="49" textAnchor="middle" className="query-caption">
              still locked&rdquo;
            </text>

            {/* customer -> orchestrator */}
            <path d="M230 60 V112" className="wire flow" stroke="#8b5cf6" />

            {/* connections orchestrator -> agents */}
            {AGENTS.map((a) => (
              <path
                key={a.id}
                d={`M230 178 C 230 250 ${a.cx} 246 ${a.cx} 314`}
                className={a.on ? "wire flow on" : "wire"}
                stroke={a.on ? a.accent : undefined}
              />
            ))}

            {/* orchestrator hub */}
            <circle cx="230" cy="146" r="30" className="orch-ring" fill="none" stroke="#8b5cf6" strokeWidth="2" />
            <rect x="196" y="116" width="68" height="60" rx="16" fill="url(#brandGrad)" />
            <circle cx="222" cy="140" r="3.4" fill="#fff" />
            <circle cx="238" cy="140" r="3.4" fill="#fff" opacity="0.85" />
            <circle cx="230" cy="154" r="3.4" fill="#fff" opacity="0.7" />

            {/* agent nodes */}
            {AGENTS.map((a, i) => (
              <g
                key={a.id}
                className={`agent-node ${a.on ? "on" : "pulse"}`}
                style={{ animationDelay: `${i * 0.35}s` }}
              >
                <rect
                  x={a.cx - 39}
                  y="314"
                  width="78"
                  height="62"
                  rx="14"
                  className="node-box"
                  stroke={a.accent}
                  strokeWidth={a.on ? 2.5 : 1.5}
                />
                <text x={a.cx} y="343" textAnchor="middle" className="node-emoji">
                  {a.emoji}
                </text>
                <text x={a.cx} y="363" textAnchor="middle" className="node-label" style={{ fontSize: 11 }}>
                  {a.name}
                </text>
              </g>
            ))}
          </svg>
        </div>
      </header>

      {/* Problem */}
      <section className="lp-section">
        <div className="lp-problem">
          <h2>
            Companies get thousands of queries a day — spanning billing, bugs,
            products and complaints. <em>No single bot handles them all well.</em>
          </h2>
          <p>
            Support Switchboard solves it the way a real support org does: a team of
            specialists behind one front desk. An orchestrator reads each request and
            hands it to the agent — or agents — best equipped to answer, every reply
            grounded in your own documentation.
          </p>
        </div>
      </section>

      {/* Agents */}
      <section className="lp-section" id="agents">
        <div className="lp-section-head">
          <div className="lp-kicker">The roster</div>
          <h2>Five specialists, one front desk</h2>
          <p>
            Each agent has its own persona, its own slice of the knowledge base, and
            its own colour — so you can see exactly who's on the line.
          </p>
        </div>
        <div className="lp-agent-grid">
          {AGENTS.map((a) => (
            <div key={a.id} className="lp-agent" style={{ ["--accent" as any]: a.accent }}>
              <div className="ic">{a.emoji}</div>
              <b>{a.name}</b>
              <p>{a.blurb}</p>
              <div className="handles">{a.handles}</div>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="lp-section" id="how">
        <div className="lp-section-head">
          <div className="lp-kicker">How it works</div>
          <h2>From question to grounded answer</h2>
          <p>Four steps run on every message — often in under a couple of seconds.</p>
        </div>
        <div className="lp-steps">
          {STEPS.map((s, i) => (
            <div key={s.t} className="lp-step">
              <div className="num">{i + 1}</div>
              <b>{s.t}</b>
              <p>{s.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="lp-section">
        <div className="lp-section-head">
          <div className="lp-kicker">Why it's different</div>
          <h2>Built like production support AI</h2>
        </div>
        <div className="lp-feat-grid">
          {FEATURES.map((f) => (
            <div key={f.t} className="lp-feat">
              <div className="fic">
                <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  {f.icon}
                </svg>
              </div>
              <b>{f.t}</b>
              <p>{f.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Stack */}
      <section className="lp-section">
        <div className="lp-stack">
          <span className="lbl">Built with</span>
          <span className="lp-chip">FastAPI</span>
          <span className="lp-chip">Next.js 14</span>
          <span className="lp-chip">OpenRouter</span>
          <span className="lp-chip">Gemini 2.5 Flash Lite</span>
          <span className="lp-chip">MiniLM + FAISS</span>
          <span className="lp-chip">SQLite</span>
        </div>
      </section>

      {/* Final CTA */}
      <section className="lp-section">
        <div className="lp-final">
          <h2>See the agents light up</h2>
          <p>Ask one question and watch the right specialists take the call.</p>
          <Link href="/chat" className="lp-cta">
            Open the live demo →
          </Link>
        </div>
      </section>

      <footer className="lp-foot">
        <span>TechMart Electronics · Support Switchboard</span>
        <span>A multi-agent RAG assistant on OpenRouter</span>
        <div style={{ display: "flex", gap: "16px", marginTop: "8px" }}>
          <Link href="/privacy">Privacy Policy</Link>
          <Link href="/terms">Terms & Conditions</Link>
        </div>
      </footer>
    </div>
  );
}
