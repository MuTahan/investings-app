from __future__ import annotations

from app.ai.base import Agent, AgentContext, Compute, signal_from_score
from app.ai.prompts import agent_reasoning_prompt
from app.domain.enums import AgentName

_REGIME_LABEL = {
    "risk_on": "Risk-on regime supportive of equities",
    "risk_off": "Risk-off regime; defensive backdrop",
    "late_cycle": "Late-cycle / cautious backdrop",
    "neutral": "Mixed macro backdrop",
}


class MacroAgent(Agent):
    name = AgentName.MACRO

    def compute(self, ctx: AgentContext) -> Compute:
        m = ctx.macro
        score = m.macro_score
        label = _REGIME_LABEL.get(m.regime, "Mixed macro backdrop")
        details = []
        if m.vix is not None:
            details.append(f"VIX {m.vix:.0f}")
        if m.market_trend:
            details.append(f"market trend {m.market_trend}")
        explanation = label + (f" ({', '.join(details)})." if details else ".")
        evidence = {
            "regime": m.regime,
            "vix": m.vix,
            "market_trend": m.market_trend,
            "regime_modifier": m.regime_modifier,
        }
        confidence = 60.0 if m.vix is not None or m.market_trend else 45.0
        return Compute(score, signal_from_score(score), confidence, evidence, explanation)

    def prompt(self, ctx: AgentContext, c: Compute) -> str:
        return agent_reasoning_prompt("macro", ctx.instrument.symbol, c.evidence, c.base_score)
