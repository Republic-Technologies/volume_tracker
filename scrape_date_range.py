"""
Date Range Scraper for Stockwatch Trades

Iterates through a date range and scrapes Stockwatch trades data, building up a historical dataset.
After processing all dates, runs the CSE depth chart scraper once for the most recent day.
"""

import argparse
from datetime import datetime, timedelta
from typing import List, Dict
import sys

# Import functions from scrape.py
from scrape import (
    scrape_stockwatch_trades,
    save_stockwatch_trades,
    scrape_cse_trades,
    save_to_json,
    save_to_csv
)


def generate_date_range(start_date: str, end_date: str) -> List[str]:
    """
    Generate a list of dates in yyyymmdd format between start_date and end_date (inclusive).
    
    Args:
        start_date: Start date in yyyymmdd format
        end_date: End date in yyyymmdd format
    
    Returns:
        List of date strings in yyyymmdd format, in chronological order (oldest first)
    """
    try:
        start = datetime.strptime(start_date, "%Y%m%d")
        end = datetime.strptime(end_date, "%Y%m%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format. Expected yyyymmdd (e.g., 20241208). Error: {e}")
    
    if start > end:
        raise ValueError(f"Start date ({start_date}) must be before or equal to end date ({end_date})")
    
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)
    
    return dates


def scrape_date_range(
    symbol: str,
    start_date: str,
    end_date: str,
    trades_filename: str = "trades.json"
) -> Dict:
    """
    Scrape Stockwatch trades for a date range.
    
    Args:
        symbol: Ticker symbol (e.g., "DOCT")
        start_date: Start date in yyyymmdd format
        end_date: End date in yyyymmdd format
        trades_filename: Output filename for trades JSON
    
    Returns:
        Dictionary with summary statistics:
        - total_dates: Total number of dates processed
        - successful_dates: List of dates that succeeded
        - failed_dates: List of dates that failed (with error messages)
        - total_trades: Total number of trades collected
    """
    dates = generate_date_range(start_date, end_date)
    total_dates = len(dates)
    
    print(f"\n{'='*60}")
    print(f"Scraping Stockwatch trades for {symbol}")
    print(f"Date range: {start_date} to {end_date} ({total_dates} days)")
    print(f"{'='*60}\n")
    
    successful_dates = []
    failed_dates = []
    total_trades = 0
    
    # Process dates in chronological order (oldest first)
    # This way, if the script is interrupted, older data is already saved
    for idx, date_str in enumerate(dates, 1):
        print(f"[{idx}/{total_dates}] Processing {date_str}...", end=" ", flush=True)
        
        try:
            # Scrape trades for this date
            trades = scrape_stockwatch_trades(symbol=symbol, date=date_str)
            
            if trades:
                # Save trades (append mode)
                save_stockwatch_trades(trades, trades_filename)
                total_trades += len(trades)
                successful_dates.append(date_str)
                print(f"✓ Found {len(trades)} trades")
            else:
                # No trades found, but not an error (could be weekend/holiday)
                successful_dates.append(date_str)
                print(f"✓ No trades found (weekend/holiday?)")
        
        except Exception as e:
            # Log error but continue with next date
            error_msg = str(e)
            failed_dates.append((date_str, error_msg))
            print(f"✗ Error: {error_msg}")
            continue
    
    return {
        "total_dates": total_dates,
        "successful_dates": successful_dates,
        "failed_dates": failed_dates,
        "total_trades": total_trades
    }


def scrape_cse_depth_chart(symbol: str) -> bool:
    """
    Scrape CSE depth chart for the most recent day.
    
    Args:
        symbol: Ticker symbol (e.g., "DOCT")
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Scraping CSE depth chart for {symbol} (most recent day)")
    print(f"{'='*60}\n")
    
    try:
        trades = scrape_cse_trades(symbol)
        
        if not trades:
            print("No depth chart data found.")
            return False
        
        # Save to JSON and CSV
        save_to_json(trades, "depth_chart.json", append=False)  # Overwrite for most recent
        save_to_csv(trades, "depth_chart.csv", append=False)  # Overwrite for most recent
        
        print(f"\n✓ Successfully saved {len(trades)} depth chart records")
        return True
    
    except Exception as e:
        print(f"\n✗ Error scraping CSE depth chart: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Scrape Stockwatch trades for a date range and CSE depth chart for the most recent day",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape last 30 days of DOCT trades
  python scrape_date_range.py

  # Scrape last 60 days
  python scrape_date_range.py --days 60

  # Scrape specific date range
  python scrape_date_range.py --start-date 20241101 --end-date 20241208

  # Different symbol
  python scrape_date_range.py --symbol AAPL --days 30
        """
    )
    
    parser.add_argument(
        '--symbol',
        type=str,
        default='DOCT',
        help='Ticker symbol to scrape (default: DOCT)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to go back from today (default: 30). Ignored if --start-date is provided.'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        default=None,
        help='Start date in yyyymmdd format (optional - if provided, use this instead of calculating from --days)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        default=None,
        help='End date in yyyymmdd format (default: today)'
    )
    
    parser.add_argument(
        '--skip-cse',
        action='store_true',
        help='Skip CSE depth chart scraping (only scrape Stockwatch trades)'
    )
    
    args = parser.parse_args()
    
    symbol = args.symbol.upper()
    
    # Calculate date range
    today = datetime.now()
    end_date_str = args.end_date or today.strftime("%Y%m%d")
    
    if args.start_date:
        start_date_str = args.start_date
    else:
        # Calculate start date from --days
        start_date = today - timedelta(days=args.days - 1)  # -1 to include today
        start_date_str = start_date.strftime("%Y%m%d")
    
    # Validate dates
    try:
        datetime.strptime(start_date_str, "%Y%m%d")
        datetime.strptime(end_date_str, "%Y%m%d")
    except ValueError as e:
        print(f"Error: Invalid date format. Use yyyymmdd format (e.g., 20241208).")
        print(f"  Start date: {start_date_str}")
        print(f"  End date: {end_date_str}")
        sys.exit(1)
    
    # Scrape Stockwatch trades for date range
    summary = scrape_date_range(
        symbol=symbol,
        start_date=start_date_str,
        end_date=end_date_str,
        trades_filename="trades.json"
    )
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Symbol: {symbol}")
    print(f"Date range: {start_date_str} to {end_date_str}")
    print(f"Total dates processed: {summary['total_dates']}")
    print(f"Successful dates: {len(summary['successful_dates'])}")
    print(f"Failed dates: {len(summary['failed_dates'])}")
    print(f"Total trades collected: {summary['total_trades']}")
    
    if summary['failed_dates']:
        print(f"\nFailed dates:")
        for date_str, error_msg in summary['failed_dates']:
            print(f"  - {date_str}: {error_msg}")
    
    print(f"\nOutput file: trades.json")
    
    # Scrape CSE depth chart (unless skipped)
    if not args.skip_cse:
        print(f"\n{'='*60}")
        cse_success = scrape_cse_depth_chart(symbol)
        if cse_success:
            print(f"\nCSE depth chart files: depth_chart.json, depth_chart.csv")
    else:
        print(f"\nSkipping CSE depth chart scraping (--skip-cse flag set)")
    
    print(f"\n{'='*60}")
    print("Scraping complete!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

