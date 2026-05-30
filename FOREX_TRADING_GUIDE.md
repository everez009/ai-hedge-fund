# AI Hedge Fund - Forex, Indices & Commodities Trading Guide

This guide explains how to use the AI Hedge Fund for trading forex pairs, indices, and commodities like XAUUSD (Gold).

## Overview

The system has been extended to support:
- **Forex Pairs**: EURUSD, GBPUSD, USDJPY, etc.
- **Commodities**: XAUUSD (Gold), XAGUSD (Silver), WTI (Oil), etc.
- **Indices**: SPX (S&P 500), NAS100 (NASDAQ), US30 (Dow Jones), etc.

## Setup

### 1. Install Dependencies

```bash
cd /Users/mac/aihedgefund
poetry install
```

### 2. Configure API Keys

Edit the `.env` file and add at least ONE of these data source API keys:

#### Option A: Alpha Vantage (Recommended - Free Tier Available)
Get your free API key from: https://www.alphavantage.co/support/#api-key

```env
ALPHAVANTAGE_API_KEY=your_api_key_here
```

#### Option B: Twelve Data (Free Tier Available)
Get your API key from: https://twelvedata.com/

```env
TWELVEDATA_API_KEY=your_api_key_here
```

#### Option C: OANDA (Requires Account)
For live/practice trading: https://developer.oanda.com/

```env
OANDA_API_KEY=your_api_key
OANDA_ACCOUNT_ID=your_account_id
OANDA_ENVIRONMENT=practice  # or 'live'
```

### 3. Set LLM API Key

You also need at least one LLM provider:

```env
OPENAI_API_KEY=your_openai_key
# OR
ANTHROPIC_API_KEY=your_anthropic_key
# OR
GROQ_API_KEY=your_groq_key
```

## Supported Instruments

### Major Forex Pairs
- EURUSD (Euro/US Dollar)
- GBPUSD (British Pound/US Dollar)
- USDJPY (US Dollar/Japanese Yen)
- USDCHF (US Dollar/Swiss Franc)
- AUDUSD (Australian Dollar/US Dollar)
- USDCAD (US Dollar/Canadian Dollar)
- NZDUSD (New Zealand Dollar/US Dollar)

### Commodities
- XAUUSD (Gold)
- XAGUSD (Silver)
- WTI (Crude Oil)
- BRENT (Brent Crude)
- NATGAS (Natural Gas)

### Indices
- SPX (S&P 500)
- NAS100 (NASDAQ 100)
- US30 (Dow Jones)
- GER30 (DAX 30)
- UK100 (FTSE 100)
- JPN225 (Nikkei 225)

## Usage

### Quick Test

Test your data sources and see supported instruments:

```bash
python examples/forex_trading.py
```

### Run the Hedge Fund

Run on specific forex/commodity instruments:

```bash
poetry run python src/main.py --ticker EURUSD,XAUUSD,GBPUSD
```

### With Date Range

```bash
poetry run python src/main.py --ticker EURUSD,XAUUSD --start-date 2024-01-01 --end-date 2024-03-01
```

### Backtesting

```bash
poetry run python src/backtester.py --ticker EURUSD,XAUUSD
```

## Architecture

### Data Providers

The system uses multiple data adapters:

1. **AlphaVantageAdapter**: Free tier available, good for forex and commodities
2. **TwelveDataAdapter**: Excellent coverage, free tier with limitations
3. **OandaAdapter**: For live trading with OANDA broker

The `ForexDataProvider` automatically selects the best available source.

### Configuration

Instrument configurations are in `config/forex_config.py`:
- Pip values
- Typical spreads
- Trading hours
- Volatility characteristics

## Trading Considerations

### Forex-Specific Features

1. **Leverage**: Default is 50:1 (configurable via `DEFAULT_LEVERAGE`)
2. **Pip Values**: Different for JPY pairs vs others
3. **Trading Sessions**: 24/5 market with different volatility by session
4. **Spreads**: Generally tighter than stocks

### Risk Management

- Default risk per trade: 1% (`RISK_PER_TRADE`)
- Maximum positions: 5 (`MAX_POSITIONS`)
- Margin requirement: 2% for forex (adjustable)

### Best Practices

1. **Start with Majors**: EURUSD, GBPUSD have tightest spreads
2. **Avoid News Times**: High volatility during major economic releases
3. **Session Awareness**: London/New York overlap has highest liquidity
4. **Correlation**: Be aware of correlated pairs (e.g., EURUSD and GBPUSD)

## Example Portfolio Configuration

For forex trading, use this portfolio structure:

```python
portfolio = {
    "cash": 100000,  # Starting capital
    "margin_requirement": 0.02,  # 2% margin (50:1 leverage)
    "positions": {...},
    "realized_gains": {...}
}
```

## Troubleshooting

### No Data Retrieved

1. Check API keys in `.env` file
2. Verify internet connection
3. Check API rate limits (Alpha Vantage free tier: 5 calls/minute)

### Symbol Not Found

Ensure correct format:
- Forex: EURUSD (6 characters, no separator)
- Commodities: XAUUSD, XAGUSD
- Indices: SPX, NAS100, US30

### API Rate Limits

If hitting rate limits:
- Upgrade to paid tier
- Add more data sources (system will failover)
- Reduce frequency of calls

## Advanced Configuration

### Custom Data Sources

Add new adapters in `src/data/forex/`:

```python
class MyCustomAdapter:
    def get_prices(self, symbol, start_date, end_date):
        # Implementation
        pass
```

Register in `src/tools/forex_api.py`.

### Modifying Risk Parameters

Edit `.env`:

```env
DEFAULT_LEVERAGE=50
RISK_PER_TRADE=0.01
MAX_POSITIONS=5
```

## Next Steps

1. Test with paper trading first
2. Start with small position sizes
3. Monitor performance closely
4. Adjust parameters based on results

## Disclaimer

This is for educational purposes only. Forex, commodities, and indices trading involves substantial risk of loss. Past performance does not guarantee future results. Always consult with a qualified financial advisor before making trading decisions.
