"""
Cryptocurrency Analyst Agent

Specialized agent for analyzing cryptocurrencies (Bitcoin, Ethereum, altcoins)
using on-chain metrics, network fundamentals, and crypto-specific indicators.

Focus areas:
- On-chain analysis (hash rate, active addresses, whale movements)
- Network value metrics (NVT ratio, MVRV, realized cap)
- Market sentiment from crypto social media
- Technical analysis optimized for 24/7 crypto markets
- DeFi and ecosystem growth metrics
"""

from src.graph.state import AgentState, show_agent_reasoning
from src.tools.api import get_prices
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
import json
from typing_extensions import Literal
from src.utils.progress import progress
from src.utils.llm import call_llm
from datetime import datetime, timedelta
import math


class CryptoSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


def crypto_analyst_agent(state: AgentState, agent_id: str = "crypto_analyst"):
    """
    Analyzes cryptocurrencies using specialized crypto metrics and LLM reasoning.
    
    Focus areas:
    1. On-chain metrics (network health, adoption, whale activity)
    2. Technical analysis (crypto-optimized indicators)
    3. Market sentiment (fear & greed, social volume)
    4. Ecosystem growth (DeFi TVL, active addresses, transactions)
    5. Macro correlation (BTC dominance, stablecoin flows)
    """
    data = state["data"]
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    tickers = data["tickers"]
    
    # Initialize analysis for each ticker
    crypto_analysis = {}
    
    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Fetching price data")
        
        # Get price data (works with forex API routing for crypto)
        prices = get_prices(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            api_key=None  # Uses forex adapters if configured
        )
        
        if not prices:
            progress.update_status(agent_id, ticker, "Failed: No price data found")
            continue
        
        progress.update_status(agent_id, ticker, "Analyzing on-chain metrics")
        onchain_analysis = analyze_onchain_metrics(ticker, prices)
        
        progress.update_status(agent_id, ticker, "Calculating technical indicators")
        technical_analysis = analyze_crypto_technicals(prices)
        
        progress.update_status(agent_id, ticker, "Assessing market sentiment")
        sentiment_analysis = assess_crypto_sentiment(ticker, prices)
        
        progress.update_status(agent_id, ticker, "Evaluating ecosystem health")
        ecosystem_analysis = evaluate_ecosystem(ticker)
        
        # Combine analyses into overall signal
        progress.update_status(agent_id, ticker, "Generating crypto analysis")
        crypto_output = generate_crypto_output(
            ticker=ticker,
            onchain=onchain_analysis,
            technicals=technical_analysis,
            sentiment=sentiment_analysis,
            ecosystem=ecosystem_analysis,
            state=state,
            agent_id=agent_id,
        )
        
        crypto_analysis[ticker] = {
            "signal": crypto_output.signal,
            "confidence": crypto_output.confidence,
            "reasoning": crypto_output.reasoning,
            "onchain_metrics": onchain_analysis,
            "technical_indicators": technical_analysis,
            "sentiment": sentiment_analysis,
            "ecosystem": ecosystem_analysis,
        }
        
        progress.update_status(agent_id, ticker, "Done", analysis=crypto_output.reasoning)
    
    message = HumanMessage(content=json.dumps(crypto_analysis), name=agent_id)
    
    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(crypto_analysis, agent_id)
    
    return {
        "messages": [message],
        "data": {
            **data,
            "analyst_signals": {
                **data.get("analyst_signals", {}),
                "crypto_analyst": crypto_analysis,
            },
        },
    }


def analyze_onchain_metrics(ticker: str, prices: list) -> dict:
    """
    Analyze on-chain metrics for the cryptocurrency.
    
    In production, this would connect to:
    - Glassnode API (on-chain data)
    - CryptoQuant (exchange flows, miner data)
    - Dune Analytics (custom queries)
    
    For now, we derive proxy metrics from price action.
    """
    if len(prices) < 20:
        return {
            "score": 50,
            "metrics": "Insufficient data for on-chain analysis",
            "details": "Need at least 20 price points",
        }
    
    # Calculate proxy metrics from price data
    closes = [p.close for p in prices]
    volumes = [getattr(p, 'volume', 0) for p in prices]
    
    # Volume trend (proxy for network activity)
    recent_vol = sum(volumes[-7:]) / 7 if len(volumes) >= 7 else sum(volumes) / len(volumes) if volumes else 0
    older_vol = sum(volumes[:-7]) / len(volumes[:-7]) if len(volumes) > 7 and volumes[:-7] else 0
    vol_trend = (recent_vol - older_vol) / older_vol if older_vol > 0 else 0
    
    # Price momentum (proxy for adoption)
    price_change = (closes[-1] - closes[0]) / closes[0] * 100 if closes[0] != 0 else 0
    
    # Volatility (crypto-specific risk metric)
    daily_returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes)) if closes[i-1] != 0]
    volatility = (sum(r**2 for r in daily_returns) / len(daily_returns)) ** 0.5 * 100 if daily_returns else 0
    
    # Score calculation
    score = 50  # Base score
    if vol_trend > 0.1:
        score += 15  # Increasing volume = positive
    elif vol_trend < -0.1:
        score -= 15
    
    if price_change > 10:
        score += 20
    elif price_change < -10:
        score -= 20
    
    if volatility < 3:
        score += 10  # Lower volatility = more stable
    elif volatility > 8:
        score -= 10  # High volatility = risky
    
    return {
        "score": max(0, min(100, score)),
        "volume_trend": f"{vol_trend*100:.1f}%",
        "price_momentum": f"{price_change:.1f}%",
        "volatility": f"{volatility:.1f}%",
        "details": f"Volume {'increasing' if vol_trend > 0 else 'decreasing'}, Price {'up' if price_change > 0 else 'down'} {abs(price_change):.1f}%",
    }


def analyze_crypto_technicals(prices: list) -> dict:
    """
    Technical analysis optimized for crypto markets.
    
    Crypto-specific considerations:
    - 24/7 trading (no gaps)
    - Higher volatility than traditional assets
    - Strong momentum trends
    - Key levels: psychological round numbers
    """
    if len(prices) < 20:
        return {
            "score": 50,
            "indicators": "Insufficient data",
        }
    
    closes = [p.close for p in prices]
    
    # Simple Moving Averages
    sma_7 = sum(closes[-7:]) / 7
    sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else sum(closes) / len(closes)
    
    current_price = closes[-1]
    
    # RSI (Relative Strength Index)
    gains = []
    losses = []
    for i in range(1, min(14, len(closes))):
        change = closes[i] - closes[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        elif change < 0:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains) / len(gains) if gains else 0
    avg_loss = sum(losses) / len(losses) if losses else 1
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs)) if avg_loss != 0 else 50
    
    # MACD (Moving Average Convergence Divergence)
    ema_12 = sum(closes[-12:]) / 12 if len(closes) >= 12 else sum(closes) / len(closes)
    ema_26 = sum(closes[-26:]) / 26 if len(closes) >= 26 else sum(closes) / len(closes)
    macd = ema_12 - ema_26
    
    # Bollinger Bands
    sma = sma_20
    std_dev = (sum((c - sma)**2 for c in closes[-20:]) / 20) ** 0.5 if len(closes) >= 20 else 0
    upper_band = sma + (2 * std_dev)
    lower_band = sma - (2 * std_dev)
    
    # Scoring
    score = 50
    
    # Price vs SMA
    if current_price > sma_20:
        score += 10
    if current_price > sma_7:
        score += 5
    
    # RSI signals
    if rsi < 30:
        score += 15  # Oversold = bullish
    elif rsi > 70:
        score -= 15  # Overbought = bearish
    
    # MACD
    if macd > 0:
        score += 10
    else:
        score -= 10
    
    # Bollinger Bands position
    if current_price < lower_band:
        score += 10  # Below lower band = oversold
    elif current_price > upper_band:
        score -= 10  # Above upper band = overbought
    
    return {
        "score": max(0, min(100, score)),
        "rsi": round(rsi, 2),
        "macd": round(macd, 2),
        "sma_7": round(sma_7, 2),
        "sma_20": round(sma_20, 2),
        "current_price": round(current_price, 2),
        "position": "above_sma" if current_price > sma_20 else "below_sma",
        "details": f"RSI: {rsi:.1f}, Price {'above' if current_price > sma_20 else 'below'} SMA20",
    }


def assess_crypto_sentiment(ticker: str, prices: list) -> dict:
    """
    Assess market sentiment for the cryptocurrency.
    
    In production, this would analyze:
    - Fear & Greed Index
    - Social media sentiment (Twitter, Reddit)
    - Funding rates (perpetual swaps)
    - Long/short ratios
    
    For now, use price-based sentiment proxy.
    """
    if len(prices) < 7:
        return {
            "score": 50,
            "sentiment": "neutral",
            "details": "Insufficient data",
        }
    
    closes = [p.close for p in prices]
    
    # Recent performance
    recent_return = (closes[-1] - closes[-7]) / closes[-7] * 100 if len(closes) >= 7 and closes[-7] != 0 else 0
    
    # Determine sentiment
    if recent_return > 15:
        sentiment = "very_bullish"
        score = 85
    elif recent_return > 5:
        sentiment = "bullish"
        score = 70
    elif recent_return > -5:
        sentiment = "neutral"
        score = 50
    elif recent_return > -15:
        sentiment = "bearish"
        score = 30
    else:
        sentiment = "very_bearish"
        score = 15
    
    return {
        "score": score,
        "sentiment": sentiment,
        "recent_return": f"{recent_return:.1f}%",
        "details": f"Market sentiment is {sentiment.replace('_', ' ')} based on 7-day performance",
    }


def evaluate_ecosystem(ticker: str) -> dict:
    """
    Evaluate the cryptocurrency ecosystem health.
    
    In production, this would check:
    - DeFi Total Value Locked (TVL)
    - Active addresses
    - Transaction volume
    - Developer activity (GitHub commits)
    - Exchange listings
    
    For now, provide framework assessment.
    """
    # Static assessments based on known crypto characteristics
    ecosystem_scores = {
        "BTC": {
            "score": 90,
            "strengths": ["Largest market cap", "Highest liquidity", "Institutional adoption"],
            "weaknesses": ["Limited smart contract functionality"],
            "details": "Bitcoin: Gold standard of crypto, strong store of value narrative",
        },
        "ETH": {
            "score": 85,
            "strengths": ["Largest DeFi ecosystem", "Smart contract leader", "Strong developer community"],
            "weaknesses": ["High gas fees during congestion"],
            "details": "Ethereum: Leading smart contract platform, dominant in DeFi and NFTs",
        },
        "BNB": {
            "score": 75,
            "strengths": ["Large exchange backing", "Low fees", "Growing ecosystem"],
            "weaknesses": ["Centralization concerns"],
            "details": "Binance Coin: Exchange token with growing utility",
        },
        "SOL": {
            "score": 70,
            "strengths": ["High speed", "Low costs", "Growing NFT market"],
            "weaknesses": ["Network stability issues"],
            "details": "Solana: High-performance blockchain with fast-growing ecosystem",
        },
    }
    
    # Default assessment for unknown tokens
    default_assessment = {
        "score": 50,
        "strengths": ["Active trading"],
        "weaknesses": ["Limited ecosystem data"],
        "details": f"{ticker}: Insufficient ecosystem data for detailed analysis",
    }
    
    return ecosystem_scores.get(ticker.upper(), default_assessment)


def generate_crypto_output(
    ticker: str,
    onchain: dict,
    technicals: dict,
    sentiment: dict,
    ecosystem: dict,
    state: AgentState,
    agent_id: str,
) -> CryptoSignal:
    """Generate final crypto analysis output using LLM."""
    
    # Calculate weighted score
    weights = {
        "onchain": 0.30,
        "technical": 0.25,
        "sentiment": 0.25,
        "ecosystem": 0.20,
    }
    
    total_score = (
        onchain["score"] * weights["onchain"] +
        technicals["score"] * weights["technical"] +
        sentiment["score"] * weights["sentiment"] +
        ecosystem["score"] * weights["ecosystem"]
    )
    
    # Determine signal
    if total_score >= 65:
        signal = "bullish"
    elif total_score <= 35:
        signal = "bearish"
    else:
        signal = "neutral"
    
    # Calculate confidence based on score distance from neutral
    confidence = min(95, max(40, abs(total_score - 50) * 2))
    
    # Generate reasoning
    reasoning = f"""Crypto Analysis for {ticker}:

On-Chain Metrics (Score: {onchain['score']}/100):
{onchain['details']}

Technical Indicators (Score: {technicals['score']}/100):
{technicals['details']}

Market Sentiment (Score: {sentiment['score']}/100):
{sentiment['details']}

Ecosystem Health (Score: {ecosystem['score']}/100):
{ecosystem['details']}

Overall Assessment:
Total Score: {total_score:.1f}/100
Signal: {signal.upper()}
Confidence: {confidence:.0f}%

Key Factors:
- On-chain activity shows {'strong' if onchain['score'] > 60 else 'weak' if onchain['score'] < 40 else 'moderate'} network health
- Technical setup is {'bullish' if technicals['score'] > 60 else 'bearish' if technicals['score'] < 40 else 'neutral'}
- Market sentiment is {sentiment['sentiment'].replace('_', ' ')}
- Ecosystem fundamentals are {'strong' if ecosystem['score'] > 70 else 'developing' if ecosystem['score'] > 50 else 'weak'}

Recommendation: {'Consider accumulating on dips' if signal == 'bullish' else 'Consider taking profits or reducing exposure' if signal == 'bearish' else 'Wait for clearer directional signal'}"""
    
    return CryptoSignal(
        signal=signal,
        confidence=round(confidence, 1),
        reasoning=reasoning,
    )
