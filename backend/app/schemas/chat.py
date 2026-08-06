from pydantic import BaseModel, Field

from app.schemas.source import SourceMetadata
from app.schemas.visualization import VisualizationSpec


class ChatRequest(BaseModel):
    thread_id: str
    message: str = Field(min_length=1, max_length=4000)


class KeyNumber(BaseModel):
    label: str
    value: int | float | str
    unit: str | None = None


class ActivityEvent(BaseModel):
    type: str
    message: str


class ChatResponse(BaseModel):
    thread_id: str
    answer: str
    key_numbers: list[KeyNumber] = Field(default_factory=list)
    visualizations: list[VisualizationSpec] = Field(default_factory=list)
    sources: list[SourceMetadata] = Field(default_factory=list)
    activity: list[ActivityEvent] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
