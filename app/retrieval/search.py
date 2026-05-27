import re

import numpy as np

from app.catalog.models import CatalogItem


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9+#.]+", text.lower()) if len(t) > 2}


class CatalogSearch:
    def __init__(self, items: list[CatalogItem], faiss_index, model):
        self.items = items
        self.index = faiss_index
        self.model = model
        self._keyword_docs = [_tokenize(item.search_text()) for item in items]

    def search(self, query: str, top_k: int = 25) -> list[CatalogItem]:
        if not self.items:
            return []
        query_tokens = _tokenize(query)
        query_emb = self.model.encode([query], normalize_embeddings=True)
        vec = np.asarray(query_emb, dtype=np.float32)
        k = min(top_k * 2, len(self.items))
        scores, indices = self.index.search(vec, k)
        ranked: list[tuple[float, int]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            s = float(score)
            if query_tokens:
                s += 0.08 * len(query_tokens & self._keyword_docs[idx])
            ranked.append((s, int(idx)))
        ranked.sort(key=lambda x: x[0], reverse=True)
        seen: set[int] = set()
        out: list[CatalogItem] = []
        for _, idx in ranked:
            if idx in seen:
                continue
            seen.add(idx)
            out.append(self.items[idx])
            if len(out) >= top_k:
                break
        return out
