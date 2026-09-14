"""
Page 2 — Prédiction en temps réel
Saisie des features → prédiction instantanée avec le modèle sélectionné
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.data_loader import (
    ELEC_FEATURES,
    WATER_FEATURES,
    load_model,
)
from utils.styling import apply_css, page_header, risk_badge, section_title

st.set_page_config(page_title="Prévention Eau — ONEE", page_icon="💧", layout="wide")
apply_css()

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h2>⚡ ONEE Smart Grid</h2>
        <p>Prédiction en Temps Réel</p>
    </div>
    """, unsafe_allow_html=True)

    model_choice = st.selectbox(
        "🤖 Modèle ML (Eau)",
        [
            "CatBoost — Eau",
            "Random Forest — Eau",
        ],
    )
    st.divider()
    st.caption("Le modèle analyse les mesures capteurs et renvoie la probabilité de panne dans les prochaines heures.")

st.markdown(page_header("💧 Prévention des Pannes — Réseau Eau",
                         "Saisissez les mesures capteurs pour obtenir une estimation du risque de panne du réseau d'eau"),
            unsafe_allow_html=True)

# ─── Feature set selection ────────────────────────────────────────────────────
is_water   = True
if model_choice == "CatBoost — Eau":
    model_file = "catboost_advanced_best.pkl"
else:
    model_file = "random_forest_water.pkl"

features   = WATER_FEATURES

# ─── Input form ───────────────────────────────────────────────────────────────
st.markdown(section_title("🎛️ Paramètres de l'équipement et capteurs"), unsafe_allow_html=True)

with st.form("prediction_form"):
    tab_sensor, tab_context, tab_env, tab_location = st.tabs(
        ["📡 Mesures capteurs", "⚙️ Contexte équipement", "🌦️ Environnement", "📍 Localisation"]
    )

    with tab_sensor:
        col1, col2, col3 = st.columns(3)
        inputs = {}
        with col1:
            inputs["temperature_c"]      = st.slider("Température (°C)", -10.0, 60.0, 25.0, 0.5)
            inputs["humidity_percent"]   = st.slider("Humidité (%)", 0.0, 100.0, 55.0, 1.0)
            inputs["vibration_mm_s"]     = st.slider("Vibration (mm/s)", 0.0, 20.0, 2.0, 0.1)
            inputs["noise_db"]           = st.slider("Bruit (dB)", 20.0, 120.0, 55.0, 1.0)
        with col2:
            if not is_water:
                inputs["voltage_v"]              = st.slider("Tension (V)", 180.0, 260.0, 220.0, 0.5)
                inputs["current_a"]              = st.slider("Courant (A)", 0.0, 100.0, 25.0, 0.5)
                inputs["power_factor"]           = st.slider("Facteur de puissance", 0.0, 1.0, 0.85, 0.01)
                inputs["frequency_hz"]           = st.slider("Fréquence (Hz)", 45.0, 55.0, 50.0, 0.1)
            else:
                inputs["pressure_bar"]           = st.slider("Pression (bar)", 0.0, 15.0, 4.0, 0.1)
                inputs["water_flow_l_min"]       = st.slider("Débit eau (L/min)", 0.0, 500.0, 120.0, 1.0)
        with col3:
            if not is_water:
                inputs["energy_consumption_kwh"] = st.slider("Consommation énergie (kWh)", 0.0, 500.0, 80.0, 1.0)
            inputs["anomaly_score"]          = st.slider("Score d'anomalie", 0.0, 1.0, 0.15, 0.01)

    with tab_context:
        col1, col2, col3 = st.columns(3)
        with col1:
            inputs["equipment_age_years"]        = st.slider("Âge équipement (ans)", 0, 40, 8, 1)
            inputs["maintenance_delay_days"]     = st.slider("Délai maintenance (jours)", 0, 365, 30, 1)
            inputs["operating_hours"]            = st.slider("Heures opération", 0, 100000, 15000, 100)
        with col2:
            inputs["failure_history_last_30_days"]= st.slider("Pannes (30 derniers jours)", 0, 10, 0, 1)
            inputs["failure_history_last_year"]  = st.slider("Pannes (année dernière)", 0, 50, 2, 1)
            inputs["maintenance_overdue"]        = st.selectbox("Maintenance en retard ?", [0, 1])
        with col3:
            inputs["usage_intensity"]            = st.slider("Intensité d'usage", 0.0, 1.0, 0.6, 0.01)
            inputs["vibration_age_interaction"]  = st.number_input(
                "Vibration × Âge", value=float(inputs.get("vibration_mm_s", 2.0) * inputs.get("equipment_age_years", 8)),
                format="%.2f"
            )

    with tab_env:
        col1, col2, col3 = st.columns(3)
        with col1:
            inputs["rainfall_mm"]       = st.slider("Pluie (mm)", 0.0, 100.0, 5.0, 0.5)
            inputs["wind_speed"]        = st.slider("Vent (km/h)", 0.0, 100.0, 20.0, 1.0)
        with col2:
            inputs["dust_level"]        = st.slider("Niveau poussière", 0.0, 1.0, 0.3, 0.01)
            inputs["ambient_temperature"]= st.slider("Température ambiante (°C)", -5.0, 50.0, 22.0, 0.5)
        with col3:
            inputs["peak_hour"]         = st.selectbox("Heure de pointe ?", [0, 1])
            inputs["weekend"]           = st.selectbox("Weekend ?", [0, 1])
            inputs["holiday"]           = st.selectbox("Jour férié ?", [0, 1])

    with tab_location:
        col1, col2, col3 = st.columns(3)
        with col1:
            city = st.selectbox("Ville", ["Agadir", "Casablanca", "Fès", "Laayoune",
                                           "Marrakech", "Meknes", "Oujda", "Rabat", "Tangier", "Dakhla"])
        with col2:
            district = st.selectbox("District", ["District_1", "District_2",
                                                   "District_3", "District_4", "District_5"])
        with col3:
            eq_types_elec  = ["distribution_box", "smart_meter", "substation", "transformer"]
            eq_types_water = ["pipe", "pumping_station", "water_tank", "water_treatment_plant"]
            eq_type  = st.selectbox("Type d'équipement", eq_types_water if is_water else eq_types_elec)
            season   = st.selectbox("Saison", ["Autumn", "Spring", "Summer", "Winter"])
            hour_val = st.slider("Heure (0–23)", 0, 23, 12)
            dow_val  = st.slider("Jour semaine (0=lundi)", 0, 6, 2)
            month_val= st.slider("Mois (1–12)", 1, 12, 6)

    submitted = st.form_submit_button("🚀 Lancer la prédiction", use_container_width=True)

# ─── Prediction logic ─────────────────────────────────────────────────────────
if submitted:
    inputs["hour"]       = hour_val
    inputs["day_of_week"]= dow_val
    inputs["month"]      = month_val

    # Build a zero-filled row then set the known values
    row = {f: 0.0 for f in features}
    for k, v in inputs.items():
        if k in row:
            row[k] = float(v)

    # One-hot city
    cities = ["Casablanca", "Dakhla", "Fès", "Laayoune", "Marrakech", "Meknes", "Oujda", "Rabat", "Tangier"]
    for c in cities:
        key = f"city_{c}"
        if key in row:
            row[key] = 1.0 if city == c else 0.0

    # One-hot district (District_1 is the baseline)
    for d in ["District_2", "District_3", "District_4", "District_5"]:
        key = f"district_{d}"
        if key in row:
            row[key] = 1.0 if district == d else 0.0

    # One-hot equipment type
    if is_water:
        for et in ["pumping_station", "water_tank"]:
            key = f"equipment_type_{et}"
            if key in row:
                row[key] = 1.0 if eq_type == et else 0.0
    else:
        for et in ["smart_meter", "substation", "transformer"]:
            key = f"equipment_type_{et}"
            if key in row:
                row[key] = 1.0 if eq_type == et else 0.0

    # One-hot season (Autumn is baseline)
    for s in ["Spring", "Summer", "Winter"]:
        key = f"season_{s}"
        if key in row:
            row[key] = 1.0 if season == s else 0.0

    X = pd.DataFrame([row])

    with st.spinner("Chargement du modèle et calcul…"):
        model = load_model(model_file)

    if model is not None:
        try:
            # Align columns strictly
            model_cols = model.feature_names_in_ if hasattr(model, "feature_names_in_") else features
            # Fill missing cols with 0 and reorder
            for col in model_cols:
                if col not in X.columns:
                    X[col] = 0.0
            X = X[model_cols]

            proba = float(model.predict_proba(X)[0, 1])
            
            # Application du seuil selon le modèle
            thresholds = {
                "Random Forest — Électricité": 0.23,
                "Random Forest — Eau": 0.36,
                "XGBoost — Électricité": 0.14,
                "LightGBM — Électricité": 0.145,
                "CatBoost — Électricité": 0.139,
                "CatBoost — Eau": 0.177,
            }
            threshold = thresholds.get(model_choice, 0.50)
            pred  = 1 if proba >= threshold else 0

            # Risk level
            if proba < 0.30:
                risk, risk_css, emoji = "Low", "#00e676", "✅"
                recommendation = "Aucune action immédiate requise. Surveiller normalement."
            elif proba < 0.60:
                risk, risk_css, emoji = "Medium", "#ff9800", "⚠️"
                recommendation = "Planifier une inspection dans les 7 prochains jours."
            else:
                risk, risk_css, emoji = "High", "#ff5252", "🚨"
                recommendation = "Intervention urgente requise ! Envoyer un technicien sous 48 h."

            # ─── Result display ───────────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            r1, r2, r3 = st.columns([1, 1.2, 1], gap="large")

            with r1:
                st.markdown(f"""
                <div class="prediction-box">
                    <div class="proba-label">Probabilité de panne</div>
                    <div class="proba-value" style="color:{risk_css};">{proba:.1%}</div>
                    <div style="margin-top:0.6rem;">{risk_badge(risk)}</div>
                </div>
                """, unsafe_allow_html=True)

            with r2:
                # Gauge chart
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=proba * 100,
                    number={"suffix": " %", "font": {"size": 36, "color": risk_css}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": "#8b9cbd"},
                        "bar": {"color": risk_css, "thickness": 0.25},
                        "bgcolor": "rgba(255,255,255,0.04)",
                        "borderwidth": 0,
                        "steps": [
                            {"range": [0, 30],   "color": "rgba(0,230,118,0.12)"},
                            {"range": [30, 60],  "color": "rgba(255,152,0,0.12)"},
                            {"range": [60, 100], "color": "rgba(255,82,82,0.12)"},
                        ],
                        "threshold": {"line": {"color": risk_css, "width": 4}, "thickness": 0.75, "value": proba * 100},
                    },
                ))
                fig_gauge.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e8f0fe", family="Inter"),
                    height=260,
                    margin=dict(l=20, r=20, t=30, b=20),
                )
                st.plotly_chart(fig_gauge, use_container_width=True)

            with r3:
                st.markdown(f"""
                <div class="prediction-box" style="text-align:left;">
                    <div class="proba-label" style="margin-bottom:0.8rem;">Recommandation</div>
                    <div style="font-size:2rem; margin-bottom:0.5rem;">{emoji}</div>
                    <div style="font-size:0.9rem; line-height:1.7; color:#e8f0fe;">{recommendation}</div>
                    <hr style="border-color:rgba(255,255,255,0.1); margin:1rem 0;">
                    <div style="font-size:0.78rem; color:#8b9cbd;">
                        <b>Modèle :</b> {model_choice}<br>
                        <b>Décision :</b> {"⚠️ Panne probable" if pred == 1 else "✅ Pas de panne prévue"}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Top contributing features (RF only)
            if hasattr(model, "feature_importances_"):
                st.markdown(section_title("📊 Facteurs contributeurs (Top 10)"), unsafe_allow_html=True)
                imp = pd.DataFrame({
                    "feature": model_cols,
                    "importance": model.feature_importances_,
                    "value": X.iloc[0].values,
                }).sort_values("importance", ascending=False).head(10)

                fig_imp = go.Figure(go.Bar(
                    y=imp["feature"],
                    x=imp["importance"],
                    orientation="h",
                    marker=dict(
                        color=imp["importance"],
                        colorscale=[[0, "#1a6fff"], [1, "#00d4ff"]],
                    ),
                    text=[f"{v:.3f}" for v in imp["importance"]],
                    textposition="outside",
                    textfont=dict(color="#8b9cbd", size=11),
                ))
                fig_imp.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#8b9cbd"),
                    height=320,
                    margin=dict(l=0, r=60, t=10, b=0),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.06)", title="Importance"),
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_imp, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Erreur lors de la prédiction : {e}")
    else:
        st.error("❌ Impossible de charger le modèle. Vérifiez que le fichier `.pkl` est présent dans `models/`.")

st.markdown('<div class="main-footer">ONEE Smart Grid Intelligence Platform · 2021–2024</div>', unsafe_allow_html=True)
