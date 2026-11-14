from collections import defaultdict


def group_evidence_by_competitor(records: list[dict]) -> dict:
    grouped = defaultdict(list)

    for record in records:
        domain = str(record.get("domain", "")).strip().lower()

        if domain:
            grouped[domain].append(record)

    return dict(grouped)


def get_evidence_context(records: list[dict]) -> str:
    """Prepare traceable evidence context for LLM analysis."""

    lines = []

    for index, record in enumerate(records, start=1):
        lines.append(
            f"""
Evidence {index}
Competitor: {record.get('competitor_name', '')}
Signal: {record.get('signal_type', '')}
Category: {record.get('category', '')}
Product area: {record.get('product_area', '')}
Sentiment: {record.get('sentiment', '')}
Finding: {record.get('signal_text', '')}
Source: {record.get('source_url', '')}
Date: {record.get('signal_date', '')}
""".strip()
        )

    return "\n\n".join(lines)