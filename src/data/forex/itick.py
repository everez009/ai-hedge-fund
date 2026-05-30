"""
iTick API Adapter for Global Indices

Provides access to global stock market indices with real-time data.
Free tier offers unlimited basic calls with token authentication.

Documentation: https://api.itick.org/
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from src.data.models import Price


class ITickAdapter:
    """Adapter for iTick API - Best free tier for global indices"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or ""
        self.base_url = "https://api.itick.org"
        
        # Map common index names to iTick codes
        self.index_map = {
            "SPX": "SPX",           # S&P 500
            "S&P500": "SPX",        # Alternative name
            "NAS100": "IXIC",       # NASDAQ Composite (use IXIC instead of NDX)
            "NASDAQ": "IXIC",       # Alternative name
            "US30": "DJI",          # Dow Jones Industrial Average
            "DOW": "DJI",           # Alternative name
            "GER30": "GDAXI",       # German DAX
            "FTSE": "FTSE",         # FTSE 100
            "NIKKEI": "N225",       # Nikkei 225
            "HSI": "HSI",           # Hang Seng Index
            "VIX": "VIX",           # Volatility Index
        }
    
    def get_index_prices(self, symbol: str, start_date: str, end_date: str) -> List[Price]:
        """
        Fetch index prices from iTick API
        
        Args:
            symbol: Index symbol (e.g., 'SPX', 'IXIC', 'DJI')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of Price objects
        """
        # Map symbol to iTick code
        itick_code = self.index_map.get(symbol.upper(), symbol.upper())
        
        if not self.api_key:
            print("⚠️  iTick API key not configured")
            return []
        
        try:
            # Get historical K-line data (daily)
            prices = self._get_kline_data(itick_code, start_date, end_date)
            
            if prices:
                print(f"✅ iTick: Fetched {len(prices)} price points for {symbol} ({itick_code})")
                return prices
            else:
                print(f"❌ iTick: No data returned for {symbol}")
                return []
                
        except Exception as e:
            print(f"❌ iTick API error for {symbol}: {str(e)}")
            return []
    
    def _get_kline_data(self, code: str, start_date: str, end_date: str) -> List[Price]:
        """
        Get historical K-line data for an index
        
        Uses /indices/kline endpoint with daily kType=8
        """
        url = f"{self.base_url}/indices/kline"
        
        params = {
            "region": "GB",  # Global market
            "code": code,
            "kType": 8,      # Daily K-line
            "limit": 100     # Last 100 days (iTick free tier limit per request)
        }
        
        headers = {
            "accept": "application/json",
            "token": self.api_key
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"iTick API error: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return []
        
        data = response.json()
        
        # Check for errors
        if data.get("code") != 0:
            print(f"iTick API error: {data.get('msg', 'Unknown error')}")
            return []
        
        # Parse the response
        kline_data = data.get("data", [])
        if not kline_data:
            print(f"No K-line data found for {code}")
            return []
        
        prices = []
        for candle in kline_data:
            try:
                # Convert timestamp to date string
                timestamp_ms = candle.get("t", 0)
                if timestamp_ms:
                    date_str = datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d")
                else:
                    continue
                
                # Filter by date range
                if start_date <= date_str <= end_date:
                    price = Price(
                        ticker=code,
                        time=date_str,
                        open=float(candle.get("o", 0)),
                        high=float(candle.get("h", 0)),
                        low=float(candle.get("l", 0)),
                        close=float(candle.get("c", 0)),
                        volume=int(candle.get("v", 0))
                    )
                    prices.append(price)
                    
            except Exception as e:
                print(f"Error parsing candle data: {e}")
                continue
        
        # Sort by date
        prices.sort(key=lambda x: x.time)
        
        return prices
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """
        Get current price for an index
        
        Args:
            symbol: Index symbol
            
        Returns:
            Current price or None
        """
        itick_code = self.index_map.get(symbol.upper(), symbol.upper())
        
        if not self.api_key:
            return None
        
        try:
            url = f"{self.base_url}/indices/quote"
            params = {
                "region": "GB",
                "code": itick_code
            }
            headers = {
                "accept": "application/json",
                "token": self.api_key
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0 and data.get("data"):
                    return float(data["data"].get("ld", 0))  # ld = last price
            
            return None
            
        except Exception as e:
            print(f"Error fetching current price for {symbol}: {e}")
            return None
