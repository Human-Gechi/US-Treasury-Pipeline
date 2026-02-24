from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(AsyncAttrs, DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class Records(Base):
    """SQLAlchemy model representing the avg_us_securities_2001_present table in the database."""

    __tablename__ = "avg_us_securities_2001_present"
    record_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    record_year: Mapped[int] = mapped_column(
        Integer,
        Computed("COALESCE(EXTRACT(YEAR FROM record_date)::INT, 0)", persisted=True),
    )
    security_type_desc: Mapped[str] = mapped_column(
        String(100),
        CheckConstraint(
            "security_type_desc IN ('Marketable', 'Non-marketable', 'Interest-bearing Debt')"
        ),
    )
    security_desc: Mapped[str] = mapped_column(String(100))
    avg_interest_rate_amt: Mapped[Decimal] = mapped_column(
        Numeric(7, 5), server_default="0"
    )
    __table_args__ = (
        UniqueConstraint(
            "record_date",
            "security_type_desc",
            "security_desc",
            name="uq_records_constraint",
        ),
    )


class APIHealthCheck(Base):
    """SQLAlchemy model representing the api_health_checks table in the database."""

    __tablename__ = "api_health_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    checked_at: Mapped[date] = mapped_column(Date, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    status_message: Mapped[str] = mapped_column(String(255))
    latency_ms: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_healthy: Mapped[bool] = mapped_column(Boolean, nullable=False)
    __table_args__ = (
        CheckConstraint("is_healthy IN (TRUE, FALSE)", name="check_is_healthy"),
    )
