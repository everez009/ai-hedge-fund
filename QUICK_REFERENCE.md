# Quick Reference Card - AI Hedge Fund for Forex

## 📍 Location
```
/Users/mac/aihedgefund
```

## 🔑 Required API Keys (Add to .env)

### Data Provider (Pick 1+)
- **Alpha Vantage** (FREE): https://www.alphavantage.co/support/#api-key
- **Twelve Data** (FREE): https://twelvedata.com/

### AI Provider (Pick 1+)
- **OpenAI**: https://platform.openai.com/
- **Anthropic**: https://anthropic.com/

## 🚀 Quick Commands

```bash
# Navigate to project
cd /Users/mac/aihedgefund

# Test setup
poetry run python test_forex_setup.py

# Run analysis
poetry run python src/main.py --ticker EURUSD,XAUUSD

# Backtest
poetry run python src/backtester.py --ticker EURUSD

# Example script
poetry run python examples/forex_trading.py
```

## 💹 Supported Instruments

**Forex**: EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD  
**Commodities**: XAUUSD (Gold), XAGUSD (Silver), WTI, BRENT  
**Indices**: SPX, NAS100, US30, GER30  

## 📊 Example Tickers

```bash
# Single instrument
poetry run python src/main.py --ticker XAUUSD

# Multiple forex pairs
poetry run python src/main.py --ticker EURUSD,GBPUSD,USDJPY

# Mixed portfolio
poetry run python src/main.py --ticker EURUSD,XAUUSD,NAS100

# Custom date range
poetry run python src/main.py --ticker EURUSD --start-date 2024-01-01 --end-date 2024-03-01
```

## ⚙️ Configuration (.env)

```env
# Data APIs
ALPHAVANTAGE_API_KEY=your_key_here
TWELVEDATA_API_KEY=your_key_here

# LLM APIs
OPENAI_API_KEY=sk-...

# Trading Params
DEFAULT_LEVERAGE=10
RISK_PER_TRADE=0.01
MAX_POSITIONS=5
```

## 📁 Key Files

- `GETTING_STARTED.md` - Full setup guide
- `FOREX_TRADING_GUIDE.md` - Trading strategies
- `config/forex_config.py` - Instrument specifications
- `src/tools/forex_api.py` - Data provider
- `.env` - Your API keys

## ⚠️ Important

- Educational purposes only
- NOT for real trading
- Paper trade first
- High risk of loss in forex/commodities
- Consult financial advisor

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| No data sources | Add API key to .env |
| Import error | Run `poetry install` |
| Rate limit | Wait or upgrade API tier |
| Symbol not found | Use format: EURUSD (6 chars) |

## 📚 Learn More

- Alpha Vantage Docs: https://www.alphavantage.co/documentation/
- Twelve Data Docs: https://twelvedata.com/docs
- Original Project: https://github.com/virattt/ai-hedge-fund

---
**Ready?** Add API keys → Test → Trade (paper)! 📈
