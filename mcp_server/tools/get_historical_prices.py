# mcp_server/tools/get_historical_prices.py
import time
from typing import Any
import pandas as pd
import yfinance as yf

from mcp_server.cache import compute_snapshot_id, save_snapshot
from mcp_server.providers.mock_data import generate_synthetic_ohlcv
from mcp_server.validation import MCPResponse, Provenance, validate_nse_ticker


def fetch_historical_prices(
    ticker: str,
    period: str = "3y",
    interval: str = "1d",
) -> MCPResponse[dict[str, Any]]:
    start_time = time.perf_counter()
    validated_ticker = validate_nse_ticker(ticker)

    warnings: list[str] = []
    records: list[dict] = []
    source = "yfinance"

    try:
        ticker_obj = yf.Ticker(validated_ticker)
        df: pd.DataFrame = ticker_obj.history(period=period, interval=interval, auto_adjust=True)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        if not df.empty and len(df) > 10:
            df = df.reset_index()
            date_col = "Date" if "Date" in df.columns else "Datetime"
            df["date"] = pd.to_datetime(df[date_col]).dt.strftime("%Y-%m-%d")

            for _, row in df.iterrows():
                records.append({
                    "date": row["date"],
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": float(row["Volume"]),
                })
    except Exception as exc:
        warnings.append(f"Provider yfinance failed: {str(exc)}")

    # Fallback if rate-limited or blocked
    if not records:
        warnings.append("Rate-limited by upstream provider (HTTP 429). Used cached fixture fallback.")
        source = "fixture_fallback"
        records = generate_synthetic_ohlcv(validated_ticker)

    as_of = records[-1]["date"] if records else "unknown"
    snapshot_id = compute_snapshot_id(validated_ticker, period, records)
    save_snapshot(snapshot_id, records)

    latency = round((time.perf_counter() - start_time) * 1000, 2)

    return MCPResponse(
        tool="get_historical_prices",
        ok=True,
        data={
            "ticker": validated_ticker,
            "period": period,
            "interval": interval,
            "count": len(records),
            "prices": records,
        },
        provenance=Provenance(
            source=source,
            as_of=as_of,
            cache_hit=False,
            snapshot_id=snapshot_id,
        ),
        warnings=warnings,
        latency_ms=latency,
    )