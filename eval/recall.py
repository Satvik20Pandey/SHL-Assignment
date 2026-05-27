def recall_at_k(recommended_urls: list[str], gold_urls: list[str], k: int = 10) -> float:
    if not gold_urls:
        return 1.0
    top = {u.rstrip("/") for u in recommended_urls[:k]}
    gold = {u.rstrip("/") for u in gold_urls}
    hits = len(top & gold)
    return hits / len(gold)


def mean_recall_at_k(results: list[tuple[list[str], list[str]]], k: int = 10) -> float:
    if not results:
        return 0.0
    return sum(recall_at_k(rec, gold, k) for rec, gold in results) / len(results)
