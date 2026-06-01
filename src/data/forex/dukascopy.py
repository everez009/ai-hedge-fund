"""
Dukascopy Tick Data Downloader & Adapter

Downloads free tick data from Dukascopy's datafeed servers and resamples
to daily (or other) OHLCV candles. No API key is required — Dukascopy
provides free, unlimited access to historical tick data for forex,
commodities (XAUUSD, XAGUSD), indices, and crypto.

How it works:
1. Connects to https://datafeed.dukascopy.com/datafeed
2. Downloads .bi5 compressed tick files hour-by-hour
3. Decompresses using LZMA
4. Parses binary tick data (20 bytes: time_ms, ask, bid, ask_vol, bid_vol)
5. Resamples to daily OHLCV candles
6. Returns list of Price objects

Binary record format (20 bytes, big-endian):
    uint32  time_ms    (milliseconds since start of hour)
    uint32  ask        (ask price in pip units)
    uint32  bid        (bid price in pip units)
    float32 ask_vol    (ask volume)
    float32 bid_vol    (bid volume)

Price conversion:
    actual_price = raw_uint32_value * pip_factor
    pip_factor depends on instrument:
      - Forex pairs (5-digit): 1e-5  (EURUSD -> 1.03952)
      - Gold (XAUUSD):         1e-3  (2615.502)
      - Silver (XAGUSD):       1e-3
      - Indices (US30, etc.):  1e-2
      - Crypto (BTCUSD):       1e-1
"""

import lzma
import logging
import struct
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Optional

import requests

from src.data.models import Price

logger = logging.getLogger(__name__)

# Pip factors: how to convert raw uint32 price to actual price
PIP_FACTORS = {
    # --- Commodities (3 decimal places) ---
    "XAUUSD": 1e-3,
    "XAGUSD": 1e-3,
    "XPTUSD": 1e-3,
    "XPDUSD": 1e-3,
    # --- Indices (2 decimal places) ---
    "US30": 1e-2,
    "NAS100": 1e-2,
    "SPX": 1e-2,
    "GER30": 1e-2,
    "UK100": 1e-2,
    "FRA40": 1e-2,
    "ESP35": 1e-2,
    "JPN225": 1e-2,
    "AUS200": 1e-2,
    "HKG33": 1e-2,
    "CHN50": 1e-2,
    "SUI30": 1e-2,
    "EUSTX50": 1e-2,
    # --- Crypto (1 decimal place) ---
    "BTCUSD": 1e-1,
    "ETHUSD": 1e-1,
    # --- JPY pairs (3 decimal places) ---
    "USDJPY": 1e-3,
    "EURJPY": 1e-3,
    "GBPJPY": 1e-3,
    "CHFJPY": 1e-3,
    "AUDJPY": 1e-3,
    "NZDJPY": 1e-3,
    "CADJPY": 1e-3,
}

# Default pip factor for standard 5-digit forex pairs
DEFAULT_PIP_FACTOR = 1e-5

# Symbol aliases: map common names to Dukascopy symbol names
SYMBOL_ALIASES = {
    "GOLD": "XAUUSD",
    "SILVER": "XAGUSD",
    "DJI": "US30",
    "DOW": "US30",
    "IXIC": "NAS100",
    "NASDAQ": "NAS100",
    "NDX": "NAS100",
    "DAX": "GER30",
    "FTSE": "UK100",
    "NIKKEI": "JPN225",
    "N225": "JPN225",
    "HSI": "HKG33",
    "SP500": "SPX",
    "S&P500": "SPX",
}

# Binary record: 20 bytes big-endian
_TICK_STRUCT = struct.Struct(">IIIff")


def normalize_symbol(symbol: str) -> str:
    """Normalize a symbol to its Dukascopy datafeed name."""
    s = symbol.upper().strip().replace("/", "").replace("_", "").replace("-", "")
    return SYMBOL_ALIASES.get(s, s)


def get_pip_factor(symbol: str) -> float:
    """Return the multiplier to convert Dukascopy integer prices to float."""
    norm = normalize_symbol(symbol)
    return PIP_FACTORS.get(norm, DEFAULT_PIP_FACTOR)


def _parse_ticks(raw: bytes, date: datetime, hour: int, pip_factor: float) -> list:
    """
    Parse Dukascopy binary tick data from a decompressed .bi5 file.

    Each record is 20 bytes: uint32 time_ms, uint32 ask, uint32 bid, float32 ask_vol, float32 bid_vol.
    """
    ticks = []
    num_records = len(raw) // 20
    if num_records == 0:
        return ticks

    hour_start = date.replace(hour=hour, minute=0, second=0, microsecond=0)

    for i in range(num_records):
        try:
            time_ms, ask_raw, bid_raw, ask_vol, bid_vol = _TICK_STRUCT.unpack_from(raw, i * 20)
            if time_ms == 0 and ask_raw == 0 and bid_raw == 0:
                continue

            tick_time = hour_start + timedelta(milliseconds=time_ms)
            bid_price = bid_raw * pip_factor
            ask_price = ask_raw * pip_factor

            if bid_price <= 0 or ask_price <= 0:
                continue

            mid = (bid_price + ask_price) / 2.0
            ticks.append({
                "time": tick_time,
                "bid": bid_price,
                "ask": ask_price,
                "mid": mid,
                "volume": int(abs(ask_vol) + abs(bid_vol)),
            })
        except struct.error:
            continue

    return ticks


def _resample_to_daily(ticks: list, symbol: str) -> List[Price]:
    """
    Resample a list of tick dicts to daily OHLCV candles.

    Each tick dict: {'time': datetime, 'mid': float, 'volume': int}
    """
    by_date: dict[str, list] = defaultdict(list)
    for t in ticks:
        date_key = t["time"].strftime("%Y-%m-%d")
        by_date[date_key].append(t)

    prices = []
    for date_key in sorted(by_date):
        day_ticks = by_date[date_key]
        mids = [t["mid"] for t in day_ticks if t["mid"] > 0]
        if not mids:
            continue

        price = Price(
            ticker=symbol,
            time=date_key,
            open=round(mids[0], 6),
            high=round(max(mids), 6),
            low=round(min(mids), 6),
            close=round(mids[-1], 6),
            volume=sum(t["volume"] for t in day_ticks),
        )
        prices.append(price)

    return prices


class DukascopyAdapter:
    """
    Adapter for Dukascopy free tick data feed.

    Downloads compressed tick files from datafeed.dukascopy.com,
    parses them, and resamples to daily OHLCV candles.

    No API key is required — this is a free, public data feed.

    Supports: Forex pairs, XAUUSD, XAGUSD, indices (US30, NAS100, SPX),
    and crypto (BTCUSD, ETHUSD).
    """

    BASE_URL = "https://datafeed.dukascopy.com/datafeed"

    def __init__(self, api_key: str = None, base_url: str = None):
        # api_key is accepted for interface compatibility but not required
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self._session = requests.Session()
        self._session.trust_env = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

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
            symbol: e.g. 'EURUSD', 'XAUUSD', 'US30'
            start_date: 'YYYY-MM-DD'
            end_date:   'YYYY-MM-DD'
            interval:   Only '1day' is currently supported.

        Returns:
            List[Price] sorted by time ascending.
        """
        norm = normalize_symbol(symbol)

        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            logger.warning("Dukascopy: invalid date format for %s/%s", start_date, end_date)
            return []

        # Cap range to avoid excessively long downloads
        max_days = 180
        if (end_dt - start_dt).days > max_days:
            logger.info("Dukascopy: capping date range to %d days (was %d)",
                        max_days, (end_dt - start_dt).days)
            start_dt = end_dt - timedelta(days=max_days)

        pip_factor = get_pip_factor(norm)

        # Download tick data day by day
        all_ticks = []
        current = start_dt
        total_days = (end_dt - start_dt).days + 1

        while current <= end_dt:
            day_ticks = self._download_day(norm, current, pip_factor)
            if day_ticks:
                all_ticks.extend(day_ticks)
                logger.debug("Dukascopy: %s %s — %d ticks",
                             norm, current.strftime("%Y-%m-%d"), len(day_ticks))
            current += timedelta(days=1)

        if not all_ticks:
            logger.warning("Dukascopy: no tick data downloaded for %s (%s to %s)",
                           norm, start_date, end_date)
            return []

        # Resample to daily candles
        candles = _resample_to_daily(all_ticks, symbol)
        logger.info("Dukascopy: %d daily candles for %s (%d ticks total)",
                    len(candles), norm, len(all_ticks))
        return candles

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get the latest available price by downloading the most recent day's data."""
        norm = normalize_symbol(symbol)
        pip_factor = get_pip_factor(norm)

        # Try today and yesterday
        today = datetime.utcnow()
        for delta in range(3):
            day = today - timedelta(days=delta)
            ticks = self._download_day(norm, day, pip_factor)
            if ticks:
                return ticks[-1]["mid"]

        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _download_day(self, symbol: str, date: datetime, pip_factor: float) -> list:
        """Download all 24 hourly tick files for a single day."""
        day_ticks = []
        # Dukascopy uses 0-indexed months and days
        year = date.year
        month = date.month - 1
        day = date.day - 1

        for hour in range(24):
            url = f"{self.base_url}/{symbol}/{year}/{month:02d}/{day:02d}/{hour:02d}h_ticks.bi5"
            try:
                resp = self._session.get(url, timeout=10)
                if resp.status_code != 200 or len(resp.content) < 20:
                    continue
                # Decompress LZMA
                decompressed = lzma.decompress(resp.content)
                if not decompressed:
                    continue
                ticks = _parse_ticks(decompressed, date, hour, pip_factor)
                day_ticks.extend(ticks)
            except (lzma.LZMAError, requests.RequestException, struct.error):
                continue

        return day_ticks
