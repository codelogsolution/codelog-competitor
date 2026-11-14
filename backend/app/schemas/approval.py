
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApprovalActionRequest(BaseModel):
    actor: str = "reviewer"
    comment: str = Field(default="", max_length=2000)


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    competitor_name: str
    domain: str
    status: str
    created_at: datetime
