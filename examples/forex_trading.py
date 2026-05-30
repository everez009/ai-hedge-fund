"""
Example: AI Hedge Fund for Forex, Indices, and Commodities Trading
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.tools.forex_api import get_forex_provider
from config.forex_config import FOREX_PAIRS, COMMODITIES, INDICES


def test_data_sources():
    print("=" * 80)
    print("Testing Forex Data Sources")
    print("=" * 80)
    
    provider = get_forex_provider()
    available = provider.get_available_sources()
    
    print(f"\nAvailable data sources: {available}")
    
    if not available:
        print("\nNo data sources configured. Please add API keys to .env file:")
        print("  - ALPHAVANTAGE_API_KEY (free tier available)")
        print("  - TWELVEDATA_API_KEY (free tier available)")
        print("  - OANDA_API_KEY (requires account)")
        return False
    
    return True


def fetch_sample_data():
    print("\n" + "=" * 80)
    print("Fetching Sample Data")
    print("=" * 80)
    
    provider = get_forex_provider()
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    test_instruments = [
        ("EURUSD", "Forex Major Pair"),
        ("XAUUSD", "Gold Commodity"),
        ("GBPUSD", "Forex Major Pair"),
    ]
    
    for symbol, description in test_instruments:
        print(f"\n{symbol} ({description}):")
        print("-" * 60)
        
        prices = provider.get_prices(symbol, start_date, end_date)
        
        if prices:
            print(f"  Retrieved {len(prices)} price points")
            print(f"  Latest price: ${prices[-1].close:.5f}")
        else:
            print(f"  No data retrieved")


def display_supported_instruments():
    print("\n" + "=" * 80)
    print("Supported Instruments")
    print("=" * 80)
    
    print("\nFOREX PAIRS:")
    print("-" * 60)
    for symbol, info in FOREX_PAIRS.items():
        print(f"  - {symbol:8s} - {info['name']}")
    
    print("\nCOMMODITIES:")
    print("-" * 60)
    for symbol, info in COMMODITIES.items():
        print(f"  - {symbol:8s} - {info['name']}")
    
    print("\nINDICES:")
    print("-" * 60)
    for symbol, info in INDICES.items():
        print(f"  - {symbol:8s} - {info['name']}")


if __name__ == "__main__":
    print("\nAI Hedge Fund - Forex, Indices & Commodities Edition")
    print("=" * 80)
    
    if not test_data_sources():
        print("\nPlease configure at least one data source in .env file.")
        sys.exit(1)
    
    display_supported_instruments()
    fetch_sample_data()
    
    print("\nDemo complete!")
