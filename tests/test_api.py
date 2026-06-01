from unittest.mock import MagicMock

from src.tools.api import get_prices


def test_get_prices_uses_global_forex_provider(monkeypatch):
    fake_price = MagicMock(open=1.0, high=1.0, low=1.0, close=1.0, volume=1, time="2024-01-01")
    fake_provider = MagicMock()
    fake_provider.get_prices.return_value = [fake_price]
    monkeypatch.setattr("src.tools.api.get_forex_provider", lambda: fake_provider)

    prices = get_prices("EURUSD", "2024-01-01", "2024-01-05")

    assert len(prices) == 1
    assert prices[0].close == 1.0
    fake_provider.get_prices.assert_called_once_with("EURUSD", "2024-01-01", "2024-01-05")
