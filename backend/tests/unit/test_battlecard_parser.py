import pytest

from app.services.battlecard_service import BattlecardService


def valid_payload():
    return {
        "overview": "Evidence-backed overview",
        "positioning": "Not available in supplied evidence",
        "strengths": ["[Evidence 1] Public product page describes a feature."],
        "weaknesses": [],
        "product_gaps": [],
        "pricing": "Not available in supplied evidence",
        "opportunities": ["Consider reviewing this product area."],
        "threat_level": "Medium",
        "recommended_actions": ["Validate the finding with the product team."],
        "evidence_notes": ["[Evidence 1] https://example.com/product"],
    }


def test_parse_battlecard_plain_json():
    import json

    parsed = BattlecardService._parse_battlecard(json.dumps(valid_payload()))
    assert parsed.overview == "Evidence-backed overview"
    assert parsed.threat_level == "Medium"


def test_parse_battlecard_json_inside_markdown_fence():
    import json

    raw = "```json\n" + json.dumps(valid_payload()) + "\n```"
    parsed = BattlecardService._parse_battlecard(raw)
    assert parsed.recommended_actions


def test_parse_battlecard_rejects_invalid_schema():
    with pytest.raises(ValueError):
        BattlecardService._parse_battlecard('{"overview": "missing fields"}')
