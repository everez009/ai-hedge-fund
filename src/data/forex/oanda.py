"""
OANDA API Adapter for Forex Trading
Supports live and practice trading accounts
"""
import os
import requests
from typing import List, Dict, Optional
from datetime import datetime
from src.data.models import Price


def _requests_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


class OandaAdapter:
    """Adapter for OANDA REST API v20"""
    
    def __init__(self, api_key: str = None, account_id: str = None, environment: str = "practice"):
        self.api_key = api_key or os.environ.get("OANDA_API_KEY")
        self.account_id = account_id or os.environ.get("OANDA_ACCOUNT_ID")
        self.environment = environment or os.environ.get("OANDA_ENVIRONMENT", "practice")
        
        if not self.api_key:
            raise ValueError("OANDA API key is required. Set OANDA_API_KEY environment variable.")
        
        # Set base URL based on environment
        if self.environment == "live":
            self.base_url = "https://api-fxtrade.oanda.com"
        else:
            self.base_url = "https://api-fxpractice.oanda.com"
            
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_prices(self, instrument: str, start_date: str, end_date: str, 
                   granularity: str = "D") -> List[Price]:
        """
        Fetch candlestick data from OANDA
        
        Args:
            instrument: Currency pair (e.g., 'EUR_USD', 'XAU_USD')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: Candlestick granularity ('S5', 'S10', 'S15', 'S30', 'M1', 'M2', 'M4', 'M5', 'M10', 'M15', 'M30', 'H1', 'H2', 'H3', 'H4', 'H6', 'H8', 'H12', 'D', 'W', 'M')
            
        Returns:
            List of Price objects
        """
        # Normalize instrument format
        normalized_instrument = self._normalize_instrument(instrument)
        
        params = {
            "price": "MBA",  # Mid, Bid, Ask prices
            "granularity": granularity,
            "from": start_date,
            "to": end_date,
            "count": 5000  # Maximum candles per request
        }
        
        url = f"{self.base_url}/v3/instruments/{normalized_instrument}/candles"
        session = _requests_session()
        response = session.get(url, headers=self.headers, params=params, timeout=15)
        
        if response.status_code != 200:
            print(f"Error fetching OANDA data: {response.status_code}")
            print(response.text)
            return []
        
        data = response.json()
        
        if "candles" not in data:
            print(f"No candlestick data found for {instrument}")
            return []
        
        prices = []
        for candle in data["candles"]:
            if candle["complete"]:  # Only use complete candles
                try:
                    mid = candle["mid"]
                    price = Price(
                        ticker=instrument,
                        time=candle["time"],
                        open=float(mid["o"]),
                        high=float(mid["h"]),
                        low=float(mid["l"]),
                        close=float(mid["c"]),
                        volume=int(candle.get("volume", 0))
                    )
                    prices.append(price)
                except Exception as e:
                    continue
        
        prices.sort(key=lambda x: x.time)
        return prices
    
    def _normalize_instrument(self, instrument: str) -> str:
        """Normalize instrument format for OANDA"""
        # Convert EURUSD to EUR_USD
        if len(instrument) == 6 and instrument.isalpha():
            return f"{instrument[:3]}_{instrument[3:]}"
        
        # Convert XAUUSD to XAU_USD
        if "_" not in instrument and len(instrument) >= 6:
            if instrument.startswith("XAU"):
                return "XAU_USD"
            elif instrument.startswith("XAG"):
                return "XAG_USD"
        
        return instrument.replace("/", "_")
    
    def get_current_price(self, instrument: str) -> Optional[Dict]:
        """Get current bid/ask prices"""
        normalized_instrument = self._normalize_instrument(instrument)
        
        params = {"instruments": normalized_instrument}
        url = f"{self.base_url}/v3/pricing"
        session = _requests_session()
        response = session.get(url, headers=self.headers, params=params, timeout=15)
        
        if response.status_code != 200:
            return None
        
        data = response.json()
        
        if "prices" in data and len(data["prices"]) > 0:
            price_data = data["prices"][0]
            return {
                "instrument": instrument,
                "time": price_data["time"],
                "bid": float(price_data["bids"][0]["price"]),
                "ask": float(price_data["asks"][0]["price"]),
                "spread": float(price_data["asks"][0]["price"]) - float(price_data["bids"][0]["price"])
            }
        
        return None
    
    def get_account_summary(self) -> Optional[Dict]:
        """Get account summary information"""
        url = f"{self.base_url}/v3/accounts/{self.account_id}/summary"
        session = _requests_session()
        response = session.get(url, headers=self.headers, timeout=15)
        
        if response.status_code != 200:
            print(f"Error fetching account summary: {response.status_code}")
            return None
        
        return response.json()["account"]
    
    def place_order(self, instrument: str, units: float, order_type: str = "MARKET", 
                    side: str = "BUY", stop_loss: float = None, take_profit: float = None) -> Optional[Dict]:
        """
        Place a trade order
        
        Args:
            instrument: Currency pair
            units: Number of units (positive for buy, negative for sell)
            order_type: Order type ('MARKET', 'LIMIT', 'STOP')
            side: 'BUY' or 'SELL'
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Order response dictionary
        """
        normalized_instrument = self._normalize_instrument(instrument)
        
        order_data = {
            "order": {
                "instrument": normalized_instrument,
                "units": str(units),
                "type": order_type,
                "positionFill": "DEFAULT"
            }
        }
        
        if stop_loss:
            order_data["order"]["stopLossOnFill"] = {
                "price": str(stop_loss),
                "timeInForce": "GTC"
            }
        
        if take_profit:
            order_data["order"]["takeProfitOnFill"] = {
                "price": str(take_profit)
            }
        
        url = f"{self.base_url}/v3/accounts/{self.account_id}/orders"
        session = _requests_session()
        response = session.post(url, headers=self.headers, json=order_data, timeout=15)
        
        if response.status_code != 201:
            print(f"Error placing order: {response.status_code}")
            print(response.text)
            return None
        
        return response.json()
    
    def get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        url = f"{self.base_url}/v3/accounts/{self.account_id}/openPositions"
        session = _requests_session()
        response = session.get(url, headers=self.headers, timeout=15)
        
        if response.status_code != 200:
            return []
        
        data = response.json()
        return data.get("positions", [])
    
    def close_position(self, instrument: str) -> Optional[Dict]:
        """Close an existing position"""
        normalized_instrument = self._normalize_instrument(instrument)
        
        url = f"{self.base_url}/v3/accounts/{self.account_id}/positions/{normalized_instrument}/close"
        session = _requests_session()
        response = session.put(url, headers=self.headers, timeout=15)
        
        if response.status_code != 200:
            print(f"Error closing position: {response.status_code}")
            return None
        
        return response.json()
