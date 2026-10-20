import numpy as np
import pandas as pd
from pydantic import BaseModel


class ScenarioProjection(BaseModel):
    horizon_months: int
    amount_inr: float
    percentile_5: float
    percentile_50: float
    percentile_95: float
    seed: int


def run_monte_carlo_simulation(
    daily_returns: pd.Series,
    amount_inr: float = 500000.0,
    horizon_months: int = 12,
    num_simulations: int = 10000,
    seed: int = 42,
) -> ScenarioProjection:
    np.random.seed(seed)
    trading_days = horizon_months * 21
    clean_returns = daily_returns.dropna().values

    if len(clean_returns) < 30:
        clean_returns = np.random.normal(0.0004, 0.015, size=252)

    sampled_indices = np.random.choice(len(clean_returns), size=(num_simulations, trading_days), replace=True)
    sampled_returns = clean_returns[sampled_indices]

    growth_factors = np.prod(1.0 + sampled_returns, axis=1)
    final_values = amount_inr * growth_factors

    p5 = float(np.percentile(final_values, 5))
    p50 = float(np.percentile(final_values, 50))
    p95 = float(np.percentile(final_values, 95))

    return ScenarioProjection(
        horizon_months=horizon_months,
        amount_inr=amount_inr,
        percentile_5=round(p5, 2),
        percentile_50=round(p50, 2),
        percentile_95=round(p95, 2),
        seed=seed,
    )