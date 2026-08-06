from typing import Literal

from pydantic import BaseModel, Field

ChartType = Literal["bar", "line", "table"]


class VisualizationSpec(BaseModel):
    type: ChartType
    title: str
    x_key: str | None = None
    y_key: str | None = None
    unit: str | None = None
    data: list[dict[str, str | int | float | None]] = Field(default_factory=list)
