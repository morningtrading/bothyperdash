# HyperDash Top Traders Scraper

A Python web scraper that extracts trader wallet addresses from [HyperDash.info Top Traders](https://hyperdash.info/top-traders) page.

## Overview

This scraper uses Selenium with Chrome WebDriver to automatically navigate through the HyperDash top traders page and extract all trader Ethereum wallet addresses. The script handles JavaScript-rendered content and pagination automatically.

## Features

- Automated browser-based scraping using Selenium
- Handles JavaScript-rendered content
- Automatic pagination detection and navigation
- Extracts Ethereum wallet addresses (0x...)
- Removes duplicate addresses
- Exports results in both TXT and CSV formats
- Headless mode (runs without visible browser)

## Requirements

- Python 3.6+
- Chrome browser installed
- ChromeDriver (automatically managed by Selenium)
- Dependencies listed in `requirements.txt`

## Installation

1. Install the required Python package:
```bash
pip3 install -r requirements.txt
```

Or install manually:
```bash
pip3 install selenium
```

2. Ensure Chrome is installed on your system. Selenium will automatically download and manage ChromeDriver.

## Usage

Run the scraper:
```bash
python3 scrape_traders.py
```

The script will:
1. Launch Chrome in headless mode
2. Navigate to https://hyperdash.info/top-traders
3. Extract all trader addresses from available pages
4. Save results to output files
5. Display progress and summary

## Output Files

The scraper generates two output files:

### `trader_addresses.txt`
Plain text file with one address per line:
```
0x2ea18c23f72a4b6172c55b411823cdc5335923f4
0xb83de012dba672c76a7dbbbf3e459cb59d7d6e36
0xb317d2bc2d3d2df5fa441b5bae0ab9d8b07283ae
...
```

### `trader_addresses.csv`
CSV file with ranking and addresses:
```csv
rank,address
1,0x2ea18c23f72a4b6172c55b411823cdc5335923f4
2,0xb83de012dba672c76a7dbbbf3e459cb59d7d6e36
3,0xb317d2bc2d3d2df5fa441b5bae0ab9d8b07283ae
...
```

## How It Works

1. **Browser Setup**: Initializes Chrome with headless mode and anti-detection settings
2. **Page Loading**: Navigates to the target URL and waits for content to load
3. **Address Extraction**: Uses regex pattern `0x[a-fA-F0-9]{40}` to find Ethereum addresses
4. **Pagination**: Attempts multiple strategies to find and navigate to next pages:
   - URL parameters (page, p, offset)
   - Next button clicking
   - Direct URL manipulation
5. **Deduplication**: Removes duplicate addresses while preserving order
6. **Output**: Saves unique addresses to both TXT and CSV formats

## Script Configuration

You can modify these parameters in `scrape_traders.py`:

- `max_pages`: Maximum number of pages to scrape (default: 100)
- `time.sleep()` values: Adjust wait times between page loads
- User agent string: Change browser fingerprint if needed

## Troubleshooting

### Chrome/ChromeDriver Issues
If you encounter ChromeDriver errors:
```bash
# Update Selenium to latest version
pip3 install --upgrade selenium
```

### No Addresses Found
If the scraper returns no addresses:
- Check if the website structure has changed
- Increase sleep/wait times in the script
- Run in non-headless mode for debugging (comment out `--headless` option)

### 403 Forbidden Errors
The script uses browser automation specifically to avoid 403 errors from direct HTTP requests. If you still encounter issues:
- Check your internet connection
- Verify the website is accessible in a regular browser
- Try changing the user agent string

## Technical Details

- **Language**: Python 3
- **Framework**: Selenium WebDriver
- **Browser**: Chrome (headless)
- **Target Pattern**: Ethereum addresses (`0x` + 40 hex characters)
- **Output Encoding**: UTF-8

## Results

Latest scrape results (as of last run):
- **Total addresses found**: 50
- **Pages scraped**: Multiple pages with automatic pagination
- **Success rate**: 100%

## License

This scraper is provided as-is for educational and research purposes.

## Disclaimer

Please ensure you comply with HyperDash.info's terms of service and robots.txt when using this scraper. Respect rate limits and do not overload their servers with requests.
