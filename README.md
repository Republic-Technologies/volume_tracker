# Volume Tracker - Stock Scraper

Scrapes time & sales data from CSE and Stockwatch websites.

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Set Up Authentication (for Stockwatch only)

Create a `secrets.json` file in the project root with your Stockwatch credentials:

```json
{
  "username": "your_username_here",
  "password": "your_password_here"
}
```

**Note:** `secrets.json` is already in `.gitignore` to protect your credentials.

## Usage

### Scrape CSE Data (No authentication required)

```bash
# Scrape DOCT (default)
python scrape.py

# Scrape a different symbol
python scrape.py --symbol DOCT

# Explicitly specify CSE source (default)
python scrape.py --source cse --symbol DOCT
```

**Output files:**
- `depth_chart.json`
- `depth_chart.csv`

### Scrape Stockwatch Data (Requires authentication)

```bash
# Scrape DOCT for today's date
python scrape.py --source stockwatch --symbol DOCT

# Scrape for a specific date (format: yyyymmdd)
python scrape.py --source stockwatch --symbol DOCT --date 20240115

# Scrape a different symbol
python scrape.py --source stockwatch --symbol AAPL --date 20240115
```

**Output file:**
- `trades.json`

## Command-Line Arguments

| Argument | Description | Default | Required |
|----------|-------------|---------|----------|
| `--symbol` | Ticker symbol to scrape | `DOCT` | No |
| `--source` | Data source: `cse` or `stockwatch` | `cse` | No |
| `--date` | Date in yyyymmdd format (for Stockwatch) | Today's date | No |

## Examples

```bash
# CSE examples
python scrape.py                                    # DOCT from CSE
python scrape.py --symbol AAPL                      # AAPL from CSE

# Stockwatch examples
python scrape.py --source stockwatch               # DOCT for today
python scrape.py --source stockwatch --date 20240115  # DOCT for Jan 15, 2024
python scrape.py --source stockwatch --symbol AAPL --date 20240115
```

## Troubleshooting

### "Authentication file 'secrets.json' not found"
- Create `secrets.json` with your Stockwatch username and password (see Setup step 3)

### "Login may have failed"
- Check that your username and password are correct in `secrets.json`
- The login page structure may have changed - check the error message for details

### "No trades found"
- Verify the symbol is correct
- For Stockwatch, check that the date is valid and has trading data
- Some dates may not have any trades

### Playwright errors
- Make sure you've run `playwright install chromium`
- Try running with `headless=False` in the code to see what's happening (modify `scrape.py`)

