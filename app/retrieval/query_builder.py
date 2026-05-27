import re

BOOST_TERMS: dict[str, list[str]] = {
    "leadership": ["opq", "leadership", "executive", "personality"],
    "cxo": ["opq", "leadership", "executive"],
    "director": ["opq", "leadership", "executive"],
    "sales": ["sales", "opq", "global skills", "transformation"],
    "graduate": ["graduate", "verify", "scenarios", "gsa"],
    "contact": ["contact center", "svar", "customer service", "simulation"],
    "call center": ["contact center", "svar", "customer service"],
    "java": ["java", "spring", "sql", "verify"],
    "rust": ["coding", "linux", "networking", "verify"],
    "engineer": ["verify", "opq", "knowledge"],
    "financial": ["numerical", "financial", "statistics", "graduate"],
    "safety": ["safety", "dependability", "dsi", "workplace health"],
    "plant": ["safety", "dependability", "manufacturing"],
    "hipaa": ["hipaa", "medical", "dependability", "opq", "word"],
    "excel": ["excel", "word", "microsoft"],
    "word": ["word", "excel", "microsoft"],
    "personality": ["opq", "personality"],
    "cognitive": ["verify", "ability", "aptitude"],
    "situational": ["scenarios", "situational", "judgment", "graduate"],
    "bilingual": ["spanish", "language", "opq", "dependability"],
    "admin": ["excel", "word", "opq", "administrative"],
}


def expand_query(text: str) -> str:
    lower = text.lower()
    extras: list[str] = []
    for trigger, terms in BOOST_TERMS.items():
        if trigger in lower:
            extras.extend(terms)
    if extras:
        return f"{text} {' '.join(sorted(set(extras)))}"
    return text


def extract_skill_terms(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9+#.]+", text.lower()))
    known = {
        "java", "spring", "sql", "aws", "docker", "rust", "angular", "python",
        "excel", "word", "hipaa", "sales", "graduate", "leadership", "personality",
        "cognitive", "numerical", "safety", "contact", "center", "spanish", "english",
    }
    return tokens & known
