"""
Forex, Indices, and Commodities Data Adapters
"""
from .twelvedata import TwelveDataAdapter
from .oanda import OandaAdapter
from .itick import ITickAdapter
from .dukascopy import DukascopyAdapter
from .massive import MassiveAdapter

__all__ = ['TwelveDataAdapter', 'OandaAdapter', 'ITickAdapter', 'DukascopyAdapter', 'MassiveAdapter']
