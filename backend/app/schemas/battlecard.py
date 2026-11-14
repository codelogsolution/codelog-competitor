
from typing import Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class BattlecardContent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    overview: str
    positioning: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    product_gaps: list[str] = Field(default_factory=list)
    pricing: str
    opportunities: list[str] = Field(default_factory=list)
    threat_level: Literal["High", "Medium", "Low"]
    recommended_actions: list[str] = Field(default_factory=list)
    evidence_notes: list[str] = Field(default_factory=list)


class BattlecardGenerateRequest(BaseModel):
    competitor_name: str
    domain: str


class BattlecardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    competitor_name: str
    domain: str
    status: str
    content: BattlecardContent
    evidence_urls: list[str]
    created_at: datetime
