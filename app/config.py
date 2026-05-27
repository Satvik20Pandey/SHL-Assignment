from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    catalog_path: Path = ROOT / "data" / "catalog.json"
    catalog_url: str = (
        "https://tcp-us-prod-rnd.shl.com/voiceRater/shl-ai-hiring/shl_product_catalog.json"
    )
    index_cache_dir: Path = ROOT / "data" / "index_cache"
    retrieval_top_k: int = 25
    max_recommendations: int = 10
    max_turns: int = 8
    llm_max_tokens: int = 1200


settings = Settings()
