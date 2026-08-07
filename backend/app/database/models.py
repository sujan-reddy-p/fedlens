from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Agency(Base):
    __tablename__ = "agencies"

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    aliases: Mapped[str] = mapped_column(String(1000), default="")
    spending_records: Mapped[list["SpendingRecord"]] = relationship(back_populates="agency")


class SpendingRecord(Base):
    __tablename__ = "spending_records"
    __table_args__ = (
        Index("ix_spending_agency_period", "agency_code", "period_start", "period_end"),
        Index("ix_spending_agency_fiscal_year", "agency_code", "fiscal_year"),
        UniqueConstraint("agency_code", "fiscal_year", "category", name="uq_spending_agency_year_category"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agency_code: Mapped[str] = mapped_column(ForeignKey("agencies.code"), nullable=False)
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str | None] = mapped_column(String(255))
    obligations: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    outlays: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_demo: Mapped[bool] = mapped_column(default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    agency: Mapped[Agency] = relationship(back_populates="spending_records")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_loaded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
