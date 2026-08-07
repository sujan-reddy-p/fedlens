from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class FedLensQuery(BaseModel):
    intent: Literal["agency_spending", "agency_comparison", "agency_trend"]
    agency: str | None = None
    agencies: list[str] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    metric: Literal["obligations", "outlays"] = "obligations"
    group_by: Literal["year", "month", "category"] = "year"
