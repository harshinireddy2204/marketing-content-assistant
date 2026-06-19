"""Content generation via Google Gemini (google-genai SDK)."""

import json
import re
import time
from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from src.content_types import CONTENT_TYPES
from src.prompts import (
    GENERATION_SYSTEM_INSTRUCTION,
    VOICE_SYSTEM_INSTRUCTION,
    build_generation_prompt,
    build_voice_extraction_prompt,
)


DEFAULT_MODEL = "gemini-2.5-flash"
# Free-tier alternatives (as of June 2026):
#   gemini-2.5-flash       - 10 RPM, 250 RPD, best quality on free tier
#   gemini-2.5-flash-lite  - 15 RPM, 1000 RPD, lower quality but more headroom
# gemini-2.0-flash was deprecated June 1, 2026 (free quota zeroed).
MAX_OUTPUT_TOKENS = 1500
TEMPERATURE = 0.85

# Retry config: free tier has tight RPM. If we hit a 429, brief backoff usually clears it.
MAX_RETRIES = 2
INITIAL_BACKOFF_SECONDS = 2.0


def _call_with_retry(call_fn):
    """Wrap a Gemini API call with exponential backoff on 429 rate limits."""
    backoff = INITIAL_BACKOFF_SECONDS
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return call_fn()
        except Exception as e:
            msg = str(e).upper()
            is_rate_limit = (
                "429" in msg or "RATE" in msg or "QUOTA" in msg or "RESOURCE_EXHAUSTED" in msg
            )
            if not is_rate_limit or attempt == MAX_RETRIES:
                raise
            last_error = e
            time.sleep(backoff)
            backoff *= 2
    raise last_error if last_error else RuntimeError("retry loop exited unexpectedly")


class VariantScores(BaseModel):
    clarity: int = Field(ge=1, le=10)
    specificity: int = Field(ge=1, le=10)
    novelty: int = Field(ge=1, le=10)
    brand_fit: int = Field(ge=1, le=10)
    reading_ease: int = Field(ge=1, le=10)

    @property
    def overall(self) -> float:
        return round(
            (self.clarity + self.specificity + self.novelty + self.brand_fit + self.reading_ease) / 5,
            1,
        )


class Variant(BaseModel):
    headline: str = ""
    body: str
    strategy: str = ""
    rationale: str = ""
    scores: VariantScores | None = None


class GenerationResult(BaseModel):
    variants: list[Variant] = Field(min_length=1)


class VoiceProfile(BaseModel):
    tone_descriptors: list[str] = Field(default_factory=list)
    signature_phrases: list[str] = Field(default_factory=list)
    vocabulary_level: str = ""
    sentence_rhythm: str = ""
    perspective: str = ""
    avoid_words: list[str] = Field(default_factory=list)
    voice_summary: str = ""


def parse_json_tolerant(raw: str) -> dict[str, Any]:
    """Tolerant JSON parser: strips markdown fences, falls back to first {...}."""
    text = raw.strip()

    fence_pattern = r"^```(?:json)?\s*(.*?)\s*```$"
    match = re.match(fence_pattern, text, flags=re.DOTALL)
    if match:
        text = match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Model returned malformed JSON. Raw output: {raw[:200]}..."
            ) from e

    raise ValueError(f"No JSON object found in model output: {raw[:200]}...")


class ContentGenerator:
    """Generates variants with strategy + scores in a single call."""

    def __init__(self, api_key: str, model_name: str = DEFAULT_MODEL):
        if not api_key:
            raise ValueError("API key is required")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def generate(
        self,
        product_name: str,
        product_description: str,
        audience: str,
        content_type: str,
        tone: str,
        language: str,
        n_variants: int = 3,
        keywords: str = "",
        avoid: str = "",
        voice_profile: dict | None = None,
    ) -> dict[str, Any]:
        if content_type not in CONTENT_TYPES:
            raise ValueError(f"Unknown content type: {content_type}")

        spec = CONTENT_TYPES[content_type]
        prompt = build_generation_prompt(
            product_name=product_name,
            product_description=product_description,
            audience=audience,
            content_type_spec=spec,
            tone=tone,
            language=language,
            n_variants=n_variants,
            keywords=keywords,
            avoid=avoid,
            voice_profile=voice_profile,
        )

        response = _call_with_retry(
            lambda: self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=GENERATION_SYSTEM_INSTRUCTION,
                    temperature=TEMPERATURE,
                    max_output_tokens=MAX_OUTPUT_TOKENS,
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
        )

        raw_text = response.text or ""
        parsed = parse_json_tolerant(raw_text)
        validated = GenerationResult.model_validate(parsed)
        return validated.model_dump()


class VoiceExtractor:
    """Distills brand writing samples into a portable voice profile."""

    def __init__(self, api_key: str, model_name: str = DEFAULT_MODEL):
        if not api_key:
            raise ValueError("API key is required")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def extract(self, samples: list[str]) -> dict[str, Any]:
        cleaned = [s.strip() for s in samples if s.strip()]
        if len(cleaned) < 1:
            raise ValueError("Provide at least 1 writing sample.")

        prompt = build_voice_extraction_prompt(cleaned)

        response = _call_with_retry(
            lambda: self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=VOICE_SYSTEM_INSTRUCTION,
                    temperature=0.3,
                    max_output_tokens=800,
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
        )

        raw_text = response.text or ""
        parsed = parse_json_tolerant(raw_text)
        validated = VoiceProfile.model_validate(parsed)
        return validated.model_dump()