# Unified Multi-Source Wallet Scraper and Analyzer

## Overview

The **unified_scraper.py** is a comprehensive tool that combines scraping from all three data sources (Hyperdash, Coinglass, and CoinMarketMan), merges the results, removes duplicates, enriches wallet data with Hyperliquid API information, and ranks wallets by performance while filtering out automated trading bots (hyper scrapers).

## Features

### 🔍 Multi-Source Scraping
- **Hyperdash.info** - Top traders leaderboard
- **Coinglass.com** - Range-based trader rankings  
- **CoinMarketMan.com** - Money Printer segment (+$1M PNL traders)
- Automatic deduplication across all sources
- Source tracking for each wallet

### 📊 Comprehensive Data Enrichment
- Portfolio performance metrics from Hyperliquid API
- Current position data and unrealized PnL
- Account value and exposure percentage
- Trading history analysis (Sharpe ratio, drawdown, win rate)
- Trader age and total trades

### 🏆 Intelligent Ranking System
- Performance-based ranking using composite scores
- Filters: minimum Sharpe ratio, maximum drawdown
- Automated hyper scraper detection and exclusion
- Normalized metrics for fair comparison

### 🤖 Hyper Scraper Detection
Automatically identifies and filters out likely automated trading bots based on:
- Extremely high trade frequency (>50 trades/day average)
- New accounts with suspicious activity patterns
- Preserves human traders for genuine performance analysis

## Quick Start

### Basic Usage

```bash
# Analyze existing wallet library
python3 unified_scraper.py --analyze

# Scrape all sources and analyze
python3 unified_scraper.py --scrape --analyze

# Scrape only (no analysis)
python3 unified_scraper.py --scrape
```

### Advanced Usage

```bash
# Custom scraping with more pages
python3 unified_scraper.py --scrape --analyze \
  --hyperdash-pages 20 \
  --coinglass-pages 15

# Analyze with custom filters
python3 unified_scraper.py --analyze \
  --min-sharpe 2.0 \
  --max-drawdown 0.3 \
  --rate-limit 1.0

# Full workflow with CoinMarketMan authentication
python3 unified_scraper.py --scrape --analyze \
  --cmm-email your@email.com \
  --cmm-password yourpassword

# Use environment variables for credentials
export CMM_EMAIL="your@email.com"
export CMM_PASSWORD="yourpassword"
python3 unified_scraper.py --scrape --analyze
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--scrape` | Scrape wallet addresses from all sources | - |
| `--analyze` | Analyze and enrich wallet data | - |
| `--hyperdash-pages N` | Pages to scrape from Hyperdash | 10 |
| `--coinglass-pages N` | Pages to scrape from Coinglass | 10 |
| `--include-cmm` | Include CoinMarketMan | True |
| `--cmm-email EMAIL` | CoinMarketMan login email | $CMM_EMAIL |
| `--cmm-password PASS` | CoinMarketMan login password | $CMM_PASSWORD |
| `--input FILE` | Input CSV with addresses | scrapped_wallet_library.csv |
| `--output FILE` | Output CSV file | big_file.csv |
| `--rate-limit SECS` | API rate limit in seconds | 0.5 |
| `--min-sharpe N` | Minimum Sharpe ratio | 1.5 |
| `--max-drawdown N` | Maximum drawdown | 0.5 |
| `--exclude-hyper-scrapers` | Exclude automated bots | True |
| `--headless` | Run browser headless | True |
| `--no-headless` | Show browser window | - |

## Output Files

### big_file.csv (Full Dataset)
Contains all scraped wallets with complete enrichment:

**Columns:**
- `address` - Wallet address
- `sources` - Comma-separated list of sources
- `sharpe_ratio` - Annualized Sharpe ratio
- `max_drawdown` - Maximum drawdown percentage
- `win_rate` - Win rate (0-1)
- `cum_pnl_pct` - Cumulative PnL percentage
- `trader_age_days` - Days since first trade
- `total_trades` - Total number of trades
- `num_positions` - Current open positions
- `unrealized_pnl` - Unrealized profit/loss
- `account_value` - Current account value
- `exposure_pct` - Exposure percentage (margin/account × 100)
- `total_margin_used` - Total margin in use
- `is_hyper_scraper` - Boolean flag for automated bots

### big_file_ranked.csv (Top Performers)
Filtered and ranked subset meeting performance criteria:

**Additional Columns:**
- `rank` - Performance ranking (1 = best)
- `sharpe_normalized` - Normalized Sharpe ratio (0-1)
- `drawdown_normalized` - Normalized drawdown score (0-1)
- `winrate_normalized` - Normalized win rate (0-1)
- `performance_score` - Composite performance score (0-1)

## Performance Score Calculation

The composite performance score is calculated as:

```
performance_score = 0.5 × sharpe_normalized + 
                   0.3 × drawdown_normalized + 
                   0.2 × winrate_normalized
```

Where each metric is min-max normalized to [0, 1].

## Workflow Phases

### Phase 1: Multi-Source Scraping
1. Scrapes Hyperdash for top traders
2. Scrapes Coinglass for range-based rankings
3. Scrapes CoinMarketMan for money printer segment
4. Deduplicates addresses (case-insensitive)
5. Tracks source(s) for each wallet

### Phase 2: Data Enrichment
1. Fetches portfolio data from Hyperliquid API
2. Analyzes trading performance metrics
3. Fetches current position data
4. Calculates exposure and unrealized PnL
5. Rate-limited to respect API constraints

### Phase 3: Merged DataFrame Creation
1. Combines all data into comprehensive DataFrame
2. Includes source tracking
3. Flags potential hyper scrapers
4. Preserves all enrichment attributes

### Phase 4: Performance Ranking
1. Filters out hyper scrapers (if enabled)
2. Applies minimum performance criteria
3. Calculates normalized metrics
4. Computes composite performance scores
5. Ranks wallets by performance

## Hyper Scraper Detection

Wallets are flagged as hyper scrapers if they meet any of these criteria:

1. **High Frequency**: Average >50 trades per day
2. **Suspicious Pattern**: <30 days old with >500 trades

This helps focus analysis on genuine human traders rather than automated bots.

## Example Workflows

### Daily Research Workflow
```bash
# 1. Quick scrape and analyze
python3 unified_scraper.py --scrape --analyze \
  --hyperdash-pages 5 \
  --coinglass-pages 5 \
  --output daily_analysis.csv

# 2. Review top performers
head -20 daily_analysis_ranked.csv
```

### Deep Analysis Workflow
```bash
# 1. Comprehensive scraping
python3 unified_scraper.py --scrape \
  --hyperdash-pages 30 \
  --coinglass-pages 20 \
  --cmm-email your@email.com \
  --cmm-password yourpass

# 2. Analyze with strict filters
python3 unified_scraper.py --analyze \
  --min-sharpe 2.5 \
  --max-drawdown 0.3 \
  --rate-limit 1.5 \
  --output elite_traders.csv

# 3. Review results
cat elite_traders_ranked.csv | column -t -s,
```

### Incremental Update Workflow
```bash
# 1. Scrape new wallets (appends to library)
python3 script_scrap_wallet.py -s hyperdash -p 10
python3 script_scrap_wallet.py -s coinglass -p 10

# 2. Analyze updated library
python3 unified_scraper.py --analyze \
  --input scrapped_wallet_library.csv \
  --output updated_analysis.csv
```

## Performance Tips

- **Start with fewer pages** for testing (5-10 pages)
- **Increase rate-limit** if hitting API errors (try 1.0-2.0)
- **Use environment variables** for credentials (more secure)
- **Run overnight** for comprehensive scraping (20+ pages)
- **Save intermediate results** by running scrape and analyze separately

## Troubleshooting

### "No addresses found"
- Check internet connection
- Verify website structure hasn't changed
- Try with `--no-headless` to see browser activity

### "HTTP 429 Rate Limit"
- Increase `--rate-limit` value (try 1.5 or 2.0)
- Reduce number of wallets being analyzed
- Wait a few minutes and retry

### "No wallets meeting criteria"
- Lower `--min-sharpe` threshold
- Increase `--max-drawdown` threshold
- Check if wallets have sufficient trading history

### CoinMarketMan Login Issues
- Verify credentials are correct
- Try running with `--no-headless` to debug
- Check if account has access to data

## Integration with Existing Tools

This tool complements the existing scripts:

- **script_scrap_wallet.py** - Single-source scraping
- **script_portfolio.py** - Portfolio analysis only
- **trader_menu.sh** - Interactive menu interface

You can still use the individual scripts for specific tasks, or use `unified_scraper.py` for the complete workflow.

## Data Privacy & Ethics

- Respect rate limits and API terms of service
- Do not overload servers with excessive requests
- Wallet addresses are public blockchain data
- Use data for personal research only
- Comply with all applicable data protection laws

## Future Enhancements

Potential improvements for future versions:

- [ ] Support for additional trader ranking sources
- [ ] Machine learning-based trader classification
- [ ] Historical performance tracking over time
- [ ] Alert system for top performer changes
- [ ] Integration with trading strategy backtesting
- [ ] Web dashboard for visualization
- [ ] Export to multiple formats (JSON, Excel, etc.)

## Technical Details

### Dependencies
- Python 3.6+
- selenium >= 4.15.0
- aiohttp >= 3.9.0
- aiolimiter >= 1.1.0
- pandas >= 2.0.0
- numpy >= 1.24.0

### API Endpoints Used
- `https://api.hyperliquid.xyz/info` (portfolio, positions, metadata)

### Rate Limiting
- Default: 1 request per 0.5 seconds
- Adjustable via `--rate-limit` parameter
- Concurrent connections limited to 50

## Support

For issues, feature requests, or questions:
1. Check this guide first
2. Review existing documentation
3. Open an issue on the repository

## License

This project is provided as-is for educational and research purposes.
