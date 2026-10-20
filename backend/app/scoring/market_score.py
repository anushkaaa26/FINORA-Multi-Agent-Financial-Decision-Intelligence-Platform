from pydantic import BaseModel, Field
from app.schemas.state import Signal


class MarketScoreResult(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0)
    signals: list[Signal]


def _map_piecewise(val: float, points: list[tuple[float, float]]) -> float:
    if val <= points[0][0]:
        return float(points[0][1])
    if val >= points[-1][0]:
        return float(points[-1][1])

    for i in range(len(points) - 1):
        x0, y0 = points[i]
        x1, y1 = points[i + 1]
        if x0 <= val <= x1:
            slope = (y1 - y0) / (x1 - x0)
            return float(y0 + slope * (val - x0))
    return float(points[-1][1])


def compute_market_score(
    price: float,
    sma_50: float,
    sma_200: float,
    stock_12m_ret: float,
    nifty_12m_ret: float,
    rsi_14: float,
    macd_hist: float,
    macd_hist_slope: float,
    vol_20d_avg: float,
    vol_100d_avg: float,
    vol_1y: float,
    vol_3y: float,
) -> MarketScoreResult:
    signals: list[Signal] = []

    # 1. Trend
    if price > sma_200 and sma_50 > sma_200:
        trend_score = 100.0
        trend_dir = "bullish"
    elif price < sma_200 and sma_50 < sma_200:
        trend_score = 0.0
        trend_dir = "bearish"
    else:
        trend_score = 50.0
        trend_dir = "neutral"

    signals.append(
        Signal(
            name="trend_alignment",
            raw_value=1.0 if trend_score == 100 else (0.0 if trend_score == 0 else 0.5),
            mapped_score=trend_score,
            weight=30.0,
            direction=trend_dir,
        )
    )

    # 2. Momentum
    spread = stock_12m_ret - nifty_12m_ret
    mom_score = _map_piecewise(spread, [(-0.20, 0.0), (0.0, 50.0), (0.20, 100.0)])
    signals.append(
        Signal(
            name="relative_momentum_12m",
            raw_value=round(spread, 4),
            mapped_score=round(mom_score, 2),
            weight=25.0,
            direction="bullish" if spread > 0.02 else ("bearish" if spread < -0.02 else "neutral"),
        )
    )

    # 3. RSI 14
    if rsi_14 <= 50:
        rsi_score = _map_piecewise(rsi_14, [(20.0, 0.0), (30.0, 50.0), (40.0, 100.0), (50.0, 100.0)])
    else:
        rsi_score = _map_piecewise(rsi_14, [(50.0, 100.0), (60.0, 100.0), (70.0, 50.0), (80.0, 0.0)])

    signals.append(
        Signal(
            name="rsi_14",
            raw_value=round(rsi_14, 2),
            mapped_score=round(rsi_score, 2),
            weight=15.0,
            direction="neutral" if (40 <= rsi_14 <= 60) else ("overbought" if rsi_14 > 60 else "oversold"),
        )
    )

    # 4. MACD
    if macd_hist > 0 and macd_hist_slope > 0:
        macd_score = 100.0
        macd_dir = "bullish"
    elif macd_hist < 0 and macd_hist_slope < 0:
        macd_score = 0.0
        macd_dir = "bearish"
    else:
        macd_score = 50.0
        macd_dir = "neutral"

    signals.append(
        Signal(
            name="macd_momentum",
            raw_value=round(macd_hist, 4),
            mapped_score=macd_score,
            weight=15.0,
            direction=macd_dir,
        )
    )

    # 5. Volume Trend
    vol_ratio = vol_20d_avg / vol_100d_avg if vol_100d_avg > 0 else 1.0
    vol_score = _map_piecewise(vol_ratio, [(0.8, 0.0), (1.0, 50.0), (1.3, 100.0)])
    signals.append(
        Signal(
            name="volume_trend",
            raw_value=round(vol_ratio, 3),
            mapped_score=round(vol_score, 2),
            weight=5.0,
            direction="bullish" if vol_ratio >= 1.05 else ("bearish" if vol_ratio <= 0.95 else "neutral"),
        )
    )

    # 6. Volatility Regime
    vol_regime = vol_1y / vol_3y if vol_3y > 0 else 1.0
    vol_regime_score = _map_piecewise(vol_regime, [(0.7, 100.0), (1.0, 60.0), (1.4, 0.0)])
    signals.append(
        Signal(
            name="volatility_regime",
            raw_value=round(vol_regime, 3),
            mapped_score=round(vol_regime_score, 2),
            weight=10.0,
            direction="low_vol" if vol_regime < 1.0 else "expanding_vol",
        )
    )

    total_weight = sum(s.weight for s in signals)
    weighted_score = sum(s.mapped_score * s.weight for s in signals) / total_weight

    return MarketScoreResult(score=round(weighted_score, 2), signals=signals)