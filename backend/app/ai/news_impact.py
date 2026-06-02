"""Deterministic news-impact scoring.

A cheap, reproducible per-headline impact signal (keyword-based), shared by the
News & Sentiment agent and the news-workflow service. Real NLP/LLM scoring can be added
behind the same `score_headline` shape later; this keeps the workflow working with $0
data and in deterministic mode.
"""

from __future__ import annotations

_BULLISH = {
    "beat",
    "beats",
    "surge",
    "surges",
    "jump",
    "jumps",
    "upgrade",
    "upgraded",
    "record",
    "growth",
    "raises",
    "raised",
    "tops",
    "soars",
    "gains",
    "rally",
    "outperform",
    "wins",
    "approval",
    "approved",
    "expands",
    "partnership",
    "buyback",
    "dividend",
}
_BEARISH = {
    "miss",
    "misses",
    "plunge",
    "plunges",
    "downgrade",
    "downgraded",
    "cut",
    "cuts",
    "lawsuit",
    "probe",
    "falls",
    "drops",
    "warns",
    "warning",
    "slump",
    "recall",
    "fraud",
    "halts",
    "investigation",
    "layoffs",
    "bankruptcy",
    "delays",
    "guidance",
    "weak",
}


def score_headline(headline: str) -> int:
    """Impact score in [-100, 100]; +ve bullish, -ve bearish, 0 neutral."""
    words = {w.strip(".,!?:;'\"()").lower() for w in headline.split()}
    bull = len(words & _BULLISH)
    bear = len(words & _BEARISH)
    return max(-100, min(100, (bull - bear) * 30))


def label(score: int | float) -> str:
    if score >= 15:
        return "bullish"
    if score <= -15:
        return "bearish"
    return "neutral"
