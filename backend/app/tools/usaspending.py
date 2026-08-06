from dataclasses import dataclass


@dataclass(frozen=True)
class AgencySpendingQuery:
    agency_name: str
    fiscal_year: int


def normalize_agency_name(name: str) -> str:
    return " ".join(name.strip().split())
