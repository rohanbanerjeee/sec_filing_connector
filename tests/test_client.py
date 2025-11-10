"""Tests for SEC Filing Connector."""

import json
from datetime import date
from pathlib import Path

import pytest

from sec_connector.client import SECClient
from sec_connector.models import Company, Filing, FilingFilter


@pytest.fixture
def companies_data():
    """Load company tickers fixture."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / "company_tickers.json") as f:
        return json.load(f)


@pytest.fixture
def filings_data():
    """Load filings fixture."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / "filings_sample.json") as f:
        return json.load(f)


@pytest.fixture
def client(companies_data, filings_data):
    """Create SECClient instance."""
    return SECClient(companies_data, filings_data)


class TestCompanyModel:
    """Test Company model validation."""

    def test_valid_company(self):
        """Test creating a valid Company."""
        company = Company(ticker="AAPL", cik="0000320193", name="Apple Inc.")
        assert company.ticker == "AAPL"
        assert company.cik == "0000320193"
        assert company.name == "Apple Inc."

    def test_invalid_company_missing_field(self):
        """Test that Company rejects missing fields."""
        with pytest.raises(Exception):  # Pydantic validation error
            Company(ticker="AAPL", cik="320193")  # Missing name


class TestFilingModel:
    """Test Filing model validation."""

    def test_valid_filing(self):
        """Test creating a valid Filing."""
        filing = Filing(
            cik="320193",
            company_name="Apple Inc.",
            form_type="10-K",
            filing_date=date(2023, 11, 3),
            accession_number="0000320193-23-000077"
        )
        assert filing.cik == "320193"
        assert filing.form_type == "10-K"
        assert filing.filing_date == date(2023, 11, 3)

    def test_invalid_filing_bad_date(self):
        """Test that Filing rejects invalid date format."""
        with pytest.raises(Exception):  # Pydantic validation error
            Filing(
                cik="320193",
                company_name="Apple Inc.",
                form_type="10-K",
                filing_date="not-a-date",  # Invalid date format
                accession_number="0000320193-23-000077"
            )


class TestFilingFilterModel:
    """Test FilingFilter model."""

    def test_defaults(self):
        """Test FilingFilter defaults."""
        filter_obj = FilingFilter()
        assert filter_obj.form_types is None
        assert filter_obj.date_from is None
        assert filter_obj.date_to is None
        assert filter_obj.limit == 10

    def test_custom_values(self):
        """Test FilingFilter with custom values."""
        filter_obj = FilingFilter(
            form_types=["10-K", "10-Q"],
            date_from=date(2023, 1, 1),
            date_to=date(2023, 12, 31),
            limit=5
        )
        assert filter_obj.form_types == ["10-K", "10-Q"]
        assert filter_obj.limit == 5


class TestLookupCompany:
    """Test SECClient.lookup_company() method."""

    def test_valid_ticker_returns_company(self, client):
        """Test that valid ticker returns Company object."""
        company = client.lookup_company("AAPL")
        assert isinstance(company, Company)
        assert company.ticker == "AAPL"
        assert company.name == "Apple Inc."

    def test_invalid_ticker_raises_value_error(self, client):
        """Test that invalid ticker raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            client.lookup_company("INVALID")

    def test_empty_ticker_raises_value_error(self, client):
        """Test that empty ticker raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            client.lookup_company("")
        with pytest.raises(ValueError, match="cannot be empty"):
            client.lookup_company("   ")

    def test_case_insensitive_lookup(self, client):
        """Test that lookup is case-insensitive."""
        company1 = client.lookup_company("aapl")
        company2 = client.lookup_company("AAPL")
        company3 = client.lookup_company("AaPl")
        assert company1.ticker == company2.ticker == company3.ticker == "AAPL"

    def test_cik_zero_padding(self, client):
        """Test that CIK is zero-padded to 10 digits."""
        company = client.lookup_company("AAPL")
        assert len(company.cik) == 10
        assert company.cik == "0000320193"

        company2 = client.lookup_company("MSFT")
        assert len(company2.cik) == 10
        assert company2.cik == "0000789019"


class TestListFilings:
    """Test SECClient.list_filings() method."""

    def test_no_filters_returns_all_filings_limited(self, client):
        """Test that no filters returns all filings (limited)."""
        company = client.lookup_company("AAPL")
        filters = FilingFilter(limit=100)  # Large limit to get all
        filings = client.list_filings(company.cik, filters)

        # Should return all Apple filings
        assert len(filings) == 4
        assert all(f.cik == company.cik or f.cik.zfill(10) == company.cik for f in filings)

    def test_form_type_filter(self, client):
        """Test that form type filter works."""
        company = client.lookup_company("AAPL")
        filters = FilingFilter(form_types=["10-K"], limit=100)
        filings = client.list_filings(company.cik, filters)

        assert len(filings) == 2  # Two 10-K filings for Apple
        assert all(f.form_type == "10-K" for f in filings)

    def test_date_range_filter(self, client):
        """Test that date range filter works."""
        company = client.lookup_company("AAPL")
        filters = FilingFilter(
            date_from=date(2023, 1, 1),
            date_to=date(2023, 12, 31),
            limit=100
        )
        filings = client.list_filings(company.cik, filters)

        assert len(filings) == 1  # One filing in 2023
        assert filings[0].filing_date == date(2023, 11, 3)

    def test_results_sorted_newest_first(self, client):
        """Test that results are sorted by date descending."""
        company = client.lookup_company("AAPL")
        filters = FilingFilter(limit=100)
        filings = client.list_filings(company.cik, filters)

        # Check that dates are in descending order
        dates = [f.filing_date for f in filings]
        assert dates == sorted(dates, reverse=True)

    def test_limit_respected(self, client):
        """Test that limit is respected."""
        company = client.lookup_company("AAPL")
        filters = FilingFilter(limit=2)
        filings = client.list_filings(company.cik, filters)

        assert len(filings) == 2

    def test_combined_filters(self, client):
        """Test that combined filters work correctly."""
        company = client.lookup_company("AAPL")
        filters = FilingFilter(
            form_types=["10-K"],
            date_from=date(2022, 1, 1),
            date_to=date(2023, 12, 31),
            limit=10
        )
        filings = client.list_filings(company.cik, filters)

        # Should return 10-K filings in 2022-2023
        assert len(filings) == 2
        assert all(f.form_type == "10-K" for f in filings)
        assert all(date(2022, 1, 1) <= f.filing_date <= date(2023, 12, 31) for f in filings)

    def test_different_company_filings(self, client):
        """Test that filings are filtered by CIK."""
        msft_company = client.lookup_company("MSFT")
        filters = FilingFilter(limit=100)
        msft_filings = client.list_filings(msft_company.cik, filters)

        # Should only return Microsoft filings
        assert len(msft_filings) == 2
        assert all("Microsoft" in f.company_name for f in msft_filings)

