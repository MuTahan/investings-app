from __future__ import annotations

import uuid

from app.schemas.market import InstrumentOut
from app.schemas.portfolio import HoldingOut
from app.services.portfolio_service import PortfolioService


def _holding(symbol: str, market_value: float) -> HoldingOut:
    return HoldingOut(
        id=uuid.uuid4(),
        instrument=InstrumentOut(id=uuid.uuid4(), symbol=symbol, name=symbol, type="stock"),
        quantity=1,
        avg_cost=1,
        market_value=market_value,
    )


def test_diversification_single_position_is_zero():
    holdings = [_holding("AAPL", 1000.0)]
    summary = PortfolioService._summary(1000.0, 800.0, {"Technology": 1000.0}, holdings)
    assert summary.diversification_score == 0.0
    assert summary.unrealized_pl == 200.0
    assert summary.unrealized_pl_pct == 25.0
    assert summary.sector_exposure == {"Technology": 1.0}


def test_diversification_equal_positions_is_high():
    holdings = [_holding("AAPL", 500.0), _holding("MSFT", 500.0)]
    summary = PortfolioService._summary(1000.0, 1000.0, {"Technology": 1000.0}, holdings)
    # HHI = 0.5^2 + 0.5^2 = 0.5 -> diversification = 50
    assert summary.diversification_score == 50.0


def test_empty_portfolio_summary():
    summary = PortfolioService._summary(0.0, 0.0, {}, [])
    assert summary.market_value == 0.0
    assert summary.diversification_score == 0.0
    assert summary.sector_exposure == {}
