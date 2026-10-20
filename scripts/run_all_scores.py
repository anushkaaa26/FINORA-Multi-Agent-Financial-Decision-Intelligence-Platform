# scripts/run_all_scores.py
import sys
from pathlib import Path

# Add backend and root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "backend"))
sys.path.insert(0, str(root_dir))

import numpy as np
import pandas as pd
from app.quant.fundamentals_risk import compute_risk_metrics
from app.quant.metrics import (
    calculate_annualized_volatility,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
)
from app.scoring.fundamentals_score import compute_fundamentals_score
from app.scoring.market_score import compute_market_score
from app.scoring.risk_score import compute_risk_score
from mcp_server.tools.get_company_financials import fetch_company_financials
from mcp_server.tools.get_historical_prices import fetch_historical_prices


def main():
    ticker = "TATAMOTORS.NS"
    benchmark = "^NSEI"

    print(f"--> [MCP] Fetching price data for {ticker} & {benchmark}...")
    stock_res = fetch_historical_prices(ticker=ticker, period="3y")
    bench_res = fetch_historical_prices(ticker=benchmark, period="3y")

    print(f"--> [MCP] Fetching financials data for {ticker}...")
    fin_res = fetch_company_financials(ticker=ticker)

    # 1. Price series setup
    stock_df = pd.DataFrame(stock_res.data["prices"])
    stock_df["date"] = pd.to_datetime(stock_df["date"])
    stock_df.set_index("date", inplace=True)
    stock_prices = stock_df["close"]

    bench_df = pd.DataFrame(bench_res.data["prices"])
    bench_df["date"] = pd.to_datetime(bench_df["date"])
    bench_df.set_index("date", inplace=True)
    bench_prices = bench_df["close"]

    # 2. Market Score computation
    current_price = float(stock_prices.iloc[-1])
    sma_50 = float(calculate_sma(stock_prices, 50).iloc[-1])
    sma_200 = float(calculate_sma(stock_prices, 200).iloc[-1])
    lookback_12m = min(252, len(stock_prices) - 1)
    stock_12m_ret = float((stock_prices.iloc[-1] / stock_prices.iloc[-lookback_12m]) - 1.0)
    bench_12m_ret = float((bench_prices.iloc[-1] / bench_prices.iloc[-lookback_12m]) - 1.0)
    rsi_14 = calculate_rsi(stock_prices, 14)
    macd_vals = calculate_macd(stock_prices)
    vol_20d = float(stock_df["volume"].rolling(20).mean().iloc[-1])
    vol_100d = float(stock_df["volume"].rolling(100).mean().iloc[-1])
    stock_returns = stock_prices.pct_change().dropna()
    vol_1y = calculate_annualized_volatility(stock_returns.iloc[-252:])
    vol_3y = calculate_annualized_volatility(stock_returns)

    market_res = compute_market_score(
        price=current_price,
        sma_50=sma_50,
        sma_200=sma_200,
        stock_12m_ret=stock_12m_ret,
        nifty_12m_ret=bench_12m_ret,
        rsi_14=rsi_14,
        macd_hist=macd_vals["hist"],
        macd_hist_slope=macd_vals["hist_slope"],
        vol_20d_avg=vol_20d,
        vol_100d_avg=vol_100d,
        vol_1y=vol_1y,
        vol_3y=vol_3y,
    )

    # 3. Fundamentals Score computation
    fin_metrics = fin_res.data["metrics"]
    fundamentals_res = compute_fundamentals_score(
        pe_ratio=fin_metrics["pe_ratio"],
        pb_ratio=fin_metrics["pb_ratio"],
        roe=fin_metrics["roe"],
        net_margin=fin_metrics["net_margin"],
        debt_to_equity=fin_metrics["debt_to_equity"],
        revenue_cagr_3y=fin_metrics["revenue_cagr_3y"],
    )

    # 4. Risk Score computation
    risk_metrics = compute_risk_metrics(stock_prices, bench_prices, horizon_days=21)
    risk_res = compute_risk_score(
        var_95=risk_metrics["var_95"],
        sharpe_ratio=risk_metrics["sharpe_ratio"],
        max_drawdown=risk_metrics["max_drawdown"],
        beta=risk_metrics["beta"],
        annualized_volatility=risk_metrics["annualized_volatility"],
    )

    # 5. Evidence Balance (Balanced Profile: 30% Market, 35% Fundamentals, 35% Risk)
    evidence_balance = (
        0.30 * market_res.score + 0.35 * fundamentals_res.score + 0.35 * risk_res.score
    )

    # 6. Confidence formula from build plan
    scores_arr = np.array([market_res.score, fundamentals_res.score, risk_res.score])
    score_std = float(np.std(scores_arr))
    agreement = max(0.0, 1.0 - (score_std / 50.0))
    confidence = 100.0 * 1.0 * agreement * 1.0

    print("\n" + "=" * 60)
    print(f"FINORA COMPREHENSIVE TRI-SCORE REPORT: {ticker}")
    print("=" * 60)
    print(f"Market Score:       {market_res.score:>6.2f} / 100.00")
    print(f"Fundamentals Score: {fundamentals_res.score:>6.2f} / 100.00")
    print(f"Risk Score:         {risk_res.score:>6.2f} / 100.00 (higher = lower risk)")
    print("-" * 60)
    print(f"EVIDENCE BALANCE:   {evidence_balance:>6.2f} / 100.00")
    print(f"CONFIDENCE:         {confidence:>6.2f} % (score agreement: {agreement:.2f})")
    print("=" * 60)
    print(f"Tool Snapshots:     [Prices: {stock_res.provenance.snapshot_id}]")
    print(f"                    [Financials: {fin_res.provenance.snapshot_id}]")
    print("=" * 60)


if __name__ == "__main__":
    main()