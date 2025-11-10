"""Core SEC client logic for company lookup and filing filtering."""

from sec_connector.models import Company, Filing, FilingFilter


class SECClient:
    """Client for looking up companies and filtering SEC filings."""

    def __init__(self, companies_data: dict[str, dict], filings_data: list[dict]) -> None:
        """
        Initialize with company ticker->info mapping and filings data.

        Args:
            companies_data: Dictionary mapping ticker symbols to company info (cik, name)
            filings_data: List of filing dictionaries with cik, company_name, form_type, filing_date, accession_number
        """
        self._companies = companies_data
        self._filings_data = filings_data

    def lookup_company(self, ticker: str) -> Company:
        """
        Find company by ticker, raise ValueError if not found.

        Args:
            ticker: Stock ticker symbol (case-insensitive)

        Returns:
            Company object with zero-padded CIK

        Raises:
            ValueError: If ticker is not found or is empty
        """
        if not ticker or not ticker.strip():
            raise ValueError("Ticker cannot be empty")

        ticker_upper = ticker.upper().strip()
        company_info = self._companies.get(ticker_upper)

        if company_info is None:
            raise ValueError(f"Company with ticker '{ticker}' not found")

        # Zero-pad CIK to 10 digits
        cik = company_info["cik"]
        cik_padded = cik.zfill(10)

        return Company(
            ticker=ticker_upper,
            cik=cik_padded,
            name=company_info["name"]
        )

    def list_filings(self, cik: str, filters: FilingFilter) -> list[Filing]:
        """
        Get filings for a CIK, applying filters.

        - Filter by form_types (if provided)
        - Filter by date range (if provided)
        - Sort by date descending
        - Limit results

        Args:
            cik: Company CIK (will be normalized to 10 digits)
            filters: FilingFilter object with filter criteria

        Returns:
            List of Filing objects matching the filters, sorted by date descending
        """
        # Normalize CIK to 10 digits for comparison
        cik_normalized = cik.zfill(10)

        # Filter filings by CIK
        matching_filings = [
            filing_dict for filing_dict in self._filings_data
            if filing_dict["cik"].zfill(10) == cik_normalized
        ]

        # Convert to Filing objects
        filings = []
        for filing_dict in matching_filings:
            try:
                filing = Filing(**filing_dict)
                filings.append(filing)
            except Exception as e:
                # Skip invalid filings
                continue

        # Apply form_type filter
        if filters.form_types is not None and len(filters.form_types) > 0:
            filings = [
                f for f in filings
                if f.form_type in filters.form_types
            ]

        # Apply date range filter
        if filters.date_from is not None:
            filings = [
                f for f in filings
                if f.filing_date >= filters.date_from
            ]

        if filters.date_to is not None:
            filings = [
                f for f in filings
                if f.filing_date <= filters.date_to
            ]

        # Sort by filing_date descending (newest first)
        filings.sort(key=lambda f: f.filing_date, reverse=True)

        # Apply limit
        return filings[:filters.limit]

