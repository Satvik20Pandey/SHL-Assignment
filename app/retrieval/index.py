from pathlib import Path

import faiss
import numpy as np

from app.catalog.models import CatalogItem
from app.retrieval.search import CatalogSearch


def build_search_index(items: list[CatalogItem], cache_dir: Path | None = None) -> CatalogSearch:
    from sentence_transformers import SentenceTransformer

    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    model = SentenceTransformer(model_name)
    texts = [item.search_text() for item in items]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    embeddings = np.asarray(embeddings, dtype=np.float32)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(cache_dir / "faiss.index"))
    return CatalogSearch(items, index, model)
