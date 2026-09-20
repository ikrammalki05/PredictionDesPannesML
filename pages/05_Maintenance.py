"""
Page 4 — Maintenance
Historique, techniciens, statistiques préventif/correctif
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import CITY_COORDS, load_equipments, load_maintenance, load_technicians
from utils.styling import apply_css, metric_card, page_header, section_title

st.set_page_config(page_title="Maintenance — ONEE", page_icon="", layout="wide")
apply_css()

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h2> ONEE Predictive System</h2>
        <p>Gestion de la Maintenance</p>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Filtres")
    maint_type_filter = st.multiselect("Type de maintenance", ["Preventive", "Corrective"], default=["Preventive", "Corrective"])
    year_filter       = st.multiselect("Année", [2021, 2022, 2023, 2024], default=[2021, 2022, 2023, 2024])
    result_filter     = st.selectbox("Résultat", ["Tous", "OK - No issues found", "Minor issue fixed", "Major repair needed"])

st.markdown(page_header(" Maintenance du Réseau",
                         "Suivi des interventions préventives et correctives sur les équipements"),
            unsafe_allow_html=True)

# ─── Load ─────────────────────────────────────────────────────────────────────
with st.spinner("Chargement…"):
    maint  = load_maintenance()
    equips = load_equipments()
    techs  = load_technicians()

if maint.empty:
    st.error("Aucune donnée de maintenance disponible.")
    st.stop()

# ─── Merge ────────────────────────────────────────────────────────────────────
df = maint.copy()
if not equips.empty and "equipment_id" in df.columns:
    df = df.merge(equips[["equipment_id", "city", "network_type", "equipment_type"]],
                  on="equipment_id", how="left")

# ─── Filter ───────────────────────────────────────────────────────────────────
if maint_type_filter and "maintenance_type" in df.columns:
    df = df[df["maintenance_type"].isin(maint_type_filter)]
if year_filter and "maintenance_date" in df.columns:
    df = df[df["maintenance_date"].dt.year.isin(year_filter)]
if result_filter != "Tous" and "result" in df.columns:
    df = df[df["result"] == result_filter]

if df.empty:
    st.warning("Aucune maintenance ne correspond aux filtres.")
    st.stop()

# ─── KPIs ─────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
total_cost = df["maintenance_cost_MAD"].sum() if "maintenance_cost_MAD" in df.columns else 0
avg_dur    = df["duration_hours"].mean() if "duration_hours" in df.columns else 0
n_prev     = (df["maintenance_type"] == "Preventive").sum() if "maintenance_type" in df.columns else 0
n_corr     = (df["maintenance_type"] == "Corrective").sum() if "maintenance_type" in df.columns else 0

with k1: st.markdown(metric_card("", f"{len(df):,}", "Interventions filtrées"), unsafe_allow_html=True)
with k2: st.markdown(metric_card("", f"{total_cost/1e6:.1f}M MAD", "Coût total"), unsafe_allow_html=True)
with k3: st.markdown(metric_card("️", f"{n_prev:,}", "Préventives"), unsafe_allow_html=True)
with k4: st.markdown(metric_card("", f"{n_corr:,}", "Correctives"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Monthly trend + type breakdown ───────────────────────────────────────────
col_trend, col_type = st.columns([1.6, 1], gap="large")

with col_trend:
    st.markdown(section_title(" Évolution mensuelle des interventions"), unsafe_allow_html=True)
    if "maintenance_date" in df.columns and "maintenance_type" in df.columns:
        monthly = (
            df.dropna(subset=["maintenance_date"])
            .set_index("maintenance_date")
            .groupby([pd.Grouper(freq="ME"), "maintenance_type"])
            .size()
            .reset_index(name="count")
        )
        monthly.columns = ["date", "type", "count"]

        fig_trend = px.area(
            monthly, x="date", y="count", color="type",
            color_discrete_map={"Preventive": "#00d4ff", "Corrective": "#ff9800"},
            labels={"date": "", "count": "Interventions", "type": "Type"},
        )
        fig_trend.update_traces(opacity=0.7)
        fig_trend.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b9cbd"), height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#8b9cbd")),
            hovermode="x unified",
        )
        st.plotly_chart(fig_trend, use_container_width=True)



with col_type:
    st.markdown(section_title("️ Répartition préventif / correctif"), unsafe_allow_html=True)
    if "maintenance_type" in df.columns:
        type_counts = df["maintenance_type"].value_counts()
        fig_donut = go.Figure(go.Pie(
            labels=type_counts.index,
            values=type_counts.values,
            hole=0.6,
            marker_colors=["#00d4ff", "#ff9800"],
            textinfo="percent+label",
            textfont_size=13,
        ))
        fig_donut.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#e8f0fe"),
            showlegend=False, height=280,
            margin=dict(l=0, r=0, t=10, b=0),
            annotations=[dict(text=f"{len(df):,}<br>total", x=0.5, y=0.5,
                              font_size=16, font_color="#00d4ff", showarrow=False)],
        )
        st.plotly_chart(fig_donut, use_container_width=True)

# ─── Cost by city + result ────────────────────────────────────────────────────
col_city, col_result = st.columns(2, gap="large")

with col_city:
    st.markdown(section_title("️ Coût moyen de maintenance par ville"), unsafe_allow_html=True)
    if "city" in df.columns and "maintenance_cost_MAD" in df.columns:
        city_cost = df.groupby("city")["maintenance_cost_MAD"].mean().reset_index()
        city_cost.columns = ["city", "avg_cost"]
        city_cost = city_cost.sort_values("avg_cost", ascending=True)
        fig_c = px.bar(
            city_cost, x="avg_cost", y="city", orientation="h",
            color="avg_cost",
            color_continuous_scale=[[0, "#1a6fff"], [1, "#00d4ff"]],
            labels={"avg_cost": "Coût moyen (MAD)", "city": ""},
        )
        fig_c.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b9cbd"), coloraxis_showscale=False,
            height=300, margin=dict(l=0, r=10, t=10, b=0),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        )
        st.plotly_chart(fig_c, use_container_width=True)

with col_result:
    st.markdown(section_title(" Distribution des résultats"), unsafe_allow_html=True)
    if "result" in df.columns:
        res_counts = df["result"].value_counts().reset_index()
        res_counts.columns = ["result", "count"]
        colors_res = {
            "OK - No issues found": "#00e676",
            "Minor issue fixed": "#ff9800",
            "Major repair needed": "#ff5252",
        }
        fig_res = px.bar(
            res_counts, x="count", y="result", orientation="h",
            color="result", color_discrete_map=colors_res,
            labels={"count": "Nb interventions", "result": ""},
        )
        fig_res.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b9cbd"), showlegend=False,
            height=300, margin=dict(l=0, r=10, t=10, b=0),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        )
        st.plotly_chart(fig_res, use_container_width=True)

# ─── Technician table ─────────────────────────────────────────────────────────
st.markdown(section_title(" Top 10 techniciens les plus actifs"), unsafe_allow_html=True)
if "technician_id" in df.columns:
    tech_activity = df["technician_id"].value_counts().head(10).reset_index()
    tech_activity.columns = ["technician_id", "nb_interventions"]
    if not techs.empty and "technician_id" in techs.columns:
        tech_activity = tech_activity.merge(techs, on="technician_id", how="left")
    st.dataframe(tech_activity.reset_index(drop=True), use_container_width=True, hide_index=True)

# ─── Detail table ─────────────────────────────────────────────────────────────
with st.expander(" Voir le tableau complet des interventions (200 dernières)"):
    display_cols = [c for c in ["maintenance_id", "equipment_id", "city", "technician_id",
                                  "maintenance_date", "maintenance_type", "maintenance_cost_MAD",
                                  "duration_hours", "result", "next_maintenance"]
                    if c in df.columns]
    st.dataframe(
        df[display_cols].sort_values("maintenance_date", ascending=False).head(200).reset_index(drop=True),
        use_container_width=True, hide_index=True,
    )

st.markdown('<div class="main-footer">ONEE Predictive System Intelligence Platform · 2021–2024</div>', unsafe_allow_html=True)
