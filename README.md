# Voiceprint

**Marketing copy that sounds like you, not like AI.**

Voiceprint is an open source tool for marketers and founders. Paste a few samples of your existing brand writing and Voiceprint extracts your voice DNA. Then every piece of copy it generates (product descriptions, social posts, email subjects, ad copy) sounds like your brand, not like a generic AI model.

[![tests](https://github.com/YOUR_USERNAME/voiceprint/actions/workflows/tests.yml/badge.svg)](https://github.com/YOUR_USERNAME/voiceprint/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev)

**[Live demo](https://YOUR_APP_NAME.streamlit.app)**

---

## Why Voiceprint

Most AI copy tools have one fundamental problem: every brand's output sounds the same. Same hedging, same em dashes, same "Here's the thing:" openings, same overconfident superlatives.

Voiceprint is built around three ideas that most generators skip:

### 1. Brand Voice DNA
Paste 1 to 5 samples of your existing writing. Voiceprint extracts a portable voice profile (tone descriptors, signature phrases, sentence rhythm, words you avoid) and applies it to every generation. The result reads like you wrote it, not a template.

### 2. Strategy tagging
Every variant is built around a specific persuasion strategy: Social Proof, Loss Aversion, Curiosity Gap, Aspiration, Authority, Reciprocity, Belonging, Contrast, or Concrete Specificity. The strategy is labeled on each variant, so you can match the angle to the campaign rather than picking whichever wording "sounds best".

### 3. Honest scoring
Every variant is scored 1 to 10 on five dimensions: clarity, specificity, novelty, brand fit, reading ease. Not every variant scores 9. A 7 with an honest breakdown is more useful than a flattering 9, and the dashboard surfaces the highest scorer so you can copy and ship.

## Features

- **7 content types**: Product descriptions (short and long), social posts (LinkedIn, Twitter/X, Instagram), email subject + preview, Google Search ad copy
- **8 tones**: Professional, Friendly, Playful, Luxurious, Technical, Bold, Warm, Inspirational
- **8 languages**: English, Spanish, French, German, Portuguese, Hindi, Japanese, Mandarin
- **9 persuasion strategies**: Each variant uses a different one
- **5-dimension scoring** on every variant
- **Brand Voice DNA** extracted from your own writing samples
- **Session history** with downloadable JSON or Markdown
- **Layered cost protection** so the app stays free even at scale

## Cost protection

The app is built to stay at $0 even if it goes viral.

| Layer | Protection |
|---|---|
| Free tier | Gemini 2.0 Flash: 1500 requests/day, 15 requests/min, no credit card required |
| Session cap | 10 generations per browser session (configurable) |
| BYOK | Heavy users paste their own free key in the sidebar |
| Output cap | 1500 max tokens per response |
| Input cap | Hard limits on every text field |
| Billing cap | Set $0 cap in Google AI Studio for true peace of mind |

If the shared key hits its daily limit, the UI clearly asks users to bring their own free key. Your cost stays at zero.

## Run locally

```bash
git clone https://github.com/YOUR_USERNAME/voiceprint.git
cd voiceprint

pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml and paste your free Gemini key
# Get one at: https://aistudio.google.com/apikey

streamlit run app.py
```

Open http://localhost:8501.

## Deploy free on Streamlit Community Cloud

1. Push this repo to your GitHub account.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, pick this repo, set the main file to `app.py`.
4. Open **Advanced settings → Secrets** and paste:
   ```toml
   GEMINI_API_KEY = "your_key_here"
   ```
5. Click **Deploy**. You'll get a public URL.

## How it works

```
┌─────────────────────┐
│  Brand Voice Tab    │  Paste samples → VoiceExtractor → voice profile (JSON)
└──────────┬──────────┘
           │ profile saved to session state
           ▼
┌─────────────────────┐
│  Generate Tab       │  Form inputs + voice profile → ContentGenerator
└──────────┬──────────┘
           │ one LLM call returns variants with strategy + scores
           ▼
┌─────────────────────┐
│  Output             │  Rendered variant cards + downloadable JSON/Markdown
└─────────────────────┘
```

**Two LLM calls total** for a full workflow:
1. Voice extraction (once per voice profile)
2. Generation (one call returns variants, strategies, and scores together)

Cost per workflow is well within the free tier.

## Project structure

```
voiceprint/
├── app.py                          # Streamlit dashboard
├── src/
│   ├── content_types.py            # Format, tone, language definitions
│   ├── strategies.py               # 9 persuasion strategies with colors
│   ├── prompts.py                  # Generation + voice extraction templates
│   ├── generator.py                # ContentGenerator + VoiceExtractor
│   └── rate_limiter.py             # Session-level cost protection
├── tests/
│   └── test_prompts.py             # 16 unit tests, runs in CI
├── .streamlit/
│   ├── config.toml                 # Dark theme
│   └── secrets.toml.example
├── .github/workflows/tests.yml     # CI on every push
├── requirements.txt
├── README.md
└── LICENSE
```

## Design notes

A few choices worth explaining if you're forking this:

**Prompts are isolated.** `src/prompts.py` holds every template. Iterating on copy quality is just editing that file. No API plumbing to touch.

**System instructions stay separate.** Gemini follows system instructions far more reliably than concatenated prefixes in the user prompt. We pass them via `system_instruction` in `GenerateContentConfig`.

**Pydantic validates every LLM response.** LLMs occasionally return malformed JSON despite asking nicely. We validate against `GenerationResult` and `VoiceProfile` models. If validation fails, the user sees a clean error instead of a stack trace.

**JSON parsing is tolerant.** `parse_json_tolerant` strips markdown fences and falls back to extracting the first `{...}` block. Defensive but not paranoid.

**Strategies live in data, not code.** Adding a new persuasion angle is one entry in `STRATEGIES`. The prompt template, the UI badge color, and the schema all pick it up automatically.

**No global rate limiter (yet).** Streamlit Community Cloud has ephemeral disk, so file-based counters don't survive restarts. For a true global cap, plug in Upstash Redis free tier in v2.

## Roadmap

- Star and unstar variants, then use stars as few-shot examples in the next generation
- Multi-channel export (one click: get aligned LinkedIn + Twitter + email subject for the same campaign)
- Compliance flagging for regulated industries (medical, financial)
- Voice profile sharing via export/import JSON
- Self-hosted LLM option via Ollama (Llama 3, Mistral) for privacy-conscious users

## Built with

- [Streamlit](https://streamlit.io) for the dashboard
- [Google Gemini](https://ai.google.dev) for generation (`google-genai` SDK)
- [Pydantic](https://docs.pydantic.dev) for response validation
- [pytest](https://pytest.org) for CI

## License

MIT. Use it, fork it, ship it.
