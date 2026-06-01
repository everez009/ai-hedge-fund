import pytest
from unittest.mock import patch

from src.agents.short_term_analysts import scalper_analyst_agent, daytrader_analyst_agent
from src.data.models import Price


def make_price_series(start_price: float, days: int) -> list[Price]:
    prices = []
    price = start_price
    for i in range(days):
        open_price = price
        close_price = price * (1 + 0.0015 * (i / max(days - 1, 1)))
        high_price = max(open_price, close_price) * 1.002
        low_price = min(open_price, close_price) * 0.998
        prices.append(
            Price(
                open=open_price,
                close=close_price,
                high=high_price,
                low=low_price,
                volume=1000 + i * 10,
                time=f"2024-01-{i+1:02d}T00:00:00Z",
            )
        )
        price = close_price
    return prices


@patch("src.agents.short_term_analysts.get_prices")
def test_scalper_analyst_returns_structured_output(mock_get_prices):
    mock_get_prices.return_value = make_price_series(1.10, 60)

    state = {
        "messages": [],
        "data": {
            "tickers": ["EURUSD"],
            "start_date": "2024-01-01",
            "end_date": "2024-03-01",
            "analyst_signals": {},
        },
        "metadata": {"show_reasoning": False},
    }

    result = scalper_analyst_agent(state)

    assert "messages" in result
    assert "data" in result
    assert result["data"]["analyst_signals"]
    assert "scalper_analyst_agent" in result["data"]["analyst_signals"]

    analysis = result["data"]["analyst_signals"]["scalper_analyst_agent"]
    assert "EURUSD" in analysis

    eurusd_analysis = analysis["EURUSD"]
    assert eurusd_analysis["signal"] in {"bullish", "bearish", "neutral"}
    assert isinstance(eurusd_analysis["confidence"], float)
    assert "reasoning" in eurusd_analysis
    assert "metrics" in eurusd_analysis["reasoning"]
    assert eurusd_analysis["trade_horizon"] == "scalping"


@patch("src.agents.short_term_analysts.get_prices")
def test_daytrader_analyst_returns_structured_output(mock_get_prices):
    mock_get_prices.return_value = make_price_series(1.10, 60)

    state = {
        "messages": [],
        "data": {
            "tickers": ["EURUSD"],
            "start_date": "2024-01-01",
            "end_date": "2024-03-01",
            "analyst_signals": {},
        },
        "metadata": {"show_reasoning": False},
    }

    result = daytrader_analyst_agent(state)

    assert "messages" in result
    assert "data" in result
    assert result["data"]["analyst_signals"]
    assert "daytrader_analyst_agent" in result["data"]["analyst_signals"]

    analysis = result["data"]["analyst_signals"]["daytrader_analyst_agent"]
    assert "EURUSD" in analysis

    eurusd_analysis = analysis["EURUSD"]
    assert eurusd_analysis["signal"] in {"bullish", "bearish", "neutral"}
    assert isinstance(eurusd_analysis["confidence"], float)
    assert "reasoning" in eurusd_analysis
    assert "metrics" in eurusd_analysis["reasoning"]
    assert eurusd_analysis["trade_horizon"] == "daytrading"
