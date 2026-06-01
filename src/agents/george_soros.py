import json
import math

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing_extensions import Literal

from src.graph.state import AgentState, show_agent_reasoning
from src.tools.api import get_prices, prices_to_df
from src.utils.api_key import get_api_key_from_state
from src.utils.llm import call_llm
from src.utils.progress import progress


class GeorgeSorosSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


def george_soros_agent(state: AgentState, agent_id: str = "george_soros_agent"):
    """
    Analyze currency pairs and gold through a Soros-style global macro lens:
    reflexive trends, policy/peg pressure proxies, leverage-worthy momentum,
    and disciplined downside control.
    """
    data = state["data"]
    start_date = data["start_date"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")

    soros_analysis = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Fetching macro price data")
        prices = get_prices(ticker=ticker, start_date=start_date, end_date=end_date, api_key=api_key)

        if not prices:
            progress.update_status(agent_id, ticker, "Failed: No price data found")
            continue

        prices_df = prices_to_df(prices)

        progress.update_status(agent_id, ticker, "Analyzing reflexive trend")
        reflexivity = analyze_reflexive_trend(prices_df)

        progress.update_status(agent_id, ticker, "Analyzing volatility pressure")
        volatility_pressure = analyze_volatility_pressure(prices_df)

        progress.update_status(agent_id, ticker, "Analyzing asymmetric risk")
        risk_reward = analyze_asymmetric_risk(prices_df)

        asset_type = classify_macro_asset(ticker)
        if asset_type == "gold":
            progress.update_status(agent_id, ticker, "Analyzing gold hedge demand")
            macro_specialist = analyze_gold_hedge_setup(prices_df)
        else:
            progress.update_status(agent_id, ticker, "Analyzing currency pair pressure")
            macro_specialist = analyze_currency_pair_setup(prices_df)

        total_score = reflexivity["score"] * 0.35 + volatility_pressure["score"] * 0.25 + macro_specialist["score"] * 0.25 + risk_reward["score"] * 0.15

        if total_score >= 6.8:
            signal = "bullish"
        elif total_score <= 3.2:
            signal = "bearish"
        else:
            signal = "neutral"

        confidence = round(min(95, max(10, abs(total_score - 5) * 20 + 35)), 2)
        analysis_data = {
            "asset_type": asset_type,
            "signal": signal,
            "confidence": confidence,
            "score": total_score,
            "max_score": 10,
            "reflexive_trend": reflexivity,
            "volatility_pressure": volatility_pressure,
            "macro_specialist": macro_specialist,
            "asymmetric_risk": risk_reward,
        }

        progress.update_status(agent_id, ticker, "Generating Soros macro analysis")
        soros_output = generate_soros_output(
            ticker=ticker,
            analysis_data=analysis_data,
            state=state,
            agent_id=agent_id,
        )

        soros_analysis[ticker] = {
            "signal": soros_output.signal,
            "confidence": soros_output.confidence,
            "reasoning": soros_output.reasoning,
        }

        progress.update_status(agent_id, ticker, "Done", analysis=soros_output.reasoning)

    message = HumanMessage(content=json.dumps(soros_analysis), name=agent_id)

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(soros_analysis, "George Soros Agent")

    state["data"]["analyst_signals"][agent_id] = soros_analysis
    progress.update_status(agent_id, None, "Done")

    return {"messages": [message], "data": state["data"]}


def classify_macro_asset(ticker: str) -> str:
    normalized = ticker.upper().replace("/", "").replace("_", "").replace("-", "")
    if normalized.startswith("XAU") or normalized in {"GLD", "IAU", "GOLD", "GDX", "NEM", "ABX"}:
        return "gold"
    if len(normalized) == 6 and normalized.isalpha():
        return "currency_pair"
    return "macro_asset"


def analyze_reflexive_trend(prices_df) -> dict:
    if len(prices_df) < 20:
        return {"score": 5, "details": "Insufficient price history; neutral reflexivity score."}

    close = prices_df["close"].dropna()
    if len(close) < 20:
        return {"score": 5, "details": "Insufficient closing prices; neutral reflexivity score."}

    latest = close.iloc[-1]
    returns_20d = _pct_change(close, 20)
    returns_60d = _pct_change(close, min(60, len(close) - 1))
    ma_20 = close.rolling(20).mean().iloc[-1]
    ma_60 = close.rolling(min(60, len(close))).mean().iloc[-1]

    score = 5
    details = []

    if latest > ma_20 > ma_60:
        score += 2.5
        details.append("price is above rising short and medium moving averages")
    elif latest < ma_20 < ma_60:
        score -= 2.5
        details.append("price is below falling short and medium moving averages")
    else:
        details.append("trend structure is mixed")

    if returns_20d > returns_60d > 0:
        score += 1.5
        details.append("upside momentum is accelerating")
    elif returns_20d < returns_60d < 0:
        score -= 1.5
        details.append("downside momentum is accelerating")

    return {
        "score": round(_clamp(score), 2),
        "details": "; ".join(details),
        "return_20d": round(returns_20d, 4),
        "return_60d": round(returns_60d, 4),
        "price_vs_20d_ma": round((latest / ma_20 - 1) if ma_20 else 0, 4),
        "price_vs_60d_ma": round((latest / ma_60 - 1) if ma_60 else 0, 4),
    }


def analyze_volatility_pressure(prices_df) -> dict:
    close = prices_df["close"].dropna()
    if len(close) < 30:
        return {"score": 5, "details": "Insufficient price history; neutral volatility pressure."}

    returns = close.pct_change().dropna()
    recent_vol = returns.tail(20).std() * math.sqrt(252)
    baseline_window = min(120, len(returns))
    baseline_vol = returns.tail(baseline_window).std() * math.sqrt(252)
    vol_ratio = recent_vol / baseline_vol if baseline_vol else 1
    recent_return = _pct_change(close, 20)

    score = 5
    if vol_ratio >= 1.4 and recent_return > 0:
        score += 2.5
        details = "volatility expansion confirms upside pressure"
    elif vol_ratio >= 1.4 and recent_return < 0:
        score -= 2.5
        details = "volatility expansion confirms downside pressure"
    elif vol_ratio >= 1.1:
        score += 0.5 if recent_return > 0 else -0.5
        details = "volatility is moderately elevated"
    else:
        details = "volatility pressure is contained"

    return {
        "score": round(_clamp(score), 2),
        "details": details,
        "recent_volatility": round(recent_vol, 4),
        "baseline_volatility": round(baseline_vol, 4),
        "volatility_ratio": round(vol_ratio, 2),
    }


def analyze_currency_pair_setup(prices_df) -> dict:
    close = prices_df["close"].dropna()
    if len(close) < 60:
        return {"score": 5, "details": "Insufficient FX history; neutral currency pair pressure."}

    latest = close.iloc[-1]
    high_60 = close.tail(60).max()
    low_60 = close.tail(60).min()
    range_position = (latest - low_60) / (high_60 - low_60) if high_60 > low_60 else 0.5
    return_60d = _pct_change(close, 60)

    score = 5
    if range_position >= 0.85 and return_60d > 0:
        score += 3
        details = "pair is pressing against 60-day highs, suggesting a reflexive long base/short quote setup"
    elif range_position <= 0.15 and return_60d < 0:
        score -= 3
        details = "pair is pressing against 60-day lows, suggesting a reflexive short base/long quote setup"
    else:
        details = "currency pressure is not yet decisive"

    return {
        "score": round(_clamp(score), 2),
        "details": details,
        "range_position_60d": round(range_position, 2),
        "return_60d": round(return_60d, 4),
    }


def analyze_gold_hedge_setup(prices_df) -> dict:
    close = prices_df["close"].dropna()
    if len(close) < 60:
        return {"score": 5, "details": "Insufficient gold history; neutral hedge setup."}

    latest = close.iloc[-1]
    high_90 = close.tail(min(90, len(close))).max()
    ma_50 = close.rolling(min(50, len(close))).mean().iloc[-1]
    return_60d = _pct_change(close, 60)

    score = 5
    details = []
    if latest >= high_90 * 0.98:
        score += 2
        details.append("gold is near a multi-month high")
    if latest > ma_50 and return_60d > 0:
        score += 2
        details.append("gold has positive hedge momentum")
    if return_60d < -0.08:
        score -= 2
        details.append("gold hedge demand is fading")

    if not details:
        details.append("gold hedge signal is mixed")

    return {
        "score": round(_clamp(score), 2),
        "details": "; ".join(details),
        "return_60d": round(return_60d, 4),
        "price_vs_50d_ma": round((latest / ma_50 - 1) if ma_50 else 0, 4),
    }


def analyze_asymmetric_risk(prices_df) -> dict:
    close = prices_df["close"].dropna()
    if len(close) < 30:
        return {"score": 5, "details": "Insufficient price history; neutral risk score."}

    rolling_high = close.cummax()
    drawdown = (close / rolling_high - 1).min()
    recent_drawdown = close.iloc[-1] / close.tail(min(60, len(close))).max() - 1
    recent_return = _pct_change(close, min(60, len(close) - 1))

    score = 5
    if recent_return > abs(recent_drawdown):
        score += 2
        details = "upside momentum is larger than recent drawdown risk"
    elif abs(recent_drawdown) > max(0.05, abs(recent_return) * 1.5):
        score -= 2
        details = "drawdown risk overwhelms recent upside"
    else:
        details = "risk/reward is balanced"

    return {
        "score": round(_clamp(score), 2),
        "details": details,
        "max_drawdown": round(drawdown, 4),
        "recent_drawdown": round(recent_drawdown, 4),
        "recent_return": round(recent_return, 4),
    }


def generate_soros_output(
    ticker: str,
    analysis_data: dict,
    state: AgentState,
    agent_id: str,
) -> GeorgeSorosSignal:
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a George Soros AI agent, making investment decisions using global macro principles:

                1. Exploit macro imbalances in currencies and gold.
                2. Use reflexivity: market perception can reinforce price moves and pressure policymakers.
                3. For currency pairs, interpret bullish as long the base currency and short the quote currency; bearish is short the base and long the quote.
                4. For gold, treat bullish as long gold/a stronger hedge position and bearish as reducing gold exposure.
                5. Prefer asymmetric opportunities where the upside if right exceeds the loss if wrong.
                6. Cut losses quickly when the thesis stops working; risk management comes first.

                When explaining your reasoning, use Soros's global macro voice:
                - Mention reflexive momentum or policy pressure when relevant.
                - For FX, discuss whether the pair looks like a long-base/short-quote or short-base/long-quote setup.
                - For gold, discuss hedge demand against systemic risk, inflation, or uncertainty.
                - Be decisive but acknowledge when evidence is mixed.

                Return your final output strictly in JSON with the fields:
                {{
                  "signal": "bullish" | "bearish" | "neutral",
                  "confidence": 0 to 100,
                  "reasoning": "string"
                }}
                """,
            ),
            (
                "human",
                """Based on the following analysis data for {ticker}, produce your George Soros-style macro signal.

                Analysis Data:
                {analysis_data}

                Return only valid JSON with "signal", "confidence", and "reasoning".
                """,
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    def create_default_signal():
        return GeorgeSorosSignal(
            signal=analysis_data["signal"],
            confidence=analysis_data["confidence"],
            reasoning=(
                f"{ticker} screens {analysis_data['signal']} under a Soros-style macro framework. " f"Reflexive trend score is {analysis_data['reflexive_trend']['score']}/10, " f"volatility pressure score is {analysis_data['volatility_pressure']['score']}/10, " f"specialist macro score is {analysis_data['macro_specialist']['score']}/10, " f"and asymmetric risk score is {analysis_data['asymmetric_risk']['score']}/10."
            ),
        )

    return call_llm(
        prompt=prompt,
        pydantic_model=GeorgeSorosSignal,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_signal,
    )


def _pct_change(series, periods: int) -> float:
    if len(series) <= periods or series.iloc[-periods - 1] == 0:
        return 0.0
    return float(series.iloc[-1] / series.iloc[-periods - 1] - 1)


def _clamp(value: float, lower: float = 0, upper: float = 10) -> float:
    return max(lower, min(upper, value))
