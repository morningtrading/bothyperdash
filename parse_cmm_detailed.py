#!/usr/bin/env python3
"""
Parse CoinMarketMan saved HTML files to extract complete trader data
Extracts: Rank, Wallet, Age, Perp Equity, Open Value, Leverage, Current Bias,
          24h PNL, 7d PNL, 30d PNL, All PNL
Usage: python3 parse_cmm_detailed.py [folder_path]
"""
import re
import csv
import sys
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

def parse_trader_data_from_html(html_content, file_name):
    """Parse complete trader data from CoinMarketMan HTML using BeautifulSoup"""
    soup = BeautifulSoup(html_content, 'html.parser')

    traders = []

    # Find all rows in the DataGrid
    rows = soup.find_all('div', class_='MuiDataGrid-row')

    print(f"    Found {len(rows)} table rows")

    # Map of data-field to our field names
    field_mapping = {
        'age': 'age',
        'address': 'wallet',
        'perpEquity': 'perp_equity',
        'bias': 'current_bias',
        'openValue': 'open_value',
        'exposureRatio': 'leverage',
        'pnlDay': 'pnl_24h',
        'pnlWeek': 'pnl_7d',
        'pnlMonth': 'pnl_30d',
        'pnlAllTime': 'pnl_all'
    }

    for idx, row in enumerate(rows):
        try:
            # Get all cells in the row
            cells = row.find_all('div', class_='MuiDataGrid-cell')

            trader_data = {
                'rank': idx + 1,
                'wallet': None,
                'age': None,
                'perp_equity': None,
                'open_value': None,
                'leverage': None,
                'current_bias': None,
                'pnl_24h': None,
                'pnl_7d': None,
                'pnl_30d': None,
                'pnl_all': None,
                'source_file': file_name
            }

            # Extract data using data-field attributes
            for cell in cells:
                data_field = cell.get('data-field', '')
                cell_text = cell.get_text(strip=True)

                # Skip empty cells
                if not cell_text or cell_text == '—' or cell_text == '-':
                    continue

                # Map the field
                if data_field in field_mapping:
                    field_name = field_mapping[data_field]
                    trader_data[field_name] = cell_text

            # If no wallet address found or address is truncated, search the entire row HTML
            if not trader_data['wallet'] or '...' in trader_data['wallet']:
                # Search for full Ethereum address in the row HTML
                row_html = str(row)
                full_addresses = re.findall(r'0x[a-fA-F0-9]{40}', row_html)
                if full_addresses:
                    # Use the first full address found (should be unique per row)
                    trader_data['wallet'] = full_addresses[0]

            # Only add if we have at least a wallet address
            if trader_data['wallet']:
                traders.append(trader_data)

        except Exception as e:
            print(f"      Error parsing row {idx}: {e}")
            continue

    return traders

def parse_trader_data_regex(html_content, file_name):
    """Fallback: Extract trader data using regex patterns"""
    traders = []

    # Find all wallet addresses
    eth_address_pattern = r'0x[a-fA-F0-9]{40}'
    addresses = re.findall(eth_address_pattern, html_content)

    # Remove duplicates while preserving order
    unique_addresses = []
    seen = set()
    for addr in addresses:
        if addr.lower() not in seen:
            unique_addresses.append(addr)
            seen.add(addr.lower())

    print(f"    Found {len(unique_addresses)} unique addresses (regex fallback)")

    for idx, addr in enumerate(unique_addresses):
        traders.append({
            'rank': idx + 1,
            'wallet': addr,
            'age': None,
            'perp_equity': None,
            'open_value': None,
            'leverage': None,
            'current_bias': None,
            'pnl_24h': None,
            'pnl_7d': None,
            'pnl_30d': None,
            'pnl_all': None,
            'source_file': file_name
        })

    return traders

def parse_html_files(folder_path):
    """Parse numbered HTML files (1.html through 10.html) in the folder"""
    folder = Path(folder_path)

    if not folder.exists():
        print(f"Error: Folder '{folder_path}' does not exist!")
        return []

    # Look for numbered files 1.html through 10.html
    html_files = []
    for i in range(1, 11):
        file_path = folder / f"{i}.html"
        if file_path.exists():
            html_files.append(file_path)

    if not html_files:
        print(f"No numbered HTML files (1.html - 10.html) found in '{folder_path}'")
        return []

    print(f"Found {len(html_files)} HTML file(s) in '{folder_path}'")

    all_traders = []

    for html_file in sorted(html_files):
        print(f"\nProcessing: {html_file.name}")

        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Try BeautifulSoup parsing first
            try:
                traders = parse_trader_data_from_html(content, html_file.name)
            except Exception as e:
                print(f"    BeautifulSoup parsing failed: {e}")
                print(f"    Falling back to regex extraction...")
                traders = parse_trader_data_regex(content, html_file.name)

            print(f"    Extracted {len(traders)} trader records")
            all_traders.extend(traders)

        except Exception as e:
            print(f"  Error reading {html_file.name}: {e}")

    return all_traders

def save_to_csv(traders, output_file="cmm_traders_detailed.csv"):
    """Save detailed trader data to CSV"""
    if not traders:
        print("No trader data to save!")
        return

    # Remove duplicates based on wallet address
    seen_wallets = set()
    unique_traders = []
    duplicate_count = 0

    for trader in traders:
        wallet = trader['wallet']
        if wallet and wallet.lower() not in seen_wallets:
            unique_traders.append(trader)
            seen_wallets.add(wallet.lower())
        else:
            duplicate_count += 1

    # Write to CSV
    with open(output_file, 'w', newline='') as f:
        fieldnames = [
            'rank', 'wallet', 'age', 'perp_equity', 'open_value',
            'leverage', 'current_bias', 'pnl_24h', 'pnl_7d',
            'pnl_30d', 'pnl_all', 'source_file'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_traders)

    print(f"\n{'='*60}")
    print(f"Detailed results saved to: {output_file}")
    print(f"  Total traders: {len(unique_traders)}")
    print(f"  Duplicates removed: {duplicate_count}")
    print(f"{'='*60}")

    return len(unique_traders)

def also_update_wallet_library(traders):
    """Also add wallets to the main scrapped_wallet_library.csv"""
    if not traders:
        return

    output_file = "scrapped_wallet_library.csv"
    file_exists = Path(output_file).exists()
    timestamp = datetime.now().isoformat()

    # Read existing addresses
    existing_addresses = set()
    if file_exists:
        try:
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_addresses.add(row['address'].lower())
        except:
            pass

    # Prepare new rows
    new_rows = []
    new_count = 0

    for trader in traders:
        wallet = trader['wallet']
        if wallet and wallet.lower() not in existing_addresses:
            new_rows.append({
                'address': wallet,
                'source': 'coinmarketman_manual',
                'scraped_at': timestamp
            })
            existing_addresses.add(wallet.lower())
            new_count += 1

    # Write to file
    if new_rows:
        mode = 'a' if file_exists else 'w'
        with open(output_file, mode, newline='') as f:
            fieldnames = ['address', 'source', 'scraped_at']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerows(new_rows)

        print(f"\nAlso updated {output_file}:")
        print(f"  New addresses added: {new_count}")

def filter_inactive_traders():
    """Filter out traders with pnl_30d=$0 or perp_equity=N/A"""
    detailed_file = "cmm_traders_detailed.csv"
    wallet_file = "scrapped_wallet_library.csv"

    if not Path(detailed_file).exists():
        return

    print(f"\n{'='*60}")
    print("Filtering inactive traders...")
    print(f"{'='*60}")

    # Read and filter detailed trader data
    filtered_traders = []
    original_count = 0

    with open(detailed_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            original_count += 1
            pnl_30d = row['pnl_30d'].strip()
            perp_equity = row['perp_equity'].strip()

            # Skip if pnl_30d is $0 or perp_equity is N/A
            if pnl_30d in ['$0', '0', '-$0'] or perp_equity in ['N/A', 'NA', '', '$0']:
                continue

            filtered_traders.append(row)

    removed_count = original_count - len(filtered_traders)

    # Save filtered detailed data
    with open(detailed_file, 'w', newline='') as f:
        fieldnames = ['rank', 'wallet', 'age', 'perp_equity', 'open_value', 'leverage',
                     'current_bias', 'pnl_24h', 'pnl_7d', 'pnl_30d', 'pnl_all', 'source_file']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(filtered_traders)

    # Get list of valid wallets
    valid_wallets = {row['wallet'].lower() for row in filtered_traders}

    # Filter wallet library
    if Path(wallet_file).exists():
        wallet_rows = []
        with open(wallet_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['address'].lower() in valid_wallets:
                    wallet_rows.append(row)

        # Save filtered wallet library
        with open(wallet_file, 'w', newline='') as f:
            fieldnames = ['address', 'source', 'scraped_at']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(wallet_rows)

        print(f"Removed {removed_count} inactive traders (pnl_30d=$0 or perp_equity=N/A)")
        print(f"Active traders remaining: {len(filtered_traders)}")
        print(f"Wallets in library: {len(wallet_rows)}")

    print(f"{'='*60}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = "cmm_pages"

    print("="*60)
    print("CoinMarketMan Detailed Data Parser")
    print(f"Folder: {folder_path}")
    print("="*60)

    traders = parse_html_files(folder_path)

    if traders:
        # Save detailed data
        save_to_csv(traders)

        # Also update main wallet library
        also_update_wallet_library(traders)

        # Filter out inactive traders
        filter_inactive_traders()
    else:
        print("\nNo trader data found!")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
