"""Optional demo data for a compelling first run (run: python -m app.db.seed_demo).

Creates a demo user with a populated watchlist + portfolio so the app's screens are
not empty on first login. Idempotent: does nothing if the demo user already exists.

    email:    demo@example.com
    password: demodemo123
"""

from __future__ import annotations

import asyncio

from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.db.seed import seed as seed_instruments
from app.db.session import get_sessionmaker
from app.repositories.instrument_repo import InstrumentRepository
from app.repositories.portfolio_repo import PortfolioRepository
from app.repositories.user_repo import UserRepository
from app.repositories.watchlist_repo import WatchlistRepository

logger = get_logger("db.seed_demo")

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demodemo123"
WATCHLIST = ["AAPL", "MSFT", "NVDA", "SPY", "QQQ"]
HOLDINGS = [
    ("AAPL", 10, 180.0),
    ("MSFT", 6, 380.0),
    ("NVDA", 4, 110.0),
    ("SPY", 8, 500.0),
]


async def seed_demo() -> bool:
    await seed_instruments()  # ensure instruments exist
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        users = UserRepository(session)
        if await users.get_by_email(DEMO_EMAIL):
            logger.info("demo_user_exists", extra={"email": DEMO_EMAIL})
            return False

        user = await users.create(
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
            display_name="Demo",
        )

        instruments = InstrumentRepository(session)
        watchlist_repo = WatchlistRepository(session)
        watchlist = await watchlist_repo.get_or_create_default(user.id)
        for symbol in WATCHLIST:
            inst = await instruments.get_by_symbol(symbol)
            if inst and not await watchlist_repo.get_item(watchlist.id, inst.id):
                await watchlist_repo.add_item(watchlist.id, inst.id)

        portfolio_repo = PortfolioRepository(session)
        portfolio = await portfolio_repo.get_or_create_default(user.id)
        for symbol, qty, cost in HOLDINGS:
            inst = await instruments.get_by_symbol(symbol)
            if inst and not await portfolio_repo.get_holding_by_instrument(portfolio.id, inst.id):
                await portfolio_repo.add_holding(portfolio.id, inst.id, qty, cost)

        await session.commit()
    logger.info("demo_seeded", extra={"email": DEMO_EMAIL})
    return True


if __name__ == "__main__":
    configure_logging()
    asyncio.run(seed_demo())
