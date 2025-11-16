# Hyperliquid Trader Analysis Suite

A comprehensive Python toolkit for scraping, analyzing, and tracking top Hyperliquid traders across multiple data sources.

## Overview

This suite combines multi-source web scraping with portfolio analysis to identify and track the best-performing traders on Hyperliquid. It features an interactive menu system for easy operation and automatic result syncing to Dropbox.

## Features

### Multi-Source Scraping
- **Hyperdash.info** - Top traders leaderboard
- **Coinglass.com** - Range-based trader rankings
- **CoinMarketMan.com** - Hypertracker Money Printer segment (+$1M PNL traders)
- **Manual Input** - Add specific wallet addresses
- Automated browser-based scraping using Selenium
- Handles JavaScript-rendered content and anti-bot detection
- Automatic pagination with configurable page limits
- Auto-deduplication across all sources

### Portfolio Analysis
- Sharpe ratio calculation
- Maximum drawdown tracking
- Win rate and cumulative PnL metrics
- Exposure percentage (margin used / account value)
- Current position tracking with unrealized PnL
- Configurable filtering thresholds
- Async API calls with rate limiting

### Interactive Menu System
- Color-coded TUI for easy navigation
- 7 main operations + configurable settings
- Full workflow automation (scrape + analyze)
- Automatic Dropbox sync
- Real-time result previews
- Portable configuration (no hard-coded paths)

## Requirements

- Python 3.6+
- Chrome browser installed
- ChromeDriver (automatically managed by Selenium)
- Dependencies:
  - `selenium>=4.15.0` - Web scraping
  - `aiohttp>=3.9.0` - Async API calls
  - `aiolimiter>=1.1.0` - Rate limiting
  - `pandas>=2.0.0` - Data analysis
  - `numpy>=1.24.0` - Numerical operations

## Quick Start

### Option 1: Use the Interactive Menu (Recommended)

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Launch the menu
./trader_menu.sh

# 3. Choose option 5 (Full workflow)
# 4. Results automatically saved to ~/Dropbox/_CURRENT/
```

### Option 2: Use Command-Line Scripts

```bash
# Install dependencies
pip3 install -r requirements.txt

# Scrape from Hyperdash (20 pages)
python3 script_scrap_wallet.py -s hyperdash -p 20

# Scrape from Coinglass (10 pages)
python3 script_scrap_wallet.py -s coinglass -p 10

# Scrape from CoinMarketMan Money Printer (+$1M PNL - 50 public addresses)
python3 script_scrap_wallet.py -s cmm

# Or manually save pages while logged in for ALL 427+ addresses
# See CMM_MANUAL_SCRAPING_GUIDE.md for instructions
python3 parse_cmm_html.py cmm_pages

# Analyze all scraped wallets
python3 script_portfolio.py --fetch-positions --rate-limit 1.0
```

### Option 3: Deploy Packaged Archive

```bash
# Extract the archive
tar -xzf hyperliquid_scraper.tar.gz

# Install and run
cd hyperliquid_scraper
pip3 install -r requirements.txt
./trader_menu.sh
```

## Output Files

### Local Directory (`./bothyperdash/`)

**`scrapped_wallet_library.csv`**
- All scraped wallet addresses from all sources
- Format: `address,source,timestamp`
- Auto-deduplicated

**`portfolio_analysis.csv`**
- Complete analysis of all wallets
- Columns: address, sharpe, max_drawdown, win_rate, cum_pnl_pct, trader_age_days, total_trades

**`portfolio_analysis_filtered.csv`**
- Top traders only (Sharpe > 1.5, Drawdown < 0.5)
- Same columns as full analysis
- Sorted by Sharpe ratio

**`portfolio_analysis_positions.csv`**
- Current positions for all analyzed traders
- Columns: address, num_positions, unrealized_pnl, account_value, exposure_pct, total_margin_used
- Exposure % = (margin used / account value) × 100

### Dropbox Sync (`~/Dropbox/_CURRENT/`)

The menu automatically copies results to Dropbox:

- `freshwallets.rtf` - Formatted results in RTF
- `freshwallets_filtered.csv` - Copy of top traders
- `freshwallets_positions.csv` - Copy of positions data
- `freshwallets_full.csv` - Copy of full analysis

## Architecture

### 1. Wallet Scraper (`script_scrap_wallet.py`)
- Uses Selenium with anti-bot detection measures
- Supports multiple sources via `-s` flag
- Configurable pagination with `-p` flag
- Saves to unified `scrapped_wallet_library.csv`
- Auto-deduplication across sources

### 2. Portfolio Analyzer (`script_portfolio.py`)
- Async API calls to Hyperliquid for performance data
- Rate-limited requests (configurable with `--rate-limit`)
- Calculates trader performance metrics
- Optional position fetching with `--fetch-positions`
- Filters top performers automatically

### 3. Interactive Menu (`trader_menu.sh`)
- Bash-based TUI with color output
- Combines scraping + analysis workflows
- Configurable settings (pages, thresholds, rate limits)
- Auto-sync to Dropbox
- Real-time result previews

## Configuration

### Menu Settings (Option 6)
- **Pages to scrape**: Default 10
- **Min Sharpe ratio**: Default 1.5
- **Max Drawdown**: Default 0.5 (50%)
- **API Rate limit**: Default 1.0s
- **Output directory**: Default `~/Dropbox/_CURRENT`

### Command-Line Arguments

**script_scrap_wallet.py**
```bash
-s, --source     Source: hyperdash or coinglass (required)
-p, --pages      Number of pages to scrape (default: 10)
-o, --output     Output CSV file (default: scrapped_wallet_library.csv)
```

**script_portfolio.py**
```bash
--fetch-positions   Fetch current positions (slower but more data)
--rate-limit       Seconds between API calls (default: 0.5)
--limit            Limit number of wallets to analyze
```

## Troubleshooting

### "No wallet library found"
Run option 1 or 2 in the menu to scrape wallets first, or use:
```bash
python3 script_scrap_wallet.py -s hyperdash -p 10
```

### HTTP 429 Rate Limit Errors
Increase the rate limit in settings (menu option 6) or use:
```bash
python3 script_portfolio.py --rate-limit 2.0
```

### Zero Exposure Values
This is normal for traders without open positions. The exposure_pct only shows values when traders have active margin positions.

### Chrome/ChromeDriver Issues
Update Selenium to the latest version:
```bash
pip3 install --upgrade selenium
```

### Scraper Returns No Addresses
- Check if website structure changed
- Disable headless mode for debugging
- Verify internet connection
- Check for 403/bot detection errors

### Menu Not Executable
Make the script executable:
```bash
chmod +x trader_menu.sh
```

## Performance Tips

- Start with 5-10 pages for testing
- Use `--limit` to analyze smaller batches
- Increase `--rate-limit` if hitting API limits
- Run full workflow overnight for large scrapes
- Combine both sources for comprehensive coverage

## Example Workflow

```bash
# 1. Scrape from all sources
python3 script_scrap_wallet.py -s hyperdash -p 30
python3 script_scrap_wallet.py -s coinglass -p 15
python3 script_scrap_wallet.py -s cmm

# 2. Analyze with position tracking
python3 script_portfolio.py --fetch-positions --rate-limit 1.0

# 3. View filtered results
cat portfolio_analysis_filtered.csv | column -t -s,

# 4. Check current positions
head -20 portfolio_analysis_positions.csv
```

## Documentation

- **[MENU_GUIDE.md](MENU_GUIDE.md)** - Interactive menu quick start guide
- **[README_SCRIPTS.md](README_SCRIPTS.md)** - Detailed script documentation
- **[CMM_MANUAL_SCRAPING_GUIDE.md](CMM_MANUAL_SCRAPING_GUIDE.md)** - CoinMarketMan manual scraping guide
- **requirements.txt** - Python dependencies

## Sample Results

Based on recent analysis of 150+ wallets:
- **Top traders identified**: 54 (Sharpe > 1.5)
- **Highest Sharpe ratio**: 34.7
- **Average exposure**: 15-40% of account value
- **Sources combined**: Hyperdash + Coinglass + CoinMarketMan

## Project Structure

```
bothyperdash/
├── script_scrap_wallet.py           # Multi-source wallet scraper
├── script_portfolio.py               # Portfolio analyzer
├── trader_menu.sh                    # Interactive menu system
├── requirements.txt                  # Dependencies
├── README.md                         # This file
├── README_SCRIPTS.md                 # Detailed documentation
├── MENU_GUIDE.md                     # Menu usage guide
├── hyperliquid_scraper.tar.gz       # Packaged archive
├── scrapped_wallet_library.csv      # Scraped addresses (generated)
├── portfolio_analysis.csv            # Full analysis (generated)
├── portfolio_analysis_filtered.csv   # Top traders (generated)
└── portfolio_analysis_positions.csv  # Current positions (generated)
```

## License

This project is provided as-is for educational and research purposes.

## Disclaimer

Please comply with the terms of service for all data sources:
- HyperDash.info
- Coinglass.com
- CoinMarketMan.com
- Hyperliquid API

Respect rate limits and do not overload servers with requests. This tool is intended for personal research and analysis only.
