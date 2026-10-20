import numpy as np
import pandas as pd
from app.quant.metrics import (
    calculate_annualized_volatility,
    calculate_beta,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_var,
)


def compute_risk_metrics(
    stock_prices: pd.Series,
    benchmark_prices: pd.Series,
    horizon_days: int = 21,
    risk_free_rate: float = 0.07,
) -> dict[str, float]:
    """Computes all quantitative risk indicators."""
    stock_returns = stock_prices.pct_change().dropna()
    bench_returns = benchmark_prices.pct_change().dropna()

    var_95 = calculate_var(stock_returns, confidence_level=0.95, horizon_days=horizon_days)
    sharpe = calculate_sharpe_ratio(stock_returns, risk_free_rate=risk_free_rate)
    mdd = calculate_max_drawdown(stock_prices)
    beta = calculate_beta(stock_returns, bench_returns)
    vol_ann = calculate_annualized_volatility(stock_returns)

    return {
        "var_95": float(var_95),
        "sharpe_ratio": float(sharpe),
        "max_drawdown": float(mdd),
        "beta": float(beta),
        "annualized_volatility": float(vol_ann),
    }