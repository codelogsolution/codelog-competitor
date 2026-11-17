
import json

from sqlalchemy.orm import Session

from app.ai.prompts.battlecard_prompt import BATTLECARD_SYSTEM_PROMPT
from app.ai.providers.claude_provider import ClaudeProvider
from app.ai.tools.evidence_tools import get_evidence_context
from app.models.evidence import Evidence
from app.repositories.battlecard_repository import BattlecardRepository
from app.services.scoring_service import ScoringService
from app.services.audit_service import AuditService
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

    @staticmethod
    def _normalized_domain(domain: str) -> str:
        return str(domain or "").strip().lower().removeprefix("www.").rstrip(".")

    @staticmethod
    def _record_dict(item: Evidence) -> dict:
        return {
            "competitor_name": item.competitor_name,
            "domain": item.domain,
            "source_type": item.source_type,
            "signal_type": item.signal_type,
            "category": item.category,
            "product_area": item.product_area,
            "sentiment": item.sentiment,
            "frequency": item.frequency,
            "keyword_volume": item.keyword_volume,
            "ranking_gap": item.ranking_gap,
            "signal_text": item.signal_text,
            "source_url": item.source_url,
            "signal_date": item.signal_date,
            "status": item.status,
        }

    @classmethod
    def _eligible_evidence(cls, records: list[Evidence]) -> list[Evidence]:
        """Only validated, source-backed records may enter a generated draft."""
        return [
            item for item in records
            if str(item.status or "").strip().lower() == "valid"
            and bool(str(item.signal_text or "").strip())
            and str(item.source_url or "").strip().lower().startswith(("https://", "http://"))
        ]

    @classmethod
    def _assert_battlecard_eligibility(
        cls,
        competitor_name: str,
        domain: str,
        records: list[Evidence],
    ) -> list[Evidence]:
        # Public research may support a draft, but it must not change the
        # deterministic score that qualified the competitor for research.
        scoring_records = [
            cls._record_dict(item)
            for item in records
            if str(item.signal_type or "").strip().lower() != "public_research"
        ]
        score_response = ScoringService.score_competitors(scoring_records)
        normalized_domain = cls._normalized_domain(domain)
        score = next(
            (
                item for item in score_response.results
                if cls._normalized_domain(item.domain) == normalized_domain
            ),
            None,
        )
        if score is None or score.priority != "high" or score.preliminary_score < 70:
            raise ValueError(
                "Battlecards can only be generated for high-priority competitors "
                "with a score of at least 70 from valid evidence."
            )

        usable = cls._eligible_evidence(records)
        if not usable:
            raise ValueError(
                "No usable, source-backed valid evidence is available for this competitor."
            )
        return usable

    @classmethod
    def generate(cls, db: Session, competitor_name: str, domain: str):
        normalized_domain = cls._normalized_domain(domain)
        if not normalized_domain:
            raise ValueError("A valid competitor domain is required.")

        records = (
            db.query(Evidence)
            .filter(Evidence.domain == normalized_domain)
            .all()
        )

        if not records:
            raise ValueError("No evidence available for this competitor.")

        eligible_records = cls._assert_battlecard_eligibility(
            competitor_name,
            normalized_domain,
            records,
        )

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
            for item in eligible_records
        ]

        context = get_evidence_context(evidence)
        llm = ClaudeProvider().get_chat_model()
        content = cls._generate_content(llm, competitor_name, normalized_domain, context)
        urls = sorted({item.source_url for item in eligible_records})

        saved = BattlecardRepository.create(
            db,
            {
                "competitor_name": competitor_name,
                "domain": normalized_domain,
                "status": "pending_review",
                "content": content.model_dump_json(),
                "evidence_urls": json.dumps(urls),
            },
        )
        AuditService.record(
            db=db,
            entity_id=saved.id,
            entity_type="battlecard",
            action="generated_by_ai",
            previous_status="",
            new_status="pending_review",
            actor="KOMP AI",
            comment=f"Draft generated from {len(urls)} validated evidence source(s); reviewer approval required.",
        )
        db.commit()
        db.refresh(saved)

        return {
            "id": saved.id,
            "competitor_name": saved.competitor_name,
            "domain": saved.domain,
            "status": saved.status,
            "content": content,
            "evidence_urls": urls,
            "created_at": saved.created_at,
        }
