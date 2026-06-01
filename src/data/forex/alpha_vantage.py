"""
Alpha Vantage API Adapter for Forex, Indices, and Commodities
Supports: Forex pairs (EURUSD, GBPUSD, etc.), Indices (SPX, NASDAQ, etc.), Commodities (XAUUSD, XAGUSD, etc.)
"""
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from src.data.models import Price


def _requests_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


class AlphaVantageAdapter:
    """Adapter for Alpha Vantage API to fetch forex, indices, and commodities data"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("ALPHAVANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("Alpha Vantage API key is required. Set ALPHAVANTAGE_API_KEY environment variable.")
        self.base_url = "https://www.alphavantage.co/query"
        
    def get_forex_prices(self, from_currency: str, to_currency: str, 
                         start_date: str, end_date: str, interval: str = "daily") -> List[Price]:
        """
        Fetch forex pair prices
        
        Args:
            from_currency: Base currency (e.g., 'EUR', 'GBP')
            to_currency: Quote currency (e.g., 'USD', 'JPY')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            interval: 'daily', 'weekly', 'monthly', or intraday ('1min', '5min', '15min', '30min', '60min')
            
        Returns:
            List of Price objects
        """
        function_map = {
            "daily": "FX_DAILY",
            "weekly": "FX_WEEKLY",
            "monthly": "FX_MONTHLY",
        }
        
        if interval in function_map:
            return self._get_fx_daily(from_currency, to_currency, start_date, end_date)
        else:
            return self._get_fx_intraday(from_currency, to_currency, interval)
    
    def _get_fx_daily(self, from_currency: str, to_currency: str, 
                      start_date: str, end_date: str) -> List[Price]:
        """Get daily forex data"""
        params = {
            "function": "FX_DAILY",
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "outputsize": "full",
            "apikey": self.api_key
        }
        
        session = _requests_session()
        response = session.get(self.base_url, params=params, timeout=15)
        if response.status_code != 200:
            print(f"Error fetching forex data: {response.status_code}")
            return []
        
        data = response.json()
        
        # Check for API limit message
        if "Note" in data:
            print(f"API Limit Warning: {data['Note']}")
            return []
        
        time_series_key = f"Time Series FX (Daily)"
        if time_series_key not in data:
            print(f"No data found for {from_currency}/{to_currency}")
            return []
        
        prices = []
        for date_str, values in data[time_series_key].items():
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Filter by date range
            if start_date <= date_str <= end_date:
                price = Price(
                    ticker=f"{from_currency}{to_currency}",
                    time=date_str,
                    open=float(values["1. open"]),
                    high=float(values["2. high"]),
                    low=float(values["3. low"]),
                    close=float(values["4. close"]),
                    volume=0  # Forex typically doesn't have volume data
                )
                prices.append(price)
        
        # Sort by date
        prices.sort(key=lambda x: x.time)
        return prices
    
    def _get_fx_intraday(self, from_currency: str, to_currency: str, 
                         interval: str = "60min") -> List[Price]:
        """Get intraday forex data"""
        params = {
            "function": "FX_INTRADAY",
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "interval": interval,
            "outputsize": "full",
            "apikey": self.api_key
        }
        
        session = _requests_session()
        response = session.get(self.base_url, params=params, timeout=15)
        if response.status_code != 200:
            print(f"Error fetching intraday forex data: {response.status_code}")
            return []
        
        data = response.json()
        
        time_series_key = f"Time Series FX ({interval})"
        if time_series_key not in data:
            print(f"No intraday data found for {from_currency}/{to_currency}")
            return []
        
        prices = []
        for datetime_str, values in list(data[time_series_key].items())[:1000]:  # Limit to last 1000 points
            try:
                price = Price(
                    ticker=f"{from_currency}{to_currency}",
                    time=datetime_str,
                    open=float(values["1. open"]),
                    high=float(values["2. high"]),
                    low=float(values["3. low"]),
                    close=float(values["4. close"]),
                    volume=0
                )
                prices.append(price)
            except Exception as e:
                continue
        
        prices.sort(key=lambda x: x.time)
        return prices
    
    def get_commodity_prices(self, symbol: str, start_date: str, end_date: str) -> List[Price]:
        """
        Fetch commodity prices (e.g., XAUUSD for Gold, XAGUSD for Silver)
        
        Args:
            symbol: Commodity symbol (e.g., 'XAUUSD', 'XAGUSD', 'WTI', 'BRENT')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of Price objects
        """
        # For commodities like XAUUSD, treat as forex pair
        if len(symbol) == 6 and symbol.startswith("X"):
            from_curr = symbol[:3]
            to_curr = symbol[3:]
            return self.get_forex_prices(from_curr, to_curr, start_date, end_date)
        
        # For other commodities, use TIME_SERIES_DAILY
        return self._get_time_series_daily(symbol, start_date, end_date)
    
    def get_index_prices(self, symbol: str, start_date: str, end_date: str) -> List[Price]:
        """
        Fetch index prices (e.g., SPX, IXIC, DJI)
        
        Args:
            symbol: Index symbol (e.g., 'SPX', 'IXIC', 'DJI', 'VIX')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            List of Price objects
        """
        # Map common index names to their ETF equivalents (Alpha Vantage supports ETFs on free tier)
        symbol_map = {
            "SPX": "SPY",       # S&P 500 -> SPDR S&P 500 ETF
            "NAS100": "QQQ",    # NASDAQ 100 -> Invesco QQQ ETF
            "US30": "DIA",      # Dow Jones -> SPDR Dow Jones ETF
            "DOW": "DIA",       # Alternative Dow Jones symbol
            "NASDAQ": "QQQ",    # Alternative NASDAQ symbol
            "S&P500": "SPY",    # Alternative S&P 500 symbol
        }
        
        av_symbol = symbol_map.get(symbol.upper(), symbol)
        return self._get_time_series_daily(av_symbol, start_date, end_date)
    
    def _get_time_series_daily(self, symbol: str, start_date: str, end_date: str) -> List[Price]:
        """Get daily time series data for any symbol"""
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "compact",  # Free tier only supports compact (last 100 days)
            "apikey": self.api_key
        }
        
        session = _requests_session()
        response = session.get(self.base_url, params=params, timeout=15)
        if response.status_code != 200:
            print(f"Error fetching data for {symbol}: {response.status_code}")
            return []
        
        data = response.json()
        
        # Check for API limit or error messages
        if "Information" in data:
            print(f"Alpha Vantage Info: {data['Information']}")
            # Sometimes free tier returns info but still has data
        
        if "Note" in data:
            print(f"Alpha Vantage Note: {data['Note']}")
            return []
        
        if "Error Message" in data:
            print(f"Alpha Vantage Error: {data['Error Message']}")
            return []
        
        time_series_key = "Time Series (Daily)"
        if time_series_key not in data:
            print(f"No data found for {symbol}")
            print(f"Available keys: {list(data.keys())}")
            return []
        
        prices = []
        for date_str, values in data[time_series_key].items():
            if start_date <= date_str <= end_date:
                try:
                    price = Price(
                        ticker=symbol,
                        time=date_str,
                        open=float(values["1. open"]),
                        high=float(values["2. high"]),
                        low=float(values["3. low"]),
                        close=float(values["4. close"]),
                        volume=int(values["5. volume"])
                    )
                    prices.append(price)
                except Exception as e:
                    continue
        
        if not prices:
            print(f"No prices in date range {start_date} to {end_date} for {symbol}")
            # Return all prices if date range filtering failed
            if data[time_series_key]:
                print(f"Returning all available data instead")
                for date_str, values in list(data[time_series_key].items())[:100]:  # Last 100 days
                    try:
                        price = Price(
                            ticker=symbol,
                            time=date_str,
                            open=float(values["1. open"]),
                            high=float(values["2. high"]),
                            low=float(values["3. low"]),
                            close=float(values["4. close"]),
                            volume=int(values["5. volume"])
                        )
                        prices.append(price)
                    except Exception as e:
                        continue
        
        prices.sort(key=lambda x: x.time)
        return prices
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """Get current exchange rate"""
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": self.api_key
        }
        
        session = _requests_session()
        response = session.get(self.base_url, params=params, timeout=15)
        if response.status_code != 200:
            return None
        
        data = response.json()
        if "Realtime Currency Exchange Rate" in data:
            rate_data = data["Realtime Currency Exchange Rate"]
            return float(rate_data["5. Exchange Rate"])
        
        return None
