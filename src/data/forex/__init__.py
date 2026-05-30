"""
Forex, Indices, and Commodities Data Adapters
"""
from .alpha_vantage import AlphaVantageAdapter
from .twelvedata import TwelveDataAdapter
from .oanda import OandaAdapter

__all__ = ['AlphaVantageAdapter', 'TwelveDataAdapter', 'OandaAdapter']
