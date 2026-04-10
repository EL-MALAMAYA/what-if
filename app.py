import base64
import json
import os
from pathlib import Path
from textwrap import dedent

from dotenv import load_dotenv
import streamlit as st
from simulation import run_simulation, _get_missing_vars

load_dotenv()

_ROOT = Path(__file__).resolve().parent
_LOGO_SVG = _ROOT / "assets" / "logo.svg"
_LOGO_PNG = _ROOT / "assets" / "logo.png"
_PROFILES_PATH = _ROOT / "profiles.json"


def _logo_asset_path() -> Path | None:
    if _LOGO_SVG.is_file():
        return _LOGO_SVG
    if _LOGO_PNG.is_file():
        return _LOGO_PNG
    return None


def _logo_data_uri() -> str | None:
    path = _logo_asset_path()
    if path is None:
        return None
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode()
    if path.suffix.lower() == ".svg":
        return f"data:image/svg+xml;base64,{b64}"
    return f"data:image/png;base64,{b64}"


with open(_PROFILES_PATH, "r", encoding="utf-8") as _f:
    _raw = json.load(_f)

countries_list = _raw["countries"]
relations_list = _raw["relations"]

countries_by_region: dict[str, list[dict]] = {}
for _c in countries_list:
    countries_by_region.setdefault(_c["region"], []).append(_c)

st.set_page_config(
    page_title="What If: Global Consequence Engine",
    page_icon=str(_p) if (_p := _logo_asset_path()) else "🌐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Use st.html (not st.markdown) for global CSS. Streamlit's markdown sanitizer strips
# <style> tags and leaves the stylesheet text visible in the page body.
st.html(
    dedent("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Roboto+Mono:wght@400;500;600&display=swap');
    @import url('https://unpkg.com/lucide-static@latest/font/lucide.css');

    /* ===== GLOBAL OVERRIDES ===== */
    :root {
        --bg-primary: #0b0f19;
        --bg-panel: rgba(15, 23, 42, 0.6);
        --bg-panel-solid: #0f172a;
        --border-color: #1e293b;
        --accent-cyan: #00d4ff;
        --accent-blue: #3b82f6;
        --accent-emerald: #10b981;
        --accent-amber: #f59e0b;
        --accent-red: #ef4444;
        --text-primary: #e2e8f0;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
        --font-mono: 'Roboto Mono', ui-monospace, monospace;
    }

    .stApp {
        background: var(--bg-primary) !important;
        color: var(--text-primary);
        font-family: var(--font-sans);
    }

    .stApp header,
    .stApp [data-testid="stHeader"] {
        background: transparent !important;
        display: none !important;
    }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem !important;
        max-width: 1400px;
    }

    h1, h2, h3, h4, h5, h6, p, li, span, div, label, input, textarea, button {
        font-family: var(--font-sans) !important;
        color: var(--text-primary);
    }

    /* Kill default Streamlit padding, toolbar, menu */
    #MainMenu, footer, .stDeployButton,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] { display: none !important; }

    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {
        background: var(--bg-primary) !important;
        border-right: 1px solid var(--border-color) !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: .5rem !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] li {
        color: var(--text-secondary) !important;
    }

    /* ===== .stCard — futuristic terminal panel ===== */
    .stCard {
        background-color: rgba(15, 23, 42, 0.6);
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 1.5rem;
        color: var(--text-primary);
        margin-bottom: 1rem;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }
    .stCard .card-label {
        font-family: var(--font-mono) !important;
        font-size: .65rem;
        font-weight: 600;
        letter-spacing: .14em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: .6rem;
        border-bottom: 1px solid rgba(30,41,59,.5);
        padding-bottom: .4rem;
    }

    /* ===== Legacy .card (backward compat, same aesthetic) ===== */
    .card {
        background-color: rgba(15, 23, 42, 0.6);
        border: 1px solid #1e293b;
        border-radius: 6px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
    }
    .card-label {
        font-family: var(--font-mono) !important;
        font-size: .65rem;
        font-weight: 600;
        letter-spacing: .14em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: .6rem;
        border-bottom: 1px solid rgba(30,41,59,.5);
        padding-bottom: .4rem;
    }

    /* ===== HEADER / BRAND ===== */
    .brand-bar {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1.25rem;
        flex-wrap: wrap;
        padding: 1.75rem 0 1rem;
    }
    .brand-bar .brand-logo-img {
        height: 76px;
        width: auto;
        display: block;
        flex-shrink: 0;
    }
    .dash-header {
        text-align: center;
        padding: 0 0 1rem;
    }
    .dash-header .tag {
        display: inline-block;
        background: rgba(0,212,255,.08);
        color: var(--accent-cyan);
        font-family: var(--font-mono) !important;
        font-size: .65rem;
        font-weight: 600;
        letter-spacing: .14em;
        text-transform: uppercase;
        padding: .3rem .8rem;
        border-radius: 3px;
        border: 1px solid rgba(0,212,255,.2);
        margin-bottom: .8rem;
    }
    .dash-header h1 {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, var(--accent-cyan) 50%, var(--accent-blue) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.15;
        letter-spacing: -.02em;
    }
    .dash-header .sub {
        color: var(--text-muted);
        font-size: .88rem;
        margin-top: .5rem;
        font-family: var(--font-mono) !important;
    }

    /* ===== INPUT AREA ===== */
    .stTextArea textarea {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
        color: var(--text-primary) !important;
        font-size: .9rem !important;
        padding: 1rem !important;
        font-family: var(--font-sans) !important;
        transition: border-color .2s, box-shadow .2s;
    }
    .stTextArea textarea:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 0 1px rgba(0,212,255,.2), 0 0 20px rgba(0,212,255,.05) !important;
    }
    .stTextArea label { display: none !important; }

    /* ===== BUTTON ===== */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)) !important;
        color: #0b0f19 !important;
        font-weight: 700 !important;
        font-size: .85rem !important;
        font-family: var(--font-mono) !important;
        letter-spacing: .06em;
        text-transform: uppercase;
        border: none !important;
        border-radius: 4px !important;
        padding: .65rem 2rem !important;
        transition: opacity .2s, transform .15s, box-shadow .2s;
        width: 100%;
    }
    .stButton > button:hover {
        opacity: .9 !important;
        transform: translateY(-1px);
        box-shadow: 0 0 20px rgba(0,212,255,.2) !important;
    }
    .stButton > button:active { transform: translateY(0); }

    /* ===== PREDICTION ===== */
    .prediction-text {
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.4;
    }

    /* ===== PROBABILITY RING ===== */
    .prob-wrap {
        display: flex;
        align-items: center;
        gap: 1.2rem;
    }
    .prob-ring {
        position: relative;
        width: 100px;
        height: 100px;
    }
    .prob-ring svg { transform: rotate(-90deg); }
    .prob-ring .track {
        fill: none;
        stroke: rgba(255,255,255,.04);
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
        font-family: var(--font-mono) !important;
        font-size: 1.4rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .prob-label {
        color: var(--text-secondary);
        font-size: .82rem;
        line-height: 1.5;
    }
    .prob-label strong {
        display: block;
        font-family: var(--font-mono) !important;
        font-size: .95rem;
        color: var(--text-primary);
        text-transform: uppercase;
        letter-spacing: .05em;
    }

    /* ===== REPORT ===== */
    .report-text {
        color: var(--text-secondary);
        font-size: .88rem;
        line-height: 1.8;
    }
    .report-text p { margin-bottom: .9rem; }

    /* ===== LINKS ===== */
    .link-item {
        display: flex;
        align-items: center;
        gap: .6rem;
        padding: .55rem .9rem;
        background: rgba(59,130,246,.04);
        border: 1px solid rgba(59,130,246,.12);
        border-radius: 4px;
        margin-bottom: .45rem;
        transition: background .2s, border-color .2s;
    }
    .link-item:hover {
        background: rgba(59,130,246,.1);
        border-color: rgba(59,130,246,.25);
    }
    .link-item a {
        color: var(--accent-blue);
        font-family: var(--font-mono) !important;
        font-size: .78rem;
        text-decoration: none;
        word-break: break-all;
        font-weight: 500;
    }
    .link-item a:hover { text-decoration: underline; }
    .link-item [class^="icon-"] { flex-shrink: 0; }

    /* ===== DIVIDER ===== */
    .divider {
        border: none;
        border-top: 1px solid var(--border-color);
        margin: 1.5rem 0;
    }

    /* ===== SPINNER ===== */
    .stSpinner > div { color: var(--accent-cyan) !important; }

    /* ===== LUCIDE ICON HELPERS ===== */
    [class^="icon-"], [class*=" icon-"] {
        vertical-align: -0.125em;
    }
    .card-label [class^="icon-"], .card-label [class*=" icon-"],
    .stCard .card-label [class^="icon-"], .stCard .card-label [class*=" icon-"] {
        margin-right: .35rem;
        font-size: .75rem;
        opacity: .6;
    }

    /* ===== KPI METRIC ===== */
    .kpi-metric {
        text-align: center;
        padding: 1rem 0;
    }
    .kpi-metric .kpi-value {
        font-family: var(--font-mono) !important;
        font-size: 4rem;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -.03em;
    }
    .kpi-metric .kpi-label {
        font-family: var(--font-mono) !important;
        font-size: .7rem;
        font-weight: 600;
        letter-spacing: .14em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-top: .4rem;
    }
    .kpi-metric .kpi-severity {
        font-family: var(--font-mono) !important;
        font-size: .85rem;
        font-weight: 700;
        letter-spacing: .1em;
        text-transform: uppercase;
        margin-top: .3rem;
    }

    /* ===== MINI PROFILE (right column) ===== */
    .mini-profile {
        margin-bottom: .6rem;
        padding-bottom: .6rem;
        border-bottom: 1px solid rgba(30,41,59,.4);
    }
    .mini-profile:last-child { border-bottom: none; }
    .mini-profile .mp-country {
        font-weight: 700;
        font-size: .82rem;
        color: var(--text-primary);
    }
    .mini-profile .mp-leader {
        font-size: .72rem;
        color: var(--text-muted);
        font-family: var(--font-mono) !important;
    }
    .mini-profile .mp-tags {
        margin-top: .25rem;
    }

    /* ===== STREAMLIT WIDGET OVERRIDES ===== */
    .stExpander {
        border-color: var(--border-color) !important;
    }
    .stExpander summary {
        color: var(--text-primary) !important;
    }
    [data-testid="stCaptionContainer"] {
        color: var(--text-muted) !important;
    }
    </style>
    """).strip(),
)

# ── Sidebar: Active Geopolitical Profiles ────────────────────────────────────────
CONTINENT_ICONS = {
    "North America": "\U0001F5FD",
    "South America": "\U0001F30E",
    "Europe": "\U0001F3F0",
    "Africa": "\U0001F30D",
    "Asia": "\U0001F3EF",
    "Oceania": "\U0001F30A",
}

RELATION_BADGES = {
    "ally": ("\U0001F91D", "#10b981"),
    "economic_partner": ("\U0001F4B1", "#3b82f6"),
    "hostile": ("\U000026A0\uFE0F", "#ef4444"),
    "neutral": ("\U00002796", "#64748b"),
    "strategic_competitor": ("\U00002694\uFE0F", "#f97316"),
}

with st.sidebar:
    st.markdown(
        "<div style='font-size:.7rem;font-weight:600;letter-spacing:.1em;"
        "text-transform:uppercase;color:#64748b;margin-bottom:.4rem'>"
        "<i class='icon-users' style='font-size:.7rem;margin-right:.35rem'></i>"
        "Active Geopolitical Profiles</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        f"{len(countries_list)} nations across {len(countries_by_region)} continents "
        f"| {len(relations_list)} mapped relations"
    )

    for continent, members in countries_by_region.items():
        icon = CONTINENT_ICONS.get(continent, "\U0001F310")
        with st.expander(f"{icon}  {continent}  ({len(members)})", expanded=False):
            for c in members:
                leader = c["leader"]
                _ds = c["decision_style"]
                if isinstance(_ds, dict):
                    _ds_display = ", ".join(
                        f"{k.replace('_', ' ')}: {v}" for k, v in _ds.items()
                    )
                else:
                    _ds_display = str(_ds)
                st.markdown(f"**{c['country']}** — {leader['name']}, *{leader['title']}*")
                st.markdown(
                    f"<span style='color:#94a3b8;font-size:.84rem'>"
                    f"<b>Decision style:</b> {_ds_display}</span>",
                    unsafe_allow_html=True,
                )

                interests_md = "".join(
                    f"<li style='color:#94a3b8;font-size:.8rem'>{ci}</li>"
                    for ci in c["core_interests"]
                )
                st.markdown(
                    f"<div style='font-size:.7rem;font-weight:600;color:#64748b;"
                    f"margin-top:.4rem;text-transform:uppercase;letter-spacing:.05em'>"
                    f"Core Interests</div>"
                    f"<ul style='margin:.1rem 0 .4rem;padding-left:1.2rem'>{interests_md}</ul>",
                    unsafe_allow_html=True,
                )

                red_lines_md = "".join(
                    f"<li style='color:#ef4444;font-size:.8rem'>"
                    f"<i class='icon-shield-alert' style='font-size:.7rem;margin-right:.3rem;opacity:.7'></i>{rl}</li>"
                    for rl in c.get("red_lines") or []
                )
                st.markdown(
                    f"<div style='font-size:.7rem;font-weight:600;color:#ef4444;"
                    f"margin-top:.3rem;text-transform:uppercase;letter-spacing:.05em'>"
                    f"Red Lines</div>"
                    f"<ul style='margin:.1rem 0 .4rem;padding-left:1.2rem'>{red_lines_md}</ul>",
                    unsafe_allow_html=True,
                )

                country_relations = [
                    r for r in relations_list
                    if r["from"] == c["country"] or r["to"] == c["country"]
                ]
                if country_relations:
                    rel_tags = ""
                    for r in country_relations:
                        partner = r["to"] if r["from"] == c["country"] else r["from"]
                        badge_icon, badge_color = RELATION_BADGES.get(r["type"], ("\U0001F310", "#64748b"))
                        rel_tags += (
                            f"<span style='display:inline-block;font-size:.75rem;padding:.15rem .5rem;"
                            f"margin:.15rem .2rem;border-radius:6px;border:1px solid {badge_color}33;"
                            f"color:{badge_color};background:{badge_color}11'>"
                            f"{badge_icon} {partner}</span>"
                        )
                    st.markdown(
                        f"<div style='font-size:.7rem;font-weight:600;color:#64748b;"
                        f"margin-top:.3rem;text-transform:uppercase;letter-spacing:.05em'>"
                        f"Relations</div><div style='margin:.2rem 0 .8rem'>{rel_tags}</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        "<div style='margin-bottom:.8rem'></div>",
                        unsafe_allow_html=True,
                    )

def _threat_color(probability: int) -> tuple[str, str]:
    """Return (hex color, severity label) based on probability score."""
    if probability >= 75:
        return "#ff3333", "Critical"
    elif probability >= 40:
        return "#ffcc00", "Warning"
    else:
        return "#00ffcc", "Stable"


# ── Header ──────────────────────────────────────────────────────────────────────
_logo_uri = _logo_data_uri()
_logo_html = (
    f'<img class="brand-logo-img" src="{_logo_uri}" alt="What-If.Live — Geo-politics simulator" />'
    if _logo_uri
    else ""
)
st.markdown(
    f"""
    <div class="brand-bar">
        {_logo_html}
        <div class="dash-header">
            <div class="tag"><i class="icon-radar" style="font-size:.75rem;margin-right:.3rem"></i>Multi-Agent Geopolitical Intelligence</div>
            <h1>What If: Global Consequence Engine</h1>
            <p class="sub">Pose a hypothetical scenario. Six continental AI analysts react. A director synthesizes the fallout.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Environment check ────────────────────────────────────────────────────────────
_missing_gmi = _get_missing_vars(provider="gmi")
if _missing_gmi:
    st.markdown(
        f"""
        <div class="card" style="border-color:var(--accent-amber)">
            <div class="card-label" style="color:var(--accent-amber)"><i class="icon-alert-triangle"></i>GMI Configuration Notice</div>
            <div style="color:var(--text-primary);font-size:.92rem;line-height:1.6">
                Missing GMI variable{'s' if len(_missing_gmi) > 1 else ''}: <code style="color:var(--accent-red)">{', '.join(_missing_gmi)}</code>.
                <br>You can still run simulations using the Claude provider toggle below.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Control Panel ────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="stCard"><div class="card-label">'
    '<i class="icon-radar"></i>Scenario Input</div>',
    unsafe_allow_html=True,
)
scenario = st.text_area(
    "scenario_input",
    placeholder="e.g. What if the US dollar lost its reserve currency status overnight?",
    height=100,
)
provider_label = st.radio(
    "model_provider",
    options=["GMI Cloud", "Claude API"],
    horizontal=True,
)
selected_provider = "claude" if provider_label == "Claude API" else "gmi"
claude_key_input = None
if selected_provider == "claude":
    claude_key_input = st.text_input(
        "Claude API Key (optional if CLAUDE_API_KEY is set in environment)",
        type="password",
        placeholder="sk-ant-api03-...",
    )
    if _get_missing_vars(provider="claude", claude_api_key=claude_key_input):
        st.info("Enter a Claude API key above or set CLAUDE_API_KEY in environment variables.")

col_l, col_btn, col_r = st.columns([3, 2, 3])
with col_btn:
    run_clicked = st.button("Run Simulation")
st.markdown("</div>", unsafe_allow_html=True)

# ── Simulation ───────────────────────────────────────────────────────────────────
if run_clicked:
    if not scenario.strip():
        st.warning("Please enter a scenario before running the simulation.")
    else:
        with st.spinner("Simulating global geopolitical fallout..."):
            data = run_simulation(
                scenario.strip(),
                provider=selected_provider,
                claude_api_key=(claude_key_input.strip() if claude_key_input else None),
            )

        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        probability = int(data.get("probability", 0))
        threat_hex, severity = _threat_color(probability)
        prediction = data.get("prediction", "No prediction available.")
        report = data.get("report", "")
        links = data.get("links", [])

        # ── 70 / 30 split ────────────────────────────────────────────────────
        col_main, col_right = st.columns([7, 3])

        # ── MAIN COLUMN (70%) ────────────────────────────────────────────────
        with col_main:
            # KPI Metric
            st.markdown(
                f"""
                <div class="stCard">
                    <div class="card-label"><i class="icon-activity"></i>Escalation Probability</div>
                    <div class="kpi-metric">
                        <div class="kpi-value" style="color:{threat_hex}">{probability}%</div>
                        <div class="kpi-severity" style="color:{threat_hex}">{severity}</div>
                        <div class="kpi-label">Likelihood of major global shift</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Prediction
            st.markdown(
                f"""
                <div class="stCard">
                    <div class="card-label"><i class="icon-crosshair"></i>Prediction</div>
                    <div class="prediction-text" style="border-bottom:3px solid {threat_hex};padding-bottom:.5rem">
                        {prediction}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Report
            paragraphs = [p.strip() for p in report.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [p.strip() for p in report.split("\n") if p.strip()]
            body_html = "".join(f"<p>{p}</p>" for p in paragraphs)

            st.markdown(
                f"""
                <div class="stCard">
                    <div class="card-label"><i class="icon-file-text"></i>Global Impact Report</div>
                    <div class="report-text">{body_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── RIGHT COLUMN (30%) ───────────────────────────────────────────────
        with col_right:
            # Active Profiles panel
            profiles_html = ""
            for continent, members in countries_by_region.items():
                c_icon = CONTINENT_ICONS.get(continent, "\U0001F310")
                profiles_html += (
                    f"<div style='font-size:.65rem;font-weight:600;color:var(--text-muted);"
                    f"text-transform:uppercase;letter-spacing:.1em;margin-top:.6rem;"
                    f"margin-bottom:.3rem'>{c_icon} {continent}</div>"
                )
                for c in members:
                    leader = c["leader"]
                    rel_for_country = [
                        r for r in relations_list
                        if r["from"] == c["country"] or r["to"] == c["country"]
                    ]
                    tags = ""
                    for r in rel_for_country[:4]:
                        partner = r["to"] if r["from"] == c["country"] else r["from"]
                        b_icon, b_color = RELATION_BADGES.get(r["type"], ("\U0001F310", "#64748b"))
                        tags += (
                            f"<span style='display:inline-block;font-size:.65rem;padding:.1rem .35rem;"
                            f"margin:.1rem .15rem 0 0;border-radius:3px;border:1px solid {b_color}33;"
                            f"color:{b_color};background:{b_color}11'>"
                            f"{b_icon} {partner}</span>"
                        )
                    profiles_html += (
                        f"<div class='mini-profile'>"
                        f"<div class='mp-country'>{c['country']}</div>"
                        f"<div class='mp-leader'>{leader['name']}, {leader['title']}</div>"
                        f"<div class='mp-tags'>{tags}</div>"
                        f"</div>"
                    )

            st.markdown(
                f"""
                <div class="stCard">
                    <div class="card-label"><i class="icon-users"></i>Active Geopolitical Profiles</div>
                    {profiles_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Live Data Sources panel
            if links:
                links_html = ""
                for url in links:
                    links_html += (
                        f'<div class="link-item">'
                        f'<i class="icon-external-link" style="color:var(--accent-blue);font-size:.75rem;flex-shrink:0"></i>'
                        f'<a href="{url}" target="_blank" rel="noopener">{url}</a>'
                        f"</div>"
                    )
                st.markdown(
                    f"""
                    <div class="stCard">
                        <div class="card-label"><i class="icon-bookmark"></i>Live Data Sources</div>
                        {links_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
