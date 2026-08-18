# FINORA — Multi-Agent Financial Decision-Intelligence Platform

> An agentic system that investigates a financial question the way a small analyst team would — pulling market data, financial statements, and news through governed tools, scoring risk explicitly, and producing an auditable recommendation with sources — not just an LLM guessing an answer.

**Status:** In active development. This README describes the target architecture; build progress is tracked in [Roadmap](#roadmap).

---

## 1. What FINORA Does

A user asks a question like:

> "Should I invest ₹5 lakh in Tata Motors for the next 12 months?"

Instead of a single LLM call, FINORA runs a coordinated multi-agent investigation:

1. **Market Agent** — pulls price/volume history and computes technical indicators
2. **Fundamentals Agent** — pulls financial statements and computes valuation ratios
3. **Risk Agent** — computes volatility, VaR, Sharpe ratio, drawdown from real data
4. **Decision Agent** — combines the above into a scored, explainable recommendation

Every number the system shows is traceable to a specific tool call and a specific data point — not a model's free-text guess.

**What this is not:** investment advice. FINORA is a decision-support and risk-analysis tool. Every report carries a visible disclaimer, and outputs are framed as "supporting factors / risks," never as buy/sell instructions. This framing is a deliberate design decision, not just a legal footnote — see [Guardrails](#6-guardrails--auditability).

---

## 2. Why This Project (and Why It's Scoped the Way It Is)

Earlier drafts of this idea listed 8+ agents (fraud detection, credit scoring, portfolio optimization, agent debate, full RAG over regulatory filings, etc.) to be built in parallel. That's a 3–6 month roadmap compressed into a resume bullet, and shallow coverage of ten things is worse in an interview than deep coverage of three.

This version is deliberately scoped as:
- A **real, working MVP** (Phase 1) that can be deployed and demoed honestly
- A **defined extension path** (Phases 2–4) built incrementally, side-by-side with job search, so the project keeps growing without ever being "half-fake"

Everything below distinguishes **what's built**, **what's mocked/stubbed for now**, and **what's planned** — so the README never overstates the system's actual state.

---

## 3. Architecture

```
                    Next.js Dashboard
                          │
                          ▼
                       FastAPI
                          │
                          ▼
                 LangGraph Supervisor
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   Market Agent    Fundamentals Agent   Risk Agent
        │                 │                 │
        └────────────────┬┴─────────────────┘
                          ▼
                   Decision Agent
                          │
                          ▼
                 Financial Report (with
                 sources + audit trail)

        ▲
        │
 ┌──────┴───────┐
 │  Financial   │   ← agents never call external
 │  MCP Server  │      APIs directly; all access
 └──────┬───────┘      is governed through MCP
        │
 ┌──────┼───────┐
 ▼      ▼       ▼
Market  Filings  News
 API    (RAG)    API
```

**Key architectural decision:** agents don't call external APIs or the LLM's own judgment directly for data — every data access goes through the Financial MCP Server. This is the part worth emphasizing in interviews:

> "Agent reasoning is separated from financial data access via MCP — agents call governed, logged tools rather than hitting external services directly, which makes every number in the final report traceable to a source."

---

## 4. Financial MCP Server (MVP Tool Set)

Trimmed to tools that are actually implementable with free/realistic data sources, rather than a 15-tool wishlist:

```
Financial MCP Server
├── get_stock_price(ticker)              # live/delayed quote
├── get_historical_prices(ticker, range) # OHLCV time series
├── get_company_financials(ticker)       # income statement, balance sheet
├── calculate_pe_ratio(ticker)
├── calculate_sharpe_ratio(ticker, window)
├── calculate_var(ticker, confidence)    # historical VaR
├── get_stock_news(ticker, limit)
└── search_filings(query)                # RAG over uploaded annual reports
```

Each tool call is **logged** (input, output, latency, timestamp) — this log is what powers the audit trail in section 6, and it's also a legitimate "observability" story for interviews even before Prometheus/Grafana are wired in.

**Data sourcing (stated honestly, not glossed over):**
- Market data: Yahoo Finance / `yfinance` or a free tier of Alpha Vantage / Twelve Data — no official free real-time NSE/BSE feed exists, so prices are delayed and this is disclosed in the UI.
- Financials: pulled from the same providers where available; gaps filled by parsing a small local set of real annual reports/filings (PDF) rather than claiming a live SEBI/RBI filings feed.
- News: a free news API (e.g., NewsAPI) or RSS feeds from financial news sources, with FinBERT (or a prompted LLM, clearly labeled as such) for sentiment.

---

## 5. Scoring Methodology (Defined, Not a Black Box)

A number like "Confidence: 76%" or "Risk Score: 7.2/10" needs to be explainable, not a plausible-sounding LLM output. FINORA computes these as a **weighted combination of the sub-agent scores**, not a single model guess:

- **Fundamentals score** — normalized composite of P/E vs. sector median, margin trend, debt/equity, ROE (rule-based, transparent weights)
- **Market score** — normalized composite of momentum, RSI/MACD signal, volatility relative to sector
- **Risk score** — derived directly from computed VaR, Sharpe ratio, and max drawdown (not LLM-estimated)
- **Overall confidence** — a weighted average of the three above, with weights documented in `/docs/scoring.md`, so the number in the UI can always be traced back to inputs

The Decision Agent's job is to **synthesize and explain** these computed scores in natural language — not to invent the scores itself. This distinction is worth stating explicitly in any interview: the LLM narrates and reasons over real numbers, it doesn't hallucinate them.

---

## 6. Guardrails & Auditability

Since this system touches financial recommendations, these are treated as first-class design requirements, not polish:

- **Every report includes:** the specific tool calls made, the data timestamps used, and a disclaimer that this is not investment advice.
- **No imperative language** ("buy," "sell") in generated output — recommendations are framed as "supporting factors" and "risks" for the user to weigh.
- **Audit log** of every agent decision and tool call, queryable per-report, so any output can be traced back to its inputs.
- **Tool-level guardrails on the MCP server:** input validation, per-session rate limits, no arbitrary/unbounded tool chaining.

---

## 7. Tech Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js + TypeScript, Recharts/Plotly, Tailwind |
| Backend | FastAPI |
| Agent orchestration | LangGraph |
| Tool governance | FastMCP (custom Financial MCP Server) |
| LLM | One frontier model via API (kept to one model — no multi-model sprawl) |
| RAG | Local vector store (start: Chroma/pgvector) → Elasticsearch hybrid search later |
| ML | scikit-learn, XGBoost, SHAP (added in Phase 2, see roadmap) |
| Data | PostgreSQL, Redis (caching tool calls / rate-limited API responses) |
| Observability | Structured logging → LangSmith/Prometheus/Grafana (Phase 4) |

---

## 8. Roadmap

**Phase 1 — Core MVP** *(build target: pre-deployment)*
- [ ] FastAPI backend + Next.js dashboard skeleton
- [ ] Financial MCP Server with the 8 tools above
- [ ] LangGraph supervisor with Market, Fundamentals, Risk agents
- [ ] Decision Agent with documented scoring methodology
- [ ] Minimal RAG over 5–10 real annual reports
- [ ] Disclaimer + audit trail visible in every report

**Phase 2 — Real ML**
- [ ] XGBoost-based price-direction classifier (validated on held-out data, not just displayed)
- [ ] SHAP explainability on any ML-driven score
- [ ] Forecast model comparison (ARIMA / Prophet / XGBoost) with reported RMSE

**Phase 3 — Extended agents**
- [ ] News/Sentiment Agent (FinBERT)
- [ ] Portfolio Agent (multi-asset allocation, correlation, VaR)
- [ ] Structured agent critique step before Decision Agent (real rebuttal, not just sequential handoff)

**Phase 4 — Production hardening**
- [ ] Docker + CI/CD
- [ ] Prometheus/Grafana dashboards (latency, token usage, tool-call volume)
- [ ] Backtesting harness for any predictive claim
- [ ] Deployment (Vercel/Render + managed Postgres)

*Fraud/anomaly detection and credit-risk modeling (isolation forest, logistic regression on public datasets like Kaggle's credit card fraud set) are tracked as a possible Phase 5 extension — not committed to the MVP story, since they're a different data domain (transactions) from the rest of the platform and shouldn't be bolted on just to widen the buzzword list.*

---

## 9. Resume Line (once Phase 1–2 are real)

> **FINORA — Multi-Agent Financial Decision-Intelligence Platform**
> Built an agentic financial analysis platform using LangGraph and a custom MCP server, separating agent reasoning from governed, logged data access. Implemented rule-based and XGBoost/SHAP-driven scoring for market, fundamental, and risk analysis, with an auditable decision trail and RAG over financial filings. FastAPI + Next.js, deployed on [platform].

*(Keep this line honest to what's actually built at time of applying — don't claim Phase 3/4 items until they exist.)*

---

## 10. Local Development

```bash
# backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload

# frontend
cd frontend && npm install && npm run dev

# MCP server
cd mcp_server && python server.py
```

Environment variables required: see `.env.example` (market data API key, LLM API key, Postgres connection string).

---

## Disclaimer

FINORA is a personal/educational project and a decision-support tool. It does not provide financial advice. Market data may be delayed or sourced from free-tier APIs and should not be relied on for real trading decisions.
