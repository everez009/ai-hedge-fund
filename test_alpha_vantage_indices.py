#!/usr/bin/env python3
"""Test Alpha Vantage indices directly"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")
print(f"Testing Alpha Vantage API Key: {API_KEY}")
print("="*60)

# Test different index symbols
indices_to_test = [
    "SPX",
    "SPY",  # S&P 500 ETF
    "^GSPC",  # Yahoo format
    "DJI",
    "IXIC",
    "NDX",
]

base_url = "https://www.alphavantage.co/query"

for symbol in indices_to_test:
    print(f"\nTesting symbol: {symbol}")
    print("-" * 60)
    
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "outputsize": "compact",
        "apikey": API_KEY
    }
    
    response = requests.get(base_url, params=params)
    data = response.json()
    
    if "Time Series (Daily)" in data:
        print(f"✅ SUCCESS! Found data for {symbol}")
        time_series = data["Time Series (Daily)"]
        latest_date = list(time_series.keys())[0]
        latest_data = time_series[latest_date]
        print(f"   Latest date: {latest_date}")
        print(f"   Close price: ${latest_data['4. close']}")
        break
    elif "Note" in data or "Error Message" in data:
        print(f"❌ API Error: {data.get('Note', data.get('Error Message', 'Unknown error'))}")
    else:
        print(f"❌ No data found")
        print(f"   Response keys: {list(data.keys())}")

print("\n" + "="*60)
print("Testing complete!")
