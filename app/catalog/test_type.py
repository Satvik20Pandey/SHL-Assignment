KEY_MAP = {
    "Ability & Aptitude": "A",
    "Biodata & Situational Judgment": "B",
    "Competencies": "C",
    "Development & 360": "D",
    "Assessment Exercises": "E",
    "Knowledge & Skills": "K",
    "Personality & Behavior": "P",
    "Simulations": "S",
}


def derive_test_type(keys: list[str]) -> str:
    if "Development & 360" in keys:
        return "D"
    letters: list[str] = []
    for key in keys:
        letter = KEY_MAP.get(key)
        if letter and letter not in letters:
            letters.append(letter)
    return ",".join(letters)
