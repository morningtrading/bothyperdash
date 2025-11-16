# Hyperliquid Trader Analysis Suite

Two-script system for scraping and analyzing Hyperliquid trader wallets.

## Overview

- **script_scrap_wallet.py** - Multi-source wallet scraper
- **script_portfolio.py** - Portfolio analysis and ranking

## Installation

```bash
pip3 install selenium aiohttp aiolimiter pandas numpy
```

## Workflow

### Step 1: Scrape Wallet Addresses

Scrape wallets from Hyperdash or Coinglass:

```bash
# Scrape 20 pages from Hyperdash
python3 script_scrap_wallet.py -s hyperdash -p 20

# Scrape 10 pages from Coinglass
python3 script_scrap_wallet.py -s coinglass -p 10

# Scrape from both sources (appends to same file)
python3 script_scrap_wallet.py -s hyperdash -p 10
python3 script_scrap_wallet.py -s coinglass -p 5
```

**Output:** `scrapped_wallet_library.csv` (deduplicated addresses)

### Step 2: Analyze Portfolios

Analyze scraped wallets and rank by performance:

```bash
# Analyze all wallets in library
python3 script_portfolio.py

# Analyze with custom filters
python3 script_portfolio.py --min-sharpe 2.0 --max-drawdown 0.3

# Analyze first 100 wallets only
python3 script_portfolio.py --limit 100

# Analyze and fetch current positions for top traders
python3 script_portfolio.py --fetch-positions --min-sharpe 1.5
```

**Outputs:**
- `portfolio_analysis.csv` - Full analysis of all wallets
- `portfolio_analysis_filtered.csv` - Top traders matching criteria
- `portfolio_analysis_positions.csv` - Current positions (if --fetch-positions used)

## Script Details

### script_scrap_wallet.py

**Features:**
- Multi-source support (Hyperdash, Coinglass)
- Anti-bot detection measures
- Automatic deduplication
- Timestamped scraping records
- Headless/visible browser modes

**Options:**
```
--source, -s        Source: hyperdash or coinglass (required)
--pages, -p         Number of pages to scrape (default: 10)
--output, -o        Output file (default: scrapped_wallet_library.csv)
--headless          Run in headless mode (default)
--no-headless       Show browser window
```

### script_portfolio.py

**Features:**
- Sharpe ratio calculation (annualized, risk-adjusted returns)
- Maximum drawdown tracking
- Win rate calculation
- Cumulative PnL percentage
- Trader age tracking (days/years active)
- Current position tracking with unrealized PnL
- Concurrent API calls with rate limiting

**Metrics Calculated:**
- **Sharpe Ratio** - Risk-adjusted return (higher is better)
- **Max Drawdown** - Largest peak-to-trough decline (lower is better)
- **Win Rate** - Percentage of profitable days
- **Cumulative PnL %** - Total return percentage
- **Trader Age** - Days since first trade

**Options:**
```
--input, -i         Input CSV file (default: scrapped_wallet_library.csv)
--output, -o        Output file (default: portfolio_analysis.csv)
--min-sharpe        Minimum Sharpe ratio (default: 1.5)
--max-sharpe        Maximum Sharpe ratio (default: 50)
--max-drawdown      Maximum drawdown (default: 0.5)
--limit, -l         Limit number of wallets to analyze
--fetch-positions   Fetch current positions for top traders
--rate-limit        Rate limit in seconds (default: 0.5)
```

## Example Workflow

```bash
# 1. Scrape 50 pages from Hyperdash (2500 addresses)
python3 script_scrap_wallet.py -s hyperdash -p 50

# 2. Analyze all wallets with strict criteria
python3 script_portfolio.py --min-sharpe 2.5 --max-drawdown 0.2 --fetch-positions

# 3. Review results
cat portfolio_analysis_filtered.csv
cat portfolio_analysis_positions.csv
```

## Output File Formats

### scrapped_wallet_library.csv
```csv
address,source,scraped_at
0xabc...,hyperdash,2025-11-15T13:36:36.660282
0xdef...,coinglass,2025-11-15T14:20:15.123456
```

### portfolio_analysis_filtered.csv
```csv
address,sharpe,max_drawdown,win_rate,cum_pnl_pct,trader_age_days,total_trades,trader_age_years
0xabc...,9.76,0.083,0.60,2.04,30,15,0.08
```

### portfolio_analysis_positions.csv
```csv
address,num_positions,unrealized_pnl,account_value,exposure_pct
0xabc...,2,1098693.12,22399560.00,32.58
0xdef...,14,155673.60,2815205.00,38.57
```

**Columns explained:**
- `num_positions` - Number of open positions
- `unrealized_pnl` - Current profit/loss on open trades
- `account_value` - Total account balance
- `exposure_pct` - Percentage of account actively deployed (margin used / account value × 100)

**Understanding Exposure %:**
- **0-25%** - Conservative, low risk
- **25-50%** - Moderate exposure
- **50-75%** - Aggressive positioning
- **75-100%** - Very high risk, fully deployed

*Example:* If a trader has $1M account and 30% exposure, they have $300K margin actively used in positions, leaving $700K available.

## Performance Tips

1. **Scraping:**
   - Use headless mode for faster scraping
   - Scrape during off-peak hours to avoid rate limits
   - Start with fewer pages to test

2. **Analysis:**
   - Use `--limit` to test with small batches first
   - Adjust `--rate-limit` if hitting API limits
   - Run analysis during off-peak hours for better API response

3. **Filtering:**
   - Sharpe > 2.0 = Good traders
   - Sharpe > 3.0 = Excellent traders
   - Max Drawdown < 0.3 = Conservative risk management
   - Win Rate > 0.55 = Consistent profitability

## Advanced Usage

### Chain Multiple Sources
```bash
# Build a comprehensive wallet library
python3 script_scrap_wallet.py -s hyperdash -p 30
python3 script_scrap_wallet.py -s coinglass -p 20

# Result: ~2000 unique addresses from both sources
wc -l scrapped_wallet_library.csv
```

### Incremental Analysis
```bash
# Day 1: Scrape and analyze
python3 script_scrap_wallet.py -s hyperdash -p 20
python3 script_portfolio.py

# Day 2: Add more wallets (appends to library)
python3 script_scrap_wallet.py -s hyperdash -p 20
python3 script_portfolio.py  # Re-analyzes entire library
```

### Custom Filtering
```bash
# Find ultra-conservative high-performers
python3 script_portfolio.py \
  --min-sharpe 3.0 \
  --max-drawdown 0.15 \
  --fetch-positions
```

## Troubleshooting

**"No addresses found"**
- Check internet connection
- Try `--no-headless` to see what's happening
- Website structure may have changed

**"Rate limit exceeded"**
- Increase `--rate-limit` value (e.g., `--rate-limit 1.0`)
- Reduce number of wallets analyzed with `--limit`

**"ModuleNotFoundError"**
- Install missing package: `pip3 install <package_name>`

## Data Sources

- **Hyperdash** - https://hyperdash.info/top-traders
- **Coinglass** - https://www.coinglass.com/hl/range/10
- **Hyperliquid API** - https://api.hyperliquid.xyz/info

## Notes

- Wallets are deduplicated across multiple scraping sessions
- Analysis uses 30-day historical data from Hyperliquid API
- Sharpe ratio is annualized (365-day basis)
- Unrealized PnL shows current open position profit/loss
