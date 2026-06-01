"""
Twelve Data API Adapter for Forex, Indices, and Commodities
Alternative data source with better forex/commodities coverage
"""
import os
import requests
import pandas as pd
from datetime import datetime
from typing import List, Optional
from src.data.models import Price


def _requests_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


class TwelveDataAdapter:
    """Adapter for Twelve Data API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("TWELVEDATA_API_KEY")
        if not self.api_key:
            raise ValueError("Twelve Data API key is required. Set TWELVEDATA_API_KEY environment variable.")
        self.base_url = "https://api.twelvedata.com"
        
    def get_prices(self, symbol: str, start_date: str, end_date: str, 
                   interval: str = "1day") -> List[Price]:
        """
        Fetch price data for any symbol (forex, indices, commodities)
        
        Args:
            symbol: Symbol (e.g., 'EUR/USD', 'XAU/USD', 'SPX', 'NAS100')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: Time interval ('1min', '5min', '15min', '30min', '45min', '1h', '2h', '4h', '1day', '1week', '1month')
            
        Returns:
            List of Price objects
        """
        # Normalize symbol format
        normalized_symbol = self._normalize_symbol(symbol)
        
        params = {
            "symbol": normalized_symbol,
            "interval": interval,
            "start_date": start_date,
            "end_date": end_date,
            "outputsize": 5000,
            "apikey": self.api_key
        }
        
        session = _requests_session()
        response = session.get(f"{self.base_url}/time_series", params=params, timeout=15)
        if response.status_code != 200:
            print(f"Error fetching data from Twelve Data: {response.status_code}")
            print(response.text)
            return []
        
        data = response.json()
        
        if "status" in data and data["status"] == "error":
            print(f"Twelve Data Error: {data.get('message', 'Unknown error')}")
            return []
        
        if "values" not in data:
            print(f"No data found for {symbol}")
            return []
        
        prices = []
        for item in data["values"]:
            try:
                price = Price(
                    ticker=symbol,
                    time=item["datetime"],
                    open=float(item["open"]),
                    high=float(item["high"]),
                    low=float(item["low"]),
                    close=float(item["close"]),
                    volume=int(item.get("volume", 0))
                )
                prices.append(price)
            except Exception as e:
                continue
        
        prices.sort(key=lambda x: x.time)
        return prices
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for Twelve Data"""
        symbol = symbol.upper().strip()
        
        # Forex pairs: EURUSD -> EUR/USD
        if len(symbol) == 6 and symbol.isalpha():
            return f"{symbol[:3]}/{symbol[3:]}"
        
        # XAUUSD -> XAU/USD
        if symbol.startswith("XAU"):
            return "XAU/USD"
        if symbol.startswith("XAG"):
            return "XAG/USD"
        
        # Indices - TwelveData doesn't support these on the free tier
        if symbol in ["SPX", "NAS100", "US30", "GER30", "FTSE", "NIKKEI"]:
            return symbol
        
        return symbol
    
    def get_exchange_rate(self, symbol: str) -> Optional[float]:
        """Get current exchange rate"""
        normalized_symbol = self._normalize_symbol(symbol)
        
        params = {
            "symbol": normalized_symbol,
            "apikey": self.api_key
        }
        
        session = _requests_session()
        response = session.get(f"{self.base_url}/price", params=params, timeout=15)
        if response.status_code != 200:
            return None
        
        data = response.json()
        if "price" in data:
            return float(data["price"])
        
        return None
    
    def get_technical_indicators(self, symbol: str, indicator: str, 
                                 interval: str = "1day", **kwargs) -> dict:
        """
        Get technical indicators directly from Twelve Data
        
        Args:
            symbol: Trading symbol
            indicator: Indicator name (e.g., 'RSI', 'MACD', 'SMA', 'EMA', 'BBANDS')
            interval: Time interval
            **kwargs: Additional parameters for the indicator
            
        Returns:
            Dictionary with indicator values
        """
        normalized_symbol = self._normalize_symbol(symbol)
        
        params = {
            "symbol": normalized_symbol,
            "interval": interval,
            "apikey": self.api_key,
            **kwargs
        }
        
        session = _requests_session()
        response = session.get(f"{self.base_url}/{indicator.lower()}", params=params, timeout=15)
        if response.status_code != 200:
            print(f"Error fetching {indicator}: {response.status_code}")
            return {}
        
        data = response.json()
        if "values" not in data:
            return {}
        
        return data
