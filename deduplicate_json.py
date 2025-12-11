#!/usr/bin/env python3
"""
Deduplicate entries in trades.json and depth_chart.json files.
Removes duplicate entries based on unique identifiers.
"""

import json
import sys
from typing import List, Dict, Any


def get_trade_key(trade: Dict[str, Any]) -> tuple:
    """
    Generate a unique key for a trade entry.
    A trade is unique based on: date, time_et, exchange, price, volume, buyer, seller
    """
    return (
        trade.get('date', ''),
        trade.get('time_et', ''),
        trade.get('exchange', ''),
        trade.get('price', 0),
        trade.get('volume', 0),
        trade.get('buyer', ''),
        trade.get('seller', '')
    )


def get_depth_chart_key(entry: Dict[str, Any]) -> tuple:
    """
    Generate a unique key for a depth chart entry.
    An entry is unique based on: timestamp, price, volume, buyer_broker, seller_broker, 
    bid_price, ask_price, bid_size, ask_size
    """
    return (
        entry.get('timestamp', ''),
        entry.get('price', 0),
        entry.get('volume', 0),
        entry.get('buyer_broker', ''),
        entry.get('seller_broker', ''),
        entry.get('bid_price', 0),
        entry.get('ask_price', 0),
        entry.get('bid_size', 0),
        entry.get('ask_size', 0)
    )


def deduplicate_trades(filename: str) -> int:
    """
    Remove duplicate trades from trades.json file.
    Returns the number of duplicates removed.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            trades = json.load(f)
        
        if not isinstance(trades, list):
            print(f"Error: {filename} is not a JSON array")
            return 0
        
        original_count = len(trades)
        seen = set()
        unique_trades = []
        
        for trade in trades:
            key = get_trade_key(trade)
            if key not in seen:
                seen.add(key)
                unique_trades.append(trade)
        
        duplicates_removed = original_count - len(unique_trades)
        
        if duplicates_removed > 0:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(unique_trades, f, indent=2, ensure_ascii=False)
            print(f"  Removed {duplicates_removed} duplicate(s) from {filename}")
            print(f"  {original_count} -> {len(unique_trades)} entries")
        
        return duplicates_removed
    except FileNotFoundError:
        print(f"  File {filename} not found, skipping")
        return 0
    except json.JSONDecodeError as e:
        print(f"  Error parsing {filename}: {e}")
        return 0
    except Exception as e:
        print(f"  Error processing {filename}: {e}")
        return 0


def deduplicate_depth_chart(filename: str) -> int:
    """
    Remove duplicate entries from depth_chart.json file.
    Returns the number of duplicates removed.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            entries = json.load(f)
        
        if not isinstance(entries, list):
            print(f"Error: {filename} is not a JSON array")
            return 0
        
        original_count = len(entries)
        seen = set()
        unique_entries = []
        
        for entry in entries:
            key = get_depth_chart_key(entry)
            if key not in seen:
                seen.add(key)
                unique_entries.append(entry)
        
        duplicates_removed = original_count - len(unique_entries)
        
        if duplicates_removed > 0:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(unique_entries, f, indent=2, ensure_ascii=False)
            print(f"  Removed {duplicates_removed} duplicate(s) from {filename}")
            print(f"  {original_count} -> {len(unique_entries)} entries")
        
        return duplicates_removed
    except FileNotFoundError:
        print(f"  File {filename} not found, skipping")
        return 0
    except json.JSONDecodeError as e:
        print(f"  Error parsing {filename}: {e}")
        return 0
    except Exception as e:
        print(f"  Error processing {filename}: {e}")
        return 0


def main():
    """Main function to deduplicate both JSON files."""
    print("Deduplicating JSON files...")
    
    total_removed = 0
    
    # Deduplicate trades.json
    total_removed += deduplicate_trades('trades.json')
    total_removed += deduplicate_trades('dashboard/public/trades.json')
    
    # Deduplicate depth_chart.json
    total_removed += deduplicate_depth_chart('depth_chart.json')
    total_removed += deduplicate_depth_chart('dashboard/public/depth_chart.json')
    
    if total_removed > 0:
        print(f"\nTotal duplicates removed: {total_removed}")
    else:
        print("\nNo duplicates found.")
    
    return 0 if total_removed >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())

