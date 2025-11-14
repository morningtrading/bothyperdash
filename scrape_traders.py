#!/usr/bin/env python3
"""
Scrape trader addresses from hyperdash.info/top-traders
"""
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def setup_driver():
    """Setup Chrome driver with options"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in background
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(options=chrome_options)
    return driver

def extract_addresses_from_page(driver):
    """Extract all trader addresses from the current page"""
    addresses = []

    # Wait for page to load
    time.sleep(2)

    # Look for addresses - they typically start with "0x" for Ethereum addresses
    # Try multiple strategies to find addresses

    # Strategy 1: Find all text that looks like Ethereum addresses
    page_source = driver.page_source
    eth_address_pattern = r'0x[a-fA-F0-9]{40}'
    found_addresses = re.findall(eth_address_pattern, page_source)
    addresses.extend(found_addresses)

    # Strategy 2: Look for common table/list elements
    try:
        # Try to find trader rows in a table
        rows = driver.find_elements(By.CSS_SELECTOR, 'tr, .trader-row, .trader-item, [class*="trader"]')
        for row in rows:
            text = row.text
            addr_matches = re.findall(eth_address_pattern, text)
            addresses.extend(addr_matches)
    except NoSuchElementException:
        pass

    # Remove duplicates while preserving order
    seen = set()
    unique_addresses = []
    for addr in addresses:
        addr_lower = addr.lower()
        if addr_lower not in seen:
            seen.add(addr_lower)
            unique_addresses.append(addr)

    return unique_addresses

def get_total_pages(driver):
    """Try to determine total number of pages"""
    try:
        # Look for pagination elements
        pagination_selectors = [
            '.pagination',
            '[class*="pagination"]',
            '[class*="page-"]',
            'nav[aria-label*="pagination"]'
        ]

        for selector in pagination_selectors:
            try:
                pagination = driver.find_element(By.CSS_SELECTOR, selector)
                # Extract page numbers
                page_nums = re.findall(r'\b(\d+)\b', pagination.text)
                if page_nums:
                    return max([int(p) for p in page_nums])
            except NoSuchElementException:
                continue

        # If no pagination found, assume single page or check URL parameters
        return 1
    except Exception as e:
        print(f"Error determining total pages: {e}")
        return 1

def scrape_all_pages(base_url, max_pages=100):
    """Scrape trader addresses from all pages"""
    driver = setup_driver()
    all_addresses = []

    try:
        # Load first page
        print(f"Loading {base_url}...")
        driver.get(base_url)
        time.sleep(3)  # Wait for initial load

        # Get total pages
        total_pages = get_total_pages(driver)
        print(f"Detected {total_pages} pages")

        # If we can't determine pages, try pagination
        page = 1
        no_new_addresses_count = 0

        while page <= min(max_pages, total_pages if total_pages > 1 else max_pages):
            print(f"\nScraping page {page}...")

            # Extract addresses from current page
            addresses = extract_addresses_from_page(driver)
            new_addresses = [addr for addr in addresses if addr not in all_addresses]

            if new_addresses:
                print(f"Found {len(new_addresses)} new addresses on page {page}")
                all_addresses.extend(new_addresses)
                no_new_addresses_count = 0
            else:
                print(f"No new addresses found on page {page}")
                no_new_addresses_count += 1

                # If we haven't found new addresses for 3 consecutive pages, stop
                if no_new_addresses_count >= 3:
                    print("No new addresses found for 3 consecutive attempts. Stopping.")
                    break

            # Try to go to next page
            next_page_found = False

            # Strategy 1: Try URL parameter (page, p, offset, etc.)
            url_params = [
                f"{base_url}?page={page + 1}",
                f"{base_url}?p={page + 1}",
                f"{base_url}/{page + 1}",
            ]

            for url in url_params:
                try:
                    current_url = driver.current_url
                    driver.get(url)
                    time.sleep(2)

                    # Check if URL actually changed or page content changed
                    if driver.current_url != current_url or driver.current_url == url:
                        next_page_found = True
                        page += 1
                        break
                except Exception:
                    continue

            if next_page_found:
                continue

            # Strategy 2: Try clicking "Next" button
            next_button_selectors = [
                '//button[contains(text(), "Next")]',
                '//a[contains(text(), "Next")]',
                '//button[contains(@class, "next")]',
                '//a[contains(@class, "next")]',
                '//*[@aria-label="Next"]',
                '//*[@aria-label="Next page"]'
            ]

            for selector in next_button_selectors:
                try:
                    next_button = driver.find_element(By.XPATH, selector)
                    if next_button.is_enabled():
                        next_button.click()
                        time.sleep(2)
                        next_page_found = True
                        page += 1
                        break
                except (NoSuchElementException, Exception):
                    continue

            if not next_page_found:
                print("Could not find next page. Stopping.")
                break

        print(f"\n{'='*50}")
        print(f"Scraping complete!")
        print(f"Total unique addresses found: {len(all_addresses)}")

        return all_addresses

    finally:
        driver.quit()

def main():
    """Main function"""
    base_url = "https://hyperdash.info/top-traders"

    print("Starting scraper for hyperdash.info/top-traders")
    print("This will use Selenium with Chrome in headless mode\n")

    addresses = scrape_all_pages(base_url)

    # Save to file
    output_file = "trader_addresses.txt"
    with open(output_file, 'w') as f:
        for addr in addresses:
            f.write(f"{addr}\n")

    print(f"\nAddresses saved to {output_file}")

    # Also save as CSV with index
    csv_file = "trader_addresses.csv"
    with open(csv_file, 'w') as f:
        f.write("rank,address\n")
        for i, addr in enumerate(addresses, 1):
            f.write(f"{i},{addr}\n")

    print(f"Addresses also saved to {csv_file}")

if __name__ == "__main__":
    main()
