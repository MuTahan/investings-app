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
    # --- broader S&P 100 universe (for trending / discovery) ---
    ("ABBV", "AbbVie Inc.", "stock", "NYSE", "Health Care"),
    ("ABT", "Abbott Laboratories", "stock", "NYSE", "Health Care"),
    ("ACN", "Accenture plc", "stock", "NYSE", "Technology"),
    ("ADBE", "Adobe Inc.", "stock", "NASDAQ", "Technology"),
    ("AMD", "Advanced Micro Devices Inc.", "stock", "NASDAQ", "Technology"),
    ("AMGN", "Amgen Inc.", "stock", "NASDAQ", "Health Care"),
    ("AMT", "American Tower Corporation", "stock", "NYSE", "Real Estate"),
    ("AVGO", "Broadcom Inc.", "stock", "NASDAQ", "Technology"),
    ("AXP", "American Express Company", "stock", "NYSE", "Financials"),
    ("BA", "Boeing Company", "stock", "NYSE", "Industrials"),
    ("BAC", "Bank of America Corporation", "stock", "NYSE", "Financials"),
    ("BK", "Bank of New York Mellon Corp.", "stock", "NYSE", "Financials"),
    ("BKNG", "Booking Holdings Inc.", "stock", "NASDAQ", "Consumer Discretionary"),
    ("BLK", "BlackRock Inc.", "stock", "NYSE", "Financials"),
    ("BMY", "Bristol-Myers Squibb Company", "stock", "NYSE", "Health Care"),
    ("C", "Citigroup Inc.", "stock", "NYSE", "Financials"),
    ("CAT", "Caterpillar Inc.", "stock", "NYSE", "Industrials"),
    ("CHTR", "Charter Communications Inc.", "stock", "NASDAQ", "Communication Services"),
    ("CL", "Colgate-Palmolive Company", "stock", "NYSE", "Consumer Staples"),
    ("CMCSA", "Comcast Corporation", "stock", "NASDAQ", "Communication Services"),
    ("COF", "Capital One Financial Corp.", "stock", "NYSE", "Financials"),
    ("COP", "ConocoPhillips", "stock", "NYSE", "Energy"),
    ("COST", "Costco Wholesale Corporation", "stock", "NASDAQ", "Consumer Staples"),
    ("CRM", "Salesforce Inc.", "stock", "NYSE", "Technology"),
    ("CSCO", "Cisco Systems Inc.", "stock", "NASDAQ", "Technology"),
    ("CVS", "CVS Health Corporation", "stock", "NYSE", "Health Care"),
    ("CVX", "Chevron Corporation", "stock", "NYSE", "Energy"),
    ("DHR", "Danaher Corporation", "stock", "NYSE", "Health Care"),
    ("DIS", "Walt Disney Company", "stock", "NYSE", "Communication Services"),
    ("DUK", "Duke Energy Corporation", "stock", "NYSE", "Utilities"),
    ("EMR", "Emerson Electric Co.", "stock", "NYSE", "Industrials"),
    ("F", "Ford Motor Company", "stock", "NYSE", "Consumer Discretionary"),
    ("FDX", "FedEx Corporation", "stock", "NYSE", "Industrials"),
    ("GD", "General Dynamics Corporation", "stock", "NYSE", "Industrials"),
    ("GE", "General Electric Company", "stock", "NYSE", "Industrials"),
    ("GILD", "Gilead Sciences Inc.", "stock", "NASDAQ", "Health Care"),
    ("GM", "General Motors Company", "stock", "NYSE", "Consumer Discretionary"),
    ("GOOG", "Alphabet Inc. Class C", "stock", "NASDAQ", "Communication Services"),
    ("GS", "Goldman Sachs Group Inc.", "stock", "NYSE", "Financials"),
    ("IBM", "International Business Machines", "stock", "NYSE", "Technology"),
    ("INTC", "Intel Corporation", "stock", "NASDAQ", "Technology"),
    ("INTU", "Intuit Inc.", "stock", "NASDAQ", "Technology"),
    ("ISRG", "Intuitive Surgical Inc.", "stock", "NASDAQ", "Health Care"),
    ("LIN", "Linde plc", "stock", "NASDAQ", "Materials"),
    ("LLY", "Eli Lilly and Company", "stock", "NYSE", "Health Care"),
    ("LMT", "Lockheed Martin Corporation", "stock", "NYSE", "Industrials"),
    ("LOW", "Lowe's Companies Inc.", "stock", "NYSE", "Consumer Discretionary"),
    ("MA", "Mastercard Inc.", "stock", "NYSE", "Financials"),
    ("MCD", "McDonald's Corporation", "stock", "NYSE", "Consumer Discretionary"),
    ("MDLZ", "Mondelez International Inc.", "stock", "NASDAQ", "Consumer Staples"),
    ("MDT", "Medtronic plc", "stock", "NYSE", "Health Care"),
    ("MET", "MetLife Inc.", "stock", "NYSE", "Financials"),
    ("MMM", "3M Company", "stock", "NYSE", "Industrials"),
    ("MO", "Altria Group Inc.", "stock", "NYSE", "Consumer Staples"),
    ("MRK", "Merck & Co. Inc.", "stock", "NYSE", "Health Care"),
    ("MS", "Morgan Stanley", "stock", "NYSE", "Financials"),
    ("NEE", "NextEra Energy Inc.", "stock", "NYSE", "Utilities"),
    ("NFLX", "Netflix Inc.", "stock", "NASDAQ", "Communication Services"),
    ("NKE", "Nike Inc.", "stock", "NYSE", "Consumer Discretionary"),
    ("ORCL", "Oracle Corporation", "stock", "NYSE", "Technology"),
    ("PEP", "PepsiCo Inc.", "stock", "NASDAQ", "Consumer Staples"),
    ("PFE", "Pfizer Inc.", "stock", "NYSE", "Health Care"),
    ("PM", "Philip Morris International", "stock", "NYSE", "Consumer Staples"),
    ("PYPL", "PayPal Holdings Inc.", "stock", "NASDAQ", "Financials"),
    ("QCOM", "Qualcomm Inc.", "stock", "NASDAQ", "Technology"),
    ("RTX", "RTX Corporation", "stock", "NYSE", "Industrials"),
    ("SBUX", "Starbucks Corporation", "stock", "NASDAQ", "Consumer Discretionary"),
    ("SCHW", "Charles Schwab Corporation", "stock", "NYSE", "Financials"),
    ("SO", "Southern Company", "stock", "NYSE", "Utilities"),
    ("T", "AT&T Inc.", "stock", "NYSE", "Communication Services"),
    ("TGT", "Target Corporation", "stock", "NYSE", "Consumer Discretionary"),
    ("TMO", "Thermo Fisher Scientific Inc.", "stock", "NYSE", "Health Care"),
    ("TMUS", "T-Mobile US Inc.", "stock", "NASDAQ", "Communication Services"),
    ("TXN", "Texas Instruments Inc.", "stock", "NASDAQ", "Technology"),
    ("UNP", "Union Pacific Corporation", "stock", "NYSE", "Industrials"),
    ("UPS", "United Parcel Service Inc.", "stock", "NYSE", "Industrials"),
    ("USB", "U.S. Bancorp", "stock", "NYSE", "Financials"),
    ("VZ", "Verizon Communications Inc.", "stock", "NYSE", "Communication Services"),
    ("WFC", "Wells Fargo & Company", "stock", "NYSE", "Financials"),
    ("WMT", "Walmart Inc.", "stock", "NYSE", "Consumer Staples"),
    ("XLF", "Financial Select Sector SPDR Fund", "etf", "NYSEARCA", None),
    ("XLV", "Health Care Select Sector SPDR Fund", "etf", "NYSEARCA", None),
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
