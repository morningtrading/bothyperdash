# Quick Reference: Unified Multi-Source Scraper

## TL;DR - Quick Commands

```bash
# Analyze existing wallet library
python3 unified_scraper.py --analyze

# Scrape all 3 sources + analyze
python3 unified_scraper.py --scrape --analyze

# Use interactive menu
./trader_menu.sh  # Choose option 7
```

## Output Files

| File | Description |
|------|-------------|
| `big_file.csv` | All wallets with complete data (13 columns) |
| `big_file_ranked.csv` | Top performers ranked by composite score |

## Data Columns (big_file.csv)

1. `address` - Wallet address
2. `sources` - Data source(s) - comma-separated
3. `sharpe_ratio` - Annualized Sharpe ratio
4. `max_drawdown` - Maximum drawdown (0-1)
5. `win_rate` - Win rate (0-1)
6. `cum_pnl_pct` - Cumulative PnL percentage
7. `trader_age_days` - Days since first trade
8. `total_trades` - Total number of trades
9. `num_positions` - Current open positions
10. `unrealized_pnl` - Unrealized profit/loss ($)
11. `account_value` - Current account value ($)
12. `exposure_pct` - Exposure % (margin/account × 100)
13. `total_margin_used` - Total margin in use ($)
14. `is_hyper_scraper` - Bot detection flag (True/False)

## Ranking Columns (big_file_ranked.csv)

Additional columns in ranked file:
- `rank` - Performance rank (1 = best)
- `sharpe_normalized` - Normalized Sharpe (0-1)
- `drawdown_normalized` - Normalized drawdown score (0-1)
- `winrate_normalized` - Normalized win rate (0-1)
- `performance_score` - Composite score (0-1)

## Common Options

```bash
# More pages
--hyperdash-pages 20 --coinglass-pages 15

# Stricter filters
--min-sharpe 2.0 --max-drawdown 0.3

# Slower rate limit
--rate-limit 1.5

# Custom output
--output my_analysis.csv

# Include hyper scrapers in ranking
--no-exclude-hyper-scrapers
```

## What Gets Filtered Out

### Hyper Scrapers (Automated Bots)
- Accounts with >50 trades/day average
- New accounts (<30 days) with >500 trades

### Performance Filters (Default)
- Sharpe ratio < 1.5
- Max drawdown > 0.5 (50%)
- Total trades < 10

## Performance Score Formula

```
score = 0.5 × sharpe_normalized + 
        0.3 × drawdown_normalized + 
        0.2 × winrate_normalized
```

Each metric is min-max normalized to [0, 1] for fairness.

## Typical Workflow

### 1. Initial Scrape
```bash
python3 unified_scraper.py --scrape --analyze \
  --hyperdash-pages 10 \
  --coinglass-pages 10 \
  --rate-limit 1.0
```

### 2. Review Results
```bash
# Top 20 performers
head -21 big_file_ranked.csv | column -t -s,

# Total wallets analyzed
wc -l big_file.csv

# Number of top performers
wc -l big_file_ranked.csv
```

### 3. Export to Dropbox (Manual)
```bash
cp big_file_ranked.csv ~/Dropbox/_CURRENT/
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No wallets meet criteria | Lower `--min-sharpe` or increase `--max-drawdown` |
| HTTP 429 errors | Increase `--rate-limit` (try 1.5 or 2.0) |
| Scraping timeout | Reduce pages or run overnight |
| Empty results | Check internet connection and API availability |

## Integration with Existing Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `unified_scraper.py` | All-in-one | Most use cases |
| `script_scrap_wallet.py` | Single source | Testing or specific source |
| `script_portfolio.py` | Analysis only | Analyzing existing data |
| `trader_menu.sh` | Interactive | When you prefer menus |

## Documentation

- **Full Guide**: [UNIFIED_SCRAPER_GUIDE.md](UNIFIED_SCRAPER_GUIDE.md)
- **Bug Review**: [BUG_FIXES.md](BUG_FIXES.md)
- **Implementation**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Main README**: [README.md](README.md)

## Time Estimates

| Task | Approximate Time |
|------|------------------|
| Scrape 10 pages/source | 5-10 minutes |
| Analyze 100 wallets | 2-5 minutes |
| Full workflow (100 wallets) | 10-15 minutes |
| Large scrape (30+ pages) | 30-60 minutes |

*Times vary based on network speed and rate limiting*

## Example Results

Expected output from a typical run (100 wallets):

```
Total wallets analyzed: 100
Wallets meeting criteria: 25
Hyper scrapers filtered: 3
Top Sharpe ratio: 12.4
Top performer sources: hyperdash,coinmarketman
```

## Need Help?

1. Check the guides above
2. Run with `--help` for options
3. Review error messages carefully
4. Check [BUG_FIXES.md](BUG_FIXES.md) for known issues
