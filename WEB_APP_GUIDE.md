# 🎯 How to Use AI Hedge Fund for Forex, Gold & Indices

## ✅ What's Working RIGHT NOW

### **Gold (XAUUSD)** - FULLY OPERATIONAL
- Real-time price data from TwelveData
- Current price: **$4,496.37**
- 7-day range: $4,367 - $4,581

### **Forex Pairs** - FULLY OPERATIONAL  
- EURUSD: $1.1650
- GBPUSD: $1.34
- And 5+ more major pairs

### **Stocks** - WORKING (if you have financialdatasets.ai API key)

---

## 📖 Step-by-Step Web App Guide

### **1. Open the Web Application**

The web app is already running at: **http://localhost:5173**

Click the preview button or open in your browser.

---

### **2. Understanding the Interface**

This is a **visual node-based workflow editor** (like Blender or Unreal Engine nodes).

**Left Panel**: Your saved flows  
**Center**: Canvas where you build workflows  
**Right Panel**: Available components (nodes)

---

### **3. Create Your First Analysis**

#### **Step 1: Start a New Flow**
- Click the **+** button in the "Flows" panel (left sidebar)
- Or click on your existing "xauusd" flow to edit it

#### **Step 2: Add Portfolio Input Node**
1. From the **Components** panel (right side)
2. Expand **"Start Nodes"**
3. **Drag** "Portfolio Input" onto the canvas
4. **Click** the node to configure:
   ```
   Available Cash: $1000 (or your amount)
   
   Positions:
   - Ticker: xauusd
   - Shares: 1 (or number of units)
   - Price: Leave blank or enter current price
   ```

#### **Step 3: Add Analyst Nodes**
From the **"Analysts"** section in Components panel:

**Popular choices for forex/commodities:**
- **Technical Analyst** - Best for forex trading signals
- **Warren Buffett** - Value investing approach
- **Risk Manager** - Position sizing & risk assessment

**Drag them onto the canvas**

#### **Step 4: Connect the Nodes**
1. **Click** the output dot (right side) of Portfolio Input
2. **Drag** to the input dot (left side) of an analyst node
3. You'll see a connection line appear
4. **Repeat** to chain multiple analysts:
   ```
   [Portfolio Input] → [Technical Analyst] → [Risk Manager]
   ```

#### **Step 5: Run the Analysis**
1. **Select** the run mode from dropdown (usually "Single Run")
2. **Click** the ▶ (play) button
3. **Watch** the status change: Idle → Running → Complete
4. **Click** "Output" on completed nodes to see results

---

### **4. Example Workflows**

#### **Example A: Gold Analysis**
```
[Portfolio Input]
  Cash: $5000
  Position: xauusd, 1 unit
  
  ↓
  
[Technical Analyst]
  - Analyzes price trends
  - Identifies support/resistance
  - Provides entry/exit signals
  
  ↓
  
[Risk Manager]
  - Calculates position size
  - Sets stop-loss levels
  - Risk/reward ratio
```

#### **Example B: Multi-Instrument Portfolio**
```
[Portfolio Input]
  Cash: $10,000
  Positions:
  - xauusd: 2 units
  - eurusd: 1000 units
  - gbpusd: 1000 units
  
  ↓
  
[Warren Buffett] → [Technical Analyst] → [Risk Manager]
```

---

### **5. Interpreting Results**

When you click **"Output"** on an analyst node, you'll see:

**Technical Analyst:**
- Current trend (bullish/bearish)
- Key price levels
- Entry/exit recommendations
- Technical indicators (RSI, MACD, etc.)

**Value Investors (Buffett, Graham, etc.):**
- Intrinsic value assessment
- Buy/hold/sell recommendation
- Risk factors
- Financial analysis

**Risk Manager:**
- Maximum position size
- Stop-loss suggestions
- Portfolio risk metrics
- Margin requirements

---

## 🎯 Quick Start Cheat Sheet

### **Test These Tickers (All Working):**

| Ticker | Name | Type | Current Price |
|--------|------|------|---------------|
| `xauusd` | Gold | Commodity | ~$4,496 |
| `eurusd` | EUR/USD | Forex | ~$1.165 |
| `gbpusd` | GBP/USD | Forex | ~$1.34 |
| `usdjpy` | USD/JPY | Forex | Varies |
| `xagusd` | Silver | Commodity | Varies |

### **Important Tips:**

1. ✅ **Always use lowercase** in the web app: `xauusd` not `XAUUSD`
2. ✅ **Set realistic cash amounts** based on the instrument price
3. ✅ **Start with one instrument** before building complex portfolios
4. ✅ **Use Technical Analyst** for forex - it's specifically designed for trading signals
5. ✅ **Chain Risk Manager last** - it needs input from other analysts

---

## ⚠️ Indices Status

**SPX, NAS100, US30** - Currently NOT working

**Reason**: Requires Alpha Vantage API key (free)

**To enable indices:**
1. Get free key: https://www.alphavantage.co/support/#api-key
2. Edit `.env` file: `ALPHAVANTAGE_API_KEY=your_key_here`
3. Restart backend server

---

## 🆘 Troubleshooting

### **Problem**: "No data returned" or "Failed to fetch"
**Solution**: 
- Check you're using lowercase: `xauusd` not `XAUUSD`
- Verify TwelveData API key is in `.env`
- Check backend is running (Terminal 4)

### **Problem**: Node won't connect
**Solution**:
- Make sure output (right dot) connects to input (left dot)
- Some nodes only accept specific connections
- Check node is properly configured first

### **Problem**: Analysis hangs or takes too long
**Solution**:
- Check OpenAI API key is valid
- Reduce number of analysts
- Check internet connection

### **Problem**: "Module not found" errors
**Solution**:
- Backend needs restart after code changes
- Kill port 8000 and restart with poetry

---

##  What You'll See

### **Sample Gold Analysis Output:**

```
Technical Analyst Report for XAUUSD:
─────────────────────────────────────
Current Price: $4,496.37
Trend: Bullish
Support: $4,367
Resistance: $4,581
RSI: 52 (Neutral)

Recommendation: BUY
Entry: $4,450-4,500
Stop Loss: $4,350
Take Profit: $4,650

Risk/Reward Ratio: 2.5:1
```

---

##  Ready to Start?

1. **Open web app**: http://localhost:5173
2. **Create new flow**: Click + button
3. **Add Portfolio Input**: Drag from Components
4. **Configure**: Enter `xauusd` and your cash amount
5. **Add analysts**: Drag Technical Analyst
6. **Connect**: Portfolio → Analyst
7. **Run**: Click ▶ play button
8. **View results**: Click Output on completed node

**That's it!** You're now analyzing gold and forex with AI! 🎉

---

## 📚 Additional Resources

- **Status Document**: See [MULTI_INSTRUMENT_STATUS.md](MULTI_INSTRUMENT_STATUS.md)
- **API Configuration**: Check [.env](.env) file for your keys
- **Original Project**: https://github.com/virattt/ai-hedge-fund

---

**Questions?** The system is designed to be self-explanatory once you see it working. Start with gold (XAUUSD) - it's the most popular and works perfectly!
