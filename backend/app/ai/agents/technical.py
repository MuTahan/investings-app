from __future__ import annotations

from app.ai.base import Agent, AgentContext, Compute, clamp, signal_from_score
from app.ai.indicators import technical_math
from app.ai.prompts import agent_reasoning_prompt
from app.domain.enums import AgentName


class TechnicalAgent(Agent):
    name = AgentName.TECHNICAL

    def compute(self, ctx: AgentContext) -> Compute:
        ind = technical_math.compute(ctx.candles)
        score = 50.0
        notes: list[str] = []

        if ind.price is not None and ind.sma50 is not None:
            if ind.price > ind.sma50:
                score += 8
                notes.append("price above 50-day MA")
            else:
                score -= 8
                notes.append("price below 50-day MA")
        if ind.price is not None and ind.sma200 is not None:
            if ind.price > ind.sma200:
                score += 8
                notes.append("above 200-day MA")
            else:
                score -= 8
        if ind.macd is not None:
            if ind.macd.histogram > 0:
                score += 10
                notes.append("positive MACD")
            else:
                score -= 10
                notes.append("negative MACD")
        if ind.rsi is not None:
            if ind.rsi > 70:
                score -= 5
                notes.append(f"overbought (RSI {ind.rsi:.0f})")
            elif ind.rsi < 30:
                score += 5
                notes.append(f"oversold (RSI {ind.rsi:.0f})")
        if ind.momentum is not None:
            score += 5 if ind.momentum > 0 else -5
        if ind.breakout:
            score += 5
            notes.append("breakout")
        if ind.volume_ratio is not None and ind.volume_ratio > 1.5:
            score += 2

        score = clamp(score, 0, 100)
        signal = signal_from_score(score)
        confidence = clamp(45 + min(ctx.data_quality.n_candles, 200) / 5, 45, 85)
        explanation = (
            "Technical picture: " + ", ".join(notes) + "."
            if notes
            else "Insufficient price history for a strong technical read."
        )
        evidence = {
            "rsi": round(ind.rsi, 1) if ind.rsi is not None else None,
            "macd_hist": round(ind.macd.histogram, 3) if ind.macd else None,
            "sma50": round(ind.sma50, 2) if ind.sma50 else None,
            "sma200": round(ind.sma200, 2) if ind.sma200 else None,
            "momentum_pct": round(ind.momentum, 2) if ind.momentum is not None else None,
            "breakout": ind.breakout,
        }
        return Compute(score, signal, confidence, evidence, explanation)

    def prompt(self, ctx: AgentContext, c: Compute) -> str:
        return agent_reasoning_prompt("technical", ctx.instrument.symbol, c.evidence, c.base_score)
