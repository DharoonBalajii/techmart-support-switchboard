"""RAG knowledge base: load company docs, chunk, embed, and retrieve.

Primary path uses sentence-transformers (MiniLM) + FAISS for semantic search.
If those libraries are unavailable, it falls back to a lightweight lexical
scorer so the server still runs and the demo still works.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from core.config import get_settings

# Map each knowledge-base file to the agent domain it serves. Keys are
# normalised (lower-case, no separators) so both "refund_policy.md" and
# "RefundPolicy.pdf" resolve to the same domain.
DOMAIN_BY_FILE = {
    "faq": "faq",
    "refundpolicy": "billing",
    "pricing": "product",
    "products": "product",
    "shippingpolicy": "faq",
    "warranty": "product",
    "installationguide": "technical",
    "usermanual": "technical",
}


@dataclass
class Chunk:
    document: str
    domain: str
    text: str


@dataclass
class Retrieved:
    document: str
    snippet: str
    score: float


def _domain_for(filename: str) -> str:
    stem = Path(filename).stem.lower().replace("_", "").replace("-", "").replace(" ", "")
    return DOMAIN_BY_FILE.get(stem, "faq")


def _read_document(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception:
            return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _chunk(text: str, size: int = 700, overlap: int = 120) -> list[str]:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    # Prefer splitting on blank lines, then pack paragraphs up to `size`.
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paras:
        if len(buf) + len(para) + 2 <= size:
            buf = f"{buf}\n\n{para}".strip()
        else:
            if buf:
                chunks.append(buf)
            if len(para) <= size:
                buf = para
            else:
                for i in range(0, len(para), size - overlap):
                    chunks.append(para[i : i + size])
                buf = ""
    if buf:
        chunks.append(buf)
    return chunks or ([text] if text else [])


_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class KnowledgeBase:
    """Loads and indexes the knowledge base once, then answers retrievals."""

    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self._index = None  # FAISS index for vector database
        self._model = None
        self._df: Counter = Counter()  # doc-frequency for lexical fallback
        self.backend = "lexical"
        self._load()
        self._build_index()

    # ---- loading -------------------------------------------------------
    def _load(self) -> None:
        kb_dir = get_settings().knowledge_base_dir
        if not kb_dir.exists():
            return
        for path in sorted(kb_dir.iterdir()):
            if path.suffix.lower() not in {".md", ".txt", ".pdf"}:
                continue
            raw = _read_document(path)
            domain = _domain_for(path.name)
            for piece in _chunk(raw):
                self.chunks.append(Chunk(document=path.stem, domain=domain, text=piece))

    def _build_index(self) -> None:
        if not self.chunks:
            return
        try:
            from sentence_transformers import SentenceTransformer
            import faiss

            self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            vecs = self._model.encode(
                [c.text for c in self.chunks],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            # Create a FAISS vector database index using inner product (cosine similarity)
            self._index = faiss.IndexFlatIP(vecs.shape[1])
            self._index.add(vecs)
            self.backend = "semantic (MiniLM + FAISS)"
        except Exception as e:
            print("Falling back to lexical search:", e)
            # Lexical fallback: precompute document frequencies for tf-idf.
            for chunk in self.chunks:
                for term in set(_tokens(chunk.text)):
                    self._df[term] += 1
            self.backend = "lexical (tf-idf fallback)"

    # ---- retrieval -----------------------------------------------------
    def retrieve(self, query: str, k: int = 4, domain: str | None = None) -> list[Retrieved]:
        if not self.chunks:
            return []
        candidates = [
            (i, c) for i, c in enumerate(self.chunks) if domain is None or c.domain == domain
        ]
        if not candidates:  # domain had no docs — search everything
            candidates = list(enumerate(self.chunks))

        if self._index is not None and self._model is not None:
            scored = self._semantic(query, candidates)
        else:
            scored = self._lexical(query, candidates)

        scored.sort(key=lambda t: t[1], reverse=True)
        out: list[Retrieved] = []
        for idx, score in scored[:k]:
            if score <= 0:
                continue
            chunk = self.chunks[idx]
            out.append(
                Retrieved(
                    document=chunk.document,
                    snippet=chunk.text[:280].strip(),
                    score=round(float(score), 3),
                )
            )
        return out

    def _semantic(self, query, candidates):
        qv = self._model.encode([query], normalize_embeddings=True)[0].reshape(1, -1)
        
        # Search the entire FAISS index
        k_search = len(self.chunks)
        sims, idxs = self._index.search(qv, k_search)
        
        candidate_idxs = {i for i, _ in candidates}
        scored = []
        for sim, idx in zip(sims[0], idxs[0]):
            if idx in candidate_idxs:
                scored.append((idx, float(sim)))
                
        return scored

    def _lexical(self, query, candidates):
        q_terms = _tokens(query)
        n_docs = len(self.chunks)
        scored = []
        for idx, chunk in candidates:
            terms = _tokens(chunk.text)
            tf = Counter(terms)
            score = 0.0
            for term in q_terms:
                if term in tf:
                    idf = math.log(1 + n_docs / (1 + self._df.get(term, 0)))
                    score += (tf[term] / (len(terms) or 1)) * idf
            scored.append((idx, score))
        return scored


_kb: KnowledgeBase | None = None


def get_kb() -> KnowledgeBase:
    global _kb
    if _kb is None:
        _kb = KnowledgeBase()
    return _kb
