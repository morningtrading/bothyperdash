# CoinMarketMan Manual Scraping Guide

This guide explains how to manually save CoinMarketMan pages and extract all wallet addresses (all 427+ instead of just 50).

## Why Manual Scraping?

CoinMarketMan requires authentication to see all 427+ wallets. Instead of automating the login (which is complex), you can manually save pages while logged in, and the script will extract all addresses.

## Step-by-Step Instructions

### 1. Login to CoinMarketMan

1. Open your browser and go to: https://app.coinmarketman.com/hypertracker/segments/money-printer
2. Click the sign-in/profile button
3. Login with your credentials:
   - Email: `morningtrader`
   - Password: `48E2mu7$S^Jt$-j`

### 2. Save Each Page as HTML

Once logged in, you should see all 427 wallets with pagination controls.

**For each page:**

1. Scroll down to make sure the DataGrid loads all rows on the current page
2. Right-click anywhere on the page → **"Save As"** (or press `Ctrl+S` / `Cmd+S`)
3. Choose **"Webpage, Complete"** or **"HTML Only"**
4. Save to: `/home/titus/bothyperdash/cmm_pages/`
5. Name it: `page_1.html`, `page_2.html`, `page_3.html`, etc.
6. Click the "Next" page button
7. Repeat steps 1-6 for all pages

**Tips:**
- You don't need to save images/CSS - "HTML Only" is fine
- Keep the filenames sequential: page_1.html, page_2.html, etc.
- If there are 427 wallets and 50 per page, you'll have about 9 pages

### 3. Run the Parser Script

Once you've saved all pages:

```bash
cd /home/titus/bothyperdash
python3 parse_cmm_detailed.py cmm_pages
```

**The script will:**
- ✅ Read all HTML files in `cmm_pages/` folder
- ✅ Extract all trader data (Rank, Wallet, Age, Perp Equity, Open Value, Leverage, Current Bias, 24h/7d/30d/All PNL)
- ✅ Remove duplicates automatically
- ✅ Save detailed data to `cmm_traders_detailed.csv`
- ✅ Add wallet addresses to `scrapped_wallet_library.csv`
- ✅ Show you how many new traders were found

### 4. Example Output

```
============================================================
CoinMarketMan Detailed Data Parser
Folder: cmm_pages
============================================================
Found 9 HTML file(s) in 'cmm_pages'

Processing: page_1.html
    Found 50 table rows
    Extracted 50 trader records

Processing: page_2.html
    Found 50 table rows
    Extracted 50 trader records

Processing: page_3.html
    Found 50 table rows
    Extracted 48 trader records

... [more pages] ...

Processing: page_9.html
    Found 27 table rows
    Extracted 27 trader records

============================================================
Detailed results saved to: cmm_traders_detailed.csv
  Total traders: 427
  Duplicates removed: 0
============================================================

Also updated scrapped_wallet_library.csv:
  New addresses added: 427
```

## Alternative: Use Different Folder

If you want to organize by segment or date:

```bash
# Create a custom folder
mkdir -p ~/cmm_money_printer_2025_01

# Save pages there, then run:
python3 parse_cmm_detailed.py ~/cmm_money_printer_2025_01
```

## Other Segments

You can also scrape other segments:

- Smart Money: https://app.coinmarketman.com/hypertracker/segments/smart-money
- Grinder: https://app.coinmarketman.com/hypertracker/segments/grinder
- Humble Earner: https://app.coinmarketman.com/hypertracker/segments/humble-earner
- Exit Liquidity: https://app.coinmarketman.com/hypertracker/segments/exit-liquidity
- Semi-Rekt: https://app.coinmarketman.com/hypertracker/segments/semi-rekt
- Full Rekt: https://app.coinmarketman.com/hypertracker/segments/full-rekt
- Giga-Rekt: https://app.coinmarketman.com/hypertracker/segments/giga-rekt

Just repeat the same process for each segment!

## Cleaning Up

After parsing, you can delete the HTML files to save space:

```bash
rm cmm_pages/*.html
```

The addresses are already in your `scrapped_wallet_library.csv` file!

## Quick Reference

```bash
# 1. Save pages manually to cmm_pages/ folder while logged in

# 2. Parse all saved HTML files (extracts all trader data)
python3 parse_cmm_detailed.py cmm_pages

# 3. View results
head -10 cmm_traders_detailed.csv

# 4. (Optional) Clean up HTML files
rm cmm_pages/*.html

# 5. Run analysis as usual
python3 script_portfolio.py --fetch-positions --rate-limit 1.0
```

---

**Note:** This manual method is actually more reliable than automated login and gives you full control over which segments and pages you want to scrape!
