"""
Unified Forex, Indices, and Commodities API Provider
Integrates multiple data sources for comprehensive market coverage
"""
import os
from typing import List, Optional
from src.data.models import Price
from src.data.forex import AlphaVantageAdapter, TwelveDataAdapter, OandaAdapter
from src.data.forex.itick import ITickAdapter


class ForexDataProvider:
    """
    Unified data provider for forex, indices, and commodities
    Automatically selects the best available data source
    """
    
    def __init__(self):
        self.adapters = {}
        self._initialize_adapters()
        
    def _initialize_adapters(self):
        """Initialize available data adapters based on API keys"""
        # iTick (Best for indices - unlimited free tier)
        if os.environ.get("ITICK_API_KEY"):
            try:
                self.adapters["itick"] = ITickAdapter()
                print("✓ iTick adapter initialized (primary for indices)")
            except Exception as e:
                print(f"✗ Failed to initialize iTick: {e}")
        
        # Alpha Vantage
        if os.environ.get("ALPHAVANTAGE_API_KEY"):
            try:
                self.adapters["alphavantage"] = AlphaVantageAdapter()
                print("✓ Alpha Vantage adapter initialized")
            except Exception as e:
                print(f"✗ Failed to initialize Alpha Vantage: {e}")
        
        # Twelve Data
        if os.environ.get("TWELVEDATA_API_KEY"):
            try:
                self.adapters["twelvedata"] = TwelveDataAdapter()
                print("✓ Twelve Data adapter initialized")
            except Exception as e:
                print(f"✗ Failed to initialize Twelve Data: {e}")
        
        # OANDA
        if os.environ.get("OANDA_API_KEY"):
            try:
                self.adapters["oanda"] = OandaAdapter()
                print("✓ OANDA adapter initialized")
            except Exception as e:
                print(f"✗ Failed to initialize OANDA: {e}")
        
        if not self.adapters:
            print("⚠ Warning: No forex data adapters initialized. Please set at least one API key.")
    
    def get_prices(self, symbol: str, start_date: str, end_date: str, 
                   source: str = None) -> List[Price]:
        """
        Get price data from the best available source
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD', 'XAUUSD', 'SPX')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            source: Specific source to use ('alphavantage', 'twelvedata', 'oanda') or None for auto
            
        Returns:
            List of Price objects
        """
        # Determine symbol type
        symbol_type = self._classify_symbol(symbol)
        
        # If specific source requested, use it
        if source and source in self.adapters:
            return self._get_from_source(source, symbol, start_date, end_date, symbol_type)
        
        # Try each adapter in priority order
        # For indices, use iTick first (best free tier), then Alpha Vantage
        if symbol_type == "index":
            priority_order = ["itick", "alphavantage", "twelvedata", "oanda"]
        else:
            priority_order = ["twelvedata", "alphavantage", "oanda"]
        
        for adapter_name in priority_order:
            if adapter_name in self.adapters:
                try:
                    prices = self._get_from_source(adapter_name, symbol, start_date, end_date, symbol_type)
                    if prices:
                        print(f"✓ Successfully fetched {len(prices)} prices for {symbol} from {adapter_name}")
                        return prices
                except Exception as e:
                    print(f"✗ Error with {adapter_name}: {e}")
                    continue
        
        print(f"⚠ No data found for {symbol}")
        return []
    
    def _get_from_source(self, source: str, symbol: str, start_date: str, 
                         end_date: str, symbol_type: str) -> List[Price]:
        """Get prices from a specific source"""
        adapter = self.adapters[source]
        
        if source == "itick":
            if symbol_type == "index":
                return adapter.get_index_prices(symbol, start_date, end_date)
            # iTick is primarily for indices, fall through for other types
        
        elif source == "alphavantage":
            if symbol_type == "forex":
                from_curr = symbol[:3]
                to_curr = symbol[3:]
                return adapter.get_forex_prices(from_curr, to_curr, start_date, end_date)
            elif symbol_type == "commodity":
                return adapter.get_commodity_prices(symbol, start_date, end_date)
            elif symbol_type == "index":
                return adapter.get_index_prices(symbol, start_date, end_date)
        
        elif source == "twelvedata":
            return adapter.get_prices(symbol, start_date, end_date)
        
        elif source == "oanda":
            return adapter.get_prices(symbol, start_date, end_date)
        
        return []
    
    def _classify_symbol(self, symbol: str) -> str:
        """Classify symbol as forex, commodity, or index"""
        # Normalize symbol
        symbol = symbol.upper().replace("/", "").replace("_", "")
        
        # Forex pairs (6 characters, all letters)
        if len(symbol) == 6 and symbol.isalpha():
            return "forex"
        
        # Commodities
        if symbol.startswith("XAU") or symbol.startswith("XAG") or symbol.startswith("XPT"):
            return "commodity"
        if symbol in ["WTI", "BRENT", "NATGAS", "COPPER"]:
            return "commodity"
        
        # Indices
        if symbol in ["SPX", "IXIC", "DJI", "VIX", "RUT"]:
            return "index"
        if symbol.startswith("NAS") or symbol.startswith("US30") or symbol.startswith("GER"):
            return "index"
        
        # Default to forex
        return "forex"
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current/latest price for a symbol"""
        # Try OANDA first for real-time prices
        if "oanda" in self.adapters:
            try:
                price_data = self.adapters["oanda"].get_current_price(symbol)
                if price_data:
                    return (price_data["bid"] + price_data["ask"]) / 2
            except:
                pass
        
        # Fall back to other sources
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        prices = self.get_prices(symbol, start_date, end_date)
        if prices:
            return prices[-1].close
        
        return None
    
    def get_available_sources(self) -> List[str]:
        """Get list of available data sources"""
        return list(self.adapters.keys())


# Global instance
_forex_provider = None


def get_forex_provider() -> ForexDataProvider:
    """Get or create the global forex data provider instance"""
    global _forex_provider
    if _forex_provider is None:
        _forex_provider = ForexDataProvider()
    return _forex_provider
