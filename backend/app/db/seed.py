"""Idempotent seed of common US instruments (run: python -m app.db.seed)."""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.logging import configure_logging, get_logger
from app.db.models.instrument import Instrument
from app.db.session import get_sessionmaker

logger = get_logger("db.seed")

# (symbol, name, type, exchange, sector)
SEED: list[tuple[str, str, str, str, str | None]] = [
    ("AAPL", "Apple Inc.", "stock", "NASDAQ", "Technology"),
    ("MSFT", "Microsoft Corporation", "stock", "NASDAQ", "Technology"),
    ("GOOGL", "Alphabet Inc. Class A", "stock", "NASDAQ", "Communication Services"),
    ("AMZN", "Amazon.com Inc.", "stock", "NASDAQ", "Consumer Discretionary"),
    ("NVDA", "NVIDIA Corporation", "stock", "NASDAQ", "Technology"),
    ("META", "Meta Platforms Inc.", "stock", "NASDAQ", "Communication Services"),
    ("TSLA", "Tesla Inc.", "stock", "NASDAQ", "Consumer Discretionary"),
    ("JPM", "JPMorgan Chase & Co.", "stock", "NYSE", "Financials"),
    ("V", "Visa Inc.", "stock", "NYSE", "Financials"),
    ("UNH", "UnitedHealth Group Inc.", "stock", "NYSE", "Health Care"),
    ("JNJ", "Johnson & Johnson", "stock", "NYSE", "Health Care"),
    ("XOM", "Exxon Mobil Corporation", "stock", "NYSE", "Energy"),
    ("PG", "Procter & Gamble Co.", "stock", "NYSE", "Consumer Staples"),
    ("HD", "Home Depot Inc.", "stock", "NYSE", "Consumer Discretionary"),
    ("KO", "Coca-Cola Co.", "stock", "NYSE", "Consumer Staples"),
    ("SPY", "SPDR S&P 500 ETF Trust", "etf", "NYSEARCA", None),
    ("VOO", "Vanguard S&P 500 ETF", "etf", "NYSEARCA", None),
    ("QQQ", "Invesco QQQ Trust", "etf", "NASDAQ", None),
    ("VTI", "Vanguard Total Stock Market ETF", "etf", "NYSEARCA", None),
    ("IWM", "iShares Russell 2000 ETF", "etf", "NYSEARCA", None),
    ("DIA", "SPDR Dow Jones Industrial Average ETF", "etf", "NYSEARCA", None),
    ("VXUS", "Vanguard Total International Stock ETF", "etf", "NASDAQ", None),
    ("AGG", "iShares Core US Aggregate Bond ETF", "etf", "NYSEARCA", None),
    ("XLK", "Technology Select Sector SPDR Fund", "etf", "NYSEARCA", None),
    ("XLE", "Energy Select Sector SPDR Fund", "etf", "NYSEARCA", None),
]


async def seed() -> int:
    sessionmaker = get_sessionmaker()
    inserted = 0
    async with sessionmaker() as session:
        existing = set((await session.execute(select(Instrument.symbol))).scalars().all())
        for symbol, name, type_, exchange, sector in SEED:
            if symbol in existing:
                continue
            session.add(
                Instrument(
                    symbol=symbol,
                    name=name,
                    type=type_,
                    exchange=exchange,
                    sector=sector,
                    currency="USD",
                    is_active=True,
                )
            )
            inserted += 1
        await session.commit()
    logger.info("seed_complete", extra={"inserted": inserted, "total": len(SEED)})
    return inserted


if __name__ == "__main__":
    configure_logging()
    asyncio.run(seed())
