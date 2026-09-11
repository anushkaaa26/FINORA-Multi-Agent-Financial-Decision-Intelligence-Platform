# FINORA

### Multi-Agent Financial Decision Intelligence Platform

> **Ask a financial question. FINORA investigates it like an analyst team.**

FINORA is an **agentic financial intelligence platform** that combines multi-agent reasoning, quantitative analysis, financial-document RAG, and governed MCP tools to investigate investment questions and produce **explainable, source-traceable decision reports**.

Instead of asking a single LLM to "analyze a stock", FINORA decomposes the investigation across specialized agents — each responsible for a different analytical dimension.

**No invented numbers. No black-box recommendations. Every computed metric is traceable to its underlying data and tool call.**

> ⚠️ **FINORA is an educational decision-support system, not financial advice.**

---

## ✨ What Makes FINORA Different?

Most AI financial assistants follow this pattern:

```text
User Question
      ↓
    LLM
      ↓
"Looks like a good investment."
```

FINORA takes a different approach:

```text
                         USER QUESTION
                              │
                              ▼
                    ┌──────────────────┐
                    │ LangGraph        │
                    │ Supervisor       │
                    └────────┬─────────┘
                             │
             ┌───────────────┼────────────────┐
             ▼               ▼                ▼
       ┌───────────┐   ┌────────────┐   ┌────────────┐
       │  MARKET   │   │FUNDAMENTAL │   │    RISK    │
       │   AGENT   │   │   AGENT    │   │   AGENT    │
       └─────┬─────┘   └──────┬─────┘   └──────┬─────┘
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                    ┌──────────────────┐
                    │ DECISION AGENT   │
                    │ + Explainability │
                    └────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │ AUDITABLE REPORT │
                    └──────────────────┘
```

The LLM **does not invent financial metrics**.

It interprets metrics that were actually computed from retrieved data.

---

# 🧠 Example

A user asks:

> **"Should I consider investing ₹5 lakh in Tata Motors for the next 12 months?"**

FINORA doesn't immediately answer.

It investigates.

### 📈 Market Agent

Analyzes:

* Historical price movement
* Volume
* Moving averages
* RSI
* MACD
* Volatility
* Momentum

### 📊 Fundamentals Agent

Analyzes:

* P/E
* P/B
* ROE
* Profit margins
* Debt-to-equity
* Revenue / earnings trends
* Valuation relative to available benchmarks

### 🛡️ Risk Agent

Computes:

* Value at Risk (VaR)
* Sharpe ratio
* Beta
* Maximum drawdown
* Historical volatility

### 🧠 Decision Agent

Synthesizes the evidence into:

* Market score
* Fundamentals score
* Risk score
* Overall confidence
* Supporting factors
* Risk factors
* Source references
* Full audit trail

The result is **evidence-backed decision intelligence**, not an LLM-generated guess.

---

# 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │    NEXT.JS DASHBOARD │
                         │ Charts • Reports     │
                         │ Sources • Audit Log  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │       FASTAPI        │
                         │      Backend API     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ LANGGRAPH SUPERVISOR │
                         └──────────┬───────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             │                      │                      │
             ▼                      ▼                      ▼
      ┌────────────┐         ┌─────────────┐        ┌────────────┐
      │   MARKET   │         │FUNDAMENTALS │        │    RISK    │
      │   AGENT    │         │    AGENT    │        │   AGENT    │
      └─────┬──────┘         └──────┬──────┘        └─────┬──────┘
            │                       │                      │
            └───────────────────────┼──────────────────────┘
                                    ▼
                         ┌──────────────────────┐
                         │   DECISION AGENT     │
                         │ Scoring + Reasoning  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ FINANCIAL REPORT     │
                         │                      │
                         │ Scores               │
                         │ Evidence             │
                         │ Sources              │
                         │ Risks                │
                         │ Audit Trail          │
                         └──────────────────────┘

                                    ▲
                                    │
                         ┌──────────────────────┐
                         │  FINANCIAL MCP       │
                         │      SERVER          │
                         └──────────┬───────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 ▼                  ▼                  ▼
            Market Data         Filings/RAG        News Data
```

---

# 🔐 MCP-Governed Data Access

A core FINORA design principle is:

> **Agents reason. Tools retrieve.**

Agents never directly access external financial APIs.

Instead, all external data access is routed through a custom **Financial MCP Server**.

```text
Agent
  │
  ▼
MCP Tool Request
  │
  ▼
Validation
  │
  ▼
Financial Data Provider
  │
  ▼
Structured Result
  │
  ▼
Agent
```

### Financial MCP Tools

| Tool                       | Purpose                      |
| -------------------------- | ---------------------------- |
| `get_stock_price()`        | Latest available price       |
| `get_historical_prices()`  | Historical market data       |
| `get_company_financials()` | Company financial statements |
| `calculate_pe_ratio()`     | P/E calculation              |
| `calculate_sharpe_ratio()` | Risk-adjusted return         |
| `calculate_var()`          | Value at Risk                |
| `get_stock_news()`         | Recent news                  |
| `search_filings()`         | RAG over financial filings   |

Every tool invocation can be logged with:

```text
Input
Output
Timestamp
Latency
Source
Session
```

This creates a machine-readable **audit trail** for the investigation.

---

# 📚 Financial RAG

FINORA can retrieve information from a corpus of real financial documents such as:

* Annual reports
* Financial filings
* Company disclosures
* Other structured financial documents

Instead of relying purely on model memory:

```text
User Question
      ↓
Document Retrieval
      ↓
Relevant Evidence
      ↓
Financial Agent
      ↓
Decision
```

This makes financial reasoning **source-grounded and inspectable**.

---

# 📐 Quantitative Scoring

FINORA separates **calculation** from **LLM reasoning**.

The system computes quantitative metrics first.

### Fundamentals Score

Based on factors such as:

```text
P/E valuation
Margin trend
Debt/Equity
ROE
```

### Market Score

Based on:

```text
Momentum
RSI
MACD
Moving averages
Volatility
```

### Risk Score

Based on:

```text
VaR
Sharpe Ratio
Maximum Drawdown
Beta
Historical Volatility
```

The final Decision Agent receives these computed signals and explains them.

### Important distinction

```text
❌ LLM → "Risk score = 82"

✅ Python/ML calculation
        ↓
   Risk score = 82
        ↓
   Decision Agent
        ↓
"Risk conditions appear relatively favorable
because..."
```

The model **narrates the evidence**.

It doesn't manufacture the evidence.

---

# 🛡️ Guardrails

FINORA is designed around financial safety and transparency.

### No fabricated metrics

Every displayed financial value should originate from a data source or deterministic computation.

### No hidden tool access

Agents interact with external financial data through governed tools.

### Auditability

Reports can expose:

* Agent execution
* Tool calls
* Input parameters
* Retrieved data
* Timestamps
* Sources

### No imperative investment language

FINORA frames outputs as:

> Supporting factors
> Risks
> Evidence
> Scenario analysis
> Confidence

rather than blindly telling users to:

> BUY / SELL

### Disclaimer

Every report includes a visible:

> **Not financial advice. Market data may be delayed or incomplete.**

---

# 🖥️ Product Experience

The planned dashboard is designed around an analyst-style workflow.

### 01 — Ask

```text
What would you like to investigate?

"Analyze Tata Motors for a 12-month horizon
with a ₹5 lakh investment scenario."

                [ Investigate ]
```

### 02 — Investigate

Live agent execution:

```text
✓ Market Agent
  Retrieved historical prices

✓ Fundamentals Agent
  Retrieved financial metrics

✓ Risk Agent
  Calculated VaR + Sharpe + Drawdown

✓ RAG
  Retrieved relevant financial documents

● Decision Agent
  Synthesizing evidence...
```

### 03 — Understand

The final report can present:

```text
┌───────────────────────────────────────┐
│ FINORA ANALYSIS                       │
│ Tata Motors                           │
├───────────────────────────────────────┤
│                                       │
│ Market       ████████░░               │
│ Fundamentals█████████░               │
│ Risk         ██████░░░░               │
│                                       │
│ Overall Confidence                    │
│ ████████░░                            │
│                                       │
├───────────────────────────────────────┤
│ KEY SUPPORTING FACTORS                │
│ • ...                                 │
│ • ...                                 │
│                                       │
│ KEY RISKS                             │
│ • ...                                 │
│ • ...                                 │
└───────────────────────────────────────┘
```

### 04 — Inspect

Users can drill down into:

**Why did FINORA reach this conclusion?**

```text
Decision Agent
      ↓
Risk Agent
      ↓
Sharpe Ratio
      ↓
Historical Data
      ↓
MCP Tool Call
      ↓
Original Data Source
```

---

# 🧰 Tech Stack

| Layer               | Technology                                          |
| ------------------- | --------------------------------------------------- |
| Frontend            | Next.js • TypeScript • Tailwind                     |
| Visualization       | Recharts / Plotly                                   |
| Backend             | FastAPI                                             |
| Agent Orchestration | LangGraph                                           |
| Tool Governance     | FastMCP                                             |
| LLM                 | Frontier LLM API                                    |
| RAG                 | Chroma / pgvector / Elasticsearch                   |
| ML                  | scikit-learn • XGBoost • SHAP                       |
| Data                | PostgreSQL • Redis                                  |
| Observability       | Structured Logging • LangSmith • Prometheus/Grafana |
| Deployment          | Docker • CI/CD                                      |

---

# 📂 Project Structure

```text
FINORA/
│
├── backend/
│   ├── agents/
│   │   ├── market.py
│   │   ├── fundamentals.py
│   │   ├── risk.py
│   │   └── decision.py
│   │
│   ├── graph/
│   │   └── supervisor.py
│   │
│   └── main.py
│
├── frontend/
│   ├── components/
│   ├── pages/
│   └── ...
│
├── mcp_server/
│   ├── server.py
│   └── tools/
│
├── ml/
│   ├── training/
│   ├── evaluation/
│   └── explainability/
│
├── rag/
│   ├── ingestion/
│   ├── retrieval/
│   └── documents/
│
├── docs/
│   ├── architecture.md
│   ├── scoring.md
│   └── evaluation.md
│
├── tests/
│
├── .env.example
├── docker-compose.yml
└── README.md
```

---

# 🚀 Roadmap

## Phase 1 — Agentic MVP

* [ ] FastAPI backend
* [ ] Next.js dashboard
* [ ] Financial MCP server
* [ ] Market Agent
* [ ] Fundamentals Agent
* [ ] Risk Agent
* [ ] Decision Agent
* [ ] LangGraph orchestration
* [ ] Basic financial RAG
* [ ] Audit trail
* [ ] Transparent scoring

## Phase 2 — Applied ML

* [ ] XGBoost price-direction classifier
* [ ] Proper train/validation/test split
* [ ] SHAP explanations
* [ ] ARIMA vs XGBoost comparison
* [ ] RMSE / MAE evaluation
* [ ] Backtesting framework

## Phase 3 — Advanced Agents

* [ ] News & Sentiment Agent
* [ ] FinBERT sentiment analysis
* [ ] Portfolio Agent
* [ ] Multi-asset correlation analysis
* [ ] Portfolio-level VaR
* [ ] Agent critique / rebuttal stage

## Phase 4 — Production

* [ ] Dockerized deployment
* [ ] CI/CD
* [ ] Prometheus metrics
* [ ] Grafana dashboards
* [ ] Persistent audit logs
* [ ] Automated backtesting
* [ ] Production monitoring

---

# 🔬 Research & Engineering Principles

FINORA is built around several principles:

### 1. Reasoning ≠ Data Access

LLMs should reason over information, not secretly retrieve or fabricate it.

### 2. Computation ≠ Narration

Quantitative metrics are calculated programmatically.

The LLM explains them.

### 3. Evidence > Confidence

A confident answer without evidence is not useful financial intelligence.

### 4. Auditability by Design

Every important decision should be inspectable.

### 5. Multi-Agent ≠ Multiple LLM Calls

Agents have **specialized responsibilities**, tools, inputs and outputs rather than simply repeating the same prompt.

---

# 📊 Current Status

> **FINORA is actively under development.**

The repository is being built incrementally toward the architecture described above.

| Component             | Status                      |
| --------------------- | --------------------------- |
| Project architecture  | 🟢 Active                   |
| MCP server            | 🟡 In development           |
| Market Agent          | 🟡 In development           |
| Fundamentals Agent    | 🟡 In development           |
| Risk Agent            | 🟡 In development           |
| Decision Agent        | 🟡 In development           |
| RAG pipeline          | 🟡 Planned / In development |
| Dashboard             | 🟡 In development           |
| Applied ML            | 🔵 Planned                  |
| Production deployment | 🔵 Planned                  |

The README intentionally distinguishes between **implemented functionality and planned architecture** to avoid overstating the current capabilities of the system.

---

# 🎯 Why FINORA?

FINORA explores a practical question:

> **What happens when an LLM is given the role of an analyst coordinator rather than being asked to act as the analyst itself?**

The goal is to combine:

**Agentic AI + MCP + RAG + Quantitative Finance + ML Explainability + Observability**

into one auditable decision-intelligence system.

---

## ⚠️ Disclaimer

FINORA is a personal project created for educational and portfolio purposes.

It is **not financial advice** and should not be used as the sole basis for investment decisions.

Financial data may be delayed, incomplete, or sourced from free-tier providers.

---

## 📜 License

MIT
