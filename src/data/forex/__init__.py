"""
Forex, Indices, and Commodities Data Adapters
"""
from .twelvedata import TwelveDataAdapter
from .oanda import OandaAdapter
from .itick import ITickAdapter
from .dukascopy import DukascopyAdapter

__all__ = ['TwelveDataAdapter', 'OandaAdapter', 'ITickAdapter', 'DukascopyAdapter']
