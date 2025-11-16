#!/usr/bin/env python3
"""
Portfolio Analysis and Ranking Script
Reads wallet addresses from scrapped_wallet_library.csv
Analyzes trading performance and ranks traders
"""
import argparse
import csv
import asyncio
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import aiohttp
from aiolimiter import AsyncLimiter


# Configuration
API_URL = "https://api.hyperliquid.xyz/info"
HEADERS = {"Content-Type": "application/json"}

# Analysis filters (defaults)
DEFAULT_MIN_SHARPE = 1.5
DEFAULT_MAX_SHARPE = 50
DEFAULT_MIN_MAX_DRAWDOWN = 0
DEFAULT_MAX_MAX_DRAWDOWN = 0.5
DEFAULT_MIN_HISTORY_DAYS = 10


async def get_portfolio_data(session: aiohttp.ClientSession, address: str):
    """Get portfolio data for an address"""
    payload = {"type": "portfolio", "user": address}
    try:
        async with session.post(API_URL, json=payload, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=20)) as r:
            if r.status != 200:
                return address, None, f"HTTP {r.status}"
            api_data = await r.json(content_type=None)
            return address, api_data, None
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        return address, None, str(e)


async def get_clearinghouse_state(session: aiohttp.ClientSession, address: str):
    """Get current positions and PnL for an address"""
    payload = {"type": "clearinghouseState", "user": address}
    try:
        async with session.post(API_URL, json=payload, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=20)) as r:
            if r.status != 200:
                return address, None, f"HTTP {r.status}"
            data = await r.json(content_type=None)
            return address, data, None
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        return address, None, str(e)


async def fetch_portfolio_data(addresses, rate_limit=0.5):
    """Fetch portfolio data for multiple addresses concurrently"""
    limiter = AsyncLimiter(1, rate_limit)
    connector = aiohttp.TCPConnector(limit=50)

    async with aiohttp.ClientSession(connector=connector) as session:
        async def fetch_one(address: str):
            async with limiter:
                print(f"  Fetching portfolio for {address[:10]}...")
                return await get_portfolio_data(session, address)

        tasks = [asyncio.create_task(fetch_one(addr)) for addr in addresses]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results


async def fetch_current_positions(addresses, rate_limit=0.5):
    """Fetch current positions for multiple addresses concurrently"""
    limiter = AsyncLimiter(1, rate_limit)
    connector = aiohttp.TCPConnector(limit=50)

    async with aiohttp.ClientSession(connector=connector) as session:
        async def fetch_one(address: str):
            async with limiter:
                print(f"  Fetching positions for {address[:10]}...")
                return await get_clearinghouse_state(session, address)

        tasks = [asyncio.create_task(fetch_one(addr)) for addr in addresses]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results


def analyze_address(data):
    """Analyze address trading data and calculate metrics"""
    try:
        perp_month_resp = data[6][1]
        pnl_history = perp_month_resp["pnlHistory"]
        equity_history = perp_month_resp["accountValueHistory"]

        # Calculate trader age
        trader_age_days = None
        if len(pnl_history) > 0:
            first_date_str = pnl_history[0][0] if isinstance(pnl_history[0], (list, tuple)) else None
            if first_date_str:
                try:
                    if isinstance(first_date_str, (int, float)):
                        first_date = datetime.fromtimestamp(first_date_str / 1000 if first_date_str > 1e10 else first_date_str)
                    else:
                        first_date = datetime.fromisoformat(first_date_str.replace('Z', '+00:00').split('T')[0])
                    today = datetime.now()
                    trader_age_days = (today - first_date).days
                except:
                    pass

        history = {}
        cumulative_pnl = 0.0
        running_max_cum_pnl = 0.0
        win_days = 0
        cum_pnl_pct = 1
        transfer_count = 0

        for i in range(1, len(pnl_history)):
            day_pnl = float(pnl_history[i][1])
            day_equity = float(equity_history[i][1])
            date_pnl = pnl_history[i][0]
            date_equity = equity_history[i][0]
            prev_equity = float(equity_history[i-1][1])

            if date_pnl != date_equity:
                continue

            # Detect large transfers (>10% of equity)
            if (prev_equity + day_pnl > 1.1 * day_equity or
                prev_equity + day_pnl < 0.9 * day_equity):
                transfer_count += 1
                continue

            # Skip if equity is 0 or too many transfers
            if prev_equity == 0 or transfer_count > 5:
                return {
                    "sharpe": 0,
                    "max_drawdown": 0,
                    "win_rate": 0,
                    "cum_pnl_pct": 0,
                    "trader_age_days": trader_age_days,
                    "total_trades": 0
                }

            cumulative_pnl += day_pnl
            drawdown = max(0.0, running_max_cum_pnl - cumulative_pnl)
            drawdown_pc = (drawdown / day_equity) if day_equity > 0 else 0.0
            running_max_cum_pnl = max(running_max_cum_pnl, cumulative_pnl)

            daily_pct_pnl = day_pnl / prev_equity
            cum_pnl_pct *= (1 + daily_pct_pnl)
            if daily_pct_pnl > 0:
                win_days += 1

            history[date_pnl] = {
                "equity": day_equity,
                "pnl": day_pnl,
                "daily_pct_pnl": daily_pct_pnl,
                "drawdown": drawdown,
                "drawdown_pct": drawdown_pc,
            }

        if len(history.keys()) < 10:
            return {
                "sharpe": 0,
                "max_drawdown": 0,
                "win_rate": 0,
                "cum_pnl_pct": 0,
                "trader_age_days": trader_age_days,
                "total_trades": len(history.keys())
            }

        mean_pnl = sum([history[d]["daily_pct_pnl"] for d in history.keys()]) / len(history.keys())
        std_pnl = np.std([history[d]["daily_pct_pnl"] for d in history.keys()])

        # Calculate Sharpe ratio
        if std_pnl == 0 or np.isnan(std_pnl) or std_pnl < 1e-10:
            sharpe = 0.0
        else:
            sharpe = (365**0.5) * (mean_pnl / std_pnl)
            if np.isinf(sharpe) or np.isnan(sharpe):
                sharpe = 0.0

        max_drawdown = max([history[d]["drawdown_pct"] for d in history.keys()])
        win_rate = win_days / len(history.keys())

        return {
            "sharpe": sharpe,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "cum_pnl_pct": cum_pnl_pct,
            "trader_age_days": trader_age_days,
            "total_trades": len(history.keys())
        }

    except Exception as e:
        return {
            "sharpe": 0,
            "max_drawdown": 0,
            "win_rate": 0,
            "cum_pnl_pct": 0,
            "trader_age_days": None,
            "total_trades": 0
        }


def safe_float(value, default=0.0):
    """Safely convert a value to float"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def extract_position_pnl(data):
    """Extract current position PnL from clearinghouse state data"""
    if not data:
        return None

    try:
        result = {}

        # Extract margin summary
        if 'marginSummary' in data:
            margin_summary = data['marginSummary']
            if margin_summary is None:
                result['account_value'] = 0.0
                result['total_margin_used'] = 0.0
                result['available_margin'] = 0.0
            else:
                result['account_value'] = safe_float(margin_summary.get('accountValue'), 0.0)
                result['total_margin_used'] = safe_float(margin_summary.get('totalMarginUsed'), 0.0)
                result['available_margin'] = result['account_value'] - result['total_margin_used']

        # Extract position details
        if 'assetPositions' in data:
            positions = data['assetPositions']
            if positions is None:
                positions = []

            total_unrealized_pnl = 0
            total_notional = 0
            position_details = []

            for pos in positions:
                if pos is None:
                    continue

                position = pos.get('position')
                if position is None:
                    position = {}

                unrealized_pnl = safe_float(position.get('unrealizedPnl'), 0.0)
                notional = safe_float(position.get('notional'), 0.0)

                asset = pos.get('asset')
                if asset is None:
                    asset_name = 'UNKNOWN'
                elif isinstance(asset, dict):
                    asset_name = asset.get('name', 'UNKNOWN')
                else:
                    asset_name = str(asset)

                total_unrealized_pnl += unrealized_pnl
                total_notional += abs(notional)

                position_details.append({
                    'asset': asset_name,
                    'notional': notional,
                    'unrealized_pnl': unrealized_pnl,
                })

            result['unrealized_pnl'] = total_unrealized_pnl
            result['total_notional_pos'] = total_notional
            result['num_positions'] = len(positions)
            result['positions'] = position_details

        if 'num_positions' not in result:
            result['num_positions'] = 0
        if 'unrealized_pnl' not in result:
            result['unrealized_pnl'] = 0
        if 'total_notional_pos' not in result:
            result['total_notional_pos'] = 0

        # Calculate exposure percentage (using margin used as proxy for exposure)
        account_value = result.get('account_value', 0)
        margin_used = result.get('total_margin_used', 0)
        if account_value > 0:
            result['exposure_pct'] = (margin_used / account_value) * 100
        else:
            result['exposure_pct'] = 0.0

        return result

    except Exception as e:
        return {'error': str(e)}


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Analyze and rank trader portfolios',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all wallets in library
  python3 script_portfolio.py

  # Analyze with custom filters
  python3 script_portfolio.py --min-sharpe 2.0 --max-drawdown 0.3

  # Analyze specific number of wallets
  python3 script_portfolio.py --limit 100

  # Analyze and fetch current positions
  python3 script_portfolio.py --fetch-positions
        """
    )

    parser.add_argument(
        '--input', '-i',
        type=str,
        default='scrapped_wallet_library.csv',
        help='Input CSV file with wallet addresses (default: scrapped_wallet_library.csv)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default='portfolio_analysis.csv',
        help='Output CSV file for analysis results (default: portfolio_analysis.csv)'
    )

    parser.add_argument(
        '--min-sharpe',
        type=float,
        default=DEFAULT_MIN_SHARPE,
        help=f'Minimum Sharpe ratio (default: {DEFAULT_MIN_SHARPE})'
    )

    parser.add_argument(
        '--max-sharpe',
        type=float,
        default=DEFAULT_MAX_SHARPE,
        help=f'Maximum Sharpe ratio (default: {DEFAULT_MAX_SHARPE})'
    )

    parser.add_argument(
        '--max-drawdown',
        type=float,
        default=DEFAULT_MAX_MAX_DRAWDOWN,
        help=f'Maximum drawdown (default: {DEFAULT_MAX_MAX_DRAWDOWN})'
    )

    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=None,
        help='Limit number of wallets to analyze (default: all)'
    )

    parser.add_argument(
        '--fetch-positions',
        action='store_true',
        help='Fetch current positions for top traders'
    )

    parser.add_argument(
        '--rate-limit',
        type=float,
        default=0.5,
        help='Rate limit in seconds between API calls (default: 0.5)'
    )

    args = parser.parse_args()

    print("="*80)
    print("Portfolio Analysis and Ranking")
    print("="*80)
    print(f"Input file: {args.input}")
    print(f"Output file: {args.output}")
    print(f"Sharpe ratio range: {args.min_sharpe} - {args.max_sharpe}")
    print(f"Max drawdown: {args.max_drawdown}")
    print(f"Rate limit: {args.rate_limit}s")
    print("="*80)
    print()

    # Read wallet addresses
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found!")
        print("Please run script_scrap_wallet.py first to scrape wallet addresses.")
        return

    addresses = []
    with open(args.input, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            addresses.append(row['address'])

    if args.limit:
        addresses = addresses[:args.limit]

    print(f"Loaded {len(addresses)} wallet addresses\n")

    # Fetch portfolio data
    print("="*80)
    print("Fetching portfolio data...")
    print("="*80)
    results = asyncio.run(fetch_portfolio_data(addresses, rate_limit=args.rate_limit))

    # Analyze addresses
    print("\n" + "="*80)
    print("Analyzing portfolios...")
    print("="*80)

    analysis_results = {}
    for address, data, error in results:
        if error:
            print(f"  ❌ {address[:10]}...: {error}")
            continue

        if data is not None:
            analysis = analyze_address(data)
            analysis_results[address] = analysis
            print(f"  ✓ {address[:10]}... - Sharpe: {analysis['sharpe']:.2f}, Win Rate: {analysis['win_rate']:.2%}")

    # Create DataFrame
    df = pd.DataFrame.from_dict(analysis_results, orient="index")
    df.index.name = 'address'

    # Add formatted trader age columns
    if 'trader_age_days' in df.columns:
        df['trader_age_years'] = df['trader_age_days'].apply(
            lambda x: round(x / 365.25, 2) if pd.notna(x) else None
        )

    print(f"\n✅ Analyzed {len(df)} wallets")

    # Filter based on criteria
    filtered_df = df[
        (df["sharpe"] > args.min_sharpe) &
        (df["sharpe"] < args.max_sharpe) &
        (df["max_drawdown"] < args.max_drawdown) &
        (df["max_drawdown"] > DEFAULT_MIN_MAX_DRAWDOWN)
    ]

    # Sort by Sharpe ratio
    filtered_df = filtered_df.sort_values('sharpe', ascending=False)

    print(f"✅ Found {len(filtered_df)} wallets matching criteria\n")

    # Display top traders
    if len(filtered_df) > 0:
        print("="*80)
        print("TOP TRADERS")
        print("="*80)
        display_cols = ['sharpe', 'max_drawdown', 'win_rate', 'cum_pnl_pct', 'total_trades', 'trader_age_days']
        print(filtered_df[display_cols].head(20).to_string())
        print()

    # Fetch current positions if requested
    if args.fetch_positions and len(filtered_df) > 0:
        print("\n" + "="*80)
        print("Fetching current positions for top traders...")
        print("="*80)

        top_addresses = list(filtered_df.index[:50])  # Top 50
        position_results = asyncio.run(fetch_current_positions(top_addresses, rate_limit=args.rate_limit))

        position_data = {}
        for address, data, error in position_results:
            if error:
                print(f"  ❌ {address[:10]}...: {error}")
            elif data:
                pnl_info = extract_position_pnl(data)
                if pnl_info and 'error' not in pnl_info:
                    position_data[address] = pnl_info
                    exposure = pnl_info.get('exposure_pct', 0)
                    print(f"  ✓ {address[:10]}... - Positions: {pnl_info.get('num_positions', 0)}, PnL: ${pnl_info.get('unrealized_pnl', 0):.2f}, Exposure: {exposure:.1f}%")

        if position_data:
            # Create positions DataFrame
            pnl_rows = []
            for wallet, pnl_info in position_data.items():
                row = {'address': wallet}
                for key, value in pnl_info.items():
                    if key != 'positions':
                        row[key] = value
                pnl_rows.append(row)

            pnl_df = pd.DataFrame(pnl_rows)

            print("\n" + "="*80)
            print("CURRENT POSITIONS SUMMARY")
            print("="*80)
            display_pos_cols = ['address', 'num_positions', 'unrealized_pnl', 'account_value', 'exposure_pct']
            available_cols = [col for col in display_pos_cols if col in pnl_df.columns]
            print(pnl_df[available_cols].to_string(index=False))

            # Save positions to separate file
            positions_file = args.output.replace('.csv', '_positions.csv')
            pnl_df.to_csv(positions_file, index=False)
            print(f"\n✓ Saved positions data to: {positions_file}")

    # Save analysis results
    print("\n" + "="*80)
    print("Saving results...")
    print("="*80)

    df.to_csv(args.output)
    print(f"✓ Saved full analysis to: {args.output}")

    filtered_file = args.output.replace('.csv', '_filtered.csv')
    filtered_df.to_csv(filtered_file)
    print(f"✓ Saved filtered results to: {filtered_file}")

    print("\n✅ Analysis complete!")


if __name__ == "__main__":
    main()
