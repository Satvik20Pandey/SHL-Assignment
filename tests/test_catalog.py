from app.catalog.test_type import derive_test_type


def test_development_report_type():
    assert derive_test_type(["Development & 360", "Personality & Behavior"]) == "D"


def test_multi_key_type():
    assert derive_test_type(["Competencies", "Knowledge & Skills"]) == "C,K"


def test_single_ability():
    assert derive_test_type(["Ability & Aptitude"]) == "A"
