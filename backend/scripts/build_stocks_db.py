#!/usr/bin/env python3
"""
Build stocks database by merging NSE and BSE listings.
Preserves existing curated data (especially sector assignments).
"""

import json
import requests
import csv
import time
from pathlib import Path
from io import StringIO

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
STOCKS_FILE = DATA_DIR / "stocks.json"

# Browser user agent
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

def title_case_company_name(name):
    """Title case a company name, preserving common abbreviations."""
    return name.title()

def fetch_nse_equities():
    """Download and parse NSE EQUITY_L.csv"""
    print("[NSE] Downloading EQUITY_L.csv...")
    try:
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Parse CSV manually
        csv_lines = StringIO(response.text)
        reader = csv.DictReader(csv_lines)

        all_rows = list(reader)
        print(f"[NSE] Raw CSV has {len(all_rows)} rows")

        # Filter to EQ series only (note: column header has leading space)
        eq_rows = [r for r in all_rows if r.get(' SERIES', '').strip() == 'EQ']
        print(f"[NSE] After EQ series filter: {len(eq_rows)} rows")

        nse_stocks = []
        for row in eq_rows:
            symbol = str(row.get('SYMBOL', '')).strip()
            name = str(row.get('NAME OF COMPANY', '')).strip()

            if symbol and name:
                nse_stocks.append({
                    "symbol": symbol,
                    "name": title_case_company_name(name),
                    "exchange": "NSE",
                    "sector": ""
                })

        print(f"[NSE] Extracted {len(nse_stocks)} valid stocks")
        return nse_stocks

    except Exception as e:
        print(f"[NSE] ERROR: {e}")
        return []

def fetch_bse_equities():
    """Download and parse BSE listing from API"""
    print("[BSE] Attempting to fetch from BseIndiaAPI...")
    try:
        # Try full API first
        url = "https://api.bseindia.com/BseIndiaAPI/api/ListOfScripData/w?Group=&Scripcode=&industry=&segment=Equity&status=Active"
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        scripdata = data.get('scripData', [])
        print(f"[BSE] Full API returned {len(scripdata)} records")

        if len(scripdata) == 0:
            # Fallback to Group=A
            print("[BSE] Trying Group=A fallback...")
            url_fallback = "https://api.bseindia.com/BseIndiaAPI/api/ListOfScripData/w?Group=A&Scripcode=&industry=&segment=Equity&status=Active"
            response = requests.get(url_fallback, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            scripdata = data.get('scripData', [])
            print(f"[BSE] Group=A returned {len(scripdata)} records")

        bse_stocks = []
        for item in scripdata:
            # BSE provides Scrip_Cd and various name fields
            symbol = item.get('Scrip_Cd', '') or item.get('ScripCode', '')
            name = item.get('Issuer_Name', '') or item.get('SecurityName', '')

            if symbol and name:
                symbol = str(symbol).strip()
                name = str(name).strip()
                bse_stocks.append({
                    "symbol": symbol,
                    "name": title_case_company_name(name),
                    "exchange": "BSE",
                    "sector": ""
                })

        print(f"[BSE] Extracted {len(bse_stocks)} valid stocks")
        return bse_stocks

    except Exception as e:
        print(f"[BSE] WARNING: Could not fetch BSE data: {e}")
        return []

def load_existing_stocks():
    """Load existing stocks.json"""
    print("[Load] Reading existing stocks.json...")
    try:
        with open(STOCKS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            stocks = data.get('stocks', [])
            print(f"[Load] Existing file has {len(stocks)} stocks")
            return stocks
    except Exception as e:
        print(f"[Load] No existing file or error: {e}")
        return []

def merge_stocks(existing, nse_list, bse_list):
    """Merge lists, preserving existing curated data."""
    # Start with existing stocks as a dict keyed by symbol
    merged_dict = {stock['symbol']: stock for stock in existing}
    print(f"[Merge] Starting with {len(merged_dict)} existing stocks")

    # Add NSE stocks (prefer NSE over BSE for duplicates)
    nse_added = 0
    for stock in nse_list:
        if stock['symbol'] not in merged_dict:
            merged_dict[stock['symbol']] = stock
            nse_added += 1
    print(f"[Merge] Added {nse_added} new NSE stocks")

    # Add BSE stocks (only if not already present)
    bse_added = 0
    for stock in bse_list:
        if stock['symbol'] not in merged_dict:
            merged_dict[stock['symbol']] = stock
            bse_added += 1
    print(f"[Merge] Added {bse_added} new BSE stocks")

    # Sort alphabetically by symbol for stable diffs
    final_list = sorted(merged_dict.values(), key=lambda x: x['symbol'])
    return final_list, len(nse_list), len(bse_list)

def save_stocks(stocks, nse_count, bse_count):
    """Write to data/stocks.json and report."""
    output = {"stocks": stocks}

    with open(STOCKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Wrote {len(stocks)} total stocks to {STOCKS_FILE}")
    print(f"  - NSE: {nse_count} unique listings")
    print(f"  - BSE: {bse_count} unique listings")
    print(f"  - Total: {len(stocks)}")

    # Show sample of new stocks
    sample = stocks[100:105] if len(stocks) > 100 else stocks[:5]
    print(f"\nSample entries (alphabetically):")
    for s in sample:
        print(f"  {s['symbol']:15} | {s['name']:40} | {s['exchange']}")

    # Check for target stocks
    symbol_set = {s['symbol'] for s in stocks}
    prism_found = 'PRSMJOHNSN' in symbol_set
    zfcv_found = 'ZFCVINDIA' in symbol_set

    print(f"\nTarget ticker verification:")
    print(f"  PRSMJOHNSN: {'✓ Found' if prism_found else '✗ Not found'}")
    print(f"  ZFCVINDIA:  {'✓ Found' if zfcv_found else '✗ Not found'}")

    if prism_found or zfcv_found:
        print(f"\nMatching entries:")
        for s in stocks:
            if s['symbol'] in ['PRSMJOHNSN', 'ZFCVINDIA']:
                print(f"  {s}")

def main():
    print("=" * 70)
    print("Building expanded stock database (NSE + BSE)")
    print("=" * 70)

    # Fetch data
    nse_stocks = fetch_nse_equities()
    time.sleep(1)  # Brief delay between requests
    bse_stocks = fetch_bse_equities()

    # Load existing and merge
    existing = load_existing_stocks()
    merged, nse_count, bse_count = merge_stocks(existing, nse_stocks, bse_stocks)

    # Save and report
    save_stocks(merged, nse_count, bse_count)

    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)

if __name__ == "__main__":
    main()
