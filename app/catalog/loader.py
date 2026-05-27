import json
from pathlib import Path
from urllib.request import urlopen

from app.catalog.models import CatalogItem
from app.catalog.test_type import derive_test_type


def fix_embedded_newlines(raw: str) -> str:
    out: list[str] = []
    in_string = False
    escape = False
    for ch in raw:
        if escape:
            out.append(ch)
            escape = False
            continue
        if ch == "\\":
            out.append(ch)
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            continue
        if in_string and ch in "\n\r":
            out.append(" ")
            continue
        out.append(ch)
    return "".join(out)


def is_prepackaged(name: str) -> bool:
    return (
        name.endswith(" Solution")
        or " Short Form" in name
        or "Job Focused Assessment" in name
    )


def parse_catalog_records(records: list[dict]) -> list[CatalogItem]:
    items: list[CatalogItem] = []
    for row in records:
        name = (row.get("name") or "").strip()
        if not name or is_prepackaged(name):
            continue
        link = (row.get("link") or "").strip()
        if not link.startswith("https://www.shl.com/"):
            continue
        keys = row.get("keys") or []
        items.append(
            CatalogItem(
                entity_id=str(row.get("entity_id", "")),
                name=name,
                url=link,
                description=(row.get("description") or "").strip(),
                keys=keys,
                job_levels=row.get("job_levels") or [],
                languages=row.get("languages") or [],
                duration=(row.get("duration") or "").strip(),
                remote=(row.get("remote") or "").strip(),
                adaptive=(row.get("adaptive") or "").strip(),
                test_type=derive_test_type(keys),
            )
        )
    return items


def load_raw_json(source: str | Path) -> list[dict]:
    if isinstance(source, Path):
        raw = source.read_text(encoding="utf-8")
    else:
        with urlopen(str(source), timeout=90) as resp:
            raw = resp.read().decode("utf-8")
    start = raw.find("[")
    if start < 0:
        raise ValueError("Catalog JSON must be an array")
    return json.loads(fix_embedded_newlines(raw[start:]))


def load_catalog(source: str | Path | None = None) -> list[CatalogItem]:
    records = load_raw_json(source) if source else []
    return parse_catalog_records(records)


def save_catalog(items: list[CatalogItem], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "entity_id": i.entity_id,
            "name": i.name,
            "link": i.url,
            "description": i.description,
            "keys": i.keys,
            "job_levels": i.job_levels,
            "languages": i.languages,
            "duration": i.duration,
            "remote": i.remote,
            "adaptive": i.adaptive,
        }
        for i in items
    ]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_catalog_from_file(path: Path) -> list[CatalogItem]:
    records = load_raw_json(path)
    return parse_catalog_records(records)
