from datetime import datetime

from pydantic import BaseModel, Field


class SourceMetadata(BaseModel):
    name: str
    endpoint: str
    retrieved_at: datetime
    parameters: dict[str, str | int | float | bool | None] = Field(default_factory=dict)
