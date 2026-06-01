import pytest
from unittest.mock import patch

from src.agents.currency_analyst import currency_pair_analyst_agent
from src.data.models import Price


def make_price_series(start_price: float, days: int) -> list[Price]:
    prices = []
    price = start_price
    for i in range(days):
        open_price = price
        close_price = price * (1 + 0.002 * i / days)
        high_price = max(open_price, close_price) * 1.001
        low_price = min(open_price, close_price) * 0.999
        prices.append(
            Price(
                open=open_price,
                close=close_price,
                high=high_price,
                low=low_price,
                volume=1000 + i,
                time=f"2024-01-{i+1:02d}T00:00:00Z",
            )
        )
        price = close_price
    return prices


@patch("src.agents.currency_analyst.get_prices")
def test_currency_pair_analyst_returns_structured_output(mock_get_prices):
    mock_get_prices.return_value = make_price_series(1.10, 70)

    state = {
        "messages": [],
        "data": {
            "tickers": ["EURUSD"],
            "start_date": "2024-01-01",
            "end_date": "2024-03-11",
            "analyst_signals": {},
        },
        "metadata": {"show_reasoning": False},
    }

    result = currency_pair_analyst_agent(state)

    assert "messages" in result
    assert "data" in result
    assert result["data"]["analyst_signals"]
    assert "currency_pair_analyst_agent" in result["data"]["analyst_signals"]
    analysis = result["data"]["analyst_signals"]["currency_pair_analyst_agent"]
    assert "EURUSD" in analysis
    usd_analysis = analysis["EURUSD"]
    assert usd_analysis["signal"] in {"bullish", "bearish", "neutral"}
    assert isinstance(usd_analysis["confidence"], float)
    assert isinstance(usd_analysis["score"], float)
    assert "reasoning" in usd_analysis
    assert set(usd_analysis["reasoning"]).issuperset({"trend", "momentum", "volatility", "range", "pair_strength"})
