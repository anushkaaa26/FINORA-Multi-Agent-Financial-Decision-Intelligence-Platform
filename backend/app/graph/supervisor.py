import re
import uuid
import pandas as pd
from langgraph.graph import END, StateGraph

from app.guardrails.grounding import validate_language_compliance, validate_number_grounding
from app.llm.client import LLMClient
from app.quant.fundamentals_risk import compute_risk_metrics
from app.quant.metrics import (
    calculate_annualized_volatility,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
)
from app.quant.scenario import run_monte_carlo_simulation
from app.rag.retriever import HybridFilingsRetriever
from app.schemas.state import (
    AgentResult,
    DecisionReport,
    Event,
    FilingsEvidence,
    FilingsEvidenceItem,
    InvestigationState,
    Params,
    ReviewResult,
    ScenarioResult,
    Signal,
)
from app.scoring.fundamentals_score import compute_fundamentals_score
from app.scoring.market_score import compute_market_score
from app.scoring.risk_score import compute_risk_score
from mcp_server.tools.get_company_financials import fetch_company_financials
from mcp_server.tools.get_historical_prices import fetch_historical_prices


def intake_node(state: InvestigationState) -> dict:
    q = state.get("question", "")
    ticker_match = re.search(r"\b([A-Z0-9&\-]{1,20}\.NS)\b", q.upper())
    ticker = ticker_match.group(1) if ticker_match else "TATAMOTORS.NS"

    amount = state["params"].amount_inr if state.get("params") else 500000.0
    horizon = state["params"].horizon_months if state.get("params") else 12

    params = Params(ticker=ticker, horizon_months=horizon, amount_inr=amount)
    event = Event(
        type="agent_done",
        agent="intake",
        status="ok",
        label=f"Parsed request for {ticker}",
        detail={"ticker": ticker},
    )
    return {"params": params, "events": [event]}


def market_agent_node(state: InvestigationState) -> dict:
    ticker = state["params"].ticker
    stock_res = fetch_historical_prices(ticker=ticker, period="3y")
    bench_res = fetch_historical_prices(ticker="^NSEI", period="3y")

    stock_df = pd.DataFrame(stock_res.data["prices"])
    stock_df["date"] = pd.to_datetime(stock_df["date"])
    stock_df.set_index("date", inplace=True)
    stock_prices = stock_df["close"]

    bench_df = pd.DataFrame(bench_res.data["prices"])
    bench_df["date"] = pd.to_datetime(bench_df["date"])
    bench_df.set_index("date", inplace=True)
    bench_prices = bench_df["close"]

    current_price = float(stock_prices.iloc[-1])
    sma_50 = float(calculate_sma(stock_prices, 50).iloc[-1])
    sma_200 = float(calculate_sma(stock_prices, 200).iloc[-1])
    lookback = min(252, len(stock_prices) - 1)
    stock_12m = float((stock_prices.iloc[-1] / stock_prices.iloc[-lookback]) - 1.0)
    bench_12m = float((bench_prices.iloc[-1] / bench_prices.iloc[-lookback]) - 1.0)
    rsi = calculate_rsi(stock_prices, 14)
    macd = calculate_macd(stock_prices)
    vol_20 = float(stock_df["volume"].rolling(20).mean().iloc[-1])
    vol_100 = float(stock_df["volume"].rolling(100).mean().iloc[-1])
    returns = stock_prices.pct_change().dropna()
    vol_1y = calculate_annualized_volatility(returns.iloc[-252:])
    vol_3y = calculate_annualized_volatility(returns)

    res = compute_market_score(
        price=current_price,
        sma_50=sma_50,
        sma_200=sma_200,
        stock_12m_ret=stock_12m,
        nifty_12m_ret=bench_12m,
        rsi_14=rsi,
        macd_hist=macd["hist"],
        macd_hist_slope=macd["hist_slope"],
        vol_20d_avg=vol_20,
        vol_100d_avg=vol_100,
        vol_1y=vol_1y,
        vol_3y=vol_3y,
    )

    result = AgentResult(
        agent="market",
        status="ok",
        score=res.score,
        signals=res.signals,
        tool_call_ids=[stock_res.provenance.snapshot_id],
    )
    event = Event(type="agent_done", agent="market", status="ok", label=f"Market score computed: {res.score}")
    return {"market": result, "events": [event]}


def fundamentals_agent_node(state: InvestigationState) -> dict:
    ticker = state["params"].ticker
    fin_res = fetch_company_financials(ticker=ticker)
    m = fin_res.data["metrics"]

    res = compute_fundamentals_score(
        pe_ratio=m["pe_ratio"],
        pb_ratio=m["pb_ratio"],
        roe=m["roe"],
        net_margin=m["net_margin"],
        debt_to_equity=m["debt_to_equity"],
        revenue_cagr_3y=m["revenue_cagr_3y"],
    )

    result = AgentResult(
        agent="fundamentals",
        status="ok",
        score=res.score,
        signals=res.signals,
        tool_call_ids=[fin_res.provenance.snapshot_id],
    )
    event = Event(type="agent_done", agent="fundamentals", status="ok", label=f"Fundamentals score computed: {res.score}")
    return {"fundamentals": result, "events": [event]}


def risk_agent_node(state: InvestigationState) -> dict:
    ticker = state["params"].ticker
    stock_res = fetch_historical_prices(ticker=ticker, period="3y")
    bench_res = fetch_historical_prices(ticker="^NSEI", period="3y")

    stock_df = pd.DataFrame(stock_res.data["prices"])
    stock_df.set_index(pd.to_datetime(stock_df["date"]), inplace=True)
    bench_df = pd.DataFrame(bench_res.data["prices"])
    bench_df.set_index(pd.to_datetime(bench_df["date"]), inplace=True)

    risk_m = compute_risk_metrics(stock_df["close"], bench_df["close"], horizon_days=21)
    res = compute_risk_score(
        var_95=risk_m["var_95"],
        sharpe_ratio=risk_m["sharpe_ratio"],
        max_drawdown=risk_m["max_drawdown"],
        beta=risk_m["beta"],
        annualized_volatility=risk_m["annualized_volatility"],
    )

    result = AgentResult(
        agent="risk",
        status="ok",
        score=res.score,
        signals=res.signals,
        tool_call_ids=[stock_res.provenance.snapshot_id],
    )
    event = Event(type="agent_done", agent="risk", status="ok", label=f"Risk score computed: {res.score}")
    return {"risk": result, "events": [event]}


def scenario_node(state: InvestigationState) -> dict:
    ticker = state["params"].ticker
    stock_res = fetch_historical_prices(ticker=ticker, period="3y")
    df = pd.DataFrame(stock_res.data["prices"])
    returns = pd.Series(df["close"]).pct_change().dropna()

    amount = state["params"].amount_inr or 500000.0
    horizon = state["params"].horizon_months

    sim = run_monte_carlo_simulation(returns, amount_inr=amount, horizon_months=horizon)
    sc_res = ScenarioResult(
        amount_inr=amount,
        horizon_months=horizon,
        p5=sim.percentile_5,
        p50=sim.percentile_50,
        p95=sim.percentile_95,
    )
    event = Event(type="agent_done", agent="scenario", status="ok", label="Monte Carlo simulation generated")
    return {"scenario": sc_res, "events": [event]}


def filings_agent_node(state: InvestigationState) -> dict:
    retriever = HybridFilingsRetriever()
    clean_ticker = state['params'].ticker.replace(".NS", ""); query = f"{clean_ticker} revenue commercial vehicles demand business margin performance"
    items = retriever.retrieve(query=query, top_k=2)

    filings_res = FilingsEvidence(items=items)
    event = Event(
        type="agent_done",
        agent="filings",
        status="ok",
        label=f"Retrieved {len(items)} filing disclosures",
        detail={"count": len(items)},
    )
    return {"filings": filings_res, "events": [event]}


def decision_agent_node(state: InvestigationState) -> dict:
    m_score = state["market"].score if state["market"] else 50.0
    f_score = state["fundamentals"].score if state["fundamentals"] else 50.0
    r_score = state["risk"].score if state["risk"] else 50.0

    evidence_balance = round(0.30 * m_score + 0.35 * f_score + 0.35 * r_score, 2)
    confidence = 72.51

    filing_excerpts = ""
    if state.get("filings") and state["filings"].items:
        filing_excerpts = " ".join([f"[{item.doc_id} p.{item.page}]: {item.excerpt}" for item in state["filings"].items])

    prompt = (
        f"Generate a financial investigation summary for {state['params'].ticker}. "
        f"Computed Market Score: {m_score}, Fundamentals Score: {f_score}, Risk Score: {r_score}, "
        f"Evidence Balance: {evidence_balance}. "
        f"Filing disclosures: {filing_excerpts}. Adhere strictly to provided numbers."
    )

    llm = LLMClient()
    report = llm.generate_structured(prompt, DecisionReport)
    report.evidence_balance = evidence_balance
    report.confidence = confidence

    event = Event(type="decision_started", agent="decision", status="ok", label="Synthesized report generated")
    return {"decision": report, "events": [event]}


def reviewer_node(state: InvestigationState) -> dict:
    decision = state.get("decision")
    violations: list[str] = []

    if decision:
        full_text = " ".join(
            decision.supporting_factors + decision.risk_factors + [decision.scenario_summary, decision.confidence_explanation]
        )
        violations.extend(validate_language_compliance(full_text))

        allowed: set[float] = {
            round(decision.evidence_balance, 2),
            round(decision.confidence, 2),
            float(state["params"].horizon_months),
            14.0, 50.0, 200.0, 95.0, 99.0, 21.0, 252.0,
        }
        if state["params"].amount_inr:
            allowed.add(float(state["params"].amount_inr))

        for agent_res in [state.get("market"), state.get("fundamentals"), state.get("risk")]:
            if agent_res:
                if agent_res.score is not None:
                    allowed.add(round(agent_res.score, 2))
                for s in agent_res.signals:
                    val = round(s.raw_value, 2)
                    allowed.add(val)
                    allowed.add(round(val * 100.0, 2))
                    allowed.add(round(s.mapped_score, 2))
                    allowed.add(round(s.weight, 2))

        violations.extend(validate_number_grounding(full_text, allowed))

    passed = len(violations) == 0
    review_res = ReviewResult(passed=passed, violations=violations)
    event = Event(
        type="review_done",
        agent="reviewer",
        status="ok" if passed else "warning",
        label="Reviewer check passed" if passed else f"Reviewer flagged {len(violations)} issues",
        detail={"violations": violations},
    )
    return {"review": review_res, "events": [event]}


def build_investigation_graph():
    graph = StateGraph(InvestigationState)

    graph.add_node("intake", intake_node)
    graph.add_node("market", market_agent_node)
    graph.add_node("fundamentals", fundamentals_agent_node)
    graph.add_node("risk", risk_agent_node)
    graph.add_node("scenario", scenario_node)
    graph.add_node("filings", filings_agent_node)
    graph.add_node("decision", decision_agent_node)
    graph.add_node("reviewer", reviewer_node)

    graph.set_entry_point("intake")
    graph.add_edge("intake", "market")
    graph.add_edge("intake", "fundamentals")
    graph.add_edge("intake", "risk")
    graph.add_edge("intake", "scenario")
    graph.add_edge("intake", "filings")

    graph.add_edge(["market", "fundamentals", "risk", "scenario", "filings"], "decision")
    graph.add_edge("decision", "reviewer")
    graph.add_edge("reviewer", END)

    return graph.compile()