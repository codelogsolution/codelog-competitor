
import json

from sqlalchemy.orm import Session

from app.ai.prompts.battlecard_prompt import BATTLECARD_SYSTEM_PROMPT
from app.ai.providers.claude_provider import ClaudeProvider
from app.ai.tools.evidence_tools import get_evidence_context
from app.models.evidence import Evidence
from app.repositories.battlecard_repository import BattlecardRepository
from app.schemas.battlecard import BattlecardContent


class BattlecardService:

    @staticmethod
    def _response_text(response) -> str:
        content = response.content
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
            return "\n".join(parts).strip()
        return str(content).strip()

    @staticmethod
    def _parse_battlecard(raw: str) -> BattlecardContent:
        """Parse a JSON object even if the model wraps it in code fences/text."""
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```json").removeprefix("```")
            if cleaned.rstrip().endswith("```"):
                cleaned = cleaned.rstrip()[:-3].strip()

        decoder = json.JSONDecoder()
        for index, character in enumerate(cleaned):
            if character != "{":
                continue
            try:
                payload, _ = decoder.raw_decode(cleaned[index:])
                if isinstance(payload, dict):
                    return BattlecardContent.model_validate(payload)
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
        raise ValueError("No valid battlecard JSON object found in model response.")

    @classmethod
    def _generate_content(cls, llm, competitor_name: str, domain: str, context: str):
        messages = [
            ("system", BATTLECARD_SYSTEM_PROMPT),
            (
                "human",
                f"Competitor: {competitor_name}\n"
                f"Domain: {domain}\n\n"
                f"Evidence:\n{context}",
            ),
        ]

        first_response = llm.invoke(messages)
        first_raw = cls._response_text(first_response)
        try:
            return cls._parse_battlecard(first_raw)
        except ValueError:
            # A single constrained repair attempt handles occasional prose,
            # Markdown fences, or malformed JSON without silently inventing data.
            repair_messages = [
                ("system", BATTLECARD_SYSTEM_PROMPT),
                (
                    "human",
                    "Your previous output was not valid JSON matching the required schema. "
                    "Return the complete corrected JSON object only. Do not add facts. "
                    "Use only the evidence below.\n\n"
                    f"Competitor: {competitor_name}\nDomain: {domain}\n"
                    f"Evidence:\n{context}\n\n"
                    f"Previous invalid output (for correction only):\n{first_raw[:6000]}",
                ),
            ]
            repaired_raw = cls._response_text(llm.invoke(repair_messages))
            try:
                return cls._parse_battlecard(repaired_raw)
            except ValueError as exc:
                raise ValueError(
                    "LLM returned incomplete or invalid battlecard JSON after one retry."
                ) from exc

    @classmethod
    def generate(cls, db: Session, competitor_name: str, domain: str):
        records = (
            db.query(Evidence)
            .filter(Evidence.domain == domain.lower())
            .all()
        )

        if not records:
            raise ValueError("No evidence available for this competitor.")

        evidence = [
            {
                "competitor_name": item.competitor_name,
                "signal_type": item.signal_type,
                "category": item.category,
                "product_area": item.product_area,
                "sentiment": item.sentiment,
                "signal_text": item.signal_text,
                "source_url": item.source_url,
                "signal_date": item.signal_date,
            }
            for item in records
        ]

        context = get_evidence_context(evidence)
        llm = ClaudeProvider().get_chat_model()
        content = cls._generate_content(llm, competitor_name, domain, context)
        urls = sorted({item.source_url for item in records})

        saved = BattlecardRepository.create(
            db,
            {
                "competitor_name": competitor_name,
                "domain": domain.lower(),
                "status": "pending_review",
                "content": content.model_dump_json(),
                "evidence_urls": json.dumps(urls),
            },
        )

        return {
            "id": saved.id,
            "competitor_name": saved.competitor_name,
            "domain": saved.domain,
            "status": saved.status,
            "content": content,
            "evidence_urls": urls,
            "created_at": saved.created_at,
        }
