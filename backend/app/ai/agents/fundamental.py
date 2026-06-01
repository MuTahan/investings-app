from __future__ import annotations

from app.ai.base import Agent, AgentContext, Compute, signal_from_score
from app.ai.indicators import fundamental_math
from app.ai.prompts import agent_reasoning_prompt
from app.domain.enums import AgentName


class FundamentalAgent(Agent):
    name = AgentName.FUNDAMENTAL

    def compute(self, ctx: AgentContext) -> Compute:
        result = fundamental_math.compute(ctx.fundamentals, ctx.instrument.type)
        explanation = f"{result.assessment}."
        if ctx.instrument.type != "etf" and result.evidence:
            parts = []
            if result.evidence.get("revenue_growth") is not None:
                parts.append(f"revenue growth {result.evidence['revenue_growth'] * 100:.0f}%")
            if result.evidence.get("op_margin") is not None:
                parts.append(f"operating margin {result.evidence['op_margin'] * 100:.0f}%")
            if result.evidence.get("pe") is not None:
                parts.append(f"P/E {result.evidence['pe']:.0f}")
            if parts:
                explanation = f"{result.assessment}: " + ", ".join(parts) + "."
        return Compute(
            result.score,
            signal_from_score(result.score),
            result.confidence,
            result.evidence,
            explanation,
        )

    def prompt(self, ctx: AgentContext, c: Compute) -> str:
        return agent_reasoning_prompt(
            "fundamental", ctx.instrument.symbol, c.evidence, c.base_score
        )
