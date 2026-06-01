"""LLM prompt builders. Agents narrate + make bounded adjustments; the Chair decides.

All prompts request strict JSON so outputs are schema-validated. The deterministic
anchor is always provided so the model adjusts rather than inventing.
"""

from __future__ import annotations

import json

_AGENT_GUIDANCE = {
    "news": "You are a markets news & sentiment analyst.",
    "technical": "You are a technical analyst focused on momentum and trend.",
    "fundamental": "You are a fundamental analyst judging long-term quality.",
    "macro": "You are a macro strategist judging market regime.",
    "portfolio_fit": "You are a portfolio strategist judging personal fit.",
}


def agent_reasoning_prompt(agent: str, symbol: str, evidence: dict, base_score: float) -> str:
    role = _AGENT_GUIDANCE.get(agent, "You are an investment analyst.")
    return (
        f"{role}\n"
        f"Symbol: {symbol}\n"
        f"Deterministic anchor score (0-100): {base_score}\n"
        f"Computed evidence (JSON):\n{json.dumps(evidence, default=str)}\n\n"
        "Assess this evidence. You may adjust the score by AT MOST ±10 from the anchor; "
        "stay at the anchor if the evidence is ambiguous. Reply with ONLY this JSON:\n"
        '{"score": <0-100 number>, "reasoning": "<one or two sentences>", '
        '"justification": "<why you moved off the anchor, or empty>"}'
    )


def news_prompt(symbol: str, headlines: list[str], base_score: float) -> str:
    joined = "\n".join(f"- {h}" for h in headlines[:8]) or "- (no recent headlines)"
    return (
        "You are a markets news & sentiment analyst.\n"
        f"Symbol: {symbol}\n"
        f"Deterministic anchor sentiment score (0-100, 50=neutral): {base_score}\n"
        f"Recent headlines:\n{joined}\n\n"
        "Assess net sentiment and momentum from these headlines. You may adjust the score "
        "by AT MOST ±10 from the anchor. Reply with ONLY this JSON:\n"
        '{"score": <0-100>, "reasoning": "<one or two sentences>", '
        '"justification": "<brief>"}'
    )


def chair_prompt(
    symbol: str,
    staff_report: list[dict],
    anchor_rating: str,
    composite_score: float,
    conflicts: list[str],
    profile: dict,
    allowed_ratings: list[str],
) -> str:
    return (
        "You are the chair of an investment committee. Six specialist agents have each "
        "produced a score and reasoning. A deterministic weighted model already computed an "
        "anchor rating. Your job: issue the FINAL rating, weighing conflicts honestly.\n\n"
        f"Symbol: {symbol}\n"
        f"Composite score (0-100): {composite_score}\n"
        f"Deterministic anchor rating: {anchor_rating}\n"
        f"Allowed final ratings (within ±1 band of the anchor): {allowed_ratings}\n"
        f"User profile: {json.dumps(profile, default=str)}\n"
        f"Detected conflicts: {conflicts or 'none'}\n"
        f"Staff report (JSON):\n{json.dumps(staff_report, default=str)}\n\n"
        "Choose a final rating ONLY from the allowed list. Reply with ONLY this JSON:\n"
        '{"final_rating": "<one of the allowed ratings>", "confidence": <0-100>, '
        '"rationale": "<two or three sentences synthesizing the debate>"}'
    )
