from __future__ import annotations

from app.domain.enums import Signal
from app.services.trending_service import TrendingService, _scores, _sentiment, _summary


def test_scores_bullish_up_day():
    s = _scores(3.0, price=103, low=100, high=104)
    assert s["trend_score"] > 50
    assert s["_momentum"] == 3.0
    assert s["_activity"] == 3.0
    assert s["_opportunity"] > 0


def test_sentiment_thresholds():
    assert _sentiment(2.0) == Signal.BULLISH
    assert _sentiment(-2.0) == Signal.BEARISH
    assert _sentiment(0.1) == Signal.NEUTRAL


def test_summary_direction_and_value():
    assert "Up" in _summary(3.2) and "3.2%" in _summary(3.2)
    assert "Down" in _summary(-1.0)


def test_rank_categories():
    svc = TrendingService.__new__(TrendingService)  # bypass __init__; _rank is pure
    snap = [
        {"symbol": "A", "change_pct": 3.0, "_momentum": 3.0, "_activity": 3.0, "_opportunity": 2.5},
        {
            "symbol": "B",
            "change_pct": -2.0,
            "_momentum": -2.0,
            "_activity": 2.0,
            "_opportunity": -1.0,
        },
        {"symbol": "C", "change_pct": 1.0, "_momentum": 1.0, "_activity": 1.0, "_opportunity": 0.9},
    ]
    assert [r["symbol"] for r in svc._rank(snap, "most_bought")] == ["A", "C"]
    assert [r["symbol"] for r in svc._rank(snap, "most_sold")] == ["B"]
    assert svc._rank(snap, "trending")[0]["symbol"] == "A"
    assert svc._rank(snap, "high_opportunity")[0]["symbol"] == "A"
