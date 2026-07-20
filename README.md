# TechMart Support Switchboard

A **multi-agent AI customer-support assistant** with RAG, built on a single
**OpenRouter** API key + a cheap model. A central orchestrator detects intent,
routes each question to one or more specialist agents (Billing, Technical,
Product, Complaint, FAQ), grounds their answers in the company knowledge base via
retrieval, and shows the whole routing decision live in the UI.

> Full architecture and rationale: [PLAN.md](PLAN.md).

## What makes it different from a chatbot
- **Real multi-agent routing** — one message can invoke several agents
  (e.g. *"I paid but Premium is still locked"* → Billing **and** Technical).
- **RAG-grounded** — answers cite the exact company documents they came from.
- **Visible orchestration** — the UI is a "switchboard": agents light up in their
  own colour as they respond, with source chips and latency shown per answer.
- **Runs with zero setup** — SQLite for memory, lexical retrieval fallback, and a
  demo mode that works even before you add an API key.

## Stack
| Layer | Tech |
|-------|------|
| Frontend | Next.js 14 (App Router) + hand-crafted CSS |
| Backend | FastAPI + Uvicorn |
| LLM | OpenRouter (OpenAI-compatible), default `google/gemini-2.5-flash-lite` |
| Embeddings | `all-MiniLM-L6-v2` (local) → FAISS, with a tf-idf fallback |
| Memory | SQLite |

## Quick start

### 1. Backend
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # installs RAG deps (MiniLM + FAISS)
cp .env.example .env                      # then paste your OpenRouter key
uvicorn main:app --reload --port 8000
```
- Get a key at https://openrouter.ai/keys and set `OPENROUTER_API_KEY` in `.env`.
- No key yet? It still runs in **demo mode** (routing + retrieval work; answers are
  stubbed). For a **free** live demo, set `OPENROUTER_MODEL` to a `:free` model.
- Health check: http://localhost:8000/api/health

### 2. Frontend
```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```
`frontend/.env.local` points at `http://localhost:8000` by default.

## How it works (request lifecycle)
```
message → /api/chat
        → router.route()      intent + agent(s)   (LLM JSON, keyword fallback)
        → knowledge.retrieve() top-k chunks per agent domain   (RAG)
        → orchestrator: each agent answers, grounded in its sources
        → aggregator merges answers → response (+ agents, sources, latency)
        → SQLite stores the turn (conversation memory)
```

## API
| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/health` | model, retrieval backend, docs indexed |
| GET | `/api/agents` | agent roster (name, colour, blurb) |
| POST | `/api/chat` | `{session_id, message}` → answer + routing trace |
| GET | `/api/history/{session_id}` | conversation history |

## Knowledge base (brief §10)
Eight **PDFs** under [`knowledge_base/`](knowledge_base/) for the fictional
**TechMart Electronics** — `FAQ.pdf`, `RefundPolicy.pdf`, `ShippingPolicy.pdf`,
`Warranty.pdf`, `Pricing.pdf`, `Products.pdf`, `InstallationGuide.pdf`,
`UserManual.pdf`. These are the RAG corpus; each is tagged to an agent domain in
`backend/rag/knowledge.py`.

The editable Markdown sources live in `knowledge_base/_src/` (ignored by the
ingester). After editing a source, rebuild the PDFs:
```bash
pip install markdown xhtml2pdf
python3 knowledge_base/build_pdfs.py
```
The ingester reads `.pdf`, `.md`, and `.txt`, so you can drop in more of any.

## Public datasets (brief §9)
Real samples of CFPB complaints, Banking77, SQuAD v2, MS MARCO, and DailyDialog
live under [`datasets/`](datasets/) — see [datasets/README.md](datasets/README.md).
Re-fetch with `python3 datasets/download_datasets.py`.

## Swapping the model
Everything routes through `backend/core/openrouter.py`. Change one env var:
```
OPENROUTER_MODEL=openai/gpt-4o-mini            # or any OpenRouter model id
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free   # zero-cost demo
```

## Cloud Deployment

This capstone project is designed to be easily deployed to the cloud.

### Backend (Render.com)
The project includes a `render.yaml` configuration file for zero-touch deployment to [Render](https://render.com).
1. Create a Render account and connect your GitHub repository.
2. Go to **Blueprints** > **New Blueprint Instance** and select your repository.
3. Render will automatically read the `render.yaml` and provision the web service.
4. Go to the dashboard for your new service and set the `OPENROUTER_API_KEY` and `RESEND_API_KEY` environment variables.

### Frontend (Vercel)
The Next.js frontend is perfectly optimized for [Vercel](https://vercel.com).
1. Connect your repository to Vercel.
2. Set the **Root Directory** to `frontend`.
3. Add the `NEXT_PUBLIC_API_URL` environment variable and set it to your Render backend URL (e.g., `https://techmart-support-backend.onrender.com`).
4. Click **Deploy**.
