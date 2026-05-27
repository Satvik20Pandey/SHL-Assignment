"""Pre-build FAISS index and embedding model for low-memory production startup."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.catalog.loader import load_catalog_from_file
from app.config import settings
from app.retrieval.index import build_search_index


def main() -> None:
    catalog = load_catalog_from_file(settings.catalog_path)
    cache_dir = settings.index_cache_dir
    print(f"Building index cache for {len(catalog)} items -> {cache_dir}")
    build_search_index(catalog, cache_dir)
    print("Index cache ready.")


if __name__ == "__main__":
    main()
