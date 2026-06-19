"""Content type definitions, tone presets, and language options."""

from typing import TypedDict


class ContentTypeSpec(TypedDict):
    name: str
    description: str
    output_guidance: str
    char_limit: int
    has_headline: bool


CONTENT_TYPES: dict[str, ContentTypeSpec] = {
    "Product description (short)": {
        "name": "Product description (short)",
        "description": "A concise product description for e-commerce listings or catalog pages.",
        "output_guidance": "Write a single compelling paragraph of 2-3 sentences (under 60 words). Focus on the core benefit and one standout feature.",
        "char_limit": 400,
        "has_headline": False,
    },
    "Product description (long)": {
        "name": "Product description (long)",
        "description": "A detailed product description with features and benefits.",
        "output_guidance": "Write 3-4 short paragraphs: hook and core benefit, key features as a short bulleted list, who it's for, call to action. Total under 200 words.",
        "char_limit": 1500,
        "has_headline": True,
    },
    "Social post (LinkedIn)": {
        "name": "Social post (LinkedIn)",
        "description": "A professional LinkedIn post.",
        "output_guidance": "Write a LinkedIn post with a strong opening line, a short story or insight, and 1-3 relevant hashtags. Under 150 words. Professional tone.",
        "char_limit": 1500,
        "has_headline": False,
    },
    "Social post (Twitter / X)": {
        "name": "Social post (Twitter / X)",
        "description": "A punchy Twitter/X post.",
        "output_guidance": "Write a single tweet under 280 characters. Hook, point, and optionally one hashtag. No links.",
        "char_limit": 280,
        "has_headline": False,
    },
    "Social post (Instagram caption)": {
        "name": "Social post (Instagram caption)",
        "description": "An Instagram caption with hashtags.",
        "output_guidance": "Write an Instagram caption: catchy first line, a short body under 80 words, and 5-8 relevant hashtags grouped at the end.",
        "char_limit": 1200,
        "has_headline": False,
    },
    "Email subject + preview": {
        "name": "Email subject + preview",
        "description": "Email subject line and preview text.",
        "output_guidance": "Output two short lines. Use the headline field for the subject (under 50 chars) and body for the preview (under 90 chars). Be specific, avoid clickbait.",
        "char_limit": 200,
        "has_headline": True,
    },
    "Ad copy (Google Search)": {
        "name": "Ad copy (Google Search)",
        "description": "Google Ads search copy: headline + description.",
        "output_guidance": "Use the headline field for a Google Ads headline (under 30 chars). Use body for description (under 90 chars). Active voice, benefit-focused, include a CTA.",
        "char_limit": 200,
        "has_headline": True,
    },
}


TONES: list[str] = [
    "Professional",
    "Friendly and conversational",
    "Playful and witty",
    "Luxurious and premium",
    "Technical and precise",
    "Bold and edgy",
    "Warm and empathetic",
    "Inspirational",
]


LANGUAGES: list[str] = [
    "English",
    "Spanish",
    "French",
    "German",
    "Portuguese",
    "Hindi",
    "Japanese",
    "Mandarin Chinese",
]


INPUT_LIMITS = {
    "product_name": 80,
    "product_description": 500,
    "audience": 200,
    "keywords": 200,
    "avoid": 200,
    "voice_sample": 3000,
}
