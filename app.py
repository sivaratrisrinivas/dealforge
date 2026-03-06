"""Streamlit UI for the Dealforge MVP."""

from __future__ import annotations

import streamlit as st

from agent import BlueprintResult, DealforgeError, generate_fal_blueprint_with_notes

MOCK_EMAIL = (
    "Hey Fal team, we are a massive e-commerce company. We need to process 100,000 "
    "product images a day. We need a custom deployment that uses a specific Dockerfile "
    "with ffmpeg installed, and it absolutely must run distributed across multiple H100 "
    "GPUs to handle the volume. Can you send us the deployment script?"
)


def _apply_theme() -> None:
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Instrument+Sans:wght@400;500;600;700&display=swap');

            :root {
                --bg: #101418;
                --panel: rgba(24, 31, 38, 0.92);
                --panel-alt: rgba(17, 22, 27, 0.9);
                --border: rgba(243, 176, 78, 0.26);
                --text: #eef2f3;
                --muted: #9ba8b4;
                --accent: #f3b04e;
                --accent-soft: rgba(243, 176, 78, 0.14);
                --success: #90d1a6;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(243, 176, 78, 0.09), transparent 28%),
                    radial-gradient(circle at top right, rgba(110, 149, 175, 0.11), transparent 24%),
                    linear-gradient(180deg, #0a0e12 0%, #101418 100%);
                color: var(--text);
                font-family: 'Instrument Sans', sans-serif;
            }

            .block-container {
                padding-top: 2.2rem;
                padding-bottom: 2rem;
                max-width: 1180px;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(13, 17, 22, 0.98), rgba(17, 22, 27, 0.95));
                border-right: 1px solid rgba(243, 176, 78, 0.12);
            }

            h1, h2, h3 {
                font-family: 'IBM Plex Mono', monospace;
                letter-spacing: 0.02em;
            }

            .hero-card {
                background: linear-gradient(180deg, rgba(24, 31, 38, 0.95), rgba(16, 20, 24, 0.96));
                border: 1px solid var(--border);
                border-radius: 24px;
                padding: 1.4rem 1.5rem 1.2rem;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.24);
                margin-bottom: 1.2rem;
            }

            .hero-kicker {
                color: var(--accent);
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.18em;
                margin-bottom: 0.6rem;
            }

            .hero-copy {
                color: var(--muted);
                max-width: 58rem;
                line-height: 1.6;
                margin-bottom: 0;
            }

            .stTextArea textarea {
                background: rgba(10, 14, 18, 0.94);
                color: var(--text);
                border: 1px solid rgba(243, 176, 78, 0.16);
                border-radius: 18px;
                font-family: 'IBM Plex Mono', monospace;
                min-height: 320px;
            }

            .stTextArea label, .stButton button, .stCodeBlock {
                font-family: 'IBM Plex Mono', monospace;
            }

            .stButton button {
                background: linear-gradient(135deg, #f3b04e, #df8c28);
                color: #111418;
                border: none;
                border-radius: 999px;
                font-weight: 700;
                padding: 0.7rem 1.1rem;
                box-shadow: 0 14px 24px rgba(223, 140, 40, 0.22);
            }

            .stButton button:hover {
                background: linear-gradient(135deg, #ffc466, #f39d37);
                color: #101418;
            }

            .result-card {
                background: linear-gradient(180deg, rgba(18, 24, 29, 0.95), rgba(12, 16, 20, 0.97));
                border: 1px solid rgba(144, 209, 166, 0.16);
                border-radius: 24px;
                padding: 1.2rem 1.3rem;
                margin-top: 1rem;
            }

            .result-label {
                color: var(--success);
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.18em;
                margin-bottom: 0.65rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_state() -> None:
    st.session_state.setdefault("client_email", "")
    st.session_state.setdefault("blueprint", None)
    st.session_state.setdefault("error_message", "")


def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### Intake Controls")
        st.caption("Seed the editor with a representative enterprise request.")
        if st.button("Mock Client Email", use_container_width=True):
            st.session_state["client_email"] = MOCK_EMAIL
            st.session_state["error_message"] = ""

        st.markdown("---")
        st.caption("Prerequisites")
        st.write("- Run `python ingest.py` once")
        st.write("- Keep Fal docs in `./fal_docs` or set `DEALFORGE_DOCS_DIR`")
        st.write("- Set `GOOGLE_API_KEY` or `GEMINI_API_KEY` in `.env` (or export)")
        st.write("- Launch with `streamlit run app.py`")


def _render_header() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-kicker">Dealforge / Fal Solutions Engineering MVP</div>
            <h1>Translate ambiguous client asks into deployment-grade Fal blueprints.</h1>
            <p class="hero-copy">
                Paste a messy enterprise requirement, retrieve the local Fal documentation export,
                and generate an AST-validated Python deployment script tuned for distributed GPU serving.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_result(result: BlueprintResult) -> None:
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown('<div class="result-label">Generated Python Blueprint</div>', unsafe_allow_html=True)
    st.code(result.code, language="python")
    st.markdown('<div class="result-label">Deployment Notes</div>', unsafe_allow_html=True)
    st.write(result.explanation)
    if result.readme:
        st.markdown('<div class="result-label">README — CLI commands</div>', unsafe_allow_html=True)
        st.markdown(result.readme)
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="Dealforge MVP", layout="wide")
    _apply_theme()
    _init_state()
    _render_sidebar()
    _render_header()

    st.subheader("Client Requirements")
    email_text = st.text_area(
        "Paste the client request or populate it from the sidebar.",
        key="client_email",
        placeholder="Paste an email thread, statement of work, or customer requirement summary...",
    )

    if st.button("Generate Enterprise Blueprint", use_container_width=True):
        if not email_text.strip():
            st.session_state["error_message"] = "Paste client requirements before generating a blueprint."
            st.session_state["blueprint"] = None
        else:
            st.session_state["error_message"] = ""
            with st.spinner("Querying Dealforge retrieval stack and validating generated Python..."):
                try:
                    st.session_state["blueprint"] = generate_fal_blueprint_with_notes(email_text)
                except DealforgeError as exc:
                    st.session_state["blueprint"] = None
                    st.session_state["error_message"] = str(exc)
                except Exception as exc:  # pragma: no cover - defensive UI guard
                    st.session_state["blueprint"] = None
                    st.session_state["error_message"] = (
                        "Unexpected failure while generating the blueprint: "
                        f"{exc}"
                    )

    if st.session_state["error_message"]:
        if "cannot be empty" in st.session_state["error_message"].lower():
            st.warning(st.session_state["error_message"])
        else:
            st.error(st.session_state["error_message"])

    blueprint = st.session_state.get("blueprint")
    if blueprint:
        _render_result(blueprint)


if __name__ == "__main__":
    main()
