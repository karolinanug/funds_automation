# Pension Fund Scraper - Multi-Source Architecture

This project scrapes pension fund data from multiple sources and generates daily consolidated reports via email.

## Directory Structure

```
pension_scraper/
├── sources/                    # Individual scraper implementations
│   ├── __init__.py
│   ├── swedbank_pensions.py   # Swedbank performance scraper
│   ├── swedbank_fondo_dydis.py # Swedbank fund sizes scraper
│   └── competitor_template.py # Template for new competitors
├── base_scraper.py             # Abstract base class for all scrapers
├── run_daily_pipeline.py       # Auto-discovery orchestrator
├── merge_data.py               # Intelligent multi-source merger
├── send_email.py               # Email dispatcher
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## How It Works

### 1. **Auto-Discovery Pipeline** (run_daily_pipeline.py)
- Automatically discovers all scrapers in `sources/` folder
- Runs each scraper sequentially
- Merges results from all sources
- Sends consolidated report via email

### 2. **Base Class Architecture** (base_scraper.py)
All scrapers inherit from `BaseScraper` which provides:
- Browser lifecycle management (setup/cleanup)
- Excel file generation
- Error handling
- Consistent interface

### 3. **Dynamic Merging** (merge_data.py)
- Discovers all `*_data_YYYY-MM-DD.xlsx` files
- Merges on "Fund name" column (outer join)
- Creates single consolidated file

## Adding a New Competitor

### Step 1: Create Scraper
Copy and customize the template:

```bash
cp sources/competitor_template.py sources/competitor1.py
```

### Step 2: Implement Your Logic
Edit `sources/competitor1.py`:

```python
class Competitor1Scraper(BaseScraper):
    def __init__(self):
        super().__init__("competitor1")  # Unique source name
    
    def get_url(self) -> str:
        return "https://competitor1.com/funds"
    
    def scrape_data(self, page) -> list:
        # Your scraping logic here
        # Must return: [{"Fund name": "X", "Other": "Y"}, ...]
        pass
```

### Step 3: Test Locally
```bash
python sources/competitor1.py
```

Should output: `✅ Excel file created: competitor1_data_2026-04-19.xlsx`

### Step 4: Automatic Integration
The pipeline will automatically:
- Discover `sources/competitor1.py`
- Run it as part of the daily workflow
- Merge its data with other sources
- Include in consolidated email report

## Data File Naming Convention

All scrapers output files in this format:
```
{source_name}_data_YYYY-MM-DD.xlsx
```

Examples:
- `swedbank_pensions_data_2026-04-19.xlsx`
- `swedbank_fondo_dydis_data_2026-04-19.xlsx`
- `competitor1_data_2026-04-19.xlsx`
- `competitor2_data_2026-04-19.xlsx`

Merge output:
- `pension_data_combined_2026-04-19.xlsx`

## Running Locally

### One-time setup:
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Run daily pipeline:
```bash
python run_daily_pipeline.py
```

### Run single scraper:
```bash
python sources/swedbank_pensions.py
```

## Cloud Automation

Deploy to GitHub Actions for hands-free daily runs:

1. Push code: `git push origin main`
2. Set GitHub secrets (Settings → Secrets and variables → Actions):
   - `GMAIL_USER`
   - `GMAIL_PASSWORD`
   - `RECIPIENT_EMAIL`
3. Workflow runs at 07:00 EET weekdays

## Dependencies

- **playwright**: Headless browser automation
- **pandas**: Data manipulation and Excel I/O
- **openpyxl**: Excel workbook handling

See `requirements.txt` for exact versions.

## Troubleshooting

### New scraper not running
- Check filename is in `sources/` folder
- Verify filename doesn't start with `_`
- Run `python run_daily_pipeline.py` to see discovery output

### Merge fails with "no Fund name column"
- Ensure your scraper's output has a `"Fund name"` column
- Adjust merge logic in `merge_data.py` if using different column names

### Playwright selector not working
- Use `page.pause()` in your scraper to debug
- Check page structure hasn't changed
- Consider adding logging: `print(f"Found {len(rows)} rows")`

## Extending Further

Current setup handles:
- ✅ Multiple scrapers per source (Swedbank: performance + sizes)
- ✅ Multiple independent sources
- ✅ Intelligent data merging
- ✅ Automated email delivery
- ✅ Cloud scheduling (GitHub Actions)
- ✅ Local scheduling (macOS launchd)

Future ideas:
- Database storage (SQLite/PostgreSQL)
- Data visualization/dashboard
- Anomaly detection
- Historical trend analysis
