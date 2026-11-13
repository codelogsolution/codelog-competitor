from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    success: bool
    original_filename: str
    stored_filename: str

    total_records: int = 0
    valid_records: int = 0
    invalid_records: int = 0
    warning_records: int = 0

    warnings: list = Field(default_factory=list)
    errors: list = Field(default_factory=list)
    records: list = Field(default_factory=list)