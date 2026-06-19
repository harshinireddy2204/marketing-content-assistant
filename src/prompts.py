"""Prompt templates.

We keep three distinct prompt families:

1. GENERATION: produces variants with strategy + scores in one call.
2. VOICE EXTRACTION: distills a brand's writing samples into a voice profile.

Keeping them isolated makes iteration safe: change a generation prompt
without breaking voice extraction, and vice versa.
"""

from src.content_types import ContentTypeSpec
from src.strategies import STRATEGIES


# ---------------------------------------------------------------------------
# Generation prompts
# ---------------------------------------------------------------------------

GENERATION_SYSTEM_INSTRUCTION = """You are a senior marketing copywriter with 15 years of experience writing for global brands across e-commerce, SaaS, and consumer goods. You write copy that is:

- Specific, not generic (avoid empty phrases like "high quality" or "innovative")
- Benefit-led (what the customer gets, not just what the product is)
- Culturally aware (you adapt phrasing for the target language and region)
- Honest (you never fabricate features, awards, statistics, or claims)
- On-brand (you match the requested tone and voice profile precisely)

You think in persuasion strategies. Each variant you write is deliberately built around ONE psychological angle. You can name and justify the angle.

You ALWAYS return valid JSON exactly matching the requested schema. No prose before or after. No markdown code fences. Just the raw JSON object."""


# Build the strategy reference dynamically from STRATEGIES so adding a new
# strategy in one place updates the prompt automatically.
def _strategy_reference() -> str:
    lines = ["Available strategies (pick a different one for each variant):"]
    for name, spec in STRATEGIES.items():
        lines.append(f"- {name}: {spec['description']}")
    return "\n".join(lines)


GENERATION_USER_TEMPLATE = """Generate marketing copy with the following parameters.

PRODUCT
- Name: {product_name}
- Description: {product_description}

AUDIENCE
{audience}

CONTENT TYPE
{content_type_name}: {content_type_description}

OUTPUT GUIDANCE
{output_guidance}

BRAND TONE
{tone}

{voice_profile_section}

LANGUAGE
Write the output in {language}. Adapt idioms and references for native speakers.

{keywords_section}
{avoid_section}

VARIANTS
Generate {n_variants} distinct variants. Each must use a DIFFERENT persuasion strategy from the list below. Do not repeat strategies. Do not paraphrase the same idea.

{strategy_reference}

SCORING
For each variant, score it 1-10 on each dimension:
- clarity: Is the message immediately understandable on first read?
- specificity: Does it use concrete details vs vague claims?
- novelty: Is the angle fresh or cliche?
- brand_fit: Does it match the tone and voice profile?
- reading_ease: Does it flow naturally for the language?

Be honest with scores. Not every variant should score 9+; a thoughtful 7 is more useful than a flattering 9.

OUTPUT SCHEMA
Return a single JSON object with this exact shape:
{{
  "variants": [
    {{
      "headline": "<headline if applicable, else empty string>",
      "body": "<main copy>",
      "strategy": "<exact name from the strategy list>",
      "rationale": "<one sentence: why this strategy fits this audience>",
      "scores": {{
        "clarity": <1-10 integer>,
        "specificity": <1-10 integer>,
        "novelty": <1-10 integer>,
        "brand_fit": <1-10 integer>,
        "reading_ease": <1-10 integer>
      }}
    }}
  ]
}}

CRITICAL: Output only the JSON. No explanation, no markdown fences, no preamble."""


def build_generation_prompt(
    product_name: str,
    product_description: str,
    audience: str,
    content_type_spec: ContentTypeSpec,
    tone: str,
    language: str,
    n_variants: int,
    keywords: str = "",
    avoid: str = "",
    voice_profile: dict | None = None,
) -> str:
    """Construct the user prompt with optional sections handled cleanly."""
    keywords_section = (
        f"KEYWORDS TO INCLUDE NATURALLY\n{keywords}\n" if keywords.strip() else ""
    )
    avoid_section = (
        f"WORDS OR PHRASES TO AVOID\n{avoid}\n" if avoid.strip() else ""
    )
    audience_text = audience.strip() if audience.strip() else "General audience"

    if voice_profile:
        voice_section = (
            "BRAND VOICE PROFILE (apply throughout)\n"
            f"- Tone descriptors: {', '.join(voice_profile.get('tone_descriptors', []))}\n"
            f"- Vocabulary level: {voice_profile.get('vocabulary_level', '')}\n"
            f"- Sentence rhythm: {voice_profile.get('sentence_rhythm', '')}\n"
            f"- Perspective: {voice_profile.get('perspective', '')}\n"
            f"- Signature phrases (use sparingly, not every variant): "
            f"{', '.join(voice_profile.get('signature_phrases', []))}\n"
            f"- Avoid these words/phrases: "
            f"{', '.join(voice_profile.get('avoid_words', []))}\n"
            f"- Voice summary: {voice_profile.get('voice_summary', '')}\n"
        )
    else:
        voice_section = ""

    return GENERATION_USER_TEMPLATE.format(
        product_name=product_name,
        product_description=product_description,
        audience=audience_text,
        content_type_name=content_type_spec["name"],
        content_type_description=content_type_spec["description"],
        output_guidance=content_type_spec["output_guidance"],
        tone=tone,
        language=language,
        n_variants=n_variants,
        keywords_section=keywords_section,
        avoid_section=avoid_section,
        voice_profile_section=voice_section,
        strategy_reference=_strategy_reference(),
    )


# ---------------------------------------------------------------------------
# Voice extraction prompts
# ---------------------------------------------------------------------------

VOICE_SYSTEM_INSTRUCTION = """You are a brand strategist who specializes in voice analysis. When given samples of a brand's writing, you can distill the patterns into a portable voice profile that another writer (human or AI) could use to produce copy that sounds authentic to the brand.

You are precise. You name specific patterns. You quote phrases when useful. You do not invent qualities that aren't in the samples.

You ALWAYS return valid JSON exactly matching the requested schema."""


VOICE_EXTRACTION_TEMPLATE = """Analyze the following writing samples from a single brand and extract a voice profile.

SAMPLES
{samples}

INSTRUCTIONS
1. Read all samples as a set, not one at a time.
2. Identify the recurring patterns in tone, vocabulary, sentence rhythm, and perspective.
3. Note any signature phrases (words or short expressions the brand uses repeatedly).
4. Note words or styles the brand seems to AVOID (e.g. corporate jargon if they write plainly).
5. Be specific. "Friendly" is too vague. "Friendly like a knowledgeable older sibling" is useful.

OUTPUT SCHEMA
Return a single JSON object with this exact shape:
{{
  "tone_descriptors": ["<3-5 specific descriptors>"],
  "signature_phrases": ["<actual phrases lifted from the samples, 2-5 items>"],
  "vocabulary_level": "<one of: basic, conversational, intermediate, advanced, technical>",
  "sentence_rhythm": "<one sentence describing how the brand structures sentences>",
  "perspective": "<one of: first-person singular (I/me), first-person plural (we/us), second-person (you), third-person, mixed>",
  "avoid_words": ["<words or stylistic patterns the brand avoids, 3-6 items>"],
  "voice_summary": "<2-3 sentences another writer could read to capture the voice>"
}}

CRITICAL: Output only the JSON. No explanation, no markdown fences, no preamble."""


def build_voice_extraction_prompt(samples: list[str]) -> str:
    """Combine samples into one prompt. Numbers them for clarity."""
    numbered = "\n\n".join(
        f"SAMPLE {i}:\n{sample.strip()}" for i, sample in enumerate(samples, 1)
    )
    return VOICE_EXTRACTION_TEMPLATE.format(samples=numbered)
