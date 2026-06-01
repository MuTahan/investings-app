"""Deterministic fundamental scoring from provider fundamentals."""

from __future__ import annotations

from dataclasses import dataclass

from app.providers.base import Fundamentals


def to_ratio(value: float | None) -> float | None:
    """Normalize a value that may be a percent (e.g. 30) or a ratio (0.30) to a ratio."""
    if value is None:
        return None
    return value / 100 if abs(value) > 1.5 else value


@dataclass
class FundamentalScore:
    score: float
    assessment: str
    confidence: float
    evidence: dict


def _assess(score: float) -> str:
    if score >= 70:
        return "High quality"
    if score >= 55:
        return "Solid"
    if score >= 45:
        return "Mixed"
    return "Weak"


def compute(f: Fundamentals | None, instrument_type: str) -> FundamentalScore:
    if f is None:
        return FundamentalScore(50.0, "Unknown (no data)", 35.0, {})

    if instrument_type == "etf":
        # ETFs: treat as diversified market exposure; reward low cost when known.
        score = 55.0
        expense = f.expense_ratio
        if expense is not None:
            score += 5 if expense < 0.002 else (-3 if expense > 0.006 else 0)
        evidence = {"expense_ratio": expense, "type": "etf"}
        return FundamentalScore(
            round(min(100, max(0, score)), 2), "Diversified ETF", 55.0, evidence
        )

    op_margin = to_ratio(f.op_margin)
    gross_margin = to_ratio(f.gross_margin)
    revenue_growth = to_ratio(f.revenue_growth)
    eps_growth = to_ratio(f.eps_growth)
    pe = f.pe

    score = 50.0
    present = 0

    if op_margin is not None:
        present += 1
        score += 12 if op_margin > 0.2 else 6 if op_margin > 0.1 else -12 if op_margin < 0 else 0
    if revenue_growth is not None:
        present += 1
        score += (
            12
            if revenue_growth > 0.15
            else 6 if revenue_growth > 0.05 else -12 if revenue_growth < 0 else 0
        )
    if eps_growth is not None:
        present += 1
        score += 10 if eps_growth > 0.15 else 5 if eps_growth > 0 else -10 if eps_growth < 0 else 0
    if pe is not None:
        present += 1
        if pe <= 0:
            score -= 6
        elif pe <= 25:
            score += 6
        elif pe > 40:
            score -= 6
    if gross_margin is not None and gross_margin > 0.4:
        score += 5

    score = round(min(100, max(0, score)), 2)
    confidence = round(40 + present * 11, 2)  # more fields -> higher confidence
    evidence = {
        "pe": pe,
        "op_margin": op_margin,
        "gross_margin": gross_margin,
        "revenue_growth": revenue_growth,
        "eps_growth": eps_growth,
    }
    return FundamentalScore(score, _assess(score), confidence, evidence)
