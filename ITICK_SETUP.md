# 🚀 iTick API Setup Guide

## Why iTick?

iTick is the **best free API for global indices** in 2026:

✅ **Unlimited free calls** (no daily limits)  
✅ **Real-time data** (<50ms latency)  
✅ **Direct index symbols** (no ETF mapping needed)  
✅ **100+ global indices** supported  
✅ **Simple REST + WebSocket** API  

---

## Get Your FREE API Token

### Step 1: Register
Visit: **https://api.itick.org/**

Click "Sign Up" or "Register" to create a free account.

### Step 2: Get Your Token
After registration, you'll receive an API token. It looks like:
```
itick_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Step 3: Configure
Add your token to the `.env` file:

```bash
ITICK_API_KEY=your_actual_token_here
```

---

## Supported Indices

| Symbol | Index Name | iTick Code |
|--------|-----------|------------|
| SPX | S&P 500 | SPX |
| NAS100 / IXIC | NASDAQ Composite | IXIC |
| US30 / DJI | Dow Jones Industrial | DJI |
| GER30 | German DAX | GDAXI |
| FTSE | FTSE 100 | FTSE |
| NIKKEI | Nikkei 225 | N225 |
| HSI | Hang Seng Index | HSI |
| VIX | Volatility Index | VIX |

And many more!

---

## Test Your Setup

Run the test script:

```bash
cd /Users/mac/aihedgefund
python test_itick.py
```

Expected output:
```
🧪 Testing iTick API Integration
======================================================================

📅 Date range: 2026-04-29 to 2026-05-29

Testing SPX (S&P 500)...
  ✅ Success! Got 21 price points
     Latest close: $754.60
     Date range: 2026-05-01 to 2026-05-29

Testing IXIC (NASDAQ Composite)...
  ✅ Success! Got 21 price points
     Latest close: $735.60
     Date range: 2026-05-01 to 2026-05-29
```

---

## Current Status

**Without iTick token:** System uses Alpha Vantage with ETF mapping (SPX→SPY)  
**With iTick token:** System uses direct index data with unlimited calls

The system automatically prioritizes iTick for indices when the token is configured.

---

## Benefits Over Alpha Vantage

| Feature | iTick | Alpha Vantage |
|---------|-------|---------------|
| Daily Limit | ✅ Unlimited | ❌ 500/day |
| Rate Limit | ✅ None | ❌ 5/min |
| Data Delay | ✅ Real-time | ⚠️ 15 min (free) |
| Symbol Mapping | ✅ Direct | ❌ Needs ETFs |
| Historical Data | ✅ 10+ years | ✅ 20+ years |

---

## Troubleshooting

### No data returned?
- Check your token is correctly set in `.env`
- Verify the symbol code is correct (use iTick codes from table above)
- Check internet connection

### Error messages?
- HTTP 401: Invalid API token
- HTTP 429: Rate limited (unlikely on free tier)
- Empty response: Symbol not found or market closed

---

## Next Steps

1. **Get your token** from https://api.itick.org/
2. **Add to .env** file
3. **Restart backend**: The system will auto-detect and use iTick
4. **Test in web app**: Try analyzing SPX or NAS100

Your AI Hedge Fund will now have **superior index data** with no rate limits! 🎉
