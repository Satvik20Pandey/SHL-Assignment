"""Offline eval: retrieval recall on sample gold URLs (no LLM)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.catalog.loader import load_catalog_from_file
from app.config import settings
from app.retrieval.index import build_search_index
from app.retrieval.query_builder import expand_query
from eval.parse_samples import load_all_samples
from eval.recall import mean_recall_at_k, recall_at_k


def main():
    catalog = load_catalog_from_file(settings.catalog_path)
    search = build_search_index(catalog)
    results = []
    for sample in load_all_samples():
        query = expand_query(" ".join(sample["user_messages"]))
        recs = [c.url for c in search.search(query, top_k=10)]
        score = recall_at_k(recs, sample["gold_urls"], 10)
        results.append((recs, sample["gold_urls"]))
        print(f"{sample['id']}: retrieval Recall@10 = {score:.2f}")
    print(f"Mean retrieval Recall@10: {mean_recall_at_k(results, 10):.3f}")


if __name__ == "__main__":
    main()
