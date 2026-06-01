import json
import math

from langchain_core.messages import HumanMessage
import numpy as np
import pandas as pd

from src.graph.state import AgentState, show_agent_reasoning
from src.tools.api import get_prices, prices_to_df
from src.utils.api_key import get_api_key_from_state
from src.utils.progress import progress


def currency_pair_analyst_agent(state: AgentState, agent_id: str = "currency_pair_analyst_agent"):
    """Analyze forex and currency pair markets with FX-aware technical and range logic."""
    data = state["data"]
    start_date = data["start_date"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")

    currency_analysis = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Fetching FX price data")
        prices = get_prices(ticker=ticker, start_date=start_date, end_date=end_date, api_key=api_key)

        if not prices:
            progress.update_status(agent_id, ticker, "Failed: No price data found")
            continue

        prices_df = prices_to_df(prices)

        if len(prices_df) < 20:
            progress.update_status(agent_id, ticker, "Failed: Insufficient FX history")
            continue

        progress.update_status(agent_id, ticker, "Calculating trend signals")
        trend_signals = analyze_currency_trend(prices_df)

        progress.update_status(agent_id, ticker, "Calculating momentum signals")
        momentum_signals = analyze_currency_momentum(prices_df)

        progress.update_status(agent_id, ticker, "Calculating volatility signals")
        volatility_signals = analyze_currency_volatility(prices_df)

        progress.update_status(agent_id, ticker, "Calculating range structure")
        range_signals = analyze_currency_range(prices_df)

        progress.update_status(agent_id, ticker, "Calculating strength pressure")
        carry_signals = analyze_currency_strength(prices_df)

        combined_score = (
            trend_signals["score"] * 0.25
            + momentum_signals["score"] * 0.25
            + volatility_signals["score"] * 0.15
            + range_signals["score"] * 0.25
            + carry_signals["score"] * 0.10
        )

        if combined_score >= 6.5:
            signal = "bullish"
        elif combined_score <= 3.5:
            signal = "bearish"
        else:
            signal = "neutral"

        confidence = round(min(100, max(10, abs(combined_score - 5) * 20 + 30)), 2)

        currency_analysis[ticker] = {
            "signal": signal,
            "confidence": confidence,
            "score": round(combined_score, 2),
            "reasoning": {
                "trend": trend_signals,
                "momentum": momentum_signals,
                "volatility": volatility_signals,
                "range": range_signals,
                "pair_strength": carry_signals,
            },
        }

        progress.update_status(agent_id, ticker, "Done", analysis=json.dumps(currency_analysis, indent=2))

    message = HumanMessage(content=json.dumps(currency_analysis), name=agent_id)

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(currency_analysis, "Currency Pair Analyst")

    state["data"]["analyst_signals"][agent_id] = currency_analysis
    progress.update_status(agent_id, None, "Done")

    return {"messages": state["messages"] + [message], "data": state["data"]}


def analyze_currency_trend(prices_df: pd.DataFrame) -> dict:
    close = prices_df["close"].dropna()
    ema_short = close.ewm(span=8, adjust=False).mean()
    ema_medium = close.ewm(span=21, adjust=False).mean()
    ema_long = close.ewm(span=50, adjust=False).mean()

    score = 5.0
    details = []

    if close.iloc[-1] > ema_short.iloc[-1] > ema_medium.iloc[-1] > ema_long.iloc[-1]:
        score += 2.5
        details.append("Strong FX uptrend: close above short, medium, and long EMAs.")
    elif close.iloc[-1] < ema_short.iloc[-1] < ema_medium.iloc[-1] < ema_long.iloc[-1]:
        score -= 2.5
        details.append("Strong FX downtrend: close below short, medium, and long EMAs.")
    else:
        details.append("Trend is mixed or consolidating.")

    return {
        "score": round(_clamp(score), 2),
        "signal": "bullish" if score > 5 else "bearish" if score < 5 else "neutral",
        "ema_short": round(float(ema_short.iloc[-1]), 6),
        "ema_medium": round(float(ema_medium.iloc[-1]), 6),
        "ema_long": round(float(ema_long.iloc[-1]), 6),
        "details": " ".join(details),
    }


def analyze_currency_momentum(prices_df: pd.DataFrame) -> dict:
    close = prices_df["close"].dropna()
    returns_10 = _pct_change(close, 10)
    returns_20 = _pct_change(close, 20)
    rsi = calculate_rsi(close, 14)

    score = 5.0
    details = []

    if returns_10 > 0 and returns_20 > 0:
        score += 2.0
        details.append("Short-term momentum is positive.")
    elif returns_10 < 0 and returns_20 < 0:
        score -= 2.0
        details.append("Short-term momentum is negative.")
    else:
        details.append("Momentum is mixed.")

    if rsi.iloc[-1] > 70:
        score += 0.5
        details.append("RSI indicates strength, but may be extended.")
    elif rsi.iloc[-1] < 30:
        score -= 0.5
        details.append("RSI indicates weakness or potential mean reversion.")

    return {
        "score": round(_clamp(score), 2),
        "signal": "bullish" if score > 5 else "bearish" if score < 5 else "neutral",
        "returns_10d": round(returns_10, 4),
        "returns_20d": round(returns_20, 4),
        "rsi": round(float(rsi.iloc[-1]), 2),
        "details": " ".join(details),
    }


def analyze_currency_volatility(prices_df: pd.DataFrame) -> dict:
    atr = calculate_atr(prices_df, 14)
    close = prices_df["close"].dropna()
    volatility = close.pct_change().rolling(14).std().iloc[-1] * math.sqrt(252)

    score = 5.0
    details = []

    if volatility > 0.08:
        score -= 1.0
        details.append("FX volatility is elevated.")
    elif volatility < 0.03:
        score += 1.0
        details.append("FX volatility is low and trend structures are easier to follow.")
    else:
        details.append("Volatility is within normal FX range.")

    return {
        "score": round(_clamp(score), 2),
        "signal": "bullish" if score > 5 else "bearish" if score < 5 else "neutral",
        "atr": round(float(atr.iloc[-1]), 6) if len(atr) else 0.0,
        "volatility": round(float(volatility), 4) if not np.isnan(volatility) else 0.0,
        "details": " ".join(details),
    }


def analyze_currency_range(prices_df: pd.DataFrame) -> dict:
    close = prices_df["close"].dropna()
    window = min(60, len(close))
    high = close.tail(window).max()
    low = close.tail(window).min()
    latest = close.iloc[-1]
    range_position = (latest - low) / (high - low) if high > low else 0.5
    returns_60 = _pct_change(close, 60)

    score = 5.0
    details = []

    if range_position >= 0.8 and returns_60 > 0:
        score += 2.5
        details.append("Pair is near 60-day highs with positive momentum.")
    elif range_position <= 0.2 and returns_60 < 0:
        score -= 2.5
        details.append("Pair is near 60-day lows with negative momentum.")
    else:
        details.append("Range structure is neutral.")

    return {
        "score": round(_clamp(score), 2),
        "signal": "bullish" if score > 5 else "bearish" if score < 5 else "neutral",
        "range_position": round(float(range_position), 4),
        "returns_60d": round(returns_60, 4),
        "details": " ".join(details),
    }


def analyze_currency_strength(prices_df: pd.DataFrame) -> dict:
    close = prices_df["close"].dropna()
    returns_5 = _pct_change(close, 5)
    recent_range = close.tail(10)

    score = 5.0
    details = []

    if returns_5 > 0 and recent_range.iloc[-1] > recent_range.mean():
        score += 1.5
        details.append("Recent momentum and price strength favor the base currency.")
    elif returns_5 < 0 and recent_range.iloc[-1] < recent_range.mean():
        score -= 1.5
        details.append("Recent momentum and price weakness favor the quote currency.")
    else:
        details.append("Pair strength is balanced.")

    return {
        "score": round(_clamp(score), 2),
        "signal": "bullish" if score > 5 else "bearish" if score < 5 else "neutral",
        "returns_5d": round(returns_5, 4),
        "short_range_mean": round(float(recent_range.mean()), 6),
        "details": " ".join(details),
    }


def calculate_rsi(series: pd.Series, window: int) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ema_up = up.ewm(span=window, adjust=False).mean()
    ema_down = down.ewm(span=window, adjust=False).mean()
    rs = ema_up / (ema_down.replace(0, np.nan))
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


def calculate_atr(prices_df: pd.DataFrame, window: int) -> pd.Series:
    high_low = prices_df["high"] - prices_df["low"]
    high_close = (prices_df["high"] - prices_df["close"].shift()).abs()
    low_close = (prices_df["low"] - prices_df["close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(window=window).mean().fillna(method="backfill")


def _pct_change(series: pd.Series, periods: int) -> float:
    if len(series) <= periods:
        return 0.0
    current = series.iloc[-1]
    previous = series.iloc[-periods]
    try:
        return (current - previous) / previous if previous else 0.0
    except Exception:
        return 0.0


def _clamp(value: float, minimum: float = 0.0, maximum: float = 10.0) -> float:
    return float(max(minimum, min(maximum, value)))
