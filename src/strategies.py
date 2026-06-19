"""Persuasion strategies (psychological angles) used to differentiate variants.

Each variant the LLM produces is deliberately built around one of these
angles. This is the core of our "strategy tagging" feature: marketers can
see *why* each variant works, not just read the words.

The list is drawn from classic persuasion psychology (Cialdini's principles
plus a few modern additions like Curiosity Gap from behavioral marketing
research).
"""

from typing import TypedDict


class Strategy(TypedDict):
    name: str
    description: str
    when_to_use: str
    color: str  # Hex color for the UI badge


STRATEGIES: dict[str, Strategy] = {
    "Concrete Specificity": {
        "name": "Concrete Specificity",
        "description": "Replace vague claims with specific, measurable details.",
        "when_to_use": "When the audience is skeptical or comparing options.",
        "color": "#06B6D4",
    },
    "Social Proof": {
        "name": "Social Proof",
        "description": "Show that others like the reader already use or trust this.",
        "when_to_use": "Early-funnel awareness, low-trust audiences.",
        "color": "#3B82F6",
    },
    "Loss Aversion": {
        "name": "Loss Aversion",
        "description": "Frame the cost of inaction or what the reader risks missing.",
        "when_to_use": "When the reader is on the fence and needs urgency.",
        "color": "#EF4444",
    },
    "Curiosity Gap": {
        "name": "Curiosity Gap",
        "description": "Open a loop that only the body or product can close.",
        "when_to_use": "Email subjects, cold ads, top-of-funnel.",
        "color": "#F59E0B",
    },
    "Aspiration": {
        "name": "Aspiration",
        "description": "Paint the future self the reader wants to become.",
        "when_to_use": "Lifestyle brands, identity-driven purchases.",
        "color": "#EC4899",
    },
    "Authority": {
        "name": "Authority",
        "description": "Lean on credentials, science, or expert endorsement.",
        "when_to_use": "Health, finance, B2B technical sales.",
        "color": "#8B5CF6",
    },
    "Reciprocity": {
        "name": "Reciprocity",
        "description": "Offer something useful first (insight, tip, free resource).",
        "when_to_use": "Content marketing, lead nurture.",
        "color": "#10B981",
    },
    "Belonging": {
        "name": "Belonging",
        "description": "Invite the reader into a tribe or community.",
        "when_to_use": "Community products, lifestyle brands.",
        "color": "#14B8A6",
    },
    "Contrast": {
        "name": "Contrast",
        "description": "Make the value obvious by comparing to a worse alternative.",
        "when_to_use": "Differentiated products in crowded markets.",
        "color": "#F97316",
    },
}


def strategy_names() -> list[str]:
    return list(STRATEGIES.keys())


def strategy_color(name: str) -> str:
    """Return the badge color for a strategy, with a safe fallback."""
    return STRATEGIES.get(name, {}).get("color", "#6B7280")
