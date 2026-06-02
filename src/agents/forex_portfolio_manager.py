"""
Portfolio Manager for FX, Indices, and Commodities Trading
Works with 5-min timeframe data
Generates entry, TP, and SL signals instead of share-based trading
"""
import json
from langchain_core.messages import HumanMessage

from src.graph.state import AgentState, show_agent_reasoning
from pydantic import BaseModel, Field
from src.utils.progress import progress


class TradeSignal(BaseModel):
    direction: str = Field(description="Trade direction: 'long', 'short', or 'wait'")
    entry_price: float = Field(description="Recommended entry price")
    stop_loss: float = Field(description="Stop loss price")
    take_profit: float = Field(description="Take profit price")
    confidence: int = Field(description="Confidence 0-100")
    risk_reward_ratio: float = Field(description="Risk/reward ratio (TP-Entry)/(Entry-SL)")
    reasoning: str = Field(description="Brief reasoning for the signal (max 150 chars)")
    position_size_pct: float = Field(description="Recommended position size as % of account (0.5-5.0%)")


class ForexPortfolioOutput(BaseModel):
    signals: dict[str, TradeSignal] = Field(description="Dictionary of ticker to trade signals")


def forex_portfolio_manager(state: AgentState, agent_id: str = "forex_portfolio_manager"):
    """
    Portfolio manager for FX, indices, and commodities.
    Generates entry/TP/SL signals based on 5-min timeframe analysis.
    """
    data = state["data"]
    analyst_signals = data.get("analyst_signals", {})
    tickers = data.get("tickers", [])
    portfolio = data.get("portfolio", {})

    equity = float(portfolio.get("equity", 100000))
    current_prices = data.get("current_prices", {})

    ticker_analysis = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Collecting analyst signals")

        # Gather signals from all analysts for this ticker
        ticker_signals = {}
        for agent_name, signals in analyst_signals.items():
            if agent_name.startswith("risk_management_agent"):
                continue
            if ticker in signals:
                sig_data = signals[ticker]
                ticker_signals[agent_name] = {
                    "signal": sig_data.get("signal", "neutral"),
                    "confidence": sig_data.get("confidence", 50),
                }
        
        # DEBUG: Log what signals we found
        if ticker_signals:
            print(f"[FX PM] {ticker}: Found {len(ticker_signals)} analyst signals: {list(ticker_signals.keys())}")
        else:
            print(f"[FX PM] {ticker}: WARNING - No analyst signals found!")

        ticker_analysis[ticker] = {
            "signals": ticker_signals,
            "current_price": current_prices.get(ticker, 0),
        }

    progress.update_status(agent_id, None, "Generating trade signals")

    # Get current price - try multiple sources
    for ticker in tickers:
        if ticker_analysis[ticker]["current_price"] == 0:
            # Try to get from risk manager data
            risk_data = analyst_signals.get("risk_management_agent", {}).get(ticker, {})
            price = risk_data.get("current_price", 0)
            ticker_analysis[ticker]["current_price"] = price
        
        # If still 0, fetch it directly from Massive/Dukascopy
        if ticker_analysis[ticker]["current_price"] == 0:
            from src.tools.api import get_prices as fetch_prices
            from datetime import datetime, timedelta
            try:
                end_date = datetime.now().strftime("%Y-%m-%d")
                start_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
                recent_prices = fetch_prices(ticker, start_date, end_date, interval="5min")
                if recent_prices:
                    ticker_analysis[ticker]["current_price"] = recent_prices[-1].close
            except Exception as e:
                pass

    result = generate_trade_signals(
        tickers=tickers,
        ticker_analysis=ticker_analysis,
        equity=equity,
        agent_id=agent_id,
        state=state,
    )

    message = HumanMessage(
        content=json.dumps({ticker: signal.model_dump() for ticker, signal in result.signals.items()}),
        name=agent_id,
    )

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(
            {ticker: signal.model_dump() for ticker, signal in result.signals.items()},
            "FX Portfolio Manager",
        )

    progress.update_status(agent_id, None, "Done")

    return {
        "messages": state["messages"] + [message],
        "data": data,
    }


def generate_trade_signals(
    tickers: list[str],
    ticker_analysis: dict[str, dict],
    equity: float,
    agent_id: str,
    state: AgentState,
) -> ForexPortfolioOutput:
    """Generate entry/TP/SL signals using LLM analysis."""

    # Build compact signal summary
    signal_summary = {}
    for ticker in tickers:
        analysis = ticker_analysis.get(ticker, {})
        price = analysis.get("current_price", 0)
        
        # If no price, skip this ticker
        if price == 0:
            continue
            
        analysts = analysis.get("signals", {})
        
        # Calculate consensus
        bullish_count = sum(1 for a in analysts.values() if a.get("signal") == "bullish")
        bearish_count = sum(1 for a in analysts.values() if a.get("signal") == "bearish")
        total = len(analysts)
        
        if total == 0:
            consensus = "neutral"
            avg_confidence = 50
        else:
            if bullish_count > bearish_count:
                consensus = "bullish"
                avg_confidence = int(sum(a.get("confidence", 50) for a in analysts.values()) / total)
            elif bearish_count > bullish_count:
                consensus = "bearish"
                avg_confidence = int(sum(a.get("confidence", 50) for a in analysts.values()) / total)
            else:
                consensus = "neutral"
                avg_confidence = 50
        
        signal_summary[ticker] = {
            "price": price,
            "consensus": consensus,
            "avg_confidence": avg_confidence,
            "analysts": analysts,
        }

    # Generate deterministic signals based on analyst consensus
    # This ensures we ALWAYS generate signals, even if LLM fails
    signals = {}
    for ticker, data in signal_summary.items():
        price = data["price"]
        consensus = data["consensus"]
        confidence = data["avg_confidence"]
        
        # Determine SL/TP based on asset volatility
        # High volatility assets (crypto, gold) need wider stops
        ticker_upper = ticker.upper()
        if any(x in ticker_upper for x in ['BTC', 'ETH', 'XAU', 'GOLD', 'XAG', 'SILVER']):
            # High volatility: 1.0% SL, 2.0% TP (1:2 risk/reward)
            sl_pct = 0.010  # 1.0%
            tp_pct = 0.020  # 2.0%
            asset_type = "high_vol"
        elif any(x in ticker_upper for x in ['US30', 'SPX', 'NAS', 'DJI', 'NDX', 'DOW']):
            # Medium volatility (indices): 0.5% SL, 1.0% TP
            sl_pct = 0.005  # 0.5%
            tp_pct = 0.010  # 1.0%
            asset_type = "medium_vol"
        else:
            # Low volatility (forex pairs): 0.15% SL, 0.30% TP
            sl_pct = 0.0015  # 0.15%
            tp_pct = 0.0030  # 0.30%
            asset_type = "low_vol"
        
        # Determine direction based on consensus and confidence
        if consensus == "bullish" and confidence >= 70:
            direction = "long"
            # Set SL below entry, TP above (1:2 risk/reward)
            stop_loss = price * (1 - sl_pct)
            take_profit = price * (1 + tp_pct)
            risk_reward = 2.0
            reasoning = f"Strong bullish consensus ({confidence}% avg confidence, {asset_type})"
            position_size = min(3.0, max(0.5, confidence / 30))
        elif consensus == "bearish" and confidence >= 70:
            direction = "short"
            # Set SL above entry, TP below (1:2 risk/reward)
            stop_loss = price * (1 + sl_pct)
            take_profit = price * (1 - tp_pct)
            risk_reward = 2.0
            reasoning = f"Strong bearish consensus ({confidence}% avg confidence, {asset_type})"
            position_size = min(3.0, max(0.5, confidence / 30))
        else:
            direction = "wait"
            stop_loss = 0
            take_profit = 0
            risk_reward = 0
            reasoning = f"Mixed signals or low confidence ({confidence}%)"
            position_size = 0
        
        signals[ticker] = TradeSignal(
            direction=direction,
            entry_price=round(price, 5),
            stop_loss=round(stop_loss, 5),
            take_profit=round(take_profit, 5),
            confidence=confidence,
            risk_reward_ratio=risk_reward,
            reasoning=reasoning,
            position_size_pct=round(position_size, 1),
        )
        
        print(f"[FX PM] {ticker}: {direction.upper()} @ {price:.5f}, SL={stop_loss:.5f}, TP={take_profit:.5f}, Conf={confidence}%")
    
    print(f"[FX PM] Generated {len(signals)} trade signals total")
    return ForexPortfolioOutput(signals=signals)
