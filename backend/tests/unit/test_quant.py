import numpy as np
import pandas as pd
import pytest
from app.quant.metrics import (
    calculate_annualized_volatility,
    calculate_beta,
    calculate_daily_returns,
    calculate_max_drawdown,
    calculate_rsi,
    calculate_sharpe_ratio,
    calculate_var,
)
from app.scoring.market_score import compute_market_score


def test_calculate_daily_returns():
    prices = pd.Series([100.0, 105.0, 102.9])
    returns = calculate_daily_returns(prices)
    assert len(returns) == 2
    assert pytest.approx(returns.iloc[0], rel=1e-3) == 0.05
    assert pytest.approx(returns.iloc[1], rel=1e-3) == -0.02


def test_calculate_rsi_edge_cases():
    # Monotonically increasing prices -> RSI must reach 100
    prices_up = pd.Series([float(i) for i in range(1, 30)])
    assert calculate_rsi(prices_up, window=14) == 100.0

    # Monotonically decreasing prices -> RSI must reach 0
    prices_down = pd.Series([float(100 - i) for i in range(30)])
    assert calculate_rsi(prices_down, window=14) == 0.0


def test_calculate_max_drawdown():
    # Peak at 100, drops to 70, recovers to 90
    prices = pd.Series([80.0, 100.0, 90.0, 70.0, 90.0])
    mdd = calculate_max_drawdown(prices)
    assert pytest.approx(mdd, rel=1e-3) == -0.30


def test_calculate_beta():
    # Benchmark returns
    bench = pd.Series([0.01, -0.02, 0.015, -0.01, 0.005] * 10)
    # Stock moves exactly 1.5x of benchmark
    stock = bench * 1.5
    b = calculate_beta(stock, bench)
    assert pytest.approx(b, rel=1e-2) == 1.5


def test_market_scoring_weights_sum_to_100():
    res = compute_market_score(
        price=1050.0,
        sma_50=1020.0,
        sma_200=980.0,
        stock_12m_ret=0.25,
        nifty_12m_ret=0.10,
        rsi_14=55.0,
        macd_hist=1.2,
        macd_hist_slope=0.3,
        vol_20d_avg=1200000.0,
        vol_100d_avg=1000000.0,
        vol_1y=0.22,
        vol_3y=0.25,
    )
    total_weights = sum(s.weight for s in res.signals)
    assert total_weights == 100.0
    assert 0.0 <= res.score <= 100.0