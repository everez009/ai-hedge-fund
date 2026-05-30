#!/usr/bin/env python3
"""
Test iTick API Integration

This script tests the iTick API adapter with various indices.
You need to register at https://api.itick.org/ to get a free token.
"""

import sys
import os
sys.path.insert(0, '/Users/mac/aihedgefund')

from src.data.forex.itick import ITickAdapter


def test_itick():
    """Test iTick API with sample indices"""
    
    print("=" * 70)
    print("🧪 Testing iTick API Integration")
    print("=" * 70)
    
    # Get API key from environment or use demo
    api_key = os.environ.get("ITICK_API_KEY", "")
    
    if not api_key or api_key == "your-itick-api-token":
        print("\n⚠️  iTick API key not configured!")
        print("\nTo get your FREE iTick API token:")
        print("1. Visit: https://api.itick.org/")
        print("2. Register for a free account")
        print("3. Copy your API token")
        print("4. Add it to .env file: ITICK_API_KEY=your_token_here")
        print("\nFor now, testing with demo mode...")
        return
    
    # Initialize adapter
    adapter = ITickAdapter(api_key=api_key)
    
    # Test indices
    test_cases = [
        ("SPX", "S&P 500"),
        ("IXIC", "NASDAQ Composite"),
        ("DJI", "Dow Jones"),
        ("FTSE", "FTSE 100"),
    ]
    
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"\n📅 Date range: {start_date} to {end_date}\n")
    
    for symbol, name in test_cases:
        print(f"Testing {symbol} ({name})...")
        
        # Get historical prices
        prices = adapter.get_index_prices(symbol, start_date, end_date)
        
        if prices:
            print(f"  ✅ Success! Got {len(prices)} price points")
            print(f"     Latest close: ${prices[-1].close:.2f}")
            print(f"     Date range: {prices[0].time} to {prices[-1].time}")
        else:
            print(f"  ❌ No data returned")
        
        print()
    
    print("=" * 70)
    print("✅ iTick API test complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_itick()
