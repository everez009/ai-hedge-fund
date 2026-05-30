"""
Configuration for Forex, Indices, and Commodities Trading
"""

FOREX_PAIRS = {
    "EURUSD": {"name": "Euro / US Dollar", "type": "major", "pip_value": 0.0001},
    "GBPUSD": {"name": "British Pound / US Dollar", "type": "major", "pip_value": 0.0001},
    "USDJPY": {"name": "US Dollar / Japanese Yen", "type": "major", "pip_value": 0.01},
    "USDCHF": {"name": "US Dollar / Swiss Franc", "type": "major", "pip_value": 0.0001},
    "AUDUSD": {"name": "Australian Dollar / US Dollar", "type": "major", "pip_value": 0.0001},
    "USDCAD": {"name": "US Dollar / Canadian Dollar", "type": "major", "pip_value": 0.0001},
    "NZDUSD": {"name": "New Zealand Dollar / US Dollar", "type": "major", "pip_value": 0.0001},
}

COMMODITIES = {
    "XAUUSD": {"name": "Gold / US Dollar", "type": "precious_metal"},
    "XAGUSD": {"name": "Silver / US Dollar", "type": "precious_metal"},
    "WTI": {"name": "Crude Oil WTI", "type": "energy"},
    "BRENT": {"name": "Brent Crude Oil", "type": "energy"},
}

INDICES = {
    "SPX": {"name": "S&P 500", "type": "us_index"},
    "NAS100": {"name": "NASDAQ 100", "type": "us_index"},
    "US30": {"name": "Dow Jones", "type": "us_index"},
    "GER30": {"name": "DAX 30", "type": "european_index"},
}

BEGINNER_INSTRUMENTS = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
HIGH_VOLATILITY_INSTRUMENTS = ["GBPJPY", "XAGUSD", "WTI", "NATGAS", "NAS100"]
