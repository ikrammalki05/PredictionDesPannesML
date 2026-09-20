"""
ONEE Predictive System — Global CSS styling for Streamlit
"""

ONEE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ─── Root variables ─────────────────────────────────────────── */
:root {
    --bg-primary:    #0a1628;
    --bg-secondary:  #0d1f3c;
    --bg-card:       rgba(255,255,255,0.05);
    --accent-cyan:   #00d4ff;
    --accent-blue:   #1a6fff;
    --accent-green:  #00e676;
    --accent-orange: #ff9800;
    --accent-red:    #ff5252;
    --text-primary:  #e8f0fe;
    --text-muted:    #8b9cbd;
    --border:        rgba(0, 212, 255, 0.15);
    --shadow:        0 8px 32px rgba(0,0,0,0.4);
    --glass:         rgba(255,255,255,0.04);
}

/* ─── Global reset ────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg-primary) !important;
    color: var(--text-primary) !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1f3c 0%, #071020 100%) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

/* ─── Sidebar title ───────────────────────────────────────────── */
.sidebar-logo {
    text-align: center;
    padding: 1.2rem 0 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}
.sidebar-logo h2 {
    font-size: 1.3rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.sidebar-logo p {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin: 0.2rem 0 0;
}

/* ─── Metric cards ────────────────────────────────────────────── */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.2rem 1.4rem;
    backdrop-filter: blur(12px);
    box-shadow: var(--shadow);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-blue));
}
.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 40px rgba(0,0,0,0.5);
}
.metric-card .metric-icon {
    font-size: 2rem;
    margin-bottom: 0.4rem;
}
.metric-card .metric-value {
    font-size: 2rem;
    font-weight: 800;
    color: var(--accent-cyan);
    line-height: 1;
}
.metric-card .metric-label {
    font-size: 0.78rem;
    color: var(--text-muted);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-top: 0.3rem;
}
.metric-card .metric-delta {
    font-size: 0.75rem;
    margin-top: 0.4rem;
    font-weight: 600;
}
.metric-card .metric-delta.up   { color: var(--accent-green); }
.metric-card .metric-delta.down { color: var(--accent-red);   }

/* ─── Page header ─────────────────────────────────────────────── */
.page-header {
    background: linear-gradient(135deg, rgba(0,212,255,0.08) 0%, rgba(26,111,255,0.06) 100%);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.8rem 2rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.page-header::after {
    content: '';
    position: absolute;
    top: -50%; right: -10%;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(0,212,255,0.06) 0%, transparent 70%);
    border-radius: 50%;
}
.page-header h1 {
    font-size: 1.8rem;
    font-weight: 800;
    margin: 0 0 0.3rem;
    background: linear-gradient(135deg, #ffffff, var(--accent-cyan));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.page-header p {
    font-size: 0.9rem;
    color: var(--text-muted);
    margin: 0;
}

/* ─── Risk badge ──────────────────────────────────────────────── */
.risk-badge {
    display: inline-block;
    padding: 0.3rem 0.9rem;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.risk-low    { background: rgba(0,230,118,0.15); color: var(--accent-green); border: 1px solid rgba(0,230,118,0.3); }
.risk-medium { background: rgba(255,152,0,0.15); color: var(--accent-orange); border: 1px solid rgba(255,152,0,0.3); }
.risk-high   { background: rgba(255,82,82,0.15); color: var(--accent-red); border: 1px solid rgba(255,82,82,0.3); }

/* ─── Section title ───────────────────────────────────────────── */
.section-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text-primary);
    border-left: 3px solid var(--accent-cyan);
    padding-left: 0.8rem;
    margin: 1.5rem 0 0.8rem;
}

/* ─── Streamlit element overrides ────────────────────────────── */
div[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}
div[data-testid="stMetricValue"] > div {
    color: var(--accent-cyan) !important;
    font-weight: 700 !important;
}

/* Inputs */
div[data-baseweb="input"] input,
div[data-baseweb="select"] div,
div[data-baseweb="slider"] {
    background-color: rgba(255,255,255,0.06) !important;
    border-color: var(--border) !important;
    color: var(--text-primary) !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue)) !important;
    color: #000 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 2rem !important;
    transition: opacity 0.2s, transform 0.1s !important;
}
.stButton > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Tabs */
button[data-baseweb="tab"] {
    font-weight: 600 !important;
    color: var(--text-muted) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--accent-cyan) !important;
    border-bottom-color: var(--accent-cyan) !important;
}

/* Selectbox label */
label[data-testid="stWidgetLabel"] {
    color: var(--text-muted) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}

/* Spinner */
[data-testid="stSpinner"] p {
    color: var(--accent-cyan) !important;
}

/* Alert boxes */
.stAlert {
    border-radius: 12px !important;
}

/* Footer */
.main-footer {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.75rem;
    padding: 2rem 0 1rem;
    border-top: 1px solid var(--border);
    margin-top: 3rem;
}

/* Prediction result box */
.prediction-box {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2rem;
    text-align: center;
    backdrop-filter: blur(12px);
}
.prediction-box .proba-value {
    font-size: 4rem;
    font-weight: 900;
    line-height: 1;
    margin: 0.5rem 0;
}
.prediction-box .proba-label {
    font-size: 0.85rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
</style>
"""


def apply_css():
    """Inject the global CSS into the Streamlit page."""
    import streamlit as st
    st.markdown(ONEE_CSS, unsafe_allow_html=True)


def metric_card(icon: str, value: str, label: str, delta: str = "", delta_dir: str = ""):
    """Render a custom metric card via HTML."""
    delta_html = ""
    if delta:
        delta_class = "up" if delta_dir == "up" else ("down" if delta_dir == "down" else "")
        arrow = "▲ " if delta_dir == "up" else ("▼ " if delta_dir == "down" else "")
        delta_html = f'<div class="metric-delta {delta_class}">{arrow}{delta}</div>'

    return f"""
    <div class="metric-card">
        <div class="metric-icon">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """


def page_header(title: str, subtitle: str = ""):
    """Render a premium page header."""
    sub_html = f'<p>{subtitle}</p>' if subtitle else ""
    return f"""
    <div class="page-header">
        <h1>{title}</h1>
        {sub_html}
    </div>
    """


def section_title(text: str):
    return f'<div class="section-title">{text}</div>'


def risk_badge(level: str) -> str:
    css = {"Low": "risk-low", "Medium": "risk-medium", "High": "risk-high"}.get(level, "risk-medium")
    return f'<span class="risk-badge {css}">{level}</span>'
