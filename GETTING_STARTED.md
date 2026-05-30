# AI Hedge Fund - Forex, Indices & Commodities Setup Guide

## Quick Start

Your AI Hedge Fund has been successfully installed and configured for forex, indices, and commodities trading!

### Location
```
/Users/mac/aihedgefund
```

## What's Been Added

### 1. Forex Data Adapters
- **AlphaVantage**: Free tier available, excellent for forex and commodities
- **TwelveData**: Great coverage with free tier
- **OANDA**: For live/practice trading

### 2. Supported Instruments

**Forex Pairs (7)**:
- EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD

**Commodities (4)**:
- XAUUSD (Gold), XAGUSD (Silver), WTI (Oil), BRENT (Oil)

**Indices (4)**:
- SPX (S&P 500), NAS100 (NASDAQ), US30 (Dow Jones), GER30 (DAX)

### 3. Configuration Files
- `.env` - API keys configuration
- `config/forex_config.py` - Instrument specifications
- `FOREX_TRADING_GUIDE.md` - Detailed documentation

## Next Steps

### Step 1: Get API Keys (Choose at least one)

**Option A: Alpha Vantage (Recommended - FREE)**
1. Visit: https://www.alphavantage.co/support/#api-key
2. Get your free API key
3. Add to `.env` file:
```
ALPHAVANTAGE_API_KEY=your_key_here
```

**Option B: Twelve Data (FREE tier)**
1. Visit: https://twelvedata.com/
2. Sign up for free account
3. Add to `.env`:
```
TWELVEDATA_API_KEY=your_key_here
```

**Option C: OANDA (Requires Account)**
For live trading:
```
OANDA_API_KEY=your_key
OANDA_ACCOUNT_ID=your_account_id
OANDA_ENVIRONMENT=practice
```

### Step 2: Set LLM API Key

You need at least one LLM provider for the AI agents:

```
OPENAI_API_KEY=sk-... (from https://platform.openai.com/)
```

OR

```
ANTHROPIC_API_KEY=sk-ant-... (from https://anthropic.com/)
```

### Step 3: Test Your Setup

```bash
cd /Users/mac/aihedgefund
poetry run python test_forex_setup.py
```

### Step 4: Run Your First Analysis

**Test with sample data:**
```bash
poetry run python examples/forex_trading.py
```

**Run the hedge fund on forex pairs:**
```bash
poetry run python src/main.py --ticker EURUSD,XAUUSD
```

**With custom date range:**
```bash
poetry run python src/main.py --ticker EURUSD,GBPUSD,XAUUSD --start-date 2024-01-01 --end-date 2024-03-01
```

**Backtest a strategy:**
```bash
poetry run python src/backtester.py --ticker EURUSD,XAUUSD
```

## File Structure

```
aihedgefund/
├── .env                          # Your API keys (already created)
├── config/
│   └── forex_config.py          # Instrument configurations
├── src/
│   ├── data/
│   │   └── forex/               # Forex data adapters
│   │       ├── alpha_vantage.py
│   │       ├── twelvedata.py
│   │       └── oanda.py
│   ├── tools/
│   │   └── forex_api.py         # Unified forex data provider
│   └── main.py                  # Main entry point
├── examples/
│   └── forex_trading.py         # Example script
├── FOREX_TRADING_GUIDE.md       # Detailed guide
├── GETTING_STARTED.md           # This file
└── test_forex_setup.py          # Quick test script
```

## Usage Examples

### Example 1: Analyze Gold (XAUUSD)
```bash
poetry run python src/main.py --ticker XAUUSD
```

### Example 2: Multiple Forex Pairs
```bash
poetry run python src/main.py --ticker EURUSD,GBPUSD,USDJPY
```

### Example 3: Mixed Portfolio
```bash
poetry run python src/main.py --ticker EURUSD,XAUUSD,NAS100
```

### Example 4: With Specific Analysts
```bash
poetry run python src/main.py --ticker EURUSD --analysts technicals,risk_management
```

## Trading Parameters

Default settings in `.env`:
- **Leverage**: 10:1 (conservative)
- **Risk per Trade**: 1% of capital
- **Max Positions**: 5 concurrent trades
- **Starting Capital**: $100,000 (configurable in code)

Adjust these based on your risk tolerance.

## Important Notes

### Forex-Specific Considerations

1. **Trading Hours**: Forex markets are open 24/5
   - Best liquidity: London-New York overlap (13:00-17:00 UTC)

2. **Pip Values**: 
   - Most pairs: 0.0001 = 1 pip
   - JPY pairs: 0.01 = 1 pip

3. **Spreads**: 
   - EURUSD: ~1 pip (tightest)
   - Exotics: 3-10 pips

4. **Volatility**:
   - Low: USDCHF, EURGBP
   - Medium: EURUSD, USDJPY
   - High: GBPJPY, XAUUSD, NAS100

### Risk Management

⚠️ **Important**: Forex trading involves significant risk!

- Start with small position sizes
- Use stop losses
- Never risk more than 1-2% per trade
- Be aware of economic calendar events
- Correlated pairs move together (e.g., EURUSD & GBPUSD)

## Troubleshooting

### "No data sources configured"
- Check `.env` file has valid API keys
- Restart your terminal after editing `.env`

### "API rate limit exceeded"
- Alpha Vantage free tier: 5 calls/minute, 500/day
- Wait or upgrade to paid tier
- Add multiple data sources for failover

### "Symbol not found"
- Use correct format: EURUSD (6 chars, no separator)
- Check supported instruments in `config/forex_config.py`

### Import errors
```bash
cd /Users/mac/aihedgefund
poetry install
```

## Documentation

- **Quick Start**: This file
- **Detailed Guide**: `FOREX_TRADING_GUIDE.md`
- **Original Docs**: `README.md`

## Support & Resources

- Alpha Vantage Docs: https://www.alphavantage.co/documentation/
- Twelve Data Docs: https://twelvedata.com/docs
- OANDA API: https://developer.oanda.com/rest-live-v20/introduction/

## Disclaimer

⚠️ **EDUCATIONAL PURPOSES ONLY**

This software is for learning and research only. It is NOT intended for real trading.

- No investment advice or guarantees
- Past performance ≠ future results
- Forex/commodities trading can result in substantial losses
- Consult a financial advisor before making any trading decisions
- You are solely responsible for any trading decisions

## Ready to Start?

1. ✅ Installation complete
2. ⏳ Add API keys to `.env`
3. ⏳ Run: `poetry run python test_forex_setup.py`
4. ⏳ Try: `poetry run python src/main.py --ticker EURUSD,XAUUSD`

Happy (paper) trading! 📈
