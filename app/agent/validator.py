from app.api.schemas import Recommendation
from app.catalog.models import CatalogItem


def validate_recommendations(
    urls: list[str],
    catalog_by_url: dict[str, CatalogItem],
    max_items: int = 10,
) -> list[Recommendation]:
    seen: set[str] = set()
    out: list[Recommendation] = []
    for url in urls:
        norm = url.strip().rstrip("/")
        item = catalog_by_url.get(norm) or catalog_by_url.get(norm + "/")
        if not item or item.url in seen:
            continue
        seen.add(item.url)
        out.append(
            Recommendation(
                name=item.name,
                url=item.url,
                test_type=item.test_type,
            )
        )
        if len(out) >= max_items:
            break
    return out
