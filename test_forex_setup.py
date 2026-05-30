#!/usr/bin/env python3
"""Quick test to verify forex data integration"""
import sys
from datetime import datetime, timedelta

try:
    from src.tools.forex_api import get_forex_provider
    from config.forex_config import FOREX_PAIRS, COMMODITIES, INDICES
    print("All imports successful")
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

print("\nInitializing Forex Data Provider...")
provider = get_forex_provider()
sources = provider.get_available_sources()
print(f"Data provider initialized")
print(f"Available sources: {sources if sources else 'None configured'}")

print("\n" + "="*60)
print("SUPPORTED INSTRUMENTS")
print("="*60)

print(f"\nForex Pairs ({len(FOREX_PAIRS)}):")
for symbol in list(FOREX_PAIRS.keys())[:5]:
    info = FOREX_PAIRS[symbol]
    print(f"  - {symbol}: {info['name']}")

print(f"\nCommodities ({len(COMMODITIES)}):")
for symbol, info in COMMODITIES.items():
    print(f"  - {symbol}: {info['name']}")

print(f"\nIndices ({len(INDICES)}):")
for symbol, info in INDICES.items():
    print(f"  - {symbol}: {info['name']}")

print("\nSetup verification complete!")
print("\nNext steps:")
print("1. Add API keys to .env file")
print("2. Run: poetry run python examples/forex_trading.py")
print("3. Run: poetry run python src/main.py --ticker EURUSD,XAUUSD")
