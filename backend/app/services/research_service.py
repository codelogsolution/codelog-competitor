
import httpx

from app.core.config import settings
from app.schemas.research import (
    CompetitorResearch,
    ResearchResponse,
    ResearchSource,
)


TAVILY_URL = "https://api.tavily.com/search"

BLOCKED_DOMAINS = {
    "example.com",
    "example.org",
    "example.net",
    "test.com",
}


class ResearchService:

    @staticmethod
    def is_researchable(competitor: dict) -> bool:
        score = int(competitor.get("preliminary_score", 0))
        priority = str(competitor.get("priority", "")).lower()

        name = str(competitor.get("competitor_name", "")).lower()
        domain = str(competitor.get("domain", "")).lower().strip()

        if score < 70 or priority != "high":
            return False

        if not name or not domain:
            return False

        if (
            domain.endswith(".invalid")
            or domain in BLOCKED_DOMAINS
            or "synthetic" in name
            or "training" in name
            or "practice rival" in name
        ):
            return False

        return True

    @staticmethod
    def build_query(name: str, domain: str) -> str:
        return (
            f'"{name}" "{domain}" '
            "(product launch OR pricing OR features OR "
            "global hiring OR country coverage OR positioning)"
        )

    @staticmethod
    def parse_sources(data: dict, max_results: int) -> list[ResearchSource]:
        sources = []

        for item in data.get("results", [])[:max_results]:
            url = item.get("url")
            if not url:
                continue

            sources.append(
                ResearchSource(
                    title=item.get("title") or "Untitled source",
                    url=url,
                    content=item.get("content") or "",
                    published_date=item.get("published_date"),
                    score=item.get("score"),
                )
            )

        return sources

    @classmethod
    async def search_competitor(
        cls,
        competitor: dict,
        max_results: int = 5,
    ) -> CompetitorResearch:

        name = str(competitor["competitor_name"])
        domain = str(competitor["domain"])
        score = int(competitor["preliminary_score"])
        query = cls.build_query(name, domain)

        if not settings.TAVILY_API_KEY:
            return CompetitorResearch(
                competitor_name=name,
                domain=domain,
                preliminary_score=score,
                status="configuration_required",
                query=query,
                message="TAVILY_API_KEY is missing from backend/.env",
            )

        payload = {
            "api_key": settings.TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "topic": "general",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(TAVILY_URL, json=payload)
                response.raise_for_status()
                data = response.json()

            sources = cls.parse_sources(data, max_results)

            return CompetitorResearch(
                competitor_name=name,
                domain=domain,
                preliminary_score=score,
                status="completed" if sources else "no_results",
                query=query,
                sources=sources,
                message=(
                    "Public sources collected."
                    if sources
                    else "No usable public sources found."
                ),
            )

        except httpx.HTTPStatusError as exc:
            return CompetitorResearch(
                competitor_name=name,
                domain=domain,
                preliminary_score=score,
                status="failed",
                query=query,
                message=f"Search provider returned HTTP {exc.response.status_code}.",
            )

        except httpx.RequestError:
            return CompetitorResearch(
                competitor_name=name,
                domain=domain,
                preliminary_score=score,
                status="failed",
                query=query,
                message="Unable to connect to the public search provider.",
            )

        except (ValueError, TypeError):
            return CompetitorResearch(
                competitor_name=name,
                domain=domain,
                preliminary_score=score,
                status="failed",
                query=query,
                message="Search provider returned an invalid response.",
            )

    @classmethod
    async def research_competitors(
        cls,
        competitors: list[dict],
        max_competitors: int = 5,
        max_results_per_competitor: int = 5,
    ) -> ResearchResponse:

        targets = []
        skipped_count = 0

        for competitor in competitors:
            if cls.is_researchable(competitor):
                targets.append(competitor)
            else:
                skipped_count += 1

        targets.sort(
            key=lambda item: int(item.get("preliminary_score", 0)),
            reverse=True,
        )

        if len(targets) > max_competitors:
            skipped_count += len(targets) - max_competitors

        targets = targets[:max_competitors]
        results = []

        for competitor in targets:
            result = await cls.search_competitor(
                competitor,
                max_results=max_results_per_competitor,
            )
            results.append(result)

        return ResearchResponse(
            success=all(
                item.status in {"completed", "no_results"}
                for item in results
            ),
            researched_count=len(results),
            skipped_count=skipped_count,
            results=results,
        )

