"""Tests for prompt construction and parsing."""

import pytest

from src.content_types import CONTENT_TYPES
from src.generator import parse_json_tolerant
from src.prompts import (
    GENERATION_SYSTEM_INSTRUCTION,
    VOICE_SYSTEM_INSTRUCTION,
    build_generation_prompt,
    build_voice_extraction_prompt,
)
from src.strategies import STRATEGIES, strategy_color


# ---------------------------------------------------------------------------
# Generation prompts
# ---------------------------------------------------------------------------
def test_system_instructions_are_non_empty():
    assert len(GENERATION_SYSTEM_INSTRUCTION) > 100
    assert "JSON" in GENERATION_SYSTEM_INSTRUCTION
    assert len(VOICE_SYSTEM_INSTRUCTION) > 50
    assert "JSON" in VOICE_SYSTEM_INSTRUCTION


def test_build_generation_prompt_includes_core_fields():
    spec = CONTENT_TYPES["Product description (short)"]
    prompt = build_generation_prompt(
        product_name="EcoFlow Bottle",
        product_description="Stainless steel water bottle.",
        audience="Outdoor enthusiasts",
        content_type_spec=spec,
        tone="Professional",
        language="English",
        n_variants=3,
    )
    assert "EcoFlow Bottle" in prompt
    assert "Outdoor enthusiasts" in prompt
    assert "Professional" in prompt
    assert "English" in prompt
    assert "3 distinct variants" in prompt


def test_build_generation_prompt_includes_strategies():
    spec = CONTENT_TYPES["Product description (short)"]
    prompt = build_generation_prompt(
        product_name="X",
        product_description="Y",
        audience="",
        content_type_spec=spec,
        tone="Professional",
        language="English",
        n_variants=3,
    )
    # Every strategy must appear in the prompt so the LLM knows the option set.
    for name in STRATEGIES:
        assert name in prompt
    # And the scoring rubric.
    for dim in ["clarity", "specificity", "novelty", "brand_fit", "reading_ease"]:
        assert dim in prompt


def test_build_generation_prompt_handles_missing_optionals():
    spec = CONTENT_TYPES["Product description (short)"]
    prompt = build_generation_prompt(
        product_name="X",
        product_description="Y",
        audience="",
        content_type_spec=spec,
        tone="Professional",
        language="English",
        n_variants=1,
    )
    assert "KEYWORDS TO INCLUDE" not in prompt
    assert "WORDS OR PHRASES TO AVOID" not in prompt
    assert "BRAND VOICE PROFILE" not in prompt
    assert "General audience" in prompt


def test_build_generation_prompt_applies_voice_profile():
    spec = CONTENT_TYPES["Product description (short)"]
    profile = {
        "tone_descriptors": ["direct", "warm"],
        "signature_phrases": ["Let's get specific."],
        "vocabulary_level": "conversational",
        "sentence_rhythm": "short and punchy",
        "perspective": "first-person plural (we/us)",
        "avoid_words": ["synergy", "leverage"],
        "voice_summary": "Direct, warm, plain-spoken.",
    }
    prompt = build_generation_prompt(
        product_name="X",
        product_description="Y",
        audience="",
        content_type_spec=spec,
        tone="Professional",
        language="English",
        n_variants=1,
        voice_profile=profile,
    )
    assert "BRAND VOICE PROFILE" in prompt
    assert "Let's get specific." in prompt
    assert "synergy" in prompt
    assert "Direct, warm, plain-spoken." in prompt


@pytest.mark.parametrize("content_type", list(CONTENT_TYPES.keys()))
def test_prompt_builds_for_every_content_type(content_type):
    spec = CONTENT_TYPES[content_type]
    prompt = build_generation_prompt(
        product_name="Test",
        product_description="Test description",
        audience="",
        content_type_spec=spec,
        tone="Professional",
        language="English",
        n_variants=1,
    )
    assert len(prompt) > 500
    assert content_type in prompt


# ---------------------------------------------------------------------------
# Voice extraction prompts
# ---------------------------------------------------------------------------
def test_voice_extraction_prompt_numbers_samples():
    prompt = build_voice_extraction_prompt(["sample one", "sample two"])
    assert "SAMPLE 1:" in prompt
    assert "SAMPLE 2:" in prompt
    assert "sample one" in prompt
    assert "sample two" in prompt


def test_voice_extraction_prompt_requests_required_fields():
    prompt = build_voice_extraction_prompt(["test"])
    for field in [
        "tone_descriptors",
        "signature_phrases",
        "vocabulary_level",
        "sentence_rhythm",
        "perspective",
        "avoid_words",
        "voice_summary",
    ]:
        assert field in prompt


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------
def test_strategies_have_required_fields():
    for name, spec in STRATEGIES.items():
        assert spec["name"] == name
        assert spec["description"]
        assert spec["when_to_use"]
        assert spec["color"].startswith("#")


def test_strategy_color_handles_unknown():
    assert strategy_color("Unknown") == "#6B7280"
    assert strategy_color("Social Proof") == "#3B82F6"


# ---------------------------------------------------------------------------
# JSON parser
# ---------------------------------------------------------------------------
def test_parse_clean_json():
    raw = '{"variants": [{"body": "test"}]}'
    parsed = parse_json_tolerant(raw)
    assert parsed["variants"][0]["body"] == "test"


def test_parse_fenced_json():
    raw = '```json\n{"variants": [{"body": "test"}]}\n```'
    parsed = parse_json_tolerant(raw)
    assert parsed["variants"][0]["body"] == "test"


def test_parse_prose_wrapped_json():
    raw = 'Here you go:\n{"variants": [{"body": "test"}]}\nLet me know!'
    parsed = parse_json_tolerant(raw)
    assert parsed["variants"][0]["body"] == "test"


def test_parse_malformed_raises():
    with pytest.raises(ValueError):
        parse_json_tolerant("totally not json")
