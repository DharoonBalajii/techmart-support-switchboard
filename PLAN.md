# Multi-Agent AI Customer Support Assistant — Implementation Plan (OpenRouter Edition)

A capstone build of a multi-agent customer-support assistant using **RAG + LLMs**, adapted to run entirely on a **single OpenRouter API key with a cheap model**. This document is the plan — no code is written yet.

---

## 0. The one change that drives everything: OpenRouter

OpenRouter is an OpenAI-compatible gateway. You keep **one** API key and can switch models by changing a string. This replaces "use OpenAI / Gemini / Llama" from the original brief.

- **Base URL:** `https://openrouter.ai/api/v1`
- **SDK:** the official `openai` Python SDK — just point `base_url` at OpenRouter and pass your OpenRouter key.
- **Only the chat/generation calls go to OpenRouter.** Embeddings stay **local and free** (see §3), so your running cost is essentially just the LLM completions.

```python
# backend: one shared client, used by every agent
from openai import OpenAI
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_headers={  # optional, for OpenRouter analytics/ranking
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Multi-Agent Support AI",
    },
)
resp = client.chat.completions.create(
    model=os.environ["OPENROUTER_MODEL"],   # e.g. google/gemini-2.5-flash-lite
    messages=[...],
    temperature=0.2,
)
```

### Cheap model choice (pick via env, no code change to switch)

| Role | Model | Why | Rough cost |
|---|---|---|---|
| **Primary (recommended)** | `google/gemini-2.5-flash-lite` | Fast, cheap, strong at routing + RAG answers, big context | ~$0.10 / ~$0.40 per 1M in/out tokens |
| Cheapest paid | `mistralai/mistral-small-24b-instruct-2501` | Even cheaper, fine for intent detection | ~$0.08 per 1M |
| Solid alt | `openai/gpt-4o-mini` | Reliable, well-documented | ~$0.15 / ~$0.60 per 1M |
| **Free fallback** | `meta-llama/llama-3.3-70b-instruct:free` or `deepseek/deepseek-chat` (check current free list) | $0 for demos; rate-limited | free |

> Prices drift — confirm on the OpenRouter models page before submitting. Strategy: **Gemini 2.0 Flash for real answers, a `:free` model as a fallback for the demo** so you never get rate-limited during your presentation. Both are just env-var swaps.

**Cost estimate for the whole project:** a full dev + testing + demo cycle (a few thousand chat turns, ~1–2k tokens each) lands around **$1–3 total** on Gemini 2.0 Flash, or **$0** if you demo on a free model. Embeddings add nothing (local).

---

## 1. Architecture (unchanged from brief, mapped to this stack)

```
Customer → Next.js chat UI
             │  (Axios → REST)
             ▼
        FastAPI backend
             │
     ┌───────┴────────┐
     ▼                ▼
Intent Detection   Conversation Memory (MongoDB)
     │
     ▼
 Agent Router ──► one or more specialized agents
     │            (Billing / Technical / Product / Complaint / FAQ)
     ▼
 RAG retrieval  ── local embeddings (MiniLM) → FAISS → company docs
     │
     ▼
 Response Aggregator → final answer  (all LLM calls via OpenRouter)
```

Every box labeled "LLM" in the original diagram = **one OpenRouter call**. The router itself is one small classification call; each agent is one RAG-grounded generation call.

---

## 2. Technology stack (finalized)

| Layer | Choice | Note |
|---|---|---|
| Frontend | **Next.js + React + Tailwind + Axios** | as brief |
| Backend | **Python FastAPI + Uvicorn** | as brief (recommended option) |
| LLM | **OpenRouter** (`openai` SDK, OpenAI-compatible) | the key adaptation |
| Embeddings | **`sentence-transformers/all-MiniLM-L6-v2`, run locally** | free, offline, no API cost |
| Vector DB | **FAISS** (local file index) | simplest; ChromaDB is a drop-in alt |
| Database | **MongoDB** (Atlas free tier) | sessions + conversation history. *SQLite is a fine simpler substitute if you want zero infra.* |
| Orchestration | plain Python functions (optionally **LangGraph** later) | start without a framework to actually learn the flow |
| Deploy | Vercel (frontend) + Render/Railway (backend) + MongoDB Atlas | as brief |

**Why local embeddings instead of an embeddings API:** OpenRouter focuses on chat/completions, not embeddings. Running MiniLM locally (a ~90 MB model) keeps RAG completely free and offline, and is the standard, defensible capstone choice.

---

## 3. RAG pipeline (build once, reuse for every agent)

**Ingestion (offline script, run when docs change):**
1. Load PDFs from `knowledge_base/` (PyPDF).
2. Chunk: ~500–800 chars, ~100 overlap.
3. Embed each chunk with MiniLM (local).
4. Store vectors + text + metadata (source file, agent-domain tag) in a FAISS index on disk.

**Query time (per request):**
1. Embed the user question with MiniLM.
2. FAISS top-k (k=4) similarity search, optionally filtered by the routed agent's domain tag.
3. Build a grounded prompt: `system role + retrieved context + conversation history + user question`.
4. One OpenRouter completion → answer, with a "say you don't know / escalate" instruction to reduce hallucination.

**Tag chunks by domain** (billing / technical / product / complaint / faq) at ingestion so the router can narrow retrieval to the right agent's documents.

---

## 4. The agents (this is the "multi-agent" grade weight — 20 pts)

- **Intent Detection Agent** — one cheap OpenRouter call that classifies the query into `{billing, refund, product, technical, complaint, faq, general}`. Return **structured JSON** (use a strict system prompt / JSON mode) so the router can parse it reliably.
- **Agent Router** — pure Python. Maps intent(s) → agent(s). Handles the **multi-agent case** from the brief (e.g. *"I paid yesterday but Premium is still locked"* → Billing **and** Technical). This is what separates the project from a plain chatbot — make routing explicit and logged.
- **5 Specialized Agents** — Billing, Technical, Product, Complaint, FAQ. Each = a distinct **system prompt persona** + RAG retrieval scoped to its domain docs + one OpenRouter call. They share the RAG pipeline and the OpenRouter client; only the prompt and doc-filter differ.
- **Response Aggregator** — when multiple agents fire, merge their answers into one coherent reply (either concatenate with headers, or a final "combine these into one answer" OpenRouter call).
- **Escalation** — if retrieval confidence is low or the complaint agent detects strong dissatisfaction → return an escalation message / create a ticket stub.

---

## 5. Folder structure

```
cv-support-ai/
├── PLAN.md                     ← this file
├── backend/
│   ├── main.py                 FastAPI app + routes
│   ├── core/
│   │   ├── openrouter.py       shared OpenRouter client + call helper
│   │   └── config.py           env loading (key, model, db uri)
│   ├── agents/
│   │   ├── intent.py           intent detection
│   │   ├── router.py           routing logic (single + multi agent)
│   │   ├── billing.py technical.py product.py complaint.py faq.py
│   │   └── aggregator.py
│   ├── rag/
│   │   ├── ingest.py           PDFs → chunks → embeddings → FAISS
│   │   ├── retrieve.py         query-time retrieval
│   │   └── embeddings.py       MiniLM wrapper (local)
│   ├── vectorstore/            FAISS index files (gitignored)
│   ├── database/
│   │   ├── mongo.py            connection
│   │   └── memory.py           save/load conversation by session_id
│   ├── models/                 pydantic request/response schemas
│   ├── requirements.txt
│   └── .env.example            OPENROUTER_API_KEY=, OPENROUTER_MODEL=, MONGODB_URI=
├── frontend/                   Next.js app (chat UI, auth, history)
├── knowledge_base/             fictional company PDFs (see §6)
└── datasets/                   optional public datasets (see §7)
```

---

## 6. Company knowledge base

Invent a fictional company (brief suggests **TechMart Electronics**) and write these as short PDFs:
`FAQ.pdf, RefundPolicy.pdf, ShippingPolicy.pdf, Warranty.pdf, Pricing.pdf, Products.pdf, InstallationGuide.pdf, UserManual.pdf`.

Tag each to a domain at ingestion (Pricing/Products → product agent, RefundPolicy → billing, InstallationGuide/UserManual → technical, etc.). These PDFs *are* the RAG corpus — keep them realistic but small (1–2 pages each) so retrieval is easy to demo.

---

## 7. Optional public datasets (for evaluation / bonus)

- **Banking77** (HF) — great to benchmark the **intent-detection** agent's accuracy.
- **CFPB Consumer Complaint DB** — realistic complaint text for the complaint agent.
- **SQuAD / MS MARCO** — QA pairs to evaluate RAG retrieval quality.
- **DailyDialog** — multi-turn conversation realism.

Use these only to *measure* (accuracy, retrieval hit-rate); the live product answers from your own knowledge base.

---

## 8. Build order (phased — each phase is demoable)

**Phase 1 — RAG core (do this first, it's 20 pts).**
Write the KB PDFs → `ingest.py` → `retrieve.py`. Prove: ask a question in a script, get a grounded answer via one OpenRouter call. No UI yet.

**Phase 2 — Agents + router.**
Intent agent (JSON out) → router → 5 agent personas → aggregator. Test the multi-agent example from the brief end to end in a script.

**Phase 3 — FastAPI layer.**
`POST /chat` (session_id, message) → runs the pipeline → returns answer + which agents fired. `POST /auth/*`, session management, conversation memory in MongoDB.

**Phase 4 — Next.js frontend.**
Login/register, chat window with history + typing indicator, Axios to backend.

**Phase 5 — Test & evaluate.**
Routing accuracy (Banking77), retrieval quality (SQuAD-style), response time, edge cases (empty retrieval → escalation).

**Phase 6 — Deploy.**
Frontend → Vercel, backend → Render/Railway, MongoDB Atlas. Put `OPENROUTER_API_KEY` in the backend host's env vars — **never** ship it to the frontend.

---

## 9. Grade-alignment checklist (100 pts from the brief)

| Component | Marks | Where it's earned here |
|---|---|---|
| Frontend Design | 10 | Phase 4 |
| Backend APIs | 15 | Phase 3 |
| Multi-Agent Architecture | 20 | Phase 2 — explicit router + multi-agent routing + logging |
| RAG Implementation | 20 | Phase 1 — MiniLM + FAISS + grounded prompts |
| LLM Integration | 15 | OpenRouter client, per-agent prompts, JSON intent |
| Database Design | 10 | MongoDB sessions + conversation memory |
| Documentation & Deployment | 10 | README + this plan + Phase 6 |

---

## 10. Security & submission notes

- API key lives **only** in the backend `.env` / host env. Add `.env` and `vectorstore/` to `.gitignore`. Commit `.env.example` with empty values.
- Deliverables to submit: source (frontend+backend), project report PDF, README with setup, **demo video (compulsory)**, KB PDFs, deployment links.
- For a safe live demo, set `OPENROUTER_MODEL` to a `:free` model so rate limits/cost can't break your presentation; switch back to Gemini 2.0 Flash for quality when needed.

---

### Next step
When you're ready, I can scaffold **Phase 1 (the RAG core + OpenRouter client)** first — it's the highest-weighted, most self-contained piece and proves the whole approach with one script.
