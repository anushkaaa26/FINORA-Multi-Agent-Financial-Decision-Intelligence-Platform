
from typing import Literal
import numpy as np
import pandas as pd


def calculate_daily_returns(prices: pd.Series) -> pd.Series:
    """Calculates daily fractional returns: r_t = (P_t / P_{t-1}) - 1."""
    if len(prices) < 2:
        return pd.Series(dtype=float)
    return prices.pct_change().dropna()


def calculate_sma(prices: pd.Series, window: int) -> pd.Series:
    """Computes Simple Moving Average for a given window."""
    return prices.rolling(window=window).mean()


def calculate_rsi(prices: pd.Series, window: int = 14) -> float:
    """
    RSI using Wilder's exponential smoothing method.
    Returns float in range [0.0, 100.0].
    """
    if len(prices) <= window:
        return 50.0  # Neutral fallback when insufficient data

    delta = prices.diff().dropna()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean().iloc[-1]
    avg_loss = loss.ewm(alpha=1.0 / window, min_periods=window, adjust=False).mean().iloc[-1]

    if avg_loss == 0.0:
        return 100.0
    if avg_gain == 0.0:
        return 0.0

    rs = avg_gain / avg_loss
    return float(100.0 - (100.0 / (1.0 + rs)))


def calculate_macd(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> dict[str, float]:
    """
    Computes MACD line, Signal line, and MACD Histogram.
    """
    if len(prices) < slow + signal:
        return {"macd": 0.0, "signal": 0.0, "hist": 0.0, "hist_slope": 0.0}

    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_series = ema_fast - ema_slow
    signal_series = macd_series.ewm(span=signal, adjust=False).mean()
    hist_series = macd_series - signal_series

    hist_slope = (
        float(hist_series.iloc[-1] - hist_series.iloc[-2]) if len(hist_series) >= 2 else 0.0
    )

    return {
        "macd": float(macd_series.iloc[-1]),
        "signal": float(signal_series.iloc[-1]),
        "hist": float(hist_series.iloc[-1]),
        "hist_slope": hist_slope,
    }


def calculate_annualized_volatility(returns: pd.Series, trading_days: int = 252) -> float:
    """Annualized volatility: std(daily_returns) * sqrt(252)."""
    if len(returns) < 2:
        return 0.0
    return float(returns.std(ddof=1) * np.sqrt(trading_days))


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.07,
    trading_days: int = 252,
) -> float:
    """
    Sharpe Ratio = (Annualized Mean Excess Return) / (Annualized Volatility)
    where r_excess = r_daily - (Rf / 252).
    """
    if len(returns) < 2:
        return 0.0
    daily_rf = risk_free_rate / trading_days
    excess_returns = returns - daily_rf
    mean_excess = excess_returns.mean() * trading_days
    vol = calculate_annualized_volatility(returns, trading_days)
    if vol == 0.0:
        return 0.0
    return float(mean_excess / vol)


def calculate_beta(stock_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Beta = Cov(r_stock, r_benchmark) / Var(r_benchmark)."""
    aligned = pd.concat([stock_returns, benchmark_returns], axis=1).dropna()
    if len(aligned) < 10:
        return 1.0  # Default neutral market beta
    cov_matrix = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])
    cov = cov_matrix[0, 1]
    var_bench = cov_matrix[1, 1]
    if var_bench == 0.0:
        return 1.0
    return float(cov / var_bench)


def calculate_var(
    returns: pd.Series,
    confidence_level: float = 0.95,
    horizon_days: int = 21,
    method: Literal["historical"] = "historical",
) -> float:
    """
    Historical Value at Risk over horizon_days:
    VaR_{alpha, h} = - percentile_{1 - alpha}(returns) * sqrt(h)
    Returns positive fractional loss (e.g., 0.12 = 12% VaR).
    """
    if len(returns) < 20:
        return 0.0
    alpha_pct = (1.0 - confidence_level) * 100.0
    cutoff = np.percentile(returns, alpha_pct)
    # Loss magnitude is reported as positive
    var_daily = -cutoff if cutoff < 0 else 0.0
    return float(var_daily * np.sqrt(horizon_days))


def calculate_max_drawdown(prices: pd.Series) -> float:
    """
    Max Drawdown = min_t (P_t / max_{s <= t}(P_s) - 1).
    Returns negative fractional value (e.g. -0.28 = -28%).
    """
    if len(prices) < 2:
        return 0.0
    cummax = prices.cummax()
    drawdowns = (prices / cummax) - 1.0
    return float(drawdowns.min())