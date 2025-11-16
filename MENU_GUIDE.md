# Trader Menu - Quick Start Guide

## Launch the Menu

```bash
./trader_menu.sh
```

## Menu Options

### 1️⃣ Scrape wallets from Hyperdash
- Scrapes trader addresses from https://hyperdash.info/top-traders
- Choose number of pages (default: 10)
- Addresses saved to `scrapped_wallet_library.csv`

### 2️⃣ Scrape wallets from Coinglass
- Scrapes trader addresses from https://www.coinglass.com/hl/range/10
- Choose number of pages (default: 10)
- Addresses saved to `scrapped_wallet_library.csv`

### 3️⃣ Manual wallet input
- Enter wallet addresses manually
- One address per line
- Validates Ethereum address format (0x + 40 hex chars)
- Adds to `scrapped_wallet_library.csv`

### 4️⃣ Analyze existing wallet library
- Analyzes all wallets in `scrapped_wallet_library.csv`
- Options:
  - Limit number of wallets to analyze
  - Fetch current positions (y/n)
- Creates:
  - `portfolio_analysis.csv` - All wallets
  - `portfolio_analysis_filtered.csv` - Top traders only
  - `portfolio_analysis_positions.csv` - Current positions (if requested)

### 5️⃣ Full workflow (Scrape + Analyze)
- Complete end-to-end process
- Choose source: Hyperdash, Coinglass, or Both
- Automatically runs analysis with position fetching
- Copies results to Dropbox

### 6️⃣ Settings
- Pages to scrape (default: 10)
- Min Sharpe ratio (default: 1.5)
- Max Drawdown (default: 0.5)
- API Rate limit (default: 1.0s)

### 7️⃣ View results
- Shows top traders summary
- Shows current positions summary
- Quick preview without opening files

### 0️⃣ Exit
- Quit the menu

## Output Files

### Local Files (bothyperdash directory)
- `scrapped_wallet_library.csv` - All scraped wallet addresses
- `portfolio_analysis.csv` - Full analysis results
- `portfolio_analysis_filtered.csv` - Top traders only
- `portfolio_analysis_positions.csv` - Current positions with exposure %

### Dropbox Files (/home/titus/Dropbox/_CURRENT/)
- `freshwallets.rtf` - Formatted results in RTF
- `freshwallets_filtered.csv` - Copy of filtered traders
- `freshwallets_positions.csv` - Copy of positions data
- `freshwallets_full.csv` - Copy of full analysis

## Quick Workflows

### Simple Workflow (Recommended)
```
1. Launch: ./trader_menu.sh
2. Choose option 5 (Full workflow)
3. Select Hyperdash (option 1)
4. Enter number of pages (e.g., 20)
5. Wait for completion
6. Results automatically copied to Dropbox!
```

### Advanced Workflow
```
1. Scrape from Hyperdash (option 1, 30 pages)
2. Scrape from Coinglass (option 2, 10 pages)
3. Add manual addresses if needed (option 3)
4. Analyze all wallets (option 4)
5. View results (option 7)
6. Results in Dropbox!
```

### Manual Address Workflow
```
1. Choose option 3 (Manual input)
2. Paste addresses (one per line)
3. Press Enter on empty line to finish
4. Choose option 4 (Analyze)
5. View results in Dropbox
```

## Tips

💡 **Start Small**: Try 5-10 pages first to test
💡 **Rate Limiting**: If you get HTTP 429 errors, increase rate limit in settings
💡 **Batch Processing**: Scrape in smaller batches to avoid API limits
💡 **Fresh Data**: Re-run analysis to get updated positions
💡 **Combine Sources**: Use both Hyperdash + Coinglass for comprehensive coverage

## Example Session

```bash
$ ./trader_menu.sh

================================
HYPERLIQUID TRADER ANALYSIS SUITE
================================

1) Scrape wallets from Hyperdash
2) Scrape wallets from Coinglass
3) Manual wallet input
4) Analyze existing wallet library
5) Full workflow (Scrape + Analyze)
6) Settings
7) View results
0) Exit

Current Settings:
  Pages to scrape: 10
  Min Sharpe: 1.5
  Max Drawdown: 0.5
  Rate Limit: 1.0s

Enter choice: 5

[Scrapes wallets...]
[Analyzes performance...]
[Fetches positions...]

✓ Results copied to: /home/titus/Dropbox/_CURRENT/freshwallets.rtf
✓ CSV files also copied to: /home/titus/Dropbox/_CURRENT/
```

## Troubleshooting

**"No wallet library found"**
- Run option 1 or 2 to scrape wallets first

**"HTTP 429 errors"**
- Increase rate limit in settings (option 6)
- Reduce number of wallets analyzed

**"Invalid address format"**
- Ensure addresses start with 0x
- Must be exactly 42 characters (0x + 40 hex)

**Menu not working**
- Make executable: `chmod +x trader_menu.sh`
- Run from bothyperdash directory
