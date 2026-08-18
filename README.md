# FINORA

**Multi-Agent Financial Decision-Intelligence Platform**

FINORA is an agentic system that investigates a financial question the way a small analyst team would — pulling market data and financial statements through governed tools, computing risk explicitly, and producing an explainable, source-traceable recommendation. It is a decision-support tool, not investment advice.

> **Status:** Actively in development. This README reflects the target architecture end-to-end; see [Roadmap](#roadmap) for what's built vs. planned.

---

## What It Does

A user asks:

> "Should I invest ₹5 lakh in Tata Motors for the next 12 months?"

FINORA runs a coordinated multi-agent pipeline instead of a single LLM call:

1. **Market Agent** — pulls price/volume history, computes technical indicators (RSI, MACD, moving averages, volatility)
2. **Fundamentals Agent** — pulls financial statements, computes valuation ratios (P/E, P/B, ROE, margins)
3. **Risk Agent** — computes VaR, Sharpe ratio, beta, and max drawdown from real historical data
4. **Decision Agent** — synthesizes the above into a scored, explainable recommendation with cited sources

Every figure shown to the user is traceable to a specific tool call and data point — never a free-text LLM guess dressed up as a number.

---

## Architecture

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
              Financial Report
        (scores + sources + audit trail)

        ▲
        │
 ┌──────┴───────┐
 │  Financial   │   Agents never call external APIs
 │  MCP Server  │   directly — all data access is
 └──────┬───────┘   routed through governed, logged tools
        │
 ┌──────┼───────┐
 ▼      ▼       ▼
Market  Filings  News
 API    (RAG)    API
```

**Core design principle:** agent reasoning is separated from data access. Agents call tools on a custom MCP server rather than hitting external APIs or making up numbers — every value in a report is logged, timestamped, and traceable back to its source.

---

## Financial MCP Server

A custom [MCP](https://modelcontextprotocol.io) server exposes governed financial tools. Agents can only interact with data through these tools:

```
Financial MCP Server
├── get_stock_price(ticker)
├── get_historical_prices(ticker, range)
├── get_company_financials(ticker)
├── calculate_pe_ratio(ticker)
├── calculate_sharpe_ratio(ticker, window)
├── calculate_var(ticker, confidence)
├── get_stock_news(ticker, limit)
└── search_filings(query)          # RAG over annual reports / filings
```

Every call is logged (inputs, outputs, latency, timestamp), which powers both the audit trail shown to users and observability metrics internally.

**Data sources:**
- Market data — Yahoo Finance / Alpha Vantage / Twelve Data (free-tier, delayed quotes; disclosed in the UI)
- Financials — pulled from provider APIs where available, supplemented by parsing a local corpus of real annual reports/filings (PDF)
- News — a free news API or RSS feeds, with sentiment via FinBERT or a labeled LLM call

---

## Scoring Methodology

Scores are computed, not guessed:

- **Fundamentals score** — weighted composite of P/E vs. sector median, margin trend, debt/equity, ROE
- **Market score** — weighted composite of momentum, RSI/MACD signal, relative volatility
- **Risk score** — derived directly from computed VaR, Sharpe ratio, and max drawdown
- **Overall confidence** — weighted average of the above, with weights documented in `docs/scoring.md`

The Decision Agent's LLM narrates and explains these computed scores in natural language — it does not generate the scores itself.

---

## Guardrails & Auditability

- Every report includes the tool calls made, data timestamps, and a visible "not investment advice" disclaimer
- No imperative language ("buy," "sell") — output is framed as supporting factors and risks
- Full audit log of every agent decision and tool call, queryable per report
- MCP server enforces input validation, per-session rate limits, and no unbounded tool chaining

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, TypeScript, Tailwind, Recharts/Plotly |
| Backend | FastAPI |
| Agent orchestration | LangGraph |
| Tool governance | FastMCP (custom Financial MCP Server) |
| LLM | Single frontier model via API |
| RAG | Chroma/pgvector → Elasticsearch hybrid search |
| ML | scikit-learn, XGBoost, SHAP |
| Data | PostgreSQL, Redis |
| Observability | Structured logging, LangSmith, Prometheus/Grafana |

---

## Roadmap

**Phase 1 — Core MVP**
- [ ] FastAPI backend + Next.js dashboard
- [ ] Financial MCP Server (8 core tools)
- [ ] LangGraph supervisor: Market, Fundamentals, Risk agents
- [ ] Decision Agent with documented scoring
- [ ] RAG over a small corpus of real annual reports
- [ ] Audit trail + disclaimer in every report

**Phase 2 — Applied ML**
- [ ] XGBoost price-direction classifier, validated on held-out data
- [ ] SHAP explainability for ML-driven scores
- [ ] Forecast model comparison (ARIMA / Prophet / XGBoost) with reported RMSE

**Phase 3 — Extended agents**
- [ ] News/Sentiment Agent (FinBERT)
- [ ] Portfolio Agent (multi-asset allocation, correlation, VaR)
- [ ] Agent critique/rebuttal step before final decision

**Phase 4 — Production**
- [ ] Docker + CI/CD
- [ ] Prometheus/Grafana dashboards
- [ ] Backtesting harness
- [ ] Deployment

---

## Local Development

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# MCP server
cd mcp_server && python server.py
```

Copy `.env.example` to `.env` and set your market data API key, LLM API key, and Postgres connection string.

---

## Project Structure

```
finora/
├── backend/          # FastAPI app, agent orchestration
├── frontend/          # Next.js dashboard
├── mcp_server/         # Financial MCP Server (FastMCP)
├── ml/                # Training scripts, notebooks, SHAP analysis
├── docs/
│   └── scoring.md      # Documented scoring weights and methodology
└── README.md
```

---

## Disclaimer

FINORA is a personal project built for educational and portfolio purposes. It is a decision-support tool, not financial advice. Market data may be delayed or sourced from free-tier APIs and should not be relied on for real trading or investment decisions.

---

## License

MIT
