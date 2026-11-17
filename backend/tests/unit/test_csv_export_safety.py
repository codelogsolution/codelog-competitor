from app.api.v1.endpoints.battlecards import safe_csv_cell


def test_csv_formula_prefixes_are_escaped():
    assert safe_csv_cell("=HYPERLINK(\"https://evil.example\")").startswith("'=")
    assert safe_csv_cell(" +SUM(1,2)").startswith("' +")
    assert safe_csv_cell("@cmd").startswith("'@")


def test_normal_csv_values_are_unchanged():
    assert safe_csv_cell("Competitor overview") == "Competitor overview"
    assert safe_csv_cell("https://example.com") == "https://example.com"
