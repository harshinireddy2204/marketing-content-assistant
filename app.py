"""Voiceprint - Marketing copy that sounds like you, not like AI.

Run locally:
    streamlit run app.py
"""

import json
from datetime import datetime
from typing import Any

import streamlit as st

from src.content_types import CONTENT_TYPES, INPUT_LIMITS, LANGUAGES, TONES
from src.generator import ContentGenerator, VoiceExtractor
from src.rate_limiter import SessionLimiter
from src.strategies import STRATEGIES, strategy_color


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Voiceprint",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Custom CSS for a polished dashboard look
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
    /* Remove default padding at top */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Header */
    .app-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.25rem;
    }
    .app-logo {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        background: linear-gradient(135deg, #8B5CF6 0%, #06B6D4 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 18px;
        color: white;
    }
    .app-title {
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, #E5E7EB 0%, #9CA3AF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .app-tagline {
        color: #9CA3AF;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    /* Metric cards */
    .metric-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #161A23;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1.25rem;
    }
    .metric-label {
        color: #9CA3AF;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        color: #E5E7EB;
        font-size: 1.6rem;
        font-weight: 700;
        line-height: 1;
    }
    .metric-sub {
        color: #6B7280;
        font-size: 0.8rem;
        margin-top: 0.4rem;
    }

    /* Variant cards */
    .variant-card {
        background: #161A23;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }
    .variant-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
    }
    .variant-label {
        color: #9CA3AF;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 600;
    }
    .variant-headline {
        color: #F3F4F6;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .variant-body {
        color: #D1D5DB;
        line-height: 1.6;
        white-space: pre-wrap;
    }

    /* Strategy badge */
    .strategy-badge {
        display: inline-block;
        padding: 0.25rem 0.625rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.01em;
    }

    /* Score ring */
    .score-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(139, 92, 246, 0.12);
        border: 1px solid rgba(139, 92, 246, 0.3);
        color: #C4B5FD;
        padding: 0.25rem 0.625rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .score-pill.good { background: rgba(16, 185, 129, 0.12); border-color: rgba(16, 185, 129, 0.3); color: #6EE7B7; }
    .score-pill.mid  { background: rgba(245, 158, 11, 0.12); border-color: rgba(245, 158, 11, 0.3); color: #FCD34D; }
    .score-pill.low  { background: rgba(239, 68, 68, 0.12);  border-color: rgba(239, 68, 68, 0.3);  color: #FCA5A5; }

    /* Sub-score chips */
    .subscore-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-top: 0.75rem;
    }
    .subscore {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.06);
        color: #9CA3AF;
        padding: 0.2rem 0.55rem;
        border-radius: 6px;
        font-size: 0.72rem;
    }
    .subscore b { color: #E5E7EB; }

    /* Hide Streamlit branding */
    #MainMenu, footer { visibility: hidden; }

    /* Smooth selectbox in dark */
    .stSelectbox label, .stTextInput label, .stTextArea label, .stSlider label {
        color: #D1D5DB !important;
        font-weight: 500;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# State initialization
# ---------------------------------------------------------------------------
limiter = SessionLimiter(max_per_session=10)

if "voice_profile" not in st.session_state:
    st.session_state.voice_profile = None
if "use_voice_profile" not in st.session_state:
    st.session_state.use_voice_profile = True
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "history" not in st.session_state:
    st.session_state.history = []  # list of dicts: { ts, params, variants }


# ---------------------------------------------------------------------------
# Sidebar: settings and key management
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Settings")

    use_byok = st.toggle(
        "Use my own Gemini key",
        value=False,
        help="Recommended for heavy use. Free key from Google AI Studio. Your key is never stored.",
    )

    if use_byok:
        api_key = st.text_input(
            "Gemini API key",
            type="password",
            placeholder="AIza...",
        )
        st.caption(
            "Get a free key at [aistudio.google.com](https://aistudio.google.com/apikey)"
        )
    else:
        api_key = st.secrets.get("GEMINI_API_KEY", "")
        if not api_key:
            st.warning(
                "No shared key configured. Enable 'Use my own key' and paste your free Gemini key."
            )

    st.divider()
    st.markdown("### Session")
    used, total = limiter.used, limiter.max_per_session
    st.progress(used / total, text=f"{used} of {total} generations used")
    if st.button("Reset session", use_container_width=True):
        limiter.reset()
        st.session_state.last_result = None
        st.session_state.history = []
        st.session_state.voice_profile = None
        st.rerun()

    st.divider()
    st.markdown("### About")
    st.caption(
        "Voiceprint is an open source tool for marketers and founders. "
        "It learns your brand voice, generates copy in multiple strategies, "
        "and scores every output."
    )
    st.markdown(
        "[GitHub](https://github.com/YOUR_USERNAME/voiceprint)  ·  "
        "[LinkedIn](https://linkedin.com/in/YOUR_HANDLE)"
    )


# ---------------------------------------------------------------------------
# Helpers for rendering
# ---------------------------------------------------------------------------
def score_class(score: float) -> str:
    if score >= 8.0:
        return "good"
    if score >= 6.5:
        return "mid"
    return "low"


def render_variant(variant: dict[str, Any], index: int) -> None:
    """Render one variant card with strategy badge and scores."""
    strategy = variant.get("strategy", "")
    color = strategy_color(strategy)
    badge_bg = color + "22"  # add alpha
    badge_border = color + "66"

    scores = variant.get("scores") or {}
    overall = 0.0
    if scores:
        overall = round(sum(scores.values()) / len(scores), 1)

    with st.container():
        st.markdown(
            f"""
<div class="variant-card">
    <div class="variant-header">
        <span class="variant-label">Variant {index}</span>
        <div style="display:flex; gap:0.5rem; align-items:center;">
            <span class="strategy-badge" style="background:{badge_bg}; border:1px solid {badge_border}; color:{color};">
                {strategy}
            </span>
            <span class="score-pill {score_class(overall)}">★ {overall}</span>
        </div>
    </div>
""",
            unsafe_allow_html=True,
        )

        if variant.get("headline"):
            st.markdown(
                f"<div class='variant-headline'>{variant['headline']}</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"<div class='variant-body'>{variant['body']}</div>",
            unsafe_allow_html=True,
        )

        if scores:
            sub = "".join(
                f"<span class='subscore'>{k.replace('_',' ')} <b>{v}</b></span>"
                for k, v in scores.items()
            )
            st.markdown(
                f"<div class='subscore-row'>{sub}</div>",
                unsafe_allow_html=True,
            )

        if variant.get("rationale"):
            with st.expander("Why this strategy"):
                st.caption(variant["rationale"])

        with st.expander("Copy text"):
            text = (
                f"{variant['headline']}\n\n{variant['body']}"
                if variant.get("headline")
                else variant["body"]
            )
            st.code(text, language=None)

        st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
<div class="app-header">
    <div class="app-logo">V</div>
    <div>
        <h1 class="app-title">Voiceprint</h1>
    </div>
</div>
<div class="app-tagline">Marketing copy that sounds like you, not like AI.</div>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Metric cards
# ---------------------------------------------------------------------------
voice_status = "Active" if st.session_state.voice_profile else "Not set"
history_count = len(st.session_state.history)
avg_score = "—"
if st.session_state.history:
    all_scores = []
    for entry in st.session_state.history:
        for v in entry.get("variants", []):
            if v.get("scores"):
                all_scores.append(sum(v["scores"].values()) / len(v["scores"]))
    if all_scores:
        avg_score = f"{round(sum(all_scores) / len(all_scores), 1)}/10"

st.markdown(
    f"""
<div class="metric-row">
    <div class="metric-card">
        <div class="metric-label">Generations</div>
        <div class="metric-value">{limiter.used} / {limiter.max_per_session}</div>
        <div class="metric-sub">This session</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Voice profile</div>
        <div class="metric-value">{voice_status}</div>
        <div class="metric-sub">{'Applied to all copy' if st.session_state.voice_profile else 'Build one in the Brand Voice tab'}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Avg quality</div>
        <div class="metric-value">{avg_score}</div>
        <div class="metric-sub">Across {history_count} generation{'s' if history_count != 1 else ''}</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_gen, tab_voice, tab_history = st.tabs(["Generate", "Brand Voice", "History"])


# ---------------------------------------------------------------------------
# Tab 1: Generate
# ---------------------------------------------------------------------------
with tab_gen:
    left, right = st.columns([1, 1.2], gap="large")

    with left:
        st.markdown("##### Input")

        product_name = st.text_input(
            "Product or brand name",
            placeholder="e.g. EcoFlow Bottle",
            max_chars=INPUT_LIMITS["product_name"],
        )
        product_description = st.text_area(
            "Product description",
            placeholder="e.g. Stainless steel water bottle. 24-hour cold retention. Made from 90% recycled materials.",
            max_chars=INPUT_LIMITS["product_description"],
            height=100,
        )
        audience = st.text_input(
            "Target audience (optional)",
            placeholder="e.g. Outdoor enthusiasts aged 25 to 40",
            max_chars=INPUT_LIMITS["audience"],
        )

        col_a, col_b = st.columns(2)
        with col_a:
            content_type = st.selectbox("Content type", list(CONTENT_TYPES.keys()))
        with col_b:
            tone = st.selectbox("Tone", TONES)

        col_c, col_d = st.columns(2)
        with col_c:
            language = st.selectbox("Language", LANGUAGES)
        with col_d:
            n_variants = st.slider("Variants", 1, 5, 3)

        with st.expander("Advanced"):
            keywords = st.text_input(
                "Keywords to include",
                placeholder="e.g. sustainable, lightweight",
                max_chars=INPUT_LIMITS["keywords"],
            )
            avoid = st.text_input(
                "Words to avoid",
                placeholder="e.g. cheap, basic",
                max_chars=INPUT_LIMITS["avoid"],
            )
            apply_voice = st.checkbox(
                "Apply brand voice profile",
                value=st.session_state.use_voice_profile,
                disabled=st.session_state.voice_profile is None,
                help="Only available after you build a voice profile in the Brand Voice tab.",
            )
            st.session_state.use_voice_profile = apply_voice

        gen_disabled = limiter.remaining() == 0 or not api_key
        generate = st.button(
            "Generate",
            type="primary",
            use_container_width=True,
            disabled=gen_disabled,
        )

    with right:
        st.markdown("##### Output")

        if generate:
            if not product_name.strip() or not product_description.strip():
                st.error("Product name and description are required.")
            else:
                with st.spinner("Generating variants and scoring them..."):
                    try:
                        profile_to_use = (
                            st.session_state.voice_profile
                            if (st.session_state.use_voice_profile and st.session_state.voice_profile)
                            else None
                        )
                        generator = ContentGenerator(api_key=api_key)
                        result = generator.generate(
                            product_name=product_name.strip(),
                            product_description=product_description.strip(),
                            audience=audience.strip(),
                            content_type=content_type,
                            tone=tone,
                            language=language,
                            n_variants=n_variants,
                            keywords=keywords.strip(),
                            avoid=avoid.strip(),
                            voice_profile=profile_to_use,
                        )
                        limiter.increment()
                        st.session_state.last_result = result
                        st.session_state.history.insert(
                            0,
                            {
                                "ts": datetime.now().strftime("%H:%M:%S"),
                                "product": product_name.strip(),
                                "content_type": content_type,
                                "tone": tone,
                                "language": language,
                                "variants": result["variants"],
                            },
                        )
                    except Exception as e:
                        msg = str(e)
                        if "API_KEY" in msg.upper() or "PERMISSION" in msg.upper():
                            st.error(
                                "Invalid or unauthorized API key. "
                                "Check your key at aistudio.google.com/apikey."
                            )
                        elif "QUOTA" in msg.upper() or "RATE" in msg.upper():
                            st.error(
                                "Gemini API quota exhausted. Try later or use your own key."
                            )
                        else:
                            st.error(f"Generation failed: {msg}")

        result = st.session_state.last_result
        if result:
            for i, variant in enumerate(result["variants"], 1):
                render_variant(variant, i)

            st.divider()
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    "Download JSON",
                    data=json.dumps(result, indent=2, ensure_ascii=False),
                    file_name="voiceprint_copy.json",
                    mime="application/json",
                    use_container_width=True,
                )
            with col_dl2:
                md_lines = []
                for i, v in enumerate(result["variants"], 1):
                    md_lines.append(f"## Variant {i} - {v.get('strategy', '')}\n")
                    if v.get("headline"):
                        md_lines.append(f"**{v['headline']}**\n")
                    md_lines.append(v["body"] + "\n")
                    if v.get("rationale"):
                        md_lines.append(f"_Why: {v['rationale']}_\n")
                st.download_button(
                    "Download Markdown",
                    data="\n".join(md_lines),
                    file_name="voiceprint_copy.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
        else:
            st.info(
                "Fill out the form on the left and click **Generate**. "
                "Each variant uses a different persuasion strategy and is scored "
                "on clarity, specificity, novelty, brand fit, and reading ease."
            )


# ---------------------------------------------------------------------------
# Tab 2: Brand Voice
# ---------------------------------------------------------------------------
with tab_voice:
    st.markdown("##### Build your brand voice profile")
    st.caption(
        "Paste 1 to 5 samples of your existing brand writing (about page, "
        "newsletter snippet, product page, recent social post). Voiceprint will "
        "distill them into a portable voice profile and apply it automatically "
        "to every future generation."
    )

    if st.session_state.voice_profile:
        st.success("Voice profile is active. New generations will use it.")
        with st.expander("Current profile", expanded=True):
            st.json(st.session_state.voice_profile)
        if st.button("Clear profile"):
            st.session_state.voice_profile = None
            st.rerun()

    st.markdown("---")

    samples_text = st.text_area(
        "Samples (one per blank line, or paste as one block)",
        placeholder=(
            "We started Acme because spreadsheets shouldn't make you cry. "
            "Now thousands of teams use us to plan, track, and ship faster.\n\n"
            "Here's something we noticed: most tools optimize for the manager. "
            "We optimize for the person who actually does the work."
        ),
        height=250,
        max_chars=INPUT_LIMITS["voice_sample"] * 5,
    )

    extract_disabled = limiter.remaining() == 0 or not api_key or not samples_text.strip()
    if st.button("Extract voice DNA", type="primary", disabled=extract_disabled):
        # Split samples by blank lines (heuristic but works well)
        raw = [s.strip() for s in samples_text.split("\n\n") if s.strip()]
        if not raw:
            st.error("Please paste at least one writing sample.")
        else:
            with st.spinner("Analyzing your writing..."):
                try:
                    extractor = VoiceExtractor(api_key=api_key)
                    profile = extractor.extract(raw)
                    st.session_state.voice_profile = profile
                    limiter.increment()
                    st.success("Voice profile extracted. Switch to Generate to use it.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Extraction failed: {e}")


# ---------------------------------------------------------------------------
# Tab 3: History
# ---------------------------------------------------------------------------
with tab_history:
    st.markdown("##### Session history")
    if not st.session_state.history:
        st.caption("No generations yet. Output from the Generate tab will appear here.")
    else:
        for i, entry in enumerate(st.session_state.history):
            with st.expander(
                f"{entry['ts']} - {entry['product']} - "
                f"{entry['content_type']} - {entry['tone']} - {entry['language']}",
                expanded=(i == 0),
            ):
                for j, v in enumerate(entry["variants"], 1):
                    render_variant(v, j)
