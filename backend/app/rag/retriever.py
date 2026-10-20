import json
import os
from typing import List
from rank_bm25 import BM25Okapi
from pydantic import BaseModel
from app.schemas.state import FilingsEvidenceItem


class DocumentChunk(BaseModel):
    doc_id: str
    page: int
    section: str
    text: str


class HybridFilingsRetriever:
    def __init__(self, corpus_path: str = ""):
        if not corpus_path:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            candidate = os.path.join(base_dir, "data", "filings")
            if os.path.exists(candidate):
                corpus_path = candidate
            elif os.path.exists("backend/data/filings"):
                corpus_path = "backend/data/filings"
            else:
                corpus_path = "data/filings"

        self.corpus_path = corpus_path
        self.chunks: List[DocumentChunk] = []
        self.bm25: BM25Okapi | None = None
        self._load_corpus()

    def _load_corpus(self):
        if not os.path.exists(self.corpus_path):
            return

        for root, _, files in os.walk(self.corpus_path):
            for file in files:
                if file.endswith(".json"):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            raw_docs = json.load(f)
                            for d in raw_docs:
                                self.chunks.append(
                                    DocumentChunk(
                                        doc_id=d["doc_id"],
                                        page=d["page"],
                                        section=d["section"],
                                        text=d["text"],
                                    )
                                )
                    except Exception as e:
                        print(f"Error loading {full_path}: {e}")

        if self.chunks:
            tokenized_corpus = [c.text.lower().split() for c in self.chunks]
            self.bm25 = BM25Okapi(tokenized_corpus)

    def retrieve(self, query: str, top_k: int = 2) -> List[FilingsEvidenceItem]:
        if not self.chunks or not self.bm25:
            return []

        tokens = query.lower().split()
        scores = self.bm25.get_scores(tokens)

        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results: List[FilingsEvidenceItem] = []
        for idx in ranked_indices:
            chunk = self.chunks[idx]
            relevance = float(scores[idx]) if scores[idx] > 0 else 0.5
            results.append(
                FilingsEvidenceItem(
                    doc_id=chunk.doc_id,
                    page=chunk.page,
                    section=chunk.section,
                    excerpt=chunk.text,
                    relevance=round(relevance, 2),
                    source_url=f"data/filings/{chunk.doc_id}#page={chunk.page}",
                )
            )
        return results
