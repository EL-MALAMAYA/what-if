import streamlit as st
from simulation import run_simulation

st.set_page_config(
    page_title="What If: Global Consequence Engine",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    :root {
        --bg-primary: #0a0e17;
        --bg-secondary: #111827;
        --bg-card: #1a2332;
        --border-color: #1e3a5f;
        --accent-cyan: #00d4ff;
        --accent-blue: #3b82f6;
        --accent-emerald: #10b981;
        --accent-amber: #f59e0b;
        --accent-red: #ef4444;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
    }

    .stApp {
        background: var(--bg-primary);
        font-family: 'Inter', sans-serif;
    }

    .stApp header { background: transparent !important; }

    .block-container {
        padding-top: 2rem !important;
        max-width: 1100px;
    }

    h1, h2, h3, h4, p, li, span, div {
        font-family: 'Inter', sans-serif !important;
    }

    /* ---------- header ---------- */
    .dash-header {
        text-align: center;
        padding: 2.5rem 0 1rem;
    }
    .dash-header .tag {
        display: inline-block;
        background: rgba(0,212,255,.1);
        color: var(--accent-cyan);
        font-size: .7rem;
        font-weight: 600;
        letter-spacing: .12em;
        text-transform: uppercase;
        padding: .35rem .9rem;
        border-radius: 999px;
        border: 1px solid rgba(0,212,255,.25);
        margin-bottom: .8rem;
    }
    .dash-header h1 {
        font-size: 2.6rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, var(--accent-cyan) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.15;
    }
    .dash-header .sub {
        color: var(--text-secondary);
        font-size: .95rem;
        margin-top: .5rem;
    }

    /* ---------- input area ---------- */
    .stTextArea textarea {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        font-size: .95rem !important;
        padding: 1rem !important;
        font-family: 'Inter', sans-serif !important;
        transition: border-color .2s;
    }
    .stTextArea textarea:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 0 2px rgba(0,212,255,.15) !important;
    }
    .stTextArea label { display: none !important; }

    /* ---------- button ---------- */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)) !important;
        color: #000 !important;
        font-weight: 700 !important;
        font-size: .95rem !important;
        border: none !important;
        border-radius: 10px !important;
        padding: .7rem 2.4rem !important;
        letter-spacing: .03em;
        transition: opacity .2s, transform .15s;
        width: 100%;
    }
    .stButton > button:hover {
        opacity: .88 !important;
        transform: translateY(-1px);
    }
    .stButton > button:active { transform: translateY(0); }

    /* ---------- cards ---------- */
    .card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.2rem;
    }
    .card-label {
        font-size: .7rem;
        font-weight: 600;
        letter-spacing: .1em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: .6rem;
    }

    /* ---------- prediction ---------- */
    .prediction-text {
        font-size: 1.55rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.35;
    }

    /* ---------- probability ring ---------- */
    .prob-wrap {
        display: flex;
        align-items: center;
        gap: 1.4rem;
    }
    .prob-ring {
        position: relative;
        width: 100px;
        height: 100px;
    }
    .prob-ring svg { transform: rotate(-90deg); }
    .prob-ring .track {
        fill: none;
        stroke: rgba(255,255,255,.06);
        stroke-width: 8;
    }
    .prob-ring .bar {
        fill: none;
        stroke-width: 8;
        stroke-linecap: round;
        transition: stroke-dashoffset .8s ease;
    }
    .prob-value {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: 800;
        color: var(--text-primary);
    }
    .prob-label {
        color: var(--text-secondary);
        font-size: .85rem;
        line-height: 1.5;
    }
    .prob-label strong {
        display: block;
        font-size: 1rem;
        color: var(--text-primary);
    }

    /* ---------- report ---------- */
    .report-text {
        color: var(--text-secondary);
        font-size: .92rem;
        line-height: 1.75;
    }
    .report-text p { margin-bottom: 1rem; }

    /* ---------- links ---------- */
    .link-item {
        display: flex;
        align-items: center;
        gap: .6rem;
        padding: .65rem 1rem;
        background: rgba(59,130,246,.06);
        border: 1px solid rgba(59,130,246,.18);
        border-radius: 10px;
        margin-bottom: .55rem;
        transition: background .2s;
    }
    .link-item:hover { background: rgba(59,130,246,.12); }
    .link-item a {
        color: var(--accent-blue);
        font-size: .85rem;
        text-decoration: none;
        word-break: break-all;
        font-weight: 500;
    }
    .link-item a:hover { text-decoration: underline; }
    .link-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: var(--accent-blue);
        flex-shrink: 0;
    }

    /* ---------- divider ---------- */
    .divider {
        border: none;
        border-top: 1px solid var(--border-color);
        margin: 1.8rem 0;
    }

    /* ---------- spinner ---------- */
    .stSpinner > div { color: var(--accent-cyan) !important; }

    /* hide streamlit chrome */
    #MainMenu, footer, .stDeployButton { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Header ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="dash-header">
        <div class="tag">Multi-Agent Geopolitical Intelligence</div>
        <h1>What If: Global Consequence Engine</h1>
        <p class="sub">Pose a hypothetical scenario. Six continental AI analysts react. A director synthesizes the fallout.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Input ────────────────────────────────────────────────────────────────────────
scenario = st.text_area(
    "scenario_input",
    placeholder="e.g. What if the US dollar lost its reserve currency status overnight?",
    height=120,
)

col_l, col_btn, col_r = st.columns([2, 1, 2])
with col_btn:
    run_clicked = st.button("Run Simulation")

# ── Simulation ───────────────────────────────────────────────────────────────────
if run_clicked:
    if not scenario.strip():
        st.warning("Please enter a scenario before running the simulation.")
    else:
        with st.spinner("Simulating global geopolitical fallout..."):
            data = run_simulation(scenario.strip())

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        # ── Prediction ───────────────────────────────────────────────────────
        prediction = data.get("prediction", "No prediction available.")
        st.markdown(
            f"""
            <div class="card">
                <div class="card-label">Prediction</div>
                <div class="prediction-text">{prediction}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Probability + Report side-by-side ────────────────────────────────
        probability = int(data.get("probability", 0))
        report = data.get("report", "")

        if probability >= 75:
            ring_color = "var(--accent-red)"
            severity = "Critical"
        elif probability >= 50:
            ring_color = "var(--accent-amber)"
            severity = "Elevated"
        elif probability >= 25:
            ring_color = "var(--accent-cyan)"
            severity = "Moderate"
        else:
            ring_color = "var(--accent-emerald)"
            severity = "Low"

        circumference = 2 * 3.14159 * 42
        dash_offset = circumference * (1 - probability / 100)

        col_prob, col_report = st.columns([1, 3])

        with col_prob:
            st.markdown(
                f"""
                <div class="card">
                    <div class="card-label">Escalation Probability</div>
                    <div class="prob-wrap">
                        <div class="prob-ring">
                            <svg width="100" height="100" viewBox="0 0 100 100">
                                <circle class="track" cx="50" cy="50" r="42"/>
                                <circle class="bar" cx="50" cy="50" r="42"
                                    stroke="{ring_color}"
                                    stroke-dasharray="{circumference}"
                                    stroke-dashoffset="{dash_offset}"/>
                            </svg>
                            <div class="prob-value">{probability}%</div>
                        </div>
                        <div class="prob-label">
                            <strong>{severity}</strong>
                            Likelihood of major global shift
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_report:
            paragraphs = [p.strip() for p in report.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [p.strip() for p in report.split("\n") if p.strip()]
            body_html = "".join(f"<p>{p}</p>" for p in paragraphs)

            st.markdown(
                f"""
                <div class="card">
                    <div class="card-label">Global Impact Report</div>
                    <div class="report-text">{body_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── Reference Links ──────────────────────────────────────────────────
        links = data.get("links", [])
        if links:
            links_html = ""
            for url in links:
                links_html += (
                    f'<div class="link-item">'
                    f'<div class="link-dot"></div>'
                    f'<a href="{url}" target="_blank" rel="noopener">{url}</a>'
                    f"</div>"
                )
            st.markdown(
                f"""
                <div class="card">
                    <div class="card-label">Reference Sources</div>
                    {links_html}
                </div>
                """,
                unsafe_allow_html=True,
            )
