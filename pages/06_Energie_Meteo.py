"""
Page 6 — Énergie & Météo
Consommation par ville/heure, corrélations météo-pannes
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

from utils.data_loader import CITY_COORDS, load_energy, load_failures, load_weather
from utils.styling import apply_css, metric_card, page_header, section_title

st.set_page_config(page_title="Énergie & Météo — ONEE", page_icon="", layout="wide")
apply_css()

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h2> ONEE Predictive System</h2>
        <p>Énergie &amp; Météo</p>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Filtres")
    city_sel = st.multiselect("Villes", list(CITY_COORDS.keys()),
                               default=["Casablanca", "Rabat", "Marrakech"])
    season_sel = st.multiselect("Saison", ["Winter", "Spring", "Summer", "Autumn"],
                                 default=["Winter", "Spring", "Summer", "Autumn"])

st.markdown(page_header(" Énergie & Météo",
                         "Analyse de la consommation énergétique et corrélations avec les conditions météorologiques"),
            unsafe_allow_html=True)

# ─── Load data ────────────────────────────────────────────────────────────────
with st.spinner("Chargement…"):
    weather  = load_weather()
    energy   = load_energy(nrows=60_000)
    failures = load_failures()

# ─── Weather KPIs ─────────────────────────────────────────────────────────────
if not weather.empty:
    wf = weather.copy()
    if city_sel and "city" in wf.columns:
        wf = wf[wf["city"].isin(city_sel)]
    if season_sel and "season" in wf.columns:
        wf = wf[wf["season"].isin(season_sel)]

    k1, k2, k3, k4 = st.columns(4)
    avg_temp = wf["avg_temperature_C"].mean() if "avg_temperature_C" in wf.columns else 0
    avg_rain = wf["total_rainfall_mm"].mean() if "total_rainfall_mm" in wf.columns else 0
    avg_hum  = wf["avg_humidity_percent"].mean() if "avg_humidity_percent" in wf.columns else 0
    avg_wind = wf["avg_wind_speed"].mean() if "avg_wind_speed" in wf.columns else 0

    with k1: st.markdown(metric_card("️", f"{avg_temp:.1f}°C", "Temp. moyenne"), unsafe_allow_html=True)
    with k2: st.markdown(metric_card("️", f"{avg_rain:.1f}mm", "Pluie moyenne/jour"), unsafe_allow_html=True)
    with k3: st.markdown(metric_card("", f"{avg_hum:.1f}%", "Humidité moyenne"), unsafe_allow_html=True)
    with k4: st.markdown(metric_card("", f"{avg_wind:.1f}km/h", "Vent moyen"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

# ─── Energy consumption heatmap ───────────────────────────────────────────────
st.markdown(section_title(" Consommation énergétique par heure et ville"), unsafe_allow_html=True)

if not energy.empty:
    ef = energy.copy()
    if city_sel and "city" in ef.columns:
        ef = ef[ef["city"].isin(city_sel)]
    if "hour" in ef.columns and "city" in ef.columns and "total_electricity_demand_kWh" in ef.columns:
        pivot = ef.groupby(["city", "hour"])["total_electricity_demand_kWh"].mean().reset_index()
        pivot_matrix = pivot.pivot(index="city", columns="hour", values="total_electricity_demand_kWh")
        fig_eheat = go.Figure(go.Heatmap(
            z=pivot_matrix.values,
            x=[f"{h:02d}h" for h in pivot_matrix.columns],
            y=pivot_matrix.index,
            colorscale=[[0, "#0a1628"], [0.5, "#1a6fff"], [1, "#00d4ff"]],
            hovertemplate="Ville: %{y}<br>Heure: %{x}<br>Consommation: %{z:.1f} kWh<extra></extra>",
        ))
        fig_eheat.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b9cbd"), height=340,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(title="Heure"),
            yaxis=dict(title=""),
        )
        st.plotly_chart(fig_eheat, use_container_width=True)
    elif "hour" in ef.columns and "total_electricity_demand_kWh" in ef.columns:
        hourly = ef.groupby("hour")["total_electricity_demand_kWh"].mean().reset_index()
        fig_hour = px.bar(hourly, x="hour", y="total_electricity_demand_kWh",
                          color="total_electricity_demand_kWh",
                          color_continuous_scale=[[0,"#1a6fff"],[1,"#00d4ff"]],
                          labels={"hour": "Heure", "total_electricity_demand_kWh": "kWh moyen"})
        fig_hour.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                font=dict(color="#8b9cbd"), coloraxis_showscale=False,
                                height=300, margin=dict(l=0,r=0,t=10,b=0),
                                xaxis=dict(gridcolor="rgba(0,0,0,0)"),
                                yaxis=dict(gridcolor="rgba(255,255,255,0.06)"))
        st.plotly_chart(fig_hour, use_container_width=True)
    else:
        st.info("Colonnes de consommation (`total_electricity_demand_kWh`, `hour`) non trouvées.")
else:
    st.info("Données de consommation énergétique indisponibles.")

# ─── Weather trends ───────────────────────────────────────────────────────────
col_temp, col_rain = st.columns(2, gap="large")

with col_temp:
    st.markdown(section_title("️ Évolution de la température par ville"), unsafe_allow_html=True)
    if not weather.empty and "observation_date" in weather.columns and "avg_temperature_C" in weather.columns:
        wf2 = weather.copy()
        if city_sel and "city" in wf2.columns:
            wf2 = wf2[wf2["city"].isin(city_sel)]
        monthly_temp = (
            wf2.dropna(subset=["observation_date"])
            .set_index("observation_date")
            .groupby(["city", pd.Grouper(freq="ME")])["avg_temperature_C"]
            .mean()
            .reset_index()
        )
        monthly_temp.columns = ["city", "date", "avg_temp"]
        fig_temp = px.line(
            monthly_temp, x="date", y="avg_temp", color="city",
            labels={"avg_temp": "Temp. (°C)", "date": "", "city": "Ville"},
        )
        fig_temp.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b9cbd"), height=310,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#8b9cbd")),
            hovermode="x unified",
        )
        st.plotly_chart(fig_temp, use_container_width=True)

with col_rain:
    st.markdown(section_title("️ Précipitations cumulées par saison"), unsafe_allow_html=True)
    if not weather.empty and "season" in weather.columns and "total_rainfall_mm" in weather.columns:
        wf3 = weather.copy()
        if season_sel and "season" in wf3.columns:
            wf3 = wf3[wf3["season"].isin(season_sel)]
        season_rain = wf3.groupby("season")["total_rainfall_mm"].sum().reset_index()
        season_rain.columns = ["season", "total_rain"]
        color_map_s = {"Winter": "#1a6fff", "Spring": "#00e676", "Summer": "#ff9800", "Autumn": "#ff5252"}
        fig_rain = px.bar(
            season_rain, x="season", y="total_rain",
            color="season", color_discrete_map=color_map_s,
            labels={"season": "Saison", "total_rain": "Pluie cumulée (mm)"},
        )
        fig_rain.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#8b9cbd"), showlegend=False,
            height=310, margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        )
        st.plotly_chart(fig_rain, use_container_width=True)

# ─── Correlation heatmap: weather vs failure ───────────────────────────────────
st.markdown(section_title(" Corrélation météo ↔ pannes (par ville)"), unsafe_allow_html=True)

if not weather.empty and not failures.empty and "observation_date" in weather.columns:
    try:
        from utils.data_loader import load_equipments
        equips = load_equipments()

        fail_enriched = failures.copy()
        if not equips.empty and "equipment_id" in fail_enriched.columns:
            fail_enriched = fail_enriched.merge(
                equips[["equipment_id", "city"]], on="equipment_id", how="left"
            )
        if "city" in fail_enriched.columns and "failure_date" in fail_enriched.columns:
            fail_enriched["date"] = fail_enriched["failure_date"].dt.date
            fail_daily = (
                fail_enriched.dropna(subset=["city", "date"])
                .groupby(["city", "date"]).size().reset_index(name="nb_failures")
            )
            fail_daily["date"] = pd.to_datetime(fail_daily["date"])

            wth = weather.copy()
            wth["date"] = pd.to_datetime(wth["observation_date"]).dt.normalize()
            merged = wth.merge(fail_daily, on=["city", "date"], how="left")
            merged["nb_failures"] = merged["nb_failures"].fillna(0)

            num_cols = [c for c in ["avg_temperature_C", "total_rainfall_mm",
                                     "avg_humidity_percent", "avg_wind_speed",
                                     "avg_dust_level", "nb_failures"] if c in merged.columns]
            corr = merged[num_cols].corr()
            fig_corr = px.imshow(
                corr, text_auto=".2f",
                color_continuous_scale=[[0, "#ff5252"], [0.5, "#0a1628"], [1, "#00d4ff"]],
                aspect="auto",
                labels={"color": "Corrélation"},
            )
            fig_corr.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8f0fe"),
                height=380,
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Colonnes nécessaires manquantes pour calculer les corrélations.")
    except Exception as e:
        st.info(f"Corrélation météo-pannes indisponible : {e}")
else:
    st.info("Données météo ou pannes indisponibles pour la corrélation.")

st.markdown('<div class="main-footer">ONEE Predictive System Intelligence Platform · 2021–2024</div>', unsafe_allow_html=True)
