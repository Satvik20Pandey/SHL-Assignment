def probe_no_rec_on_vague_turn1(turns: list[dict]) -> bool:
    if not turns:
        return False
    first = turns[0]
    return first.get("no_recommendations") or not first.get("urls")


def probe_urls_in_catalog(urls: list[str], catalog_urls: set[str]) -> bool:
    catalog = {u.rstrip("/") for u in catalog_urls}
    return all(u.rstrip("/") in catalog for u in urls)


def probe_refusal_on_legal(text: str) -> bool:
    t = text.lower()
    return "legal" in t or "compliance" in t or "counsel" in t
