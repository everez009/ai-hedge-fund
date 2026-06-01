import json
import math

import numpy as np
import pandas as pd
from langchain_core.messages import HumanMessage

from src.graph.state import AgentState, show_agent_reasoning
from src.tools.api import get_prices, prices_to_df
from src.utils.api_key import get_api_key_from_state
from src.utils.progress import progress


def safe_float(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value) or np.isnan(value):
            return default
        return float(value)
    except (ValueError, TypeError, OverflowError):
        return default


def scalper_analyst_agent(state: AgentState, agent_id: str = "scalper_analyst_agent"):
    """Short-term scalping analyst for FX, commodities, indices, and crypto."""
    data = state["data"]
    start_date = data["start_date"]
    end_date = data["end_date"]
    tickers = data["tickers"]

    scalper_analysis = {}

    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Fetching scalper price data")
        prices = get_prices(ticker=ticker, start_date=start_date, end_date=end_date, api_key=api_key)

        if not prices:
            progress.update_status(agent_id, ticker, "Failed: No price data found")
            continue

        prices_df = prices_to_df(prices)
        if len(prices_df) < 14:
            progress.update_status(agent_id, ticker, "Failed: Insufficient history")
            continue

        progress.update_status(agent_id, ticker, "Analyzing fast price action")
        scalper_signal = calculate_scalper_signal(prices_df)

        scalper_analysis[ticker] = {
            "signal": scalper_signal["signal"],
            "confidence": round(scalper_signal["confidence"] * 100, 2),
            "trade_horizon": "scalping",
            "max_position_size": 0.05,
            "reasoning": {
                "signal": scalper_signal["signal"],
                "details": scalper_signal["details"],
                "metrics": scalper_signal["metrics"],
            },
        }

        progress.update_status(agent_id, ticker, "Done", analysis=json.dumps(scalper_analysis, indent=2))

    message = HumanMessage(content=json.dumps(scalper_analysis), name=agent_id)
    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(scalper_analysis, "Scalper Analyst")

    state["data"]["analyst_signals"][agent_id] = scalper_analysis
    progress.update_status(agent_id, None, "Done")

    return {"messages": state["messages"] + [message], "data": state["data"]}


def daytrader_analyst_agent(state: AgentState, agent_id: str = "daytrader_analyst_agent"):
    """Intraday/short-term analyst for FX, commodities, indices, and crypto."""
    data = state["data"]
    start_date = data["start_date"]
    end_date = data["end_date"]
    tickers = data["tickers"]

    daytrader_analysis = {}

    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Fetching daytrader price data")
        prices = get_prices(ticker=ticker, start_date=start_date, end_date=end_date, api_key=api_key)

        if not prices:
            progress.update_status(agent_id, ticker, "Failed: No price data found")
            continue

        prices_df = prices_to_df(prices)
        if len(prices_df) < 21:
            progress.update_status(agent_id, ticker, "Failed: Insufficient history")
            continue

        progress.update_status(agent_id, ticker, "Analyzing short-term trend")
        daytrader_signal = calculate_daytrader_signal(prices_df)

        daytrader_analysis[ticker] = {
            "signal": daytrader_signal["signal"],
            "confidence": round(daytrader_signal["confidence"] * 100, 2),
            "trade_horizon": "daytrading",
            "max_position_size": 0.10,
            "reasoning": {
                "signal": daytrader_signal["signal"],
                "details": daytrader_signal["details"],
                "metrics": daytrader_signal["metrics"],
            },
        }

        progress.update_status(agent_id, ticker, "Done", analysis=json.dumps(daytrader_analysis, indent=2))

    message = HumanMessage(content=json.dumps(daytrader_analysis), name=agent_id)
    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(daytrader_analysis, "Daytrader Analyst")

    state["data"]["analyst_signals"][agent_id] = daytrader_analysis
    progress.update_status(agent_id, None, "Done")

    return {"messages": state["messages"] + [message], "data": state["data"]}


def calculate_scalper_signal(prices_df: pd.DataFrame) -> dict:
    close = prices_df["close"].dropna()
    short_ema = close.ewm(span=3, adjust=False).mean().iloc[-1]
    medium_ema = close.ewm(span=8, adjust=False).mean().iloc[-1]
    rsi = calculate_rsi(close, 5).iloc[-1]
    atr = calculate_atr(prices_df).iloc[-1]
    volatility = close.pct_change().rolling(5).std().iloc[-1]

    ema_bias = 1 if short_ema > medium_ema else -1 if short_ema < medium_ema else 0
    momentum_bias = 1 if rsi > 55 else -1 if rsi < 45 else 0
    volatility_bias = 1 if volatility < 0.015 else -1 if volatility > 0.045 else 0

    score = ema_bias * 0.45 + momentum_bias * 0.35 + volatility_bias * 0.20
    signal = "neutral"
    if score >= 0.4:
        signal = "bullish"
    elif score <= -0.4:
        signal = "bearish"

    confidence = max(0.35, min(0.95, abs(score) + 0.40))

    details = []
    details.append(f"Short EMA is {'above' if short_ema > medium_ema else 'below' if short_ema < medium_ema else 'near'} medium EMA.")
    details.append(f"RSI is {rsi:.1f}, favoring {'bullish' if rsi > 55 else 'bearish' if rsi < 45 else 'neutral'} momentum.")
    details.append(f"ATR is {atr:.4f}, volatility is {volatility:.4f}.")

    return {
        "signal": signal,
        "confidence": confidence,
        "details": " ".join(details),
        "metrics": {
            "ema_3": round(safe_float(short_ema), 6),
            "ema_8": round(safe_float(medium_ema), 6),
            "rsi_5": round(safe_float(rsi), 2),
            "atr": round(safe_float(atr), 6),
            "volatility_5d": round(safe_float(volatility), 6),
        },
    }


def calculate_daytrader_signal(prices_df: pd.DataFrame) -> dict:
    close = prices_df["close"].dropna()
    ema_short = close.ewm(span=9, adjust=False).mean().iloc[-1]
    ema_medium = close.ewm(span=21, adjust=False).mean().iloc[-1]
    rsi = calculate_rsi(close, 14).iloc[-1]
    adx = calculate_adx(prices_df).iloc[-1]["adx"]
    atr = calculate_atr(prices_df).iloc[-1]

    trend_bias = 1 if ema_short > ema_medium else -1 if ema_short < ema_medium else 0
    momentum_bias = 1 if rsi > 50 else -1 if rsi < 50 else 0
    volatility_bias = 1 if atr / close.iloc[-1] < 0.03 else -1 if atr / close.iloc[-1] > 0.08 else 0
    strength_bias = 1 if adx > 25 else -1 if adx < 15 else 0

    raw_score = trend_bias * 0.35 + momentum_bias * 0.25 + volatility_bias * 0.15 + strength_bias * 0.25
    signal = "neutral"
    if raw_score >= 0.35:
        signal = "bullish"
    elif raw_score <= -0.35:
        signal = "bearish"

    confidence = max(0.30, min(0.94, abs(raw_score) + 0.40))
    details = []
    details.append(f"Short EMA is {'above' if ema_short > ema_medium else 'below' if ema_short < ema_medium else 'near'} medium EMA.")
    details.append(f"RSI is {rsi:.1f}, ADX is {adx:.1f}.")
    details.append(f"ATR relative risk is {atr / close.iloc[-1]:.4f}.")

    return {
        "signal": signal,
        "confidence": confidence,
        "details": " ".join(details),
        "metrics": {
            "ema_9": round(safe_float(ema_short), 6),
            "ema_21": round(safe_float(ema_medium), 6),
            "rsi_14": round(safe_float(rsi), 2),
            "adx_14": round(safe_float(adx), 2),
            "atr": round(safe_float(atr), 6),
        },
    }


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    return true_range.rolling(period, min_periods=1).mean().fillna(method="ffill").fillna(0)


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

    up_move = df["high"].diff()
    down_move = df["low"].shift() - df["low"]
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    atr = tr.rolling(window=period, min_periods=1).mean()
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(window=period, min_periods=1).mean() / atr.replace(0, np.nan))
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(window=period, min_periods=1).mean() / atr.replace(0, np.nan))
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(window=period, min_periods=1).mean().fillna(0)

    return pd.DataFrame({"adx": adx, "+di": plus_di.fillna(0), "-di": minus_di.fillna(0)}, index=df.index)
