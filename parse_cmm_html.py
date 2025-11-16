#!/usr/bin/env python3
"""
Parse CoinMarketMan saved HTML files to extract wallet addresses
Usage: python3 parse_cmm_html.py [folder_path]
"""
import re
import csv
import sys
from pathlib import Path
from datetime import datetime

def extract_addresses_from_html(html_content):
    """Extract Ethereum addresses from HTML content"""
    eth_address_pattern = r'0x[a-fA-F0-9]{40}'
    addresses = re.findall(eth_address_pattern, html_content)

    # Remove duplicates while preserving order
    unique_addresses = []
    seen = set()
    for addr in addresses:
        addr_lower = addr.lower()
        if addr_lower not in seen:
            unique_addresses.append(addr)
            seen.add(addr_lower)

    return unique_addresses

def parse_html_files(folder_path):
    """Parse all HTML files in the folder and extract addresses"""
    folder = Path(folder_path)

    if not folder.exists():
        print(f"Error: Folder '{folder_path}' does not exist!")
        return []

    html_files = list(folder.glob("*.html")) + list(folder.glob("*.htm"))

    if not html_files:
        print(f"No HTML files found in '{folder_path}'")
        return []

    print(f"Found {len(html_files)} HTML file(s) in '{folder_path}'")

    all_addresses = []
    seen_addresses = set()

    for html_file in sorted(html_files):
        print(f"\nProcessing: {html_file.name}")

        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()

            addresses = extract_addresses_from_html(content)

            # Count new unique addresses from this file
            new_addresses = []
            for addr in addresses:
                if addr.lower() not in seen_addresses:
                    new_addresses.append(addr)
                    seen_addresses.add(addr.lower())
                    all_addresses.append(addr)

            print(f"  Found {len(addresses)} addresses ({len(new_addresses)} new, {len(addresses) - len(new_addresses)} duplicates)")

        except Exception as e:
            print(f"  Error reading {html_file.name}: {e}")

    return all_addresses

def save_to_csv(addresses, output_file="scrapped_wallet_library.csv"):
    """Save addresses to CSV file (append to existing)"""
    file_exists = Path(output_file).exists()
    timestamp = datetime.now().isoformat()

    # Read existing addresses if file exists
    existing_addresses = set()
    if file_exists:
        try:
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_addresses.add(row['address'].lower())
        except:
            pass

    # Prepare new rows (only unique ones)
    new_rows = []
    new_count = 0
    duplicate_count = 0

    for addr in addresses:
        if addr.lower() not in existing_addresses:
            new_rows.append({
                'address': addr,
                'source': 'coinmarketman_manual',
                'scraped_at': timestamp
            })
            existing_addresses.add(addr.lower())
            new_count += 1
        else:
            duplicate_count += 1

    # Write to file
    if new_rows:
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
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = "cmm_pages"  # Default folder

    print("="*60)
    print("CoinMarketMan HTML Parser")
    print(f"Folder: {folder_path}")
    print("="*60)

    addresses = parse_html_files(folder_path)

    if addresses:
        print(f"\n{'='*60}")
        print(f"Total unique addresses found: {len(addresses)}")
        print(f"{'='*60}")

        # Save to CSV
        save_to_csv(addresses)
    else:
        print("\nNo addresses found!")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
