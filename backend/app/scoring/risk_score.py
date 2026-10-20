from pydantic import BaseModel, Field
from app.schemas.state import Signal
from app.scoring.market_score import _map_piecewise


class RiskScoreResult(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0)
    signals: list[Signal]


def compute_risk_score(
    var_95: float,
    sharpe_ratio: float,
    max_drawdown: float,
    beta: float,
    annualized_volatility: float,
) -> RiskScoreResult:
    signals: list[Signal] = []

    var_score = _map_piecewise(var_95, [(0.10, 100.0), (0.25, 50.0), (0.45, 0.0)])
    signals.append(
        Signal(
            name="value_at_risk_95",
            raw_value=round(var_95, 4),
            mapped_score=round(var_score, 2),
            weight=25.0,
            direction="contained" if var_95 <= 0.20 else "elevated_risk",
        )
    )

    sharpe_score = _map_piecewise(sharpe_ratio, [(0.0, 0.0), (0.5, 60.0), (1.5, 100.0)])
    signals.append(
        Signal(
            name="sharpe_ratio",
            raw_value=round(sharpe_ratio, 3),
            mapped_score=round(sharpe_score, 2),
            weight=20.0,
            direction="efficient" if sharpe_ratio >= 0.8 else "inefficient",
        )
    )

    mdd_score = _map_piecewise(max_drawdown, [(-0.70, 0.0), (-0.40, 50.0), (-0.15, 100.0)])
    signals.append(
        Signal(
            name="max_drawdown_3y",
            raw_value=round(max_drawdown, 4),
            mapped_score=round(mdd_score, 2),
            weight=25.0,
            direction="resilient" if max_drawdown >= -0.30 else "severe_drawdown",
        )
    )

    if beta <= 1.0:
        beta_score = _map_piecewise(beta, [(0.5, 80.0), (0.8, 100.0), (1.0, 100.0)])
    else:
        beta_score = _map_piecewise(beta, [(1.0, 100.0), (1.3, 60.0), (1.8, 0.0)])

    signals.append(
        Signal(
            name="market_beta",
            raw_value=round(beta, 3),
            mapped_score=round(beta_score, 2),
            weight=15.0,
            direction="defensive" if beta <= 1.0 else "high_beta",
        )
    )

    vol_score = _map_piecewise(annualized_volatility, [(0.20, 100.0), (0.35, 60.0), (0.60, 0.0)])
    signals.append(
        Signal(
            name="annualized_volatility",
            raw_value=round(annualized_volatility, 4),
            mapped_score=round(vol_score, 2),
            weight=15.0,
            direction="stable" if annualized_volatility <= 0.25 else "volatile",
        )
    )

    total_weight = sum(s.weight for s in signals)
    weighted_score = sum(s.mapped_score * s.weight for s in signals) / total_weight

    return RiskScoreResult(score=round(weighted_score, 2), signals=signals)