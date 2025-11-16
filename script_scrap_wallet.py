#!/usr/bin/env python3
"""
Unified wallet scraper for multiple sources
Supports: Hyperdash, Coinglass, CoinMarketMan (with auth)
Output: scrapped_wallet_library.csv
"""
import time
import re
import argparse
import csv
import os
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException
)


def setup_driver(headless=True):
    """Setup Chrome driver with anti-detection options"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

    # Additional stealth options
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
    })

    driver = webdriver.Chrome(options=chrome_options)

    # Execute CDP commands to hide automation
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


def login_coinmarketman(driver, email, password):
    """Login to CoinMarketMan to access full data"""
    print("  Attempting to login to CoinMarketMan...")

    try:
        # Look for sign-in button or link
        wait = WebDriverWait(driver, 10)

        # Try different selectors for sign-in button
        sign_in_selectors = [
            "//button[contains(text(), 'Sign')]",
            "//a[contains(text(), 'Sign')]",
            "//button[contains(text(), 'Log')]",
            "//a[contains(text(), 'Log')]",
            "//*[@id='sign-in']",
            "//*[contains(@class, 'signin')]",
            "//*[contains(@class, 'login')]"
        ]

        sign_in_button = None
        for selector in sign_in_selectors:
            try:
                sign_in_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                print(f"    Found sign-in button with selector: {selector}")
                break
            except:
                continue

        if sign_in_button:
            sign_in_button.click()
            time.sleep(2)
            print("    Clicked sign-in button")

        # Wait for email input field
        email_input = wait.until(EC.presence_of_element_located((
            By.XPATH, "//input[@type='email' or @name='email' or contains(@placeholder, 'mail')]"
        )))
        print("    Found email input")

        # Enter email
        email_input.clear()
        email_input.send_keys(email)
        time.sleep(0.5)

        # Find password input
        password_input = driver.find_element(By.XPATH,
            "//input[@type='password' or @name='password' or contains(@placeholder, 'assword')]"
        )
        print("    Found password input")

        # Enter password
        password_input.clear()
        password_input.send_keys(password)
        time.sleep(0.5)

        # Find and click submit button
        submit_selectors = [
            "//button[@type='submit']",
            "//button[contains(text(), 'Sign')]",
            "//button[contains(text(), 'Log')]",
            "//button[contains(text(), 'Continue')]"
        ]

        for selector in submit_selectors:
            try:
                submit_button = driver.find_element(By.XPATH, selector)
                submit_button.click()
                print("    Clicked submit button")
                break
            except:
                continue

        # Wait for login to complete (check for successful navigation or element change)
        time.sleep(5)
        print("    Login attempt complete, waiting for page to update...")
        time.sleep(5)

        return True

    except Exception as e:
        print(f"    Login error: {e}")
        print("    Continuing without login (will only get first 50 results)")
        return False


def scrape_hyperdash(driver, max_pages=10):
    """Scrape addresses from Hyperdash top-traders"""
    url = "https://hyperdash.info/top-traders"
    print(f"Scraping from Hyperdash: {url}")

    driver.get(url)
    time.sleep(3)

    addresses = []
    page = 1

    while page <= max_pages:
        print(f"  Scraping page {page}...")
        time.sleep(3)

        # Scroll to load content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Find addresses
        page_source = driver.page_source
        eth_address_pattern = r'0x[a-fA-F0-9]{40}'
        found_addresses = re.findall(eth_address_pattern, page_source)

        # Remove duplicates
        new_addresses = [addr for addr in found_addresses if addr not in addresses]

        if new_addresses:
            print(f"    Found {len(new_addresses)} new addresses on page {page}")
            addresses.extend(new_addresses)
        else:
            print(f"    No new addresses on page {page}")

        # Try to go to next page
        if page >= max_pages:
            break

        next_button_selectors = [
            '//button[@aria-label="Next Page"]',
            '//*[@aria-label="Next Page"]',
        ]

        next_found = False
        for selector in next_button_selectors:
            try:
                next_button = driver.find_element(By.XPATH, selector)
                if next_button.get_attribute("disabled") is None:
                    next_button.click()
                    time.sleep(3)
                    page += 1
                    next_found = True
                    break
            except (NoSuchElementException, Exception):
                continue

        if not next_found:
            print(f"    No next button found. Stopping at page {page}.")
            break

    return addresses


def safe_click_pagination(driver, element):
    """Try multiple methods to click an element"""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.5)
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable(element))
        element.click()
        return True
    except ElementClickInterceptedException:
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except Exception:
            return False
    except Exception:
        return False


def scrape_coinglass(driver, max_pages=10, min_margin_k=True):
    """Scrape addresses from Coinglass"""
    url = "https://www.coinglass.com/hl/range/10"
    print(f"Scraping from Coinglass: {url}")

    driver.get(url)
    time.sleep(3)

    addresses = []
    page = 1

    for i in range(max_pages):
        print(f"  Scraping page {page}...")

        # Find table rows
        try:
            rows = driver.find_elements(By.CLASS_NAME, "ant-table-row-level-0")
            page_addresses = 0

            for row in rows:
                # Check margin requirement if specified
                if min_margin_k:
                    try:
                        margin_text = row.find_elements(By.CLASS_NAME, "ant-table-cell")[1].text
                        if "K" not in margin_text and "M" not in margin_text:
                            continue
                    except:
                        continue

                address = row.get_attribute("data-row-key")
                if address and address not in addresses:
                    addresses.append(address)
                    page_addresses += 1

            print(f"    Found {page_addresses} addresses on page {page}")
        except Exception as e:
            print(f"    Error extracting addresses: {e}")

        # Try to go to next page
        if page >= max_pages:
            break

        pagination = driver.find_elements(By.CLASS_NAME, "rc-pagination-item")
        clicked = False

        for p in pagination:
            if str(p.text) == str(page + 1):
                print(f"    Navigating to page {page + 1}...")
                if safe_click_pagination(driver, p):
                    page += 1
                    clicked = True
                    time.sleep(2)
                    break

        if not clicked:
            print(f"    Could not navigate to next page. Stopping at page {page}.")
            break

    return addresses


def scrape_coinmarketman(driver, segment="money-printer", email=None, password=None):
    """Scrape addresses from CoinMarketMan Hypertracker

    Available segments:
    - money-printer (+$1M PNL)
    - smart-money
    - grinder
    - humble-earner
    - exit-liquidity
    - semi-rekt
    - full-rekt
    - giga-rekt

    Note: Without authentication, only first 50 results are available.
          With login, you can access all results (e.g., 427 for money-printer).
    """
    url = f"https://app.coinmarketman.com/hypertracker/segments/{segment}"
    print(f"Scraping from CoinMarketMan: {url}")

    driver.get(url)
    print("  Waiting for page to load...")
    time.sleep(15)  # Initial load time for React app

    # Attempt login if credentials provided
    if email and password:
        login_coinmarketman(driver, email, password)
        # Give extra time for authenticated content to load
        time.sleep(5)
    else:
        print("  No credentials provided - will only get first 50 public results")
        print("  Use --cmm-email and --cmm-password to access all data")

    addresses = []
    last_count = 0
    no_change_count = 0

    print("  Scrolling to load all rows...")

    # Find the virtual scroller element
    try:
        data_grid = driver.find_element(By.CLASS_NAME, "MuiDataGrid-virtualScroller")
        print("    Found DataGrid virtual scroller")

        # First, scroll to absolute bottom to trigger loading all data
        print("    Scrolling to bottom to trigger data load...")
        for _ in range(5):
            driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", data_grid)
            time.sleep(2)

        # Then scroll back to top
        driver.execute_script("arguments[0].scrollTo(0, 0)", data_grid)
        time.sleep(2)
        print("    Initial scan complete, now scrolling through content...")
    except:
        data_grid = None
        print("    Using whole page scrolling")

    # Scroll multiple times to trigger virtualized content loading
    for scroll_attempt in range(100):
        # Scroll within the DataGrid or whole page
        if data_grid:
            # Small incremental scrolls to ensure all rows render
            driver.execute_script("arguments[0].scrollBy(0, 200)", data_grid)
            time.sleep(0.8)  # Longer wait for virtual content to render

            # Every 10 scrolls, jump to bottom to ensure we reach the end
            if scroll_attempt % 10 == 9:
                driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight)", data_grid)
                time.sleep(1.5)
        else:
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(0.8)

        # Check for new addresses every 3 scrolls
        if scroll_attempt % 3 == 2:
            # Extract addresses
            page_source = driver.page_source
            eth_address_pattern = r'0x[a-fA-F0-9]{40}'
            found_addresses = re.findall(eth_address_pattern, page_source)

            # Remove duplicates while preserving order
            unique_addresses = []
            seen = set()
            for addr in found_addresses:
                if addr.lower() not in seen:
                    unique_addresses.append(addr)
                    seen.add(addr.lower())

            current_count = len(unique_addresses)

            if current_count > last_count:
                print(f"    Progress: Found {current_count} unique addresses (scroll {scroll_attempt + 1})")
                last_count = current_count
                no_change_count = 0
                addresses = unique_addresses
            else:
                no_change_count += 1
                if no_change_count >= 6:
                    print(f"    No new addresses after {no_change_count * 3} scrolls. Stopping.")
                    break

    print(f"  Total unique addresses found: {len(addresses)}")
    return addresses


def save_to_csv(addresses, source, output_file="scrapped_wallet_library.csv"):
    """Save or append addresses to CSV file"""
    file_exists = Path(output_file).exists()
    timestamp = datetime.now().isoformat()

    # Read existing addresses if file exists
    existing_addresses = set()
    if file_exists:
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_addresses.add(row['address'].lower())

    # Prepare new rows (only unique ones)
    new_rows = []
    new_count = 0
    duplicate_count = 0

    for addr in addresses:
        if addr.lower() not in existing_addresses:
            new_rows.append({
                'address': addr,
                'source': source,
                'scraped_at': timestamp
            })
            existing_addresses.add(addr.lower())
            new_count += 1
        else:
            duplicate_count += 1

    # Write to file
    mode = 'a' if file_exists else 'w'
    with open(output_file, mode, newline='') as f:
        fieldnames = ['address', 'source', 'scraped_at']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerows(new_rows)

    print(f"\n{'='*60}")
    print(f"Results saved to: {output_file}")
    print(f"  New addresses added: {new_count}")
    print(f"  Duplicates skipped: {duplicate_count}")
    print(f"  Total in file: {len(existing_addresses)}")
    print(f"{'='*60}")

    return new_count, duplicate_count


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Scrape wallet addresses from multiple sources',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape 10 pages from Hyperdash
  python3 script_scrap_wallet.py --source hyperdash --pages 10

  # Scrape 20 pages from Coinglass
  python3 script_scrap_wallet.py --source coinglass --pages 20

  # Scrape from CoinMarketMan money-printer segment (public - 50 results)
  python3 script_scrap_wallet.py --source coinmarketman

  # Scrape from CoinMarketMan with authentication (all results - 400+)
  python3 script_scrap_wallet.py -s cmm --cmm-email your@email.com --cmm-password yourpass

  # Or use environment variables for credentials
  export CMM_EMAIL="your@email.com"
  export CMM_PASSWORD="yourpassword"
  python3 script_scrap_wallet.py -s cmm

  # Scrape from all sources
  python3 script_scrap_wallet.py --source hyperdash --pages 5
  python3 script_scrap_wallet.py --source coinglass --pages 5
  python3 script_scrap_wallet.py --source cmm --cmm-email your@email.com --cmm-password yourpass

  # Use short form
  python3 script_scrap_wallet.py -s hyperdash -p 10
  python3 script_scrap_wallet.py -s cmm
        """
    )

    parser.add_argument(
        '--source', '-s',
        type=str,
        required=True,
        choices=['hyperdash', 'coinglass', 'coinmarketman', 'cmm'],
        help='Source to scrape from: hyperdash, coinglass, or coinmarketman (cmm)'
    )

    parser.add_argument(
        '--pages', '-p',
        type=int,
        default=10,
        help='Number of pages to scrape (default: 10)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default='scrapped_wallet_library.csv',
        help='Output CSV file (default: scrapped_wallet_library.csv)'
    )

    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='Run browser in headless mode (default: True)'
    )

    parser.add_argument(
        '--no-headless',
        action='store_false',
        dest='headless',
        help='Show browser window'
    )

    parser.add_argument(
        '--cmm-email',
        type=str,
        default=os.environ.get('CMM_EMAIL'),
        help='CoinMarketMan email (or set CMM_EMAIL env var)'
    )

    parser.add_argument(
        '--cmm-password',
        type=str,
        default=os.environ.get('CMM_PASSWORD'),
        help='CoinMarketMan password (or set CMM_PASSWORD env var)'
    )

    args = parser.parse_args()

    print("="*60)
    print(f"Wallet Scraper")
    print(f"Source: {args.source}")
    print(f"Pages: {args.pages}")
    print(f"Output: {args.output}")
    print(f"Headless: {args.headless}")
    print("="*60)
    print()

    driver = None
    try:
        # Initialize driver
        driver = setup_driver(headless=args.headless)

        # Scrape based on source
        source_name = args.source
        if args.source == 'hyperdash':
            addresses = scrape_hyperdash(driver, max_pages=args.pages)
        elif args.source == 'coinglass':
            addresses = scrape_coinglass(driver, max_pages=args.pages)
        elif args.source in ['coinmarketman', 'cmm']:
            # CoinMarketMan doesn't use pagination, just one segment
            addresses = scrape_coinmarketman(
                driver,
                segment="money-printer",
                email=args.cmm_email,
                password=args.cmm_password
            )
            source_name = 'coinmarketman'
        else:
            print(f"Unknown source: {args.source}")
            return

        print(f"\nTotal addresses scraped: {len(addresses)}")

        # Save to CSV
        if addresses:
            save_to_csv(addresses, source_name, args.output)
        else:
            print("No addresses found!")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
