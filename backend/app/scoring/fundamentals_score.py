from pydantic import BaseModel, Field
from app.schemas.state import Signal
from app.scoring.market_score import _map_piecewise


class FundamentalsScoreResult(BaseModel):
    score: float = Field(..., ge=0.0, le=100.0)
    signals: list[Signal]


def compute_fundamentals_score(
    pe_ratio: float,
    pb_ratio: float,
    roe: float,
    net_margin: float,
    debt_to_equity: float,
    revenue_cagr_3y: float,
) -> FundamentalsScoreResult:
    signals: list[Signal] = []

    if pe_ratio <= 0:
        pe_score = 0.0
    else:
        pe_score = _map_piecewise(pe_ratio, [(10.0, 100.0), (20.0, 60.0), (35.0, 0.0)])
    signals.append(
        Signal(
            name="pe_valuation",
            raw_value=round(pe_ratio, 2),
            mapped_score=round(pe_score, 2),
            weight=20.0,
            direction="undervalued" if 0 < pe_ratio < 18 else "elevated",
        )
    )

    pb_score = _map_piecewise(pb_ratio, [(1.0, 100.0), (3.0, 60.0), (6.0, 0.0)])
    signals.append(
        Signal(
            name="pb_valuation",
            raw_value=round(pb_ratio, 2),
            mapped_score=round(pb_score, 2),
            weight=10.0,
            direction="attractive" if pb_ratio <= 2.5 else "premium",
        )
    )

    roe_score = _map_piecewise(roe, [(0.05, 0.0), (0.15, 70.0), (0.25, 100.0)])
    signals.append(
        Signal(
            name="return_on_equity",
            raw_value=round(roe, 4),
            mapped_score=round(roe_score, 2),
            weight=20.0,
            direction="strong" if roe >= 0.15 else "weak",
        )
    )

    margin_score = _map_piecewise(net_margin, [(0.02, 0.0), (0.10, 60.0), (0.20, 100.0)])
    signals.append(
        Signal(
            name="net_profit_margin",
            raw_value=round(net_margin, 4),
            mapped_score=round(margin_score, 2),
            weight=20.0,
            direction="healthy" if net_margin >= 0.10 else "compressed",
        )
    )

    de_score = _map_piecewise(debt_to_equity, [(0.3, 100.0), (1.0, 60.0), (2.5, 0.0)])
    signals.append(
        Signal(
            name="debt_to_equity",
            raw_value=round(debt_to_equity, 2),
            mapped_score=round(de_score, 2),
            weight=15.0,
            direction="low_leverage" if debt_to_equity < 0.8 else "leveraged",
        )
    )

    cagr_score = _map_piecewise(revenue_cagr_3y, [(-0.05, 0.0), (0.08, 60.0), (0.20, 100.0)])
    signals.append(
        Signal(
            name="revenue_growth_cagr",
            raw_value=round(revenue_cagr_3y, 4),
            mapped_score=round(cagr_score, 2),
            weight=15.0,
            direction="growing" if revenue_cagr_3y >= 0.08 else "stagnant",
        )
    )

    total_weight = sum(s.weight for s in signals)
    weighted_score = sum(s.mapped_score * s.weight for s in signals) / total_weight

    return FundamentalsScoreResult(score=round(weighted_score, 2), signals=signals)