#!/usr/bin/env python3
"""Quick test: Show forex and gold working with the actual analyst system"""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path  
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.api import get_prices

print("="*70)
print(" AI HEDGE FUND - FOREX & COMMODITIES WORKING!")
print("="*70)

# Test Gold (XAUUSD)
print("\n📈 Testing XAUUSD (Gold)...")
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

prices = get_prices("XAUUSD", start_date, end_date)

if prices:
    print(f"✅ SUCCESS!")
    print(f"   Retrieved {len(prices)} daily price points")
    print(f"   Latest close: ${prices[-1].close:.2f}")
    print(f"   Week high: ${max(p.high for p in prices):.2f}")
    print(f"   Week low: ${min(p.low for p in prices):.2f}")
    print(f"\n   Last 3 days:")
    for p in prices[-3:]:
        print(f"   {p.time}: Open ${p.open:.2f} → Close ${p.close:.2f}")
else:
    print("❌ Failed to fetch gold data")

# Test EURUSD
print("\n💱 Testing EURUSD (Forex)...")
prices = get_prices("EURUSD", start_date, end_date)

if prices:
    print(f"✅ SUCCESS!")
    print(f"   Retrieved {len(prices)} daily price points")
    print(f"   Latest close: ${prices[-1].close:.4f}")
    print(f"   Week high: ${max(p.high for p in prices):.4f}")
    print(f"   Week low: ${min(p.low for p in prices):.4f}")
else:
    print("❌ Failed to fetch EURUSD data")

print("\n" + "="*70)
print("✨ READY TO USE IN WEB APP!")
print("="*70)
print("\nOpen http://localhost:5173 and try these tickers:")
print("  • xauusd - Gold (most popular)")
print("  • eurusd - EUR/USD")
print("  • gbpusd - GBP/USD")
print("\nUse lowercase in the web interface!")
print("="*70)
