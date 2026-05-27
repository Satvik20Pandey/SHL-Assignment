from app.agent.orchestrator import AgentOrchestrator
from app.catalog.loader import load_catalog_from_file
from app.config import settings
from app.retrieval.index import build_search_index

_agent: AgentOrchestrator | None = None


def get_agent() -> AgentOrchestrator:
    global _agent
    if _agent is None:
        _agent = _init_agent()
    return _agent


def _init_agent() -> AgentOrchestrator:
    if not settings.catalog_path.exists():
        raise FileNotFoundError(f"Catalog not found: {settings.catalog_path}")
    catalog = load_catalog_from_file(settings.catalog_path)
    by_url: dict = {}
    for item in catalog:
        by_url[item.url.rstrip("/")] = item
        by_url[item.url] = item
    search = build_search_index(catalog, settings.index_cache_dir)
    return AgentOrchestrator(catalog, search, by_url)
