"""Deterministic risk assessment: volatility, concentration, valuation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.ai.base import PortfolioSnapshot
from app.domain.enums import RiskLevel
from app.providers.base import Candle, Fundamentals


def daily_returns(closes: list[float]) -> list[float]:
    returns = []
    for i in range(1, len(closes)):
        if closes[i - 1]:
            returns.append(closes[i] / closes[i - 1] - 1)
    return returns


def annualized_volatility(candles: list[Candle]) -> float | None:
    closes = [c.c for c in candles]
    rets = daily_returns(closes)
    if len(rets) < 5:
        return None
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
    return math.sqrt(var) * math.sqrt(252)


@dataclass
class RiskAssessment:
    level: RiskLevel
    confidence: float
    warnings: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)


def compute(
    *,
    candles: list[Candle],
    fundamentals: Fundamentals | None,
    portfolio: PortfolioSnapshot,
    symbol: str,
    sector: str | None,
    max_position_pct: float | None,
) -> RiskAssessment:
    points = 0
    warnings: list[str] = []

    vol = annualized_volatility(candles)
    if vol is not None:
        if vol > 0.40:
            points += 2
            warnings.append(f"High volatility ({vol * 100:.0f}% annualized)")
        elif vol > 0.25:
            points += 1
            warnings.append(f"Elevated volatility ({vol * 100:.0f}% annualized)")

    pe = fundamentals.pe if fundamentals else None
    if pe is not None and pe > 40:
        points += 1
        warnings.append(f"Rich valuation (P/E {pe:.0f})")

    beta = fundamentals.beta if fundamentals else None
    if beta is not None and beta > 1.5:
        points += 1
        warnings.append(f"High market sensitivity (beta {beta:.1f})")

    # concentration: existing exposure to this instrument's sector
    sector_weight = portfolio.sector_exposure.get(sector or "", 0.0)
    if sector_weight > 0.5:
        points += 2
        warnings.append(f"Concentrated sector exposure ({sector_weight * 100:.0f}% in {sector})")

    existing = portfolio.holds(symbol)
    if existing and max_position_pct is not None and existing.weight * 100 > max_position_pct:
        points += 2
        pos = existing.weight * 100
        warnings.append(f"Position exceeds your max size ({pos:.0f}% > {max_position_pct:.0f}%)")

    if points >= 4:
        level = RiskLevel.HIGH
    elif points >= 2:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW

    confidence = 70.0 if vol is not None else 45.0
    evidence = {
        "volatility": round(vol, 4) if vol is not None else None,
        "pe": pe,
        "beta": beta,
        "sector_exposure": round(sector_weight, 4),
        "points": points,
    }
    return RiskAssessment(level=level, confidence=confidence, warnings=warnings, evidence=evidence)
