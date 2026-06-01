from __future__ import annotations

from datetime import UTC, datetime

from app.ai.base import PortfolioSnapshot
from app.ai.indicators import fundamental_math, risk_math, technical_math
from app.providers.base import Candle, Fundamentals


def _candles(prices: list[float]) -> list[Candle]:
    return [
        Candle(t=datetime(2026, 1, 1, tzinfo=UTC), o=p, h=p + 1, l=p - 1, c=p, v=1000)
        for p in prices
    ]


def test_sma_and_insufficient_data():
    assert technical_math.sma([1, 2, 3, 4], 2) == 3.5
    assert technical_math.sma([1, 2], 5) is None


def test_rsi_all_gains_is_high():
    closes = [float(i) for i in range(1, 20)]
    rsi = technical_math.rsi(closes)
    assert rsi is not None and rsi > 99


def test_macd_needs_enough_data():
    assert technical_math.macd([1.0, 2.0, 3.0]) is None
    closes = [float(i) for i in range(1, 60)]
    result = technical_math.macd(closes)
    assert result is not None
    assert result.macd > 0  # steady uptrend -> positive MACD


def test_fundamental_quality_stock():
    f = Fundamentals(symbol="X", pe=18, op_margin=0.30, revenue_growth=0.2, eps_growth=0.2)
    result = fundamental_math.compute(f, "stock")
    assert result.score > 60
    assert result.assessment in {"Solid", "High quality"}


def test_fundamental_etf_branch():
    f = Fundamentals(symbol="SPY", expense_ratio=0.0009)
    result = fundamental_math.compute(f, "etf")
    assert 50 <= result.score <= 65
    assert "ETF" in result.assessment


def test_risk_flags_high_volatility():
    prices = [100 if i % 2 == 0 else 115 for i in range(30)]  # large alternating swings
    assessment = risk_math.compute(
        candles=_candles(prices),
        fundamentals=Fundamentals(symbol="X", pe=50, beta=2.0),
        portfolio=PortfolioSnapshot(),
        symbol="X",
        sector="Technology",
        max_position_pct=None,
    )
    assert assessment.level.value == "high"
    assert assessment.warnings


def test_risk_low_when_calm():
    prices = [100 + i * 0.1 for i in range(40)]
    assessment = risk_math.compute(
        candles=_candles(prices),
        fundamentals=Fundamentals(symbol="X", pe=18, beta=0.9),
        portfolio=PortfolioSnapshot(),
        symbol="X",
        sector="Technology",
        max_position_pct=None,
    )
    assert assessment.level.value == "low"
