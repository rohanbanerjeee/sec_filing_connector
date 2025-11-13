# SEC Filing Connector - Coding Test

## Overview

Build a Python module that fetches and filters SEC EDGAR filings. This is a **2-3 hour coding test** focusing on clean code, typing, and testability.

**You'll build:**
- Company lookup (ticker → CIK)
- Filing list with filters (form type, date range)
- Basic download capability

---

## Installation

Install the package in editable mode:

```bash
pip install -e .
```

This will install the package and its dependencies (`httpx`, `pydantic`, `pytest`).

---

## Running Tests

Run all tests with pytest:

```bash
pytest
```

For verbose output:

```bash
pytest -v
```

---

## CLI Usage

The command-line interface allows you to look up companies and filter their SEC filings.

### Basic Usage

```bash
python -m sec_connector.cli AAPL
```

### Filter by Form Type

```bash
python -m sec_connector.cli AAPL --form 10-K --limit 5
```

### Filter by Date Range

```bash
python -m sec_connector.cli AAPL --date-from 2023-01-01 --date-to 2023-12-31
```

### Multiple Form Types

```bash
python -m sec_connector.cli AAPL --form 10-K --form 10-Q
```

### JSON Output

```bash
python -m sec_connector.cli AAPL --form 10-K --json
```

### Complete Example

```bash
python -m sec_connector.cli MSFT --form 10-K --date-from 2023-01-01 --limit 3 --json
```

### Download Filings

Download filings to a directory:

```bash
python -m sec_connector.cli AAPL --form 10-K --download ./downloads
```

Download a specific filing by index (0-indexed):

```bash
python -m sec_connector.cli AAPL --form 10-K --download ./downloads --download-index 0
```

### CLI Options

- `ticker` (required): Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
- `--form`: Filter by form type (can be specified multiple times)
- `--date-from`: Filter filings from this date (YYYY-MM-DD)
- `--date-to`: Filter filings to this date (YYYY-MM-DD)
- `--limit`: Maximum number of results (default: 10)
- `--json`: Output results as JSON instead of table
- `--download DIR`: Download filings to the specified directory
- `--download-index N`: Download only the Nth filing (0-indexed, default: download all)

---

## Project Structure

```
sec_connector/
  pyproject.toml
  README.md
  sec_connector/
    __init__.py
    models.py      # Data models
    client.py      # Core logic
    cli.py         # Simple CLI
  tests/
    test_client.py
    fixtures/
      company_tickers.json
      filings_sample.json
```

---

## Setup

**Dependencies:** `httpx`, `pydantic`, `pytest`

```toml
# pyproject.toml
[project]
name = "sec-connector"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["httpx>=0.24", "pydantic>=2.0", "pytest>=7.0"]
```

---

## Task 1: Data Models (15 min)

Create Pydantic models in `models.py`:

```python
from pydantic import BaseModel
from datetime import date

class Company(BaseModel):
    ticker: str
    cik: str
    name: str

class Filing(BaseModel):
    cik: str
    company_name: str
    form_type: str
    filing_date: date
    accession_number: str
    
class FilingFilter(BaseModel):
    form_types: list[str] | None = None
    date_from: date | None = None
    date_to: date | None = None
    limit: int = 10
```

**Test:** Models validate correctly and reject bad data.

---

## Task 2: Company Lookup (20 min)

In `client.py`, implement:

```python
class SECClient:
    def __init__(self, companies_data: dict[str, dict]):
        """Initialize with company ticker->info mapping."""
        self._companies = companies_data
    
    def lookup_company(self, ticker: str) -> Company:
        """Find company by ticker, raise ValueError if not found."""
        # TODO: implement
        pass
```

**Tests:**
- Valid ticker returns Company
- Invalid ticker raises ValueError
- CIK is zero-padded to 10 digits

---

## Task 3: Filter Filings (45 min)

Implement filing search with filters:

```python
class SECClient:
    # ... previous code ...
    
    def list_filings(self, cik: str, filters: FilingFilter) -> list[Filing]:
        """
        Get filings for a CIK, applying filters.
        
        - Filter by form_types (if provided)
        - Filter by date range (if provided)
        - Sort by date descending
        - Limit results
        """
        # TODO: implement
        pass
```

**Tests:**
- No filters returns all filings (limited)
- Form type filter works (only 10-K)
- Date range filter works
- Results sorted newest first
- Limit respected

---

## Task 4: CLI (30 min)

Simple command-line interface in `cli.py`:

```python
import json
from pathlib import Path
from sec_connector.client import SECClient
from sec_connector.models import FilingFilter

def main():
    """
    Usage: python -m sec_connector.cli AAPL --form 10-K --limit 5
    """
    # TODO: Parse args (use argparse or simple sys.argv)
    # Load fixtures
    # Call client methods
    # Print results as table or JSON
    pass

if __name__ == "__main__":
    main()
```

**Test:** Run CLI with test data and verify output.

---

## Task 5: Edge Cases & Polish (20 min)

Add:
- Input validation (empty strings, invalid dates)
- Helpful error messages
- Type hints throughout
- Docstrings for public methods

---

## What We're Looking For

**Clean code** - Readable, well-organized  
**Type safety** - Proper type hints, Pydantic validation  
**Error handling** - Graceful failures with clear messages  
**Filtering logic** - Correct implementation of all filters  

---

## Submission

Provide:
1. Working code in the structure above
2. Tests that pass: `pytest tests/`
3. Brief README with:
   - How to install: `pip install -e .`
   - How to run tests: `pytest`
   - Example CLI usage

**Time estimate:** 2-3 hours

---

Good luck! Focus on correctness and clarity over completeness.
