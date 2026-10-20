import pytest
import pandas as pd
import numpy as np

from app.quant.metrics import calculate_rsi, calculate_macd, calculate_sma
from app.scoring.market_score import compute_market_score
from app.scoring.fundamentals_score import compute_fundamentals_score
from app.scoring.risk_score import compute_risk_score
from app.guardrails.grounding import validate_language_compliance, validate_number_grounding
from app.quant.scenario import run_monte_carlo_simulation


def test_rsi_bounds():
    prices = pd.Series([100.0, 102.0, 101.5, 104.0, 106.0, 105.0, 107.0, 108.0, 110.0, 109.0, 111.0, 112.0, 115.0, 114.0, 116.0, 118.0])
    rsi = calculate_rsi(prices, 14)
    assert 0.0 <= rsi <= 100.0


def test_market_score_deterministic_invariance():
    # Calling the math engine twice with identical values must return identical scores
    args = dict(
        price=950.0,
        sma_50=920.0,
        sma_200=880.0,
        stock_12m_ret=0.25,
        nifty_12m_ret=0.15,
        rsi_14=55.0,
        macd_hist=2.5,
        macd_hist_slope=0.4,
        vol_20d_avg=1500000.0,
        vol_100d_avg=1400000.0,
        vol_1y=0.22,
        vol_3y=0.24,
    )
    res1 = compute_market_score(**args)
    res2 = compute_market_score(**args)
    assert res1.score == res2.score
    assert len(res1.signals) == len(res2.signals)


def test_language_compliance_guardrail():
    dirty_text = "You should BUY this stock now, guaranteed 20% upside."
    violations = validate_language_compliance(dirty_text)
    assert len(violations) >= 2
    assert any("buy" in v for v in violations)
    assert any("guaranteed" in v for v in violations)

    clean_text = "Return on equity expanded to 22.0% while debt-to-equity ratio stabilized at 1.25."
    clean_violations = validate_language_compliance(clean_text)
    assert len(clean_violations) == 0


def test_number_grounding_guardrail():
    allowed_numbers = {22.0, 1.25, 67.2, 500000.0}
    clean_text = "Return on equity was 22.0% and debt to equity reached 1.25."
    violations = validate_number_grounding(clean_text, allowed_numbers)
    assert len(violations) == 0

    hallucinated_text = "Net profit margin unexpectedly surged by 47.8% this quarter."
    hallucination_violations = validate_number_grounding(hallucinated_text, allowed_numbers)
    assert len(hallucination_violations) == 1
    assert "47.8" in hallucination_violations[0]


def test_monte_carlo_percentile_order():
    np.random.seed(42)
    fake_returns = pd.Series(np.random.normal(0.0005, 0.015, size=500))
    sim = run_monte_carlo_simulation(fake_returns, amount_inr=500000.0, horizon_months=12)
    assert sim.percentile_5 < sim.percentile_50 < sim.percentile_95
