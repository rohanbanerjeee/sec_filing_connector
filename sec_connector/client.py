"""Core SEC client logic for company lookup and filing filtering."""

import httpx
from pathlib import Path

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

    def download_filing(self, filing: Filing, output_dir: Path | str | None = None, filename: str | None = None) -> Path:
        """
        Download a filing document from SEC EDGAR.

        Args:
            filing: Filing object to download
            output_dir: Directory to save the file (default: current directory)
            filename: Custom filename (default: {accession_number}.txt)

        Returns:
            Path to the downloaded file

        Raises:
            httpx.HTTPError: If the download fails
            ValueError: If the filing data is invalid
        """
        # Normalize CIK - remove leading zeros for URL (SEC uses numeric CIK in path)
        cik_normalized = filing.cik.zfill(10).lstrip("0") or "0"

        # Convert accession number format: "0000320193-23-000077" -> "000032019323000077"
        accession_no_dashes = filing.accession_number.replace("-", "")

        # Construct SEC EDGAR URL
        # Format: https://www.sec.gov/Archives/edgar/data/{CIK}/{accession_no}/{filename}
        base_url = f"https://www.sec.gov/Archives/edgar/data/{cik_normalized}/{accession_no_dashes}"

        # Default filename is the accession number with .txt extension
        if filename is None:
            filename = f"{filing.accession_number}.txt"

        # Determine output directory
        if output_dir is None:
            output_path = Path(filename)
        else:
            output_path = Path(output_dir) / filename

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Download the file
        # SEC requires a User-Agent header
        headers = {
            "User-Agent": "sec-connector/0.1.0 (contact@example.com)",
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov"
        }

        try:
            with httpx.Client(follow_redirects=True, timeout=30.0) as client:
                response = client.get(f"{base_url}/{filename}", headers=headers)
                response.raise_for_status()

                # Write file
                output_path.write_bytes(response.content)

                return output_path
        except httpx.HTTPStatusError as e:
            # Try alternative filename if .txt fails
            if filename.endswith(".txt"):
                alt_filename = filename.replace(".txt", ".htm")
                try:
                    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
                        response = client.get(f"{base_url}/{alt_filename}", headers=headers)
                        response.raise_for_status()
                        output_path = output_path.with_suffix(".htm")
                        output_path.write_bytes(response.content)
                        return output_path
                except httpx.HTTPStatusError:
                    pass
            raise ValueError(f"Failed to download filing: HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise ValueError(f"Failed to download filing: {e}") from e

