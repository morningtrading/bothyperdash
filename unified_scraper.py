#!/usr/bin/env python3
"""
Unified Multi-Source Wallet Scraper and Analyzer
Scrapes from all 3 sources, merges data, enriches with Hyperliquid API, and ranks by performance
"""
import argparse
import asyncio
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np
import aiohttp
from aiolimiter import AsyncLimiter

# Import scraping functions from existing modules
from script_scrap_wallet import (
    setup_driver,
    scrape_hyperdash,
    scrape_coinglass,
    scrape_coinmarketman
)

# Import analysis functions from existing modules  
from script_portfolio import (
    get_portfolio_data,
    get_clearinghouse_state,
    analyze_address,
    extract_position_pnl,
    safe_float
)

# Configuration
API_URL = "https://api.hyperliquid.xyz/info"
HEADERS = {"Content-Type": "application/json"}
DEFAULT_OUTPUT = "big_file.csv"
DEFAULT_RATE_LIMIT = 0.5


async def fetch_wallet_metadata(session: aiohttp.ClientSession, address: str):
    """Fetch additional wallet metadata from Hyperliquid API"""
    payload = {"type": "metaAndAssetCtxs"}
    try:
        async with session.post(API_URL, json=payload, headers=HEADERS, 
                              timeout=aiohttp.ClientTimeout(total=20)) as r:
            if r.status != 200:
                return address, None, f"HTTP {r.status}"
            data = await r.json(content_type=None)
            return address, data, None
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        return address, None, str(e)


async def enrich_wallet_data(addresses, rate_limit=0.5):
    """Enrich wallet data with portfolio, positions, and metadata from Hyperliquid API"""
    limiter = AsyncLimiter(1, rate_limit)
    connector = aiohttp.TCPConnector(limit=50)
    
    enriched_data = {}
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # Fetch portfolio data
        print("\n" + "="*80)
        print("Fetching portfolio data for all wallets...")
        print("="*80)
        
        async def fetch_portfolio(address: str):
            async with limiter:
                print(f"  📊 Fetching portfolio for {address[:10]}...")
                return await get_portfolio_data(session, address)
        
        portfolio_tasks = [asyncio.create_task(fetch_portfolio(addr)) for addr in addresses]
        portfolio_results = await asyncio.gather(*portfolio_tasks, return_exceptions=False)
        
        # Process portfolio data
        for address, data, error in portfolio_results:
            if not error and data:
                enriched_data[address] = {
                    'address': address,
                    'portfolio_data': data,
                    'analysis': analyze_address(data)
                }
            else:
                enriched_data[address] = {
                    'address': address,
                    'portfolio_data': None,
                    'analysis': None,
                    'error': error
                }
        
        # Fetch current positions
        print("\n" + "="*80)
        print("Fetching current positions...")
        print("="*80)
        
        async def fetch_positions(address: str):
            async with limiter:
                print(f"  💼 Fetching positions for {address[:10]}...")
                return await get_clearinghouse_state(session, address)
        
        position_tasks = [asyncio.create_task(fetch_positions(addr)) for addr in addresses]
        position_results = await asyncio.gather(*position_tasks, return_exceptions=False)
        
        # Process position data
        for address, data, error in position_results:
            if address in enriched_data and not error and data:
                enriched_data[address]['positions'] = extract_position_pnl(data)
            elif address in enriched_data:
                enriched_data[address]['positions'] = None
    
    return enriched_data


def is_hyper_scraper(wallet_data):
    """
    Identify hyper scrapers (likely bots with very high trade frequency)
    Criteria:
    - Total trades > 1000 in a short period
    - Very consistent daily trading (win rate too perfect or too consistent)
    - Low trader age but extremely high trade count
    """
    if not wallet_data or 'analysis' not in wallet_data or not wallet_data['analysis']:
        return False
    
    analysis = wallet_data['analysis']
    total_trades = analysis.get('total_trades', 0)
    trader_age_days = analysis.get('trader_age_days', 0)
    
    # High frequency trading detection
    if trader_age_days and trader_age_days > 0:
        trades_per_day = total_trades / trader_age_days
        
        # More than 50 trades per day on average suggests automated trading
        if trades_per_day > 50:
            return True
    
    # Very new trader with extremely high trades
    if trader_age_days and trader_age_days < 30 and total_trades > 500:
        return True
    
    return False


def scrape_all_sources(hyperdash_pages=10, coinglass_pages=10, 
                      include_cmm=True, cmm_email=None, cmm_password=None,
                      headless=True):
    """Scrape wallet addresses from all three sources"""
    all_addresses = []
    sources = {}
    
    driver = None
    try:
        driver = setup_driver(headless=headless)
        
        # Scrape from Hyperdash
        print("\n" + "="*80)
        print("SCRAPING FROM HYPERDASH")
        print("="*80)
        hyperdash_addresses = scrape_hyperdash(driver, max_pages=hyperdash_pages)
        for addr in hyperdash_addresses:
            sources[addr.lower()] = 'hyperdash'
        all_addresses.extend(hyperdash_addresses)
        print(f"✅ Found {len(hyperdash_addresses)} addresses from Hyperdash")
        
        # Scrape from Coinglass
        print("\n" + "="*80)
        print("SCRAPING FROM COINGLASS")
        print("="*80)
        coinglass_addresses = scrape_coinglass(driver, max_pages=coinglass_pages)
        for addr in coinglass_addresses:
            if addr.lower() not in sources:
                sources[addr.lower()] = 'coinglass'
            else:
                sources[addr.lower()] += ',coinglass'
        all_addresses.extend(coinglass_addresses)
        print(f"✅ Found {len(coinglass_addresses)} addresses from Coinglass")
        
        # Scrape from CoinMarketMan
        if include_cmm:
            print("\n" + "="*80)
            print("SCRAPING FROM COINMARKETMAN")
            print("="*80)
            cmm_addresses = scrape_coinmarketman(
                driver,
                segment="money-printer",
                email=cmm_email,
                password=cmm_password
            )
            for addr in cmm_addresses:
                if addr.lower() not in sources:
                    sources[addr.lower()] = 'coinmarketman'
                else:
                    sources[addr.lower()] += ',coinmarketman'
            all_addresses.extend(cmm_addresses)
            print(f"✅ Found {len(cmm_addresses)} addresses from CoinMarketMan")
        
    finally:
        if driver:
            driver.quit()
    
    return all_addresses, sources


def deduplicate_addresses(addresses):
    """Remove duplicate addresses (case-insensitive)"""
    seen = set()
    unique_addresses = []
    
    for addr in addresses:
        addr_lower = addr.lower()
        if addr_lower not in seen:
            seen.add(addr_lower)
            unique_addresses.append(addr)
    
    return unique_addresses


def create_merged_dataframe(enriched_data, sources):
    """Create a comprehensive dataframe with all wallet data"""
    rows = []
    
    for address, data in enriched_data.items():
        row = {'address': address}
        
        # Add source information
        row['sources'] = sources.get(address.lower(), 'unknown')
        
        # Add analysis data
        if data.get('analysis'):
            analysis = data['analysis']
            row['sharpe_ratio'] = analysis.get('sharpe', 0)
            row['max_drawdown'] = analysis.get('max_drawdown', 0)
            row['win_rate'] = analysis.get('win_rate', 0)
            row['cum_pnl_pct'] = analysis.get('cum_pnl_pct', 0)
            row['trader_age_days'] = analysis.get('trader_age_days', 0)
            row['total_trades'] = analysis.get('total_trades', 0)
        else:
            row['sharpe_ratio'] = 0
            row['max_drawdown'] = 0
            row['win_rate'] = 0
            row['cum_pnl_pct'] = 0
            row['trader_age_days'] = 0
            row['total_trades'] = 0
        
        # Add position data
        if data.get('positions'):
            positions = data['positions']
            row['num_positions'] = positions.get('num_positions', 0)
            row['unrealized_pnl'] = positions.get('unrealized_pnl', 0)
            row['account_value'] = positions.get('account_value', 0)
            row['exposure_pct'] = positions.get('exposure_pct', 0)
            row['total_margin_used'] = positions.get('total_margin_used', 0)
        else:
            row['num_positions'] = 0
            row['unrealized_pnl'] = 0
            row['account_value'] = 0
            row['exposure_pct'] = 0
            row['total_margin_used'] = 0
        
        # Mark if likely a hyper scraper
        row['is_hyper_scraper'] = is_hyper_scraper(data)
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    return df


def rank_by_performance(df, exclude_hyper_scrapers=True, 
                       min_sharpe=1.5, max_drawdown=0.5):
    """Rank wallets by performance metrics"""
    # Filter out hyper scrapers if requested
    if exclude_hyper_scrapers:
        df = df[df['is_hyper_scraper'] == False].copy()
    
    # Filter by minimum criteria
    df = df[
        (df['sharpe_ratio'] >= min_sharpe) &
        (df['max_drawdown'] <= max_drawdown) &
        (df['total_trades'] >= 10)  # Minimum history
    ].copy()
    
    # Calculate composite performance score
    # Normalize metrics and combine
    if len(df) > 0:
        # Sharpe ratio (higher is better)
        df['sharpe_normalized'] = (df['sharpe_ratio'] - df['sharpe_ratio'].min()) / \
                                  (df['sharpe_ratio'].max() - df['sharpe_ratio'].min() + 1e-6)
        
        # Max drawdown (lower is better, so invert)
        df['drawdown_normalized'] = 1 - ((df['max_drawdown'] - df['max_drawdown'].min()) / \
                                         (df['max_drawdown'].max() - df['max_drawdown'].min() + 1e-6))
        
        # Win rate (higher is better)
        df['winrate_normalized'] = (df['win_rate'] - df['win_rate'].min()) / \
                                   (df['win_rate'].max() - df['win_rate'].min() + 1e-6)
        
        # Composite score (weighted average)
        df['performance_score'] = (
            0.5 * df['sharpe_normalized'] +
            0.3 * df['drawdown_normalized'] +
            0.2 * df['winrate_normalized']
        )
        
        # Rank by performance score
        df = df.sort_values('performance_score', ascending=False)
        df['rank'] = range(1, len(df) + 1)
    
    return df


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Unified multi-source wallet scraper and analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape all sources and create big_file.csv
  python3 unified_scraper.py --scrape --analyze
  
  # Scrape with custom page counts
  python3 unified_scraper.py --scrape --hyperdash-pages 20 --coinglass-pages 15
  
  # Analyze existing scrapped_wallet_library.csv
  python3 unified_scraper.py --analyze --input scrapped_wallet_library.csv
  
  # Full workflow with CMM authentication
  python3 unified_scraper.py --scrape --analyze --cmm-email your@email.com --cmm-password pass
  
  # Custom filtering
  python3 unified_scraper.py --analyze --min-sharpe 2.0 --max-drawdown 0.3
        """
    )
    
    parser.add_argument(
        '--scrape',
        action='store_true',
        help='Scrape wallet addresses from all sources'
    )
    
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyze and enrich wallet data'
    )
    
    parser.add_argument(
        '--hyperdash-pages',
        type=int,
        default=10,
        help='Number of pages to scrape from Hyperdash (default: 10)'
    )
    
    parser.add_argument(
        '--coinglass-pages',
        type=int,
        default=10,
        help='Number of pages to scrape from Coinglass (default: 10)'
    )
    
    parser.add_argument(
        '--include-cmm',
        action='store_true',
        default=True,
        help='Include CoinMarketMan in scraping (default: True)'
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
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        default='scrapped_wallet_library.csv',
        help='Input CSV file with addresses (default: scrapped_wallet_library.csv)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=DEFAULT_OUTPUT,
        help=f'Output CSV file (default: {DEFAULT_OUTPUT})'
    )
    
    parser.add_argument(
        '--rate-limit',
        type=float,
        default=DEFAULT_RATE_LIMIT,
        help=f'API rate limit in seconds (default: {DEFAULT_RATE_LIMIT})'
    )
    
    parser.add_argument(
        '--min-sharpe',
        type=float,
        default=1.5,
        help='Minimum Sharpe ratio for ranking (default: 1.5)'
    )
    
    parser.add_argument(
        '--max-drawdown',
        type=float,
        default=0.5,
        help='Maximum drawdown for ranking (default: 0.5)'
    )
    
    parser.add_argument(
        '--exclude-hyper-scrapers',
        action='store_true',
        default=True,
        help='Exclude hyper scrapers from ranking (default: True)'
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
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.scrape and not args.analyze:
        print("Error: Must specify --scrape and/or --analyze")
        parser.print_help()
        return 1
    
    print("="*80)
    print("UNIFIED MULTI-SOURCE WALLET SCRAPER AND ANALYZER")
    print("="*80)
    print(f"Mode: {'Scrape' if args.scrape else ''} {'Analyze' if args.analyze else ''}")
    print(f"Output: {args.output}")
    print("="*80)
    print()
    
    addresses = []
    sources = {}
    
    # Phase 1: Scraping
    if args.scrape:
        print("\n" + "="*80)
        print("PHASE 1: SCRAPING FROM ALL SOURCES")
        print("="*80)
        
        scraped_addresses, sources = scrape_all_sources(
            hyperdash_pages=args.hyperdash_pages,
            coinglass_pages=args.coinglass_pages,
            include_cmm=args.include_cmm,
            cmm_email=args.cmm_email,
            cmm_password=args.cmm_password,
            headless=args.headless
        )
        
        # Deduplicate
        print("\n" + "="*80)
        print("DEDUPLICATING ADDRESSES")
        print("="*80)
        original_count = len(scraped_addresses)
        addresses = deduplicate_addresses(scraped_addresses)
        print(f"Original addresses: {original_count}")
        print(f"Unique addresses: {len(addresses)}")
        print(f"Duplicates removed: {original_count - len(addresses)}")
        
    # If not scraping, load from existing file
    elif args.analyze:
        if not Path(args.input).exists():
            print(f"Error: Input file '{args.input}' not found!")
            print("Please run with --scrape first or provide a valid input file.")
            return 1
        
        print(f"\nLoading addresses from {args.input}...")
        with open(args.input, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                addresses.append(row['address'])
                sources[row['address'].lower()] = row.get('source', 'unknown')
        
        print(f"Loaded {len(addresses)} addresses")
    
    # Phase 2: Analysis and Enrichment
    if args.analyze and addresses:
        print("\n" + "="*80)
        print("PHASE 2: ENRICHING WALLET DATA")
        print("="*80)
        
        enriched_data = asyncio.run(enrich_wallet_data(addresses, rate_limit=args.rate_limit))
        
        print("\n" + "="*80)
        print("PHASE 3: CREATING MERGED DATAFRAME")
        print("="*80)
        
        df = create_merged_dataframe(enriched_data, sources)
        print(f"Created dataframe with {len(df)} wallets")
        
        print("\n" + "="*80)
        print("PHASE 4: RANKING BY PERFORMANCE")
        print("="*80)
        
        ranked_df = rank_by_performance(
            df,
            exclude_hyper_scrapers=args.exclude_hyper_scrapers,
            min_sharpe=args.min_sharpe,
            max_drawdown=args.max_drawdown
        )
        
        print(f"Ranked {len(ranked_df)} wallets meeting criteria")
        if args.exclude_hyper_scrapers:
            hyper_scrapers = df[df['is_hyper_scraper'] == True]
            print(f"Excluded {len(hyper_scrapers)} hyper scrapers")
        
        # Save results
        print("\n" + "="*80)
        print("SAVING RESULTS")
        print("="*80)
        
        # Save full data
        df.to_csv(args.output, index=False)
        print(f"✅ Saved full data to: {args.output}")
        
        # Save ranked data
        ranked_file = args.output.replace('.csv', '_ranked.csv')
        ranked_df.to_csv(ranked_file, index=False)
        print(f"✅ Saved ranked data to: {ranked_file}")
        
        # Display top performers
        if len(ranked_df) > 0:
            print("\n" + "="*80)
            print("TOP 20 PERFORMERS")
            print("="*80)
            display_cols = ['rank', 'address', 'sharpe_ratio', 'max_drawdown', 
                          'win_rate', 'performance_score', 'sources']
            available_cols = [col for col in display_cols if col in ranked_df.columns]
            print(ranked_df[available_cols].head(20).to_string(index=False))
    
    print("\n" + "="*80)
    print("✅ COMPLETED SUCCESSFULLY")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
