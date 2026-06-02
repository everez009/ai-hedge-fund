"""
Massive.com API Adapter for Indices, Forex, and Crypto

Provides access to 11,400+ indices (S&P, Dow Jones, VIX, Nasdaq),
1,750+ forex pairs, and crypto via the Massive REST API.

API Documentation: https://massive.com/docs/rest/indices/overview

Ticker format:
    Indices:  I:SPX, I:DJI, I:NDX, I:VIX, I:XAU (gold index)
    Forex:    C:EURUSD, C:GBPUSD, C:USDJPY
    Crypto:   X:BTCUSD, X:ETHUSD

Key endpoints:
    Custom Bars: GET /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}
    Snapshot:    GET /v3/snapshot/indices?ticker.any_of=I:SPX,I:DJI

Authentication: Bearer token via Authorization header.
Free tier includes end-of-day data for select indices and forex.
"""

import logging
import os
from datetime import datetime
from typing import List, Optional

import requests

from src.data.models import Price

logger = logging.getLogger(__name__)

# Map our internal symbols to Massive ticker format
INDICES_MAP = {
    "SPX": "I:SPX",
    "S&P500": "I:SPX",
    "SP500": "I:SPX",
    "DJI": "I:DJI",
    "US30": "I:DJI",
    "DOW": "I:DJI",
    "NAS100": "I:NDX",
    "NDX": "I:NDX",
    "NASDAQ": "I:NDX",
    "IXIC": "I:NDX",
    "VIX": "I:VIX",
    "RUT": "I:RUT",
    "RUSSELL": "I:RUT",
    "GER30": "I:DAX",
    "DAX": "I:DAX",
    "UK100": "I:FTSE",
    "FTSE": "I:FTSE",
    "JPN225": "I:N225",
    "NIKKEI": "I:N225",
    "N225": "I:N225",
    "HKG33": "I:HSI",
    "HSI": "I:HSI",
    "XAU_IDX": "I:XAU",  # Gold index (not spot price)
    "FRA40": "I:CAC",
    "EUSTX50": "I:SX5E",
}


def _to_massive_ticker(symbol: str) -> str:
    """Convert a standard symbol to Massive ticker format."""
    s = symbol.upper().strip().replace("/", "").replace("_", "").replace("-", "")

    # Check indices map first
    if s in INDICES_MAP:
        return INDICES_MAP[s]

    # Forex pairs (6-char alpha): EURUSD -> C:EURUSD
    if len(s) == 6 and s.isalpha():
        return f"C:{s}"

    # Commodities: XAUUSD/XAGUSD spot prices are available as C:XAUUSD, C:XAGUSD
    # (NOT I:XAU which is a gold-mining stock index ~187)
    if s.startswith("XAU"):
        return "C:XAUUSD"  # Spot gold via forex endpoint
    if s.startswith("XAG"):
        return "C:XAGUSD"  # Spot silver via forex endpoint
    if s.startswith("XPT") or s.startswith("XPD"):
        return None  # Platinum/Palladium not available
    if s in ("WTI", "BRENT", "NATGAS", "COPPER"):
        return None  # Energy/metals not available as forex

    # Crypto
    if s in ("BTCUSD", "BTCEUR"):
        return f"X:{s}"
    if s in ("ETHUSD", "ETHEUR"):
        return f"X:{s}"

    # Default: try as index
    return f"I:{s}"


class MassiveAdapter:
    """
    Adapter for Massive.com API - Best source for indices data.

    Provides access to 11,400+ indices, 1,750+ forex pairs, and crypto.
    Free tier includes end-of-day data for select instruments.

    Authentication:
        Set MASSIVE_API_KEY environment variable.
    """

    BASE_URL = "https://api.massive.com"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("MASSIVE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Massive API key is required. Set MASSIVE_API_KEY environment variable."
            )
        self._session = requests.Session()
        self._session.trust_env = False
        self._session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
        })

    def get_prices(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1day",
    ) -> List[Price]:
        """
        Fetch daily OHLCV candles for *symbol* between *start_date* and *end_date*.

        Args:
            symbol: e.g. 'SPX', 'EURUSD', 'XAUUSD', 'US30', 'BTCUSD'
            start_date: 'YYYY-MM-DD'
            end_date:   'YYYY-MM-DD'
            interval:   '1day' (default), '1hour', '1minute', etc.

        Returns:
            List[Price] sorted by time ascending.
        """
        massive_ticker = _to_massive_ticker(symbol)

        # If the symbol can't be mapped (e.g., XAUUSD spot), skip Massive entirely
        if massive_ticker is None:
            logger.debug("Massive: skipping %s (not available on Massive)", symbol)
            return []

        # Map interval to Massive timespan/multiplier
        multiplier, timespan = self._parse_interval(interval)

        url = (
            f"{self.BASE_URL}/v2/aggs/ticker/{massive_ticker}"
            f"/range/{multiplier}/{timespan}/{start_date}/{end_date}"
        )
        params = {"limit": 50000, "sort": "asc"}

        try:
            resp = self._session.get(url, params=params, timeout=30)
        except requests.RequestException as e:
            logger.warning("Massive: request failed for %s: %s", symbol, e)
            return []

        if resp.status_code != 200:
            logger.warning(
                "Massive: HTTP %d for %s (%s)", resp.status_code, symbol, massive_ticker
            )
            return []

        try:
            data = resp.json()
        except ValueError:
            logger.warning("Massive: invalid JSON response for %s", symbol)
            return []

        if data.get("status") != "OK" and data.get("status") != "DELAYED":
            msg = data.get("message", data.get("error", "unknown"))
            logger.warning("Massive: API error for %s: %s", symbol, msg)
            return []

        results = data.get("results", [])
        if not results:
            logger.info("Massive: no results for %s (%s)", symbol, massive_ticker)
            return []

        prices = []
        for bar in results:
            try:
                timestamp_ms = bar.get("t", 0)
                if not timestamp_ms:
                    continue
                date_str = datetime.utcfromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d")
                price = Price(
                    ticker=symbol,
                    time=date_str,
                    open=float(bar["o"]),
                    high=float(bar["h"]),
                    low=float(bar["l"]),
                    close=float(bar["c"]),
                    volume=int(bar.get("v", 0) or 0),
                )
                prices.append(price)
            except (KeyError, ValueError, TypeError):
                continue

        logger.info(
            "Massive: %d daily candles for %s (%s)",
            len(prices), symbol, massive_ticker,
        )
        return prices

    def get_index_prices(
        self, symbol: str, start_date: str, end_date: str
    ) -> List[Price]:
        """Alias for get_prices — kept for interface compatibility with ITickAdapter."""
        return self.get_prices(symbol, start_date, end_date)

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get the latest price for a symbol via the snapshot endpoint."""
        massive_ticker = _to_massive_ticker(symbol)

        # If the symbol can't be mapped, skip
        if massive_ticker is None:
            return None

        # Determine the correct snapshot endpoint
        if massive_ticker.startswith("I:"):
            url = f"{self.BASE_URL}/v3/snapshot/indices"
            params = {"ticker.any_of": massive_ticker}
        elif massive_ticker.startswith("C:"):
            url = f"{self.BASE_URL}/v3/snapshot/forex"
            params = {"ticker.any_of": massive_ticker}
        elif massive_ticker.startswith("X:"):
            url = f"{self.BASE_URL}/v3/snapshot/crypto"
            params = {"ticker.any_of": massive_ticker}
        else:
            url = f"{self.BASE_URL}/v3/snapshot/indices"
            params = {"ticker.any_of": massive_ticker}

        try:
            resp = self._session.get(url, params=params, timeout=10)
            if resp.status_code != 200:
                return None

            data = resp.json()
            results = data.get("results", [])
            if not results:
                return None

            # For indices, the value is in 'value' field
            if massive_ticker.startswith("I:"):
                return float(results[0].get("value", 0))

            # For forex/crypto, use session close
            session = results[0].get("session", {})
            close = session.get("close")
            if close:
                return float(close)

            value = results[0].get("value")
            if value:
                return float(value)

            return None
        except Exception:
            return None

    @staticmethod
    def _parse_interval(interval: str) -> tuple:
        """Convert interval string to (multiplier, timespan) for Massive API."""
        mapping = {
            "1min": (1, "minute"),
            "5min": (5, "minute"),
            "15min": (15, "minute"),
            "30min": (30, "minute"),
            "1hour": (1, "hour"),
            "4hour": (4, "hour"),
            "1day": (1, "day"),
            "1week": (1, "week"),
            "1month": (1, "month"),
        }
        return mapping.get(interval, (1, "day"))
