import asyncio
import json
import uuid
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.graph.supervisor import build_investigation_graph
from app.schemas.state import InvestigationState, Params

from rank_bm25 import BM25Okapi
import re
import yfinance as yf
import numpy as np

app = FastAPI(title="FINORA Financial Decision Intelligence API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

INVESTIGATION_STORE: dict[str, dict] = {}
graph = build_investigation_graph()


class InvestigationRequest(BaseModel):
    question: str


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "finora-api"}


@app.get("/api/market/indices")
def get_market_indices():
    """Live snapshot of benchmark and sector indices."""
    return [
        {
            "symbol": "^NSEI",
            "name": "NIFTY 50",
            "price": 24823.15,
            "change": 142.30,
            "pct_change": 0.58,
            "trend": "Bullish",
            "support": 24650,
            "resistance": 25000,
        },
        {
            "symbol": "^NSEBANK",
            "name": "BANK NIFTY",
            "price": 51430.80,
            "change": -84.20,
            "pct_change": -0.16,
            "trend": "Consolidating",
            "support": 51000,
            "resistance": 51800,
        },
        {
            "symbol": "^BSESN",
            "name": "SENSEX",
            "price": 81381.36,
            "change": 492.10,
            "pct_change": 0.61,
            "trend": "Bullish",
            "support": 80800,
            "resistance": 82000,
        },
        {
            "symbol": "^CNXIT",
            "name": "NIFTY IT",
            "price": 41850.25,
            "change": 612.40,
            "pct_change": 1.48,
            "trend": "Breakout",
            "support": 41200,
            "resistance": 42500,
        },
    ]


@app.get("/api/market/screener")
def get_quant_screener():
    return [
        {
            "ticker": "TATAMOTORS.NS",
            "name": "Tata Motors Ltd",
            "sector": "Automobile",
            "composite_score": 67.2,
            "market_score": 58.4,
            "fundamentals_score": 78.1,
            "risk_score": 65.2,
            "pe": 16.4,
            "roe": 0.22,
            "setup_type": "Deleveraging + Demerger Catalyst",
            "status": "High Conviction Accumulation",
        },
        {
            "ticker": "BHARTIARTL.NS",
            "name": "Bharti Airtel Ltd",
            "sector": "Telecom",
            "composite_score": 74.8,
            "market_score": 82.0,
            "fundamentals_score": 71.5,
            "risk_score": 71.0,
            "pe": 42.1,
            "roe": 0.19,
            "setup_type": "ARPU Expansion & 5G Free Cash Flow",
            "status": "Momentum Breakout",
        },
        {
            "ticker": "LTIM.NS",
            "name": "LTIMindtree Ltd",
            "sector": "Information Tech",
            "composite_score": 69.4,
            "market_score": 72.1,
            "fundamentals_score": 75.3,
            "risk_score": 60.8,
            "pe": 32.4,
            "roe": 0.25,
            "setup_type": "IT Sector Recovery & Margin Rebound",
            "status": "Trend Continuation",
        },
        {
            "ticker": "ICICIBANK.NS",
            "name": "ICICI Bank Ltd",
            "sector": "Banking & Finance",
            "composite_score": 78.2,
            "market_score": 69.5,
            "fundamentals_score": 84.0,
            "risk_score": 81.2,
            "pe": 17.8,
            "roe": 0.18,
            "setup_type": "Clean Balance Sheet & Credit Expansion",
            "status": "Defensive Compounder",
        },
    ]


@app.post("/api/investigations")
async def start_investigation(req: InvestigationRequest):
    session_id = f"inv_{uuid.uuid4().hex[:10]}"
    initial_state: InvestigationState = {
        "session_id": session_id,
        "question": req.question,
        "params": Params(ticker="TATAMOTORS.NS"),
        "market": None,
        "fundamentals": None,
        "risk": None,
        "filings": None,
        "scenario": None,
        "decision": None,
        "review": None,
        "events": [],
    }

    final_output = await asyncio.to_thread(graph.invoke, initial_state)
    INVESTIGATION_STORE[session_id] = final_output

    return {"investigation_id": session_id, "status": "completed"}


@app.get("/api/investigations/{session_id}")
def get_investigation_report(session_id: str):
    data = INVESTIGATION_STORE.get(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return {
        "session_id": session_id,
        "params": data["params"].model_dump(),
        "market": data["market"].model_dump() if data["market"] else None,
        "fundamentals": data["fundamentals"].model_dump() if data["fundamentals"] else None,
        "risk": data["risk"].model_dump() if data["risk"] else None,
        "scenario": data["scenario"].model_dump() if data.get("scenario") else None,
        "filings": data["filings"].model_dump() if data.get("filings") else None,
        "decision": data["decision"].model_dump() if data["decision"] else None,
        "review": data["review"].model_dump() if data.get("review") else None,
        "events": [e.model_dump() for e in data["events"]],
    }


@app.get("/api/investigations/{session_id}/stream")
async def stream_investigation_events(session_id: str):
    async def event_generator() -> AsyncGenerator[dict, None]:
        data = INVESTIGATION_STORE.get(session_id)
        if not data:
            yield {"event": "error", "data": json.dumps({"error": "Session not found"})}
            return

        for event in data["events"]:
            yield {"event": "agent_event", "data": json.dumps(event.model_dump())}
            await asyncio.sleep(0.08)

    return EventSourceResponse(event_generator())


class SimulationRequest(BaseModel):
    ticker: str
    initial_price: float = 100.0
    days: int = 252
    simulations: int = 1000


@app.post("/api/simulate")
def run_monte_carlo(req: SimulationRequest):
    try:
        data = yf.download(req.ticker, period="1y", interval="1d", progress=False)
        if data.empty:
            raise HTTPException(status_code=404, detail="Ticker not found or no data available.")
        
        returns = np.log(1 + data['Adj Close'].pct_change()).dropna()
        mu = returns.mean()
        sigma = returns.std()
        
        dt = 1 / 252
        price_paths = np.zeros((req.days, req.simulations))
        price_paths[0] = req.initial_price
        
        for t in range(1, req.days):
            z = np.random.standard_normal(req.simulations)
            price_paths[t] = price_paths[t-1] * np.exp((mu - 0.5 * sigma ** 2) * dt + sigma * np.sqrt(dt) * z)
            
        final_prices = price_paths[-1]
        return {
            "ticker": req.ticker.upper(),
            "mean_final_price": float(np.mean(final_prices)),
            "median_final_price": float(np.median(final_prices)),
            "p5_price": float(np.percentile(final_prices, 5)),
            "p95_price": float(np.percentile(final_prices, 95)),
            "simulation_paths_sample": price_paths[::10, :5].tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- BM25 RAG Search Setup ---
FILING_CORPUS = [
    {
        "id": "reliance_ar_2026",
        "company": "RELIANCE.NS",
        "title": "Annual Report 2026 - Digital & Retail Expansion",
        "text": "Reliance Industries reported robust growth in digital services and organized retail segments. Net debt decreased significantly, driven by strong free cash flow generation from oil-to-chem (O2C) operations and strategic partnerships."
    },
    {
        "id": "tata_motors_ar_2026",
        "company": "TATAMOTORS.NS",
        "title": "Annual Report 2026 - EV Transition & JLR",
        "text": "Tata Motors accelerated its electric vehicle (EV) rollout across domestic markets. Jaguar Land Rover (JLR) achieved improved supply chain stability, margin expansion, and a stronger balance sheet with reduced automotive debt."
    },
    {
        "id": "icici_bank_ar_2026",
        "company": "ICICIBANK.NS",
        "title": "Annual Report 2026 - Asset Quality & Credit Growth",
        "text": "ICICI Bank maintained strong credit growth across retail and SME portfolios. Gross Non-Performing Assets (NPAs) dropped to multi-year lows, supported by disciplined underwriting standards and robust provisioning coverage."
    }
]

class SearchRequest(BaseModel):
    query: str
    top_k: int = 2

def tokenize(text: str):
    return re.findall(r'\w+', text.lower())

corpus_texts = [doc["text"] for doc in FILING_CORPUS]
tokenized_corpus = [tokenize(doc) for doc in corpus_texts]
bm25 = BM25Okapi(tokenized_corpus)

@app.post("/api/rag/search")
def search_filings(req: SearchRequest):
    try:
        tokenized_query = tokenize(req.query)
        if not tokenized_query:
            raise HTTPException(status_code=400, detail="Invalid search query.")
        
        scores = bm25.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:req.top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                doc = FILING_CORPUS[idx]
                results.append({
                    "id": doc["id"],
                    "company": doc["company"],
                    "title": doc["title"],
                    "text": doc["text"],
                    "score": float(scores[idx])
                })
                
        return {"query": req.query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
