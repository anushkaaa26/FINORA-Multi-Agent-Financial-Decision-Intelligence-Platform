# FINORA ⚡
### Autonomous Multi-Agent Financial Intelligence & Quantitative Terminal

> **Institutional-grade market analytics, Monte Carlo risk simulation, and statutory RAG search—engineered for high-conviction decision-making.**

---

## 🚀 Vision & Overview

**Finora** is a state-of-the-art, full-stack financial terminal designed to bridge the gap between complex quantitative modeling and actionable investment research. Built for modern markets, Finora moves beyond static dashboards by combining real-time NSE benchmark telemetry, stochastic risk modeling, and a Retrieval-Augmented Generation (RAG) engine that surfaces direct insights from corporate statutory filings.

Whether evaluating technical momentum, running thousands of geometric Brownian motion price paths, or parsing annual reports for hidden liabilities, Finora acts as an autonomous analytical co-pilot for equity researchers and quantitative traders.

---

## 🏗️ Core Architecture & Tech Stack

Finora is engineered with a decoupled, high-performance containerized architecture optimized for speed, scalability, and modular expansion:

┌────────────────────────────────────────────────────────┐
│                   FINORA FRONTEND                      │
│        Next.js 14 / TypeScript / Tailwind CSS          │
└───────────────────────────┬────────────────────────────┘
│ REST / SSE / HTTP
┌───────────────────────────▼────────────────────────────┐
│                   FINORA BACKEND                       │
│       FastAPI / Python 3.11 / LangGraph / Uvicorn      │
└───────────┬───────────────────────────┬────────────────┘
│                           │
┌────────▼─────────┐       ┌─────────▼──────────┐
│  Quant & Risk    │       │  Statutory RAG     │
│  Engine (NumPy,  │       │  (BM25Okapi,       │
│  yfinance)       │       │   Filing Corpus)   │
└──────────────────┘       └────────────────────┘


* **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, Recharts for financial visualization.
* **Backend**: FastAPI, Python 3.11, Uvicorn asynchronous server.
* **Quantitative Engine**: `yfinance` for real-time market data ingestion, custom NumPy vectorized Monte Carlo simulation engine.
* **Knowledge Retrieval (RAG)**: BM25 (`rank_bm25`) lexical search engine paired with curated corporate filing and annual report corpuses.
* **Infrastructure**: Fully containerized with Docker and Docker Compose for seamless local and cloud environments.

---

## 🌟 Key Features & Capabilities

### 1. 📊 Live NSE Market Telemetry & Screener
* Real-time benchmark index tracking (**NIFTY 50**, **BANK NIFTY**, **SENSEX**, **NIFTY IT**).
* Automated quantitative screening filtering stocks by ROE, P/E ratios, and composite conviction scores.

### 2. 🎲 Monte Carlo Risk Simulator
* Executes thousands of bootstrap historical return and stochastic simulations using Geometric Brownian Motion (GBM).
* Projects future asset trajectories, calculating distinct statistical horizons:
  * **Weak Case (5th Percentile)**
  * **Median Case (50th Percentile)**
  * **Strong Case (95th Percentile)**

### 3. 📄 Statutory Filing Search (BM25 RAG)
* Instantaneous lexical search across corporate annual reports, management discussions, and financial disclosures.
* Ranks and surfaces exact management quotes and disclosures with computed relevance scoring.

---

## 🛠️ Local Development & Quickstart

Get Finora running locally in under two minutes using Docker Compose:

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
* Git installed.

### Installation & Launch

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/anushkaaa26/FINORA-Multi-Agent-Financial-Decision-Intelligence-Platform.git](https://github.com/anushkaaa26/FINORA-Multi-Agent-Financial-Decision-Intelligence-Platform.git)
   cd FINORA-Multi-Agent-Financial-Decision-Intelligence-Platform
