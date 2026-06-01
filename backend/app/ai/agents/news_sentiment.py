from __future__ import annotations

from app.ai.base import Agent, AgentContext, Compute, clamp, signal_from_score
from app.ai.prompts import news_prompt
from app.domain.enums import AgentName

_BULLISH = {
    "beat",
    "beats",
    "surge",
    "surges",
    "jump",
    "jumps",
    "upgrade",
    "upgraded",
    "record",
    "growth",
    "raises",
    "raised",
    "tops",
    "soars",
    "gains",
    "rally",
    "outperform",
}
_BEARISH = {
    "miss",
    "misses",
    "plunge",
    "plunges",
    "downgrade",
    "downgraded",
    "cut",
    "cuts",
    "lawsuit",
    "probe",
    "falls",
    "drops",
    "warns",
    "warning",
    "slump",
    "recall",
    "fraud",
    "halts",
}


class NewsSentimentAgent(Agent):
    name = AgentName.NEWS

    def compute(self, ctx: AgentContext) -> Compute:
        headlines = [a.headline for a in ctx.news if a.headline]
        bull = 0
        bear = 0
        for h in headlines:
            words = {w.strip(".,!?:'\"").lower() for w in h.split()}
            bull += len(words & _BULLISH)
            bear += len(words & _BEARISH)

        score = clamp(50 + (bull - bear) * 5, 30, 70)
        confidence = clamp(40 + len(headlines) * 4, 40, 75)
        if not headlines:
            explanation = "No recent news; neutral sentiment."
            confidence = 35.0
        else:
            tone = "net-positive" if bull > bear else "net-negative" if bear > bull else "mixed"
            explanation = f"{len(headlines)} recent headlines, {tone} tone."
        evidence = {
            "n_articles": len(headlines),
            "bullish_hits": bull,
            "bearish_hits": bear,
            "headlines": headlines[:8],
        }
        return Compute(score, signal_from_score(score), confidence, evidence, explanation)

    def prompt(self, ctx: AgentContext, c: Compute) -> str:
        headlines = [a.headline for a in ctx.news if a.headline]
        return news_prompt(ctx.instrument.symbol, headlines, c.base_score)
