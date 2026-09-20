"""
Page 1 — Tableau de bord global
KPIs, carte des villes marocaines, tendances des pannes
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import (
    CITY_COORDS,
    load_alerts,
    load_equipments,
    load_failures,
    load_maintenance,
)
from utils.styling import apply_css, metric_card, page_header, section_title

st.set_page_config(page_title="Tableau de bord — ONEE", page_icon="", layout="wide")
apply_css()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h2> ONEE Predictive System</h2>
        <p>Tableau de Bord Global</p>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Filtres globaux")
    network_filter = st.selectbox("Réseau", ["Tous", "Electricity", "Water"])
    city_filter    = st.multiselect("Villes", list(CITY_COORDS.keys()), default=[])

# ─── Load data ────────────────────────────────────────────────────────────────
with st.spinner("Chargement des données…"):
    failures  = load_failures()
    equips    = load_equipments()
    alerts    = load_alerts()
    maint     = load_maintenance()

# ─── Apply filters ────────────────────────────────────────────────────────────
if not equips.empty:
    eq_filtered = equips.copy()
    if network_filter != "Tous" and "network_type" in eq_filtered.columns:
        eq_filtered = eq_filtered[eq_filtered["network_type"] == network_filter]
    if city_filter and "city" in eq_filtered.columns:
        eq_filtered = eq_filtered[eq_filtered["city"].isin(city_filter)]
    equip_ids = set(eq_filtered["equipment_id"]) if "equipment_id" in eq_filtered.columns else set()
else:
    eq_filtered = equips
    equip_ids   = set()

fail_filtered = failures.copy()
if not failures.empty and equip_ids:
    fail_filtered = failures[failures["equipment_id"].isin(equip_ids)]

# ─── Page header ──────────────────────────────────────────────────────────────
st.markdown(page_header(" Tableau de Bord Global", "Vue consolidée du réseau ONEE — Eau & Électricité"), unsafe_allow_html=True)

# ─── KPI row ──────────────────────────────────────────────────────────────────
n_equip    = len(eq_filtered)
n_failures = len(fail_filtered)
n_alerts   = len(alerts)
n_maint    = len(maint)
resolved_pct = int(fail_filtered["resolved"].astype(str).str.lower().eq("true").mean() * 100) if not fail_filtered.empty and "resolved" in fail_filtered.columns else 0
avg_cost   = f"{fail_filtered['repair_cost_MAD'].mean():,.0f}" if not fail_filtered.empty and "repair_cost_MAD" in fail_filtered.columns else "N/A"

k1, k2, k3, k4, k5 = st.columns(5)
with k1: st.markdown(metric_card("", f"{n_equip:,}", "Équipements"), unsafe_allow_html=True)
with k2: st.markdown(metric_card("", f"{n_failures:,}", "Pannes totales", "↓ en amélioration", "up"), unsafe_allow_html=True)
with k3: st.markdown(metric_card("", f"{resolved_pct} %", "Pannes résolues"), unsafe_allow_html=True)
with k4: st.markdown(metric_card("", f"{n_alerts:,}", "Alertes"), unsafe_allow_html=True)
with k5: st.markdown(metric_card("", f"{avg_cost} MAD", "Coût moy. réparation"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Map + Failures by city ───────────────────────────────────────────────────
col_map, col_bar = st.columns([1.4, 1], gap="large")

with col_map:
    st.markdown(section_title("️ Carte des équipements par ville"), unsafe_allow_html=True)

    if not equips.empty and "city" in equips.columns:
        city_counts = equips.groupby("city").size().reset_index(name="nb_equip")
        city_counts["lat"] = city_counts["city"].map(lambda c: CITY_COORDS.get(c, (30, -5))[0])
        city_counts["lon"] = city_counts["city"].map(lambda c: CITY_COORDS.get(c, (30, -5))[1])

        if not fail_filtered.empty and "equipment_id" in fail_filtered.columns:
            fail_city = (
                fail_filtered.merge(equips[["equipment_id", "city"]], on="equipment_id", how="left")
                .groupby("city").size().reset_index(name="nb_failures")
            )
            city_counts = city_counts.merge(fail_city, on="city", how="left").fillna(0)
        else:
            city_counts["nb_failures"] = 0

        fig_map = px.scatter_map(
            city_counts,
            lat="lat", lon="lon",
            size="nb_equip",
            color="nb_failures",
            hover_name="city",
            hover_data={"nb_equip": True, "nb_failures": True, "lat": False, "lon": False},
            color_continuous_scale=[[0, "#00d4ff"], [0.5, "#ff9800"], [1, "#ff5252"]],
            size_max=40,
            zoom=4.5,
            center={"lat": 31.5, "lon": -7.0},
            labels={"nb_equip": "Équipements", "nb_failures": "Pannes"},
        )
        fig_map.update_layout(
            map_style="carto-darkmatter",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=0, b=0),
            height=420,
            coloraxis_colorbar=dict(
                title=dict(text="Pannes", font=dict(color="#8b9cbd")),
                tickfont=dict(color="#8b9cbd"),
            ),
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Données de carte indisponibles.")

with col_bar:
    st.markdown(section_title(" Pannes par type d'équipement"), unsafe_allow_html=True)

    if not fail_filtered.empty and not equips.empty and "equipment_id" in fail_filtered.columns:
        merged = fail_filtered.merge(equips[["equipment_id", "equipment_type"]], on="equipment_id", how="left")
        if "equipment_type" in merged.columns:
            type_counts = merged["equipment_type"].value_counts().reset_index()
            type_counts.columns = ["type", "count"]
            fig_bar = px.bar(
                type_counts, x="count", y="type",
                orientation="h",
                color="count",
                color_continuous_scale=[[0, "#1a6fff"], [1, "#00d4ff"]],
                labels={"count": "Pannes", "type": ""},
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#8b9cbd"),
                showlegend=False,
                coloraxis_showscale=False,
                height=200,
                margin=dict(l=0, r=10, t=10, b=0),
                xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
                yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            )
            fig_bar.update_traces(marker_line_width=0)
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown(section_title(" Sévérité des pannes"), unsafe_allow_html=True)
    if not fail_filtered.empty and "severity" in fail_filtered.columns:
        sev = fail_filtered["severity"].value_counts()
        colors = {"High": "#ff5252", "Medium": "#ff9800", "Low": "#00e676", "Critical": "#d500f9"}
        fig_pie = go.Figure(go.Pie(
            labels=sev.index,
            values=sev.values,
            hole=0.55,
            marker_colors=[colors.get(s, "#8b9cbd") for s in sev.index],
            textinfo="percent+label",
            textfont_size=12,
        ))
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e8f0fe"),
            showlegend=False,
            height=190,
            margin=dict(l=0, r=0, t=0, b=0),
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# ─── Failure trend ────────────────────────────────────────────────────────────
st.markdown(section_title(" Évolution mensuelle des pannes (2021–2024)"), unsafe_allow_html=True)

if not fail_filtered.empty and "failure_date" in fail_filtered.columns:
    monthly = (
        fail_filtered.dropna(subset=["failure_date"])
        .set_index("failure_date")
        .resample("ME")
        .size()
        .reset_index(name="count")
    )
    monthly.columns = ["date", "count"]

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=monthly["date"], y=monthly["count"],
        mode="lines+markers",
        line=dict(color="#00d4ff", width=2.5),
        marker=dict(size=5, color="#00d4ff"),
        fill="tozeroy",
        fillcolor="rgba(0,212,255,0.08)",
        name="Pannes/mois",
    ))
    fig_trend.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#8b9cbd"),
        height=280,
        margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)", showgrid=True),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", showgrid=True, title="Nb pannes"),
        hovermode="x unified",
    )
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.info("Données de tendance indisponibles.")

# ─── Recent alerts table ──────────────────────────────────────────────────────
st.markdown(section_title(" Dernières alertes actives"), unsafe_allow_html=True)

if not alerts.empty:
    recent = (
        alerts[alerts["resolved"].astype(str).str.lower() == "false"]
        .sort_values("alert_timestamp", ascending=False)
        .head(10)
    )
    display_cols = [c for c in ["alert_id", "equipment_id", "alert_timestamp",
                                 "predicted_failure_probability", "risk_level",
                                 "recommended_action"] if c in recent.columns]
    st.dataframe(
        recent[display_cols].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("Aucune alerte disponible.")

st.markdown('<div class="main-footer">ONEE Predictive System Intelligence Platform · 2021–2024</div>', unsafe_allow_html=True)
