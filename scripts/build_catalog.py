"""Download SHL catalog, sanitize, filter pre-packaged bundles, save to data/catalog.json."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.catalog.loader import load_catalog, load_raw_json, parse_catalog_records, save_catalog
from app.config import settings


def main() -> None:
    print(f"Fetching catalog from {settings.catalog_url}")
    records = load_raw_json(settings.catalog_url)
    items = parse_catalog_records(records)
    out = settings.catalog_path
    save_catalog(items, out)
    print(f"Saved {len(items)} individual test solutions to {out}")


if __name__ == "__main__":
    main()
