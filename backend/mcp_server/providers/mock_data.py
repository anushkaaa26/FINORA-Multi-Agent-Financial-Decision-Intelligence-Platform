# mcp_server/providers/mock_data.py
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


def generate_synthetic_ohlcv(
    ticker: str,
    days: int = 756,  # ~3 years of trading days
    base_price: float = 950.0,
    seed: int = 42,
) -> list[dict]:
    """Generates realistic deterministic OHLCV data for offline development & tests."""
    np.random.seed(seed if ticker != "^NSEI" else seed + 1)
    if ticker == "^NSEI":
        base_price = 24000.0

    end_date = datetime.now()
    dates = []
    curr = end_date - timedelta(days=int(days * 1.5))
    while len(dates) < days:
        if curr.weekday() < 5:  # Mon-Fri
            dates.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)

    # Random walk with slight upward drift
    daily_returns = np.random.normal(0.0005, 0.015, size=days)
    price_series = base_price * np.exp(np.cumsum(daily_returns))

    records = []
    for i, date_str in enumerate(dates):
        close_p = float(price_series[i])
        noise = close_p * 0.008
        open_p = close_p + np.random.uniform(-noise, noise)
        high_p = max(open_p, close_p) + np.random.uniform(0, noise)
        low_p = min(open_p, close_p) - np.random.uniform(0, noise)
        volume = float(np.random.randint(1_000_000, 10_000_000) if ticker != "^NSEI" else 250_000_000)

        records.append({
            "date": date_str,
            "open": round(open_p, 2),
            "high": round(high_p, 2),
            "low": round(low_p, 2),
            "close": round(close_p, 2),
            "volume": volume,
        })
    return records