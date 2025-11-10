"""Data models for SEC Filing Connector."""

from pydantic import BaseModel
from datetime import date


class Company(BaseModel):
    """Represents a company with ticker, CIK, and name."""

    ticker: str
    cik: str
    name: str


class Filing(BaseModel):
    """Represents a SEC filing."""

    cik: str
    company_name: str
    form_type: str
    filing_date: date
    accession_number: str


class FilingFilter(BaseModel):
    """Filter criteria for SEC filings."""

    form_types: list[str] | None = None
    date_from: date | None = None
    date_to: date | None = None
    limit: int = 10

