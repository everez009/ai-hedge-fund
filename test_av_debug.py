#!/usr/bin/env python3
"""Debug Alpha Vantage response"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("ALPHAVANTAGE_API_KEY")

base_url = "https://www.alphavantage.co/query"

params = {
    "function": "TIME_SERIES_DAILY",
    "symbol": "SPY",
    "outputsize": "compact",
    "apikey": API_KEY
}

print("Requesting Alpha Vantage API...")
response = requests.get(base_url, params=params)

print(f"\nStatus Code: {response.status_code}")
print(f"\nFull Response:")
print(json.dumps(response.json(), indent=2))
