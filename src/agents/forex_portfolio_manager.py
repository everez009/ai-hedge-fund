"""
Portfolio Manager for FX, Indices, and Commodities Trading
Works with 5-min timeframe data
Generates entry, TP, and SL signals instead of share-based trading
"""
import json
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

from src.graph.state import AgentState, show_agent_reasoning
from pydantic import BaseModel, Field
from src.utils.progress import progress
from src.utils.llm import call_llm


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

        ticker_analysis[ticker] = {
            "signals": ticker_signals,
            "current_price": current_prices.get(ticker, 0),
        }

    progress.update_status(agent_id, None, "Generating trade signals")

    # Get current price or use fallback
    for ticker in tickers:
        if ticker_analysis[ticker]["current_price"] == 0:
            # Try to get from risk manager data
            risk_data = analyst_signals.get("risk_management_agent", {}).get(ticker, {})
            price = risk_data.get("current_price", 0)
            ticker_analysis[ticker]["current_price"] = price

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
        signal_summary[ticker] = {
            "price": analysis.get("current_price", 0),
            "analysts": analysis.get("signals", {}),
        }

    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert FX/indices/commodities trader specializing in 5-min timeframe scalping.\n"
                "Analyze the aggregated analyst signals and current price to generate precise entry, TP, and SL levels.\n"
                "For scalping on 5-min:\n"
                "- Stop loss should be 1.5-3x ATR or recent swing high/low\n"
                "- Take profit should give minimum 1:1.5 risk/reward ratio\n"
                "- Position size 0.5-3% of equity per trade\n"
                "- Only signal 'long' or 'short' if strong confluence (≥60% confidence)\n"
                "- Use 'wait' if signals are conflicting or weak\n"
                "Return JSON only with exact schema."
            ),
            (
                "human",
                "Current prices and analyst signals:\n{signals}\n\n"
                "Account equity: ${equity:,.0f}\n\n"
                "For each ticker, provide:\n"
                "- direction: 'long', 'short', or 'wait'\n"
                "- entry_price: current market price or limit entry\n"
                "- stop_loss: price level for stop loss\n"
                "- take_profit: price level for take profit\n"
                "- confidence: 0-100 based on analyst consensus\n"
                "- risk_reward_ratio: (TP-Entry)/(Entry-SL) for long, (Entry-TP)/(SL-Entry) for short\n"
                "- reasoning: concise reasoning (max 150 chars)\n"
                "- position_size_pct: 0.5-5.0% of equity\n\n"
                "Format:\n"
                "{{\n"
                '  "signals": {{\n'
                '    "TICKER": {{"direction":"long/short/wait","entry_price":float,"stop_loss":float,"take_profit":float,"confidence":int,"risk_reward_ratio":float,"reasoning":"...","position_size_pct":float}}\n'
                "  }}\n"
                "}}"
            ),
        ]
    )

    prompt_data = {
        "signals": json.dumps(signal_summary, indent=2, ensure_ascii=False),
        "equity": equity,
    }
    prompt = template.invoke(prompt_data)

    def create_default_output():
        signals = {}
        for ticker in tickers:
            price = ticker_analysis.get(ticker, {}).get("current_price", 0)
            signals[ticker] = TradeSignal(
                direction="wait",
                entry_price=price,
                stop_loss=0,
                take_profit=0,
                confidence=0,
                risk_reward_ratio=0,
                reasoning="No clear signal - insufficient data",
                position_size_pct=0,
            )
        return ForexPortfolioOutput(signals=signals)

    llm_out = call_llm(
        prompt=prompt,
        pydantic_model=ForexPortfolioOutput,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_output,
    )

    return llm_out
