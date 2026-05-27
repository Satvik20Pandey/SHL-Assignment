from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogItem:
    entity_id: str
    name: str
    url: str
    description: str
    keys: list[str]
    job_levels: list[str]
    languages: list[str]
    duration: str
    remote: str
    adaptive: str
    test_type: str

    def search_text(self) -> str:
        parts = [
            self.name,
            self.description,
            " ".join(self.keys),
            " ".join(self.job_levels),
            " ".join(self.languages),
        ]
        return " ".join(p for p in parts if p)
