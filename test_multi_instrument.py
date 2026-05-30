#!/usr/bin/env python3
"""Test forex, commodities, and indices data fetching"""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.api import get_prices

def test_instrument(ticker, name):
    """Test fetching data for an instrument"""
    print(f"\n{'='*60}")
    print(f"Testing: {name} ({ticker})")
    print(f"{'='*60}")
    
    # Get last 30 days
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    try:
        prices = get_prices(ticker, start_date, end_date)
        
        if prices:
            print(f"✅ SUCCESS: Fetched {len(prices)} price points")
            print(f"   Latest price: ${prices[-1].close:.2f}")
            print(f"   Date range: {prices[0].time} to {prices[-1].time}")
            return True
        else:
            print(f"❌ FAILED: No data returned")
            return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    print("Testing AI Hedge Fund - Multi-Instrument Support")
    print("="*60)
    
    # Test different instrument types
    tests = [
        ("XAUUSD", "Gold (Commodity)"),
        ("EURUSD", "EUR/USD (Forex)"),
        ("GBPUSD", "GBP/USD (Forex)"),
        ("SPX", "S&P 500 (Index)"),
        ("NAS100", "NASDAQ 100 (Index)"),
    ]
    
    results = {}
    for ticker, name in tests:
        results[ticker] = test_instrument(ticker, name)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    for ticker, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {ticker}")
    
    success_count = sum(1 for v in results.values() if v)
    print(f"\nTotal: {success_count}/{len(tests)} instruments working")
    
    if success_count == len(tests):
        print("\n🎉 All instruments are working! You can now use forex, commodities, and indices in the web app.")
    else:
        print("\n⚠ Some instruments failed. Check your API keys in .env file.")

if __name__ == "__main__":
    main()
