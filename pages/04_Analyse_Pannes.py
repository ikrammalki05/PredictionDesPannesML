"""
Page 3 — Analyse des pannes
Filtres dynamiques, heatmap temporelle, types, coûts, durées
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import CITY_COORDS, load_equipments, load_failures
from utils.styling import apply_css, metric_card, page_header, section_title

st.set_page_config(page_title="Analyse des Pannes — ONEE", page_icon="📊", layout="wide")
apply_css()

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h2>⚡ ONEE Smart Grid</h2>
        <p>Analyse des Pannes</p>
    </div>
    """, unsafe_allow_html=True)

    st.caption("Filtres")
    severity_filter = st.multiselect("Sévérité", ["High", "Medium", "Low"], default=["High", "Medium", "Low"])
    city_filter     = st.multiselect("Ville", list(CITY_COORDS.keys()), default=[])
    year_filter     = st.multiselect("Année", [2021, 2022, 2023, 2024], default=[2021, 2022, 2023, 2024])

st.markdown(page_header("📊 Analyse des Pannes",
                         "Exploration approfondie des incidents sur le réseau ONEE"),
            unsafe_allow_html=True)

# ─── Load ─────────────────────────────────────────────────────────────────────
with st.spinner("Chargement…"):
    failures = load_failures()
    equips   = load_equipments()

if failures.empty:
    st.error("Aucune donnée de pannes disponible.")
    st.stop()

# ─── Merge and filter ─────────────────────────────────────────────────────────
df = failures.copy()
if not equips.empty and "equipment_id" in df.columns:
    df = df.merge(
        equips[["equipment_id", "city", "network_type", "equipment_type"]],
        on="equipment_id", how="left"
    )

if severity_filter and "severity" in df.columns:
    df = df[df["severity"].isin(severity_filter)]
if city_filter and "city" in df.columns:
    df = df[df["city"].isin(city_filter)]
if year_filter and "failure_date" in df.columns:
    df = df[df["failure_date"].dt.year.isin(year_filter)]

if df.empty:
    st.warning("Aucune panne ne correspond aux filtres sélectionnés.")
    st.stop()

# ─── KPIs ─────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
total_cost = df["repair_cost_MAD"].sum() if "repair_cost_MAD" in df.columns else 0
avg_down   = df["downtime_hours"].mean() if "downtime_hours" in df.columns else 0
avg_repair = df["repair_duration_hours"].mean() if "repair_duration_hours" in df.columns else 0
n_types    = df["failure_type"].nunique() if "failure_type" in df.columns else 0

with k1: st.markdown(metric_card("💥", f"{len(df):,}", "Pannes filtrées"), unsafe_allow_html=True)
with k2: st.markdown(metric_card("💰", f"{total_cost/1e6:.1f}M MAD", "Coût total réparations"), unsafe_allow_html=True)
with k3: st.markdown(metric_card("⏱️", f"{avg_down:.1f}h", "Durée arrêt moyenne"), unsafe_allow_html=True)
with k4: st.markdown(metric_card("🔧", f"{n_types}", "Types de pannes distincts"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Failure type + cause ─────────────────────────────────────────────────────
col_left, col_right = st.columns(2, gap="large")

with col_left:
    st.markdown(section_title("💥 Répartition par type de panne"), unsafe_allow_html=True)
    if "failure_type" in df.columns:
        type_data = df["failure_type"].value_counts().reset_index()
        type_data.columns = ["type", "count"]
        fig_type = px.bar(
            type_data, x="count", y="type", orientation="h",
            color="count",
            color_continuous_scale=[[0, "#1a6fff"], [1, "#00d4ff"]],
            labels={"count": "Nombre", "type": ""},
        )
        fig_type.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b9cbd"), coloraxis_showscale=False,
            height=320, margin=dict(l=0, r=10, t=10, b=0),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig_type, use_container_width=True)

with col_right:
    st.markdown(section_title("🔍 Causes principales"), unsafe_allow_html=True)
    if "failure_cause" in df.columns:
        cause_data = df["failure_cause"].value_counts().head(8).reset_index()
        cause_data.columns = ["cause", "count"]
        fig_cause = px.pie(
            cause_data, values="count", names="cause", hole=0.5,
            color_discrete_sequence=px.colors.sequential.Blues_r,
        )
        fig_cause.update_traces(textinfo="percent+label", textfont_size=11)
        fig_cause.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e8f0fe"),
            showlegend=False, height=320, margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig_cause, use_container_width=True)

# ─── Temporal heatmap ─────────────────────────────────────────────────────────
st.markdown(section_title("🗓️ Heatmap temporelle — Pannes par mois et heure"), unsafe_allow_html=True)

if "failure_date" in df.columns:
    df_h = df.dropna(subset=["failure_date"]).copy()
    df_h["month_name"] = df_h["failure_date"].dt.strftime("%b %Y")
    df_h["hour"]       = df_h["failure_date"].dt.hour

    heat = df_h.groupby(["hour", df_h["failure_date"].dt.month]).size().unstack(fill_value=0)
    month_labels = ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun", "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
    heat.columns = [month_labels[c - 1] for c in heat.columns]

    fig_heat = go.Figure(go.Heatmap(
        z=heat.values,
        x=heat.columns,
        y=[f"{h:02d}h" for h in heat.index],
        colorscale=[[0, "#0a1628"], [0.5, "#1a6fff"], [1, "#00d4ff"]],
        hovertemplate="Mois: %{x}<br>Heure: %{y}<br>Pannes: %{z}<extra></extra>",
    ))
    fig_heat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8b9cbd"), height=350,
        margin=dict(l=40, r=10, t=10, b=0),
        xaxis=dict(title="Mois"),
        yaxis=dict(title="Heure"),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ─── Cost vs downtime scatter ─────────────────────────────────────────────────
col_s, col_c = st.columns(2, gap="large")

with col_s:
    st.markdown(section_title("💰 Coût vs Durée d'arrêt"), unsafe_allow_html=True)
    if "repair_cost_MAD" in df.columns and "downtime_hours" in df.columns:
        sample = df.dropna(subset=["repair_cost_MAD", "downtime_hours"]).sample(min(2000, len(df)), random_state=42)
        color_col = "severity" if "severity" in sample.columns else None
        color_map = {"High": "#ff5252", "Medium": "#ff9800", "Low": "#00e676"}
        fig_sc = px.scatter(
            sample, x="downtime_hours", y="repair_cost_MAD",
            color=color_col, color_discrete_map=color_map,
            opacity=0.6,
            labels={"downtime_hours": "Durée arrêt (h)", "repair_cost_MAD": "Coût réparation (MAD)"},
            hover_data=["failure_type"] if "failure_type" in sample.columns else None,
        )
        fig_sc.update_traces(marker_size=5)
        fig_sc.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b9cbd"), height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            legend=dict(font=dict(color="#8b9cbd"), bgcolor="rgba(0,0,0,0)"),
        )
        st.plotly_chart(fig_sc, use_container_width=True)

with col_c:
    st.markdown(section_title("🏙️ Pannes par ville"), unsafe_allow_html=True)
    if "city" in df.columns:
        city_data = df["city"].value_counts().reset_index()
        city_data.columns = ["city", "count"]
        fig_city = px.bar(
            city_data, x="city", y="count",
            color="count",
            color_continuous_scale=[[0, "#1a6fff"], [1, "#00d4ff"]],
            labels={"city": "Ville", "count": "Pannes"},
        )
        fig_city.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b9cbd"), coloraxis_showscale=False,
            height=300, margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(gridcolor="rgba(0,0,0,0)", tickangle=-30),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        )
        st.plotly_chart(fig_city, use_container_width=True)

# ─── Detail table ─────────────────────────────────────────────────────────────
st.markdown(section_title("📋 Tableau détaillé des pannes"), unsafe_allow_html=True)
display_cols = [c for c in ["failure_id", "equipment_id", "city", "failure_date",
                              "failure_type", "failure_cause", "severity",
                              "repair_cost_MAD", "downtime_hours", "resolved"]
                if c in df.columns]
st.dataframe(
    df[display_cols].sort_values("failure_date", ascending=False).head(200).reset_index(drop=True),
    use_container_width=True, hide_index=True,
)

st.markdown('<div class="main-footer">ONEE Smart Grid Intelligence Platform · 2021–2024</div>', unsafe_allow_html=True)
