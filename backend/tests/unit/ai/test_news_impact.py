from __future__ import annotations

from app.ai.news_impact import label, score_headline


def test_bullish_headline_scores_positive():
    s = score_headline("Company beats estimates and surges to record high")
    assert s > 0
    assert label(s) == "bullish"


def test_bearish_headline_scores_negative():
    s = score_headline("Shares plunge on lawsuit and analyst downgrade")
    assert s < 0
    assert label(s) == "bearish"


def test_neutral_headline():
    assert score_headline("Company to hold its annual shareholder meeting") == 0
    assert label(0) == "neutral"


def test_score_is_bounded():
    s = score_headline("beats surges jumps upgrade record growth raises tops soars gains rally")
    assert -100 <= s <= 100
