import json
from datetime import datetime, timedelta

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel
from typing_extensions import Literal

from src.graph.state import AgentState, show_agent_reasoning
from src.tools.api import get_company_news, get_insider_trades
from src.utils.api_key import get_api_key_from_state
from src.utils.llm import call_llm
from src.utils.progress import progress


class NancyPelosiSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: float
    reasoning: str


def nancy_pelosi_agent(state: AgentState, agent_id: str = "nancy_pelosi_agent"):
    """Analyze stocks with a congressional-disclosure momentum lens."""
    data = state["data"]
    end_date = data["end_date"]
    tickers = data["tickers"]
    api_key = get_api_key_from_state(state, "FINANCIAL_DATASETS_API_KEY")

    pelosi_analysis = {}

    for ticker in tickers:
        progress.update_status(agent_id, ticker, "Fetching disclosure-style trading data")
        insider_trades = get_insider_trades(
            ticker=ticker,
            end_date=end_date,
            start_date=_one_year_before(end_date),
            limit=1000,
            api_key=api_key,
        )

        progress.update_status(agent_id, ticker, "Fetching policy-sensitive news")
        company_news = get_company_news(ticker, end_date, limit=50, api_key=api_key)

        progress.update_status(agent_id, ticker, "Analyzing disclosure momentum")
        disclosure_momentum = analyze_disclosure_momentum(insider_trades, end_date)

        progress.update_status(agent_id, ticker, "Analyzing conviction")
        conviction = analyze_trade_conviction(insider_trades)

        progress.update_status(agent_id, ticker, "Analyzing policy catalyst exposure")
        policy_catalysts = analyze_policy_catalysts(company_news)

        weighted_score = disclosure_momentum["score"] * 0.45 + conviction["score"] * 0.35 + policy_catalysts["score"] * 0.20

        if weighted_score >= 6.5:
            signal = "bullish"
        elif weighted_score <= 3.5:
            signal = "bearish"
        else:
            signal = "neutral"

        confidence = round(min(95, max(5, abs(weighted_score - 5) * 18 + 35)), 2)
        analysis_data = {
            "signal": signal,
            "confidence": confidence,
            "score": weighted_score,
            "max_score": 10,
            "disclosure_momentum": disclosure_momentum,
            "trade_conviction": conviction,
            "policy_catalysts": policy_catalysts,
        }

        progress.update_status(agent_id, ticker, "Generating Pelosi-style analysis")
        pelosi_output = generate_pelosi_output(
            ticker=ticker,
            analysis_data=analysis_data,
            state=state,
            agent_id=agent_id,
        )

        pelosi_analysis[ticker] = {
            "signal": pelosi_output.signal,
            "confidence": pelosi_output.confidence,
            "reasoning": pelosi_output.reasoning,
        }

        progress.update_status(agent_id, ticker, "Done", analysis=pelosi_output.reasoning)

    message = HumanMessage(content=json.dumps(pelosi_analysis), name=agent_id)

    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(pelosi_analysis, "Nancy Pelosi Agent")

    state["data"]["analyst_signals"][agent_id] = pelosi_analysis
    progress.update_status(agent_id, None, "Done")

    return {"messages": [message], "data": data}


def analyze_disclosure_momentum(insider_trades: list, end_date: str | None = None) -> dict:
    """Score recent buy/sell imbalance, with newer disclosures carrying more weight."""
    if not insider_trades:
        return {
            "score": 5,
            "details": "No recent disclosure-style trade data; neutral momentum.",
            "net_weighted_shares": 0,
            "buy_count": 0,
            "sell_count": 0,
        }

    weighted_buy_shares = 0.0
    weighted_sell_shares = 0.0
    buy_count = 0
    sell_count = 0

    for trade in insider_trades:
        shares = trade.transaction_shares or 0
        if shares == 0:
            continue

        recency_weight = _recency_weight(trade.filing_date, end_date)
        if shares > 0:
            buy_count += 1
            weighted_buy_shares += shares * recency_weight
        else:
            sell_count += 1
            weighted_sell_shares += abs(shares) * recency_weight

    total = weighted_buy_shares + weighted_sell_shares
    if total == 0:
        return {
            "score": 5,
            "details": "No directional buy/sell disclosures detected; neutral momentum.",
            "net_weighted_shares": 0,
            "buy_count": buy_count,
            "sell_count": sell_count,
        }

    net_ratio = (weighted_buy_shares - weighted_sell_shares) / total
    score = 5 + net_ratio * 5

    if score >= 7:
        details = "Recent disclosure activity skews toward accumulation."
    elif score <= 3:
        details = "Recent disclosure activity skews toward distribution."
    else:
        details = "Recent disclosure activity is mixed."

    return {
        "score": round(max(0, min(10, score)), 2),
        "details": details,
        "net_weighted_shares": round(weighted_buy_shares - weighted_sell_shares, 2),
        "buy_count": buy_count,
        "sell_count": sell_count,
    }


def analyze_trade_conviction(insider_trades: list) -> dict:
    """Estimate conviction from dollar value and size concentration."""
    trades_with_value = [abs(trade.transaction_value) for trade in insider_trades if trade.transaction_value is not None and trade.transaction_value != 0]

    if not trades_with_value:
        return {
            "score": 5,
            "details": "No transaction value data available; neutral conviction.",
            "total_value": 0,
            "largest_trade_value": 0,
        }

    total_value = sum(trades_with_value)
    largest_trade = max(trades_with_value)
    concentration = largest_trade / total_value if total_value else 0

    score = 4
    if total_value >= 50_000_000:
        score += 4
    elif total_value >= 10_000_000:
        score += 3
    elif total_value >= 1_000_000:
        score += 2
    elif total_value >= 100_000:
        score += 1

    if concentration >= 0.5:
        score += 1

    return {
        "score": min(10, score),
        "details": "Higher dollar disclosure activity suggests stronger conviction.",
        "total_value": round(total_value, 2),
        "largest_trade_value": round(largest_trade, 2),
        "largest_trade_concentration": round(concentration, 2),
    }


def analyze_policy_catalysts(company_news: list) -> dict:
    """Look for news terms tied to sectors often affected by federal policy."""
    if not company_news:
        return {
            "score": 5,
            "details": "No news available; neutral policy catalyst score.",
            "matched_terms": [],
            "matched_articles": 0,
        }

    policy_terms = {
        "ai",
        "artificial intelligence",
        "chips",
        "semiconductor",
        "defense",
        "cybersecurity",
        "infrastructure",
        "energy",
        "drug",
        "pharma",
        "medicare",
        "regulation",
        "antitrust",
        "contract",
        "federal",
    }
    matched_terms = set()
    matched_articles = 0

    for article in company_news[:25]:
        title = (article.title or "").lower()
        article_matches = {term for term in policy_terms if term in title}
        if article_matches:
            matched_articles += 1
            matched_terms.update(article_matches)

    score = min(10, 4 + matched_articles * 0.8 + len(matched_terms) * 0.3)
    if matched_articles:
        details = "Recent headlines contain policy-sensitive themes."
    else:
        details = "Few obvious policy-sensitive headlines found."

    return {
        "score": round(score, 2),
        "details": details,
        "matched_terms": sorted(matched_terms),
        "matched_articles": matched_articles,
    }


def generate_pelosi_output(
    ticker: str,
    analysis_data: dict,
    state: AgentState,
    agent_id: str,
) -> NancyPelosiSignal:
    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are a Nancy Pelosi-inspired AI analyst, making investment decisions through a congressional-disclosure and policy-catalyst lens.

                Focus on:
                1. Disclosure momentum: whether recent trading disclosures skew toward accumulation or distribution.
                2. Conviction: whether transaction values and concentration suggest meaningful positioning.
                3. Policy catalysts: whether headlines point to areas sensitive to federal spending, regulation, defense, chips, AI, healthcare, energy, infrastructure, or antitrust.

                Important constraints:
                - Do not claim to know Nancy Pelosi's current holdings or private intentions.
                - Treat this as a public-disclosure momentum framework, not as financial advice.
                - Be specific about the strongest bullish and bearish evidence.
                - Explain the final stance in a concise, investor-style paragraph.

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
                """Based on the following analysis data for {ticker}, produce the Nancy Pelosi-style investment signal.

                Analysis Data:
                {analysis_data}

                Return only valid JSON with "signal", "confidence", and "reasoning".
                """,
            ),
        ]
    )

    prompt = template.invoke({"analysis_data": json.dumps(analysis_data, indent=2), "ticker": ticker})

    def create_default_signal():
        return NancyPelosiSignal(
            signal=analysis_data["signal"],
            confidence=analysis_data["confidence"],
            reasoning=(
                f"{ticker} screens {analysis_data['signal']} under a public-disclosure momentum framework. "
                f"Disclosure momentum score is {analysis_data['disclosure_momentum']['score']}/10, "
                f"trade conviction score is {analysis_data['trade_conviction']['score']}/10, "
                f"and policy catalyst score is {analysis_data['policy_catalysts']['score']}/10."
            ),
        )

    return call_llm(
        prompt=prompt,
        pydantic_model=NancyPelosiSignal,
        agent_name=agent_id,
        state=state,
        default_factory=create_default_signal,
    )


def _one_year_before(end_date: str) -> str:
    return (datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=365)).strftime("%Y-%m-%d")


def _recency_weight(filing_date: str | None, end_date: str | None = None) -> float:
    if not filing_date:
        return 0.5

    try:
        filed_at = datetime.fromisoformat(filing_date.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return 0.5

    if end_date:
        try:
            reference_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            reference_date = datetime.now()
    else:
        reference_date = datetime.now()

    days_old = max(0, (reference_date - filed_at).days)
    if days_old <= 90:
        return 1.0
    if days_old <= 180:
        return 0.75
    if days_old <= 365:
        return 0.5
    return 0.25
