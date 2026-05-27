import json
from pathlib import Path

import faiss
import numpy as np

from app.catalog.models import CatalogItem
from app.retrieval.search import CatalogSearch

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
ENTITY_ORDER_FILE = "entity_order.json"
FAISS_FILE = "faiss.index"
MODEL_DIR = "embedding_model"


def _encode(model, texts: list[str]) -> np.ndarray:
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(embeddings, dtype=np.float32)


def build_search_index(items: list[CatalogItem], cache_dir: Path | None = None) -> CatalogSearch:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL_NAME)
    texts = [item.search_text() for item in items]
    embeddings = _encode(model, texts)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    if cache_dir:
        save_index_cache(items, index, model, cache_dir)
    return CatalogSearch(items, index, model)


def save_index_cache(items: list[CatalogItem], index, model, cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(cache_dir / FAISS_FILE))
    order = [item.entity_id for item in items]
    (cache_dir / ENTITY_ORDER_FILE).write_text(json.dumps(order), encoding="utf-8")
    model.save(str(cache_dir / MODEL_DIR))


def load_search_index(items: list[CatalogItem], cache_dir: Path) -> CatalogSearch:
    from sentence_transformers import SentenceTransformer

    index_path = cache_dir / FAISS_FILE
    order_path = cache_dir / ENTITY_ORDER_FILE
    model_path = cache_dir / MODEL_DIR
    if not (index_path.exists() and order_path.exists() and model_path.exists()):
        raise FileNotFoundError(f"Index cache incomplete in {cache_dir}")

    by_id = {item.entity_id: item for item in items}
    order = json.loads(order_path.read_text(encoding="utf-8"))
    ordered_items = [by_id[eid] for eid in order]

    index = faiss.read_index(str(index_path))
    model = SentenceTransformer(str(model_path))
    return CatalogSearch(ordered_items, index, model)


def get_or_build_search_index(items: list[CatalogItem], cache_dir: Path | None) -> CatalogSearch:
    if cache_dir and (cache_dir / FAISS_FILE).exists():
        return load_search_index(items, cache_dir)
    return build_search_index(items, cache_dir)
