"""Command-line interface for SEC Filing Connector."""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from sec_connector.client import SECClient
from sec_connector.models import FilingFilter


def load_fixtures() -> tuple[dict[str, dict], list[dict]]:
    """
    Load fixture JSON files.

    Returns:
        Tuple of (companies_data, filings_data)
    """
    # Get the project root directory (parent of sec_connector package)
    project_root = Path(__file__).parent.parent
    fixtures_dir = project_root / "tests" / "fixtures"

    companies_path = fixtures_dir / "company_tickers.json"
    filings_path = fixtures_dir / "filings_sample.json"

    if not companies_path.exists():
        print(f"Error: Fixture file not found: {companies_path}", file=sys.stderr)
        sys.exit(1)

    if not filings_path.exists():
        print(f"Error: Fixture file not found: {filings_path}", file=sys.stderr)
        sys.exit(1)

    with open(companies_path) as f:
        companies_data = json.load(f)

    with open(filings_path) as f:
        filings_data = json.load(f)

    return companies_data, filings_data


def format_filing_table(filings: list) -> str:
    """Format filings as a simple table."""
    if not filings:
        return "No filings found."

    lines = []
    lines.append(f"{'Form':<10} {'Date':<12} {'Accession Number':<30}")
    lines.append("-" * 60)

    for filing in filings:
        lines.append(
            f"{filing.form_type:<10} {str(filing.filing_date):<12} {filing.accession_number:<30}"
        )

    return "\n".join(lines)


def main() -> None:
    """
    Main CLI entry point.

    Usage: python -m sec_connector.cli AAPL --form 10-K --limit 5
    """
    parser = argparse.ArgumentParser(
        description="Look up SEC filings for a company by ticker symbol"
    )
    parser.add_argument(
        "ticker",
        help="Stock ticker symbol (e.g., AAPL, MSFT)"
    )
    parser.add_argument(
        "--form",
        dest="form_types",
        action="append",
        help="Filter by form type (e.g., 10-K, 10-Q). Can be specified multiple times."
    )
    parser.add_argument(
        "--date-from",
        type=str,
        help="Filter filings from this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--date-to",
        type=str,
        help="Filter filings to this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    # Parse dates
    date_from = None
    date_to = None

    if args.date_from:
        try:
            date_from = date.fromisoformat(args.date_from)
        except ValueError:
            print(f"Error: Invalid date format for --date-from: {args.date_from}", file=sys.stderr)
            print("Expected format: YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

    if args.date_to:
        try:
            date_to = date.fromisoformat(args.date_to)
        except ValueError:
            print(f"Error: Invalid date format for --date-to: {args.date_to}", file=sys.stderr)
            print("Expected format: YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

    # Load fixtures
    try:
        companies_data, filings_data = load_fixtures()
    except Exception as e:
        print(f"Error loading fixtures: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize client
    client = SECClient(companies_data, filings_data)

    # Lookup company
    try:
        company = client.lookup_company(args.ticker)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create filter
    filters = FilingFilter(
        form_types=args.form_types,
        date_from=date_from,
        date_to=date_to,
        limit=args.limit
    )

    # Get filings
    filings = client.list_filings(company.cik, filters)

    # Output results
    if args.json:
        output = {
            "company": {
                "ticker": company.ticker,
                "cik": company.cik,
                "name": company.name
            },
            "filings": [
                {
                    "form_type": f.form_type,
                    "filing_date": str(f.filing_date),
                    "accession_number": f.accession_number,
                    "company_name": f.company_name
                }
                for f in filings
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        print(f"\nCompany: {company.name} ({company.ticker})")
        print(f"CIK: {company.cik}\n")
        print(format_filing_table(filings))


if __name__ == "__main__":
    main()

