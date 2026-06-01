"""Deterministic technical indicators. Pure functions over price/volume series.

All return None when there is insufficient data so callers can degrade gracefully.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.providers.base import Candle


def sma(values: list[float], period: int) -> float | None:
    if len(values) < period or period <= 0:
        return None
    return sum(values[-period:]) / period


def ema(values: list[float], period: int) -> float | None:
    if len(values) < period or period <= 0:
        return None
    k = 2 / (period + 1)
    e = sum(values[:period]) / period  # seed with SMA
    for v in values[period:]:
        e = v * k + e * (1 - k)
    return e


def rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) < period + 1:
        return None
    gains = 0.0
    losses = 0.0
    for i in range(-period, 0):
        change = values[i] - values[i - 1]
        if change >= 0:
            gains += change
        else:
            losses -= change
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


@dataclass
class Macd:
    macd: float
    signal: float
    histogram: float


def macd(values: list[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Macd | None:
    if len(values) < slow + signal:
        return None
    # build the MACD line series, then EMA-signal it
    macd_line: list[float] = []
    for end in range(slow, len(values) + 1):
        window = values[:end]
        fast_ema = ema(window, fast)
        slow_ema = ema(window, slow)
        if fast_ema is None or slow_ema is None:
            continue
        macd_line.append(fast_ema - slow_ema)
    signal_line = ema(macd_line, signal)
    if not macd_line or signal_line is None:
        return None
    line = macd_line[-1]
    return Macd(macd=line, signal=signal_line, histogram=line - signal_line)


def momentum_pct(values: list[float], period: int = 10) -> float | None:
    if len(values) < period + 1:
        return None
    past = values[-period - 1]
    if past == 0:
        return None
    return (values[-1] / past - 1) * 100


def breakout(candles: list[Candle], lookback: int = 20) -> bool:
    if len(candles) < lookback + 1:
        return False
    prior_high = max(c.h for c in candles[-lookback - 1 : -1])
    return candles[-1].c > prior_high


def volume_ratio(candles: list[Candle], period: int = 20) -> float | None:
    vols = [c.v for c in candles if c.v is not None]
    if len(vols) < period + 1:
        return None
    avg = sum(vols[-period - 1 : -1]) / period
    if avg == 0:
        return None
    return vols[-1] / avg


@dataclass
class TechnicalIndicators:
    rsi: float | None
    macd: Macd | None
    sma50: float | None
    sma200: float | None
    momentum: float | None
    breakout: bool
    volume_ratio: float | None
    price: float | None


def compute(candles: list[Candle]) -> TechnicalIndicators:
    closes = [c.c for c in candles]
    return TechnicalIndicators(
        rsi=rsi(closes),
        macd=macd(closes),
        sma50=sma(closes, 50),
        sma200=sma(closes, 200),
        momentum=momentum_pct(closes),
        breakout=breakout(candles),
        volume_ratio=volume_ratio(candles),
        price=closes[-1] if closes else None,
    )
