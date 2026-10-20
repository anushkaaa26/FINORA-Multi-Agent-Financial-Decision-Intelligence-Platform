import json
import pandas as pd

from app.quant.metrics import (
    calculate_annualized_volatility,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
)
from app.scoring.market_score import compute_market_score
from mcp_server.tools.get_historical_prices import fetch_historical_prices


def main():
    ticker = "TATAMOTORS.NS"
    benchmark = "^NSEI"

    print(f"Fetching historical prices for {ticker}...")
    stock_res = fetch_historical_prices(ticker=ticker, period="3y")
    if not stock_res.ok or not stock_res.data:
        print(f"Error fetching {ticker}: {stock_res.warnings}")
        return

    print(f"Fetching benchmark prices for {benchmark}...")
    bench_res = fetch_historical_prices(ticker=benchmark, period="3y")
    if not bench_res.ok or not bench_res.data:
        print(f"Error fetching benchmark: {bench_res.warnings}")
        return

    stock_df = pd.DataFrame(stock_res.data["prices"])
    stock_df["date"] = pd.to_datetime(stock_df["date"])
    stock_df.set_index("date", inplace=True)
    stock_prices = stock_df["close"]
    stock_volumes = stock_df["volume"]

    bench_df = pd.DataFrame(bench_res.data["prices"])
    bench_df["date"] = pd.to_datetime(bench_df["date"])
    bench_df.set_index("date", inplace=True)
    bench_prices = bench_df["close"]

    current_price = float(stock_prices.iloc[-1])
    sma_50 = float(calculate_sma(stock_prices, 50).iloc[-1])
    sma_200 = float(calculate_sma(stock_prices, 200).iloc[-1])

    lookback_12m = min(252, len(stock_prices) - 1)
    stock_12m_ret = float((stock_prices.iloc[-1] / stock_prices.iloc[-lookback_12m]) - 1.0)
    bench_12m_ret = float((bench_prices.iloc[-1] / bench_prices.iloc[-lookback_12m]) - 1.0)

    rsi_14 = calculate_rsi(stock_prices, 14)
    macd_vals = calculate_macd(stock_prices)

    vol_20d = float(stock_volumes.rolling(20).mean().iloc[-1])
    vol_100d = float(stock_volumes.rolling(100).mean().iloc[-1])

    stock_daily_returns = stock_prices.pct_change().dropna()
    vol_1y = calculate_annualized_volatility(stock_daily_returns.iloc[-252:])
    vol_3y = calculate_annualized_volatility(stock_daily_returns)

    result = compute_market_score(
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

    print("\n" + "=" * 55)
    print(f"FINORA MARKET SCORE AUDIT: {ticker}")
    print("=" * 55)
    print(f"As of:              {stock_res.provenance.as_of}")
    print(f"Snapshot ID:        {stock_res.provenance.snapshot_id}")
    print(f"Current Price:      INR {current_price:.2f}")
    print(f"Overall Score:      {result.score:.2f} / 100.00")
    print("\nSignal Breakdown:")
    for s in result.signals:
        print(f"  - {s.name:<25} raw: {s.raw_value:>10} | score: {s.mapped_score:>6.1f} | weight: {s.weight:>4.1f}% [{s.direction}]")
    print("=" * 55)


if __name__ == "__main__":
    main()
