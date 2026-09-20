"""
ONEE Predictive System
Main Streamlit entry point
"""

import sys
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from utils.styling import apply_css, metric_card



st.set_page_config(
    page_title="ONEE Predictive System — Prédiction des Pannes",
    
    layout="wide",
    initial_sidebar_state="expanded",
)



apply_css()




with st.sidebar:

    st.markdown(
        """<div class="sidebar-logo">
<h2> ONEE maintenance prediction </h2>
<p>Système de Prédiction des Pannes</p>
</div>""",
        unsafe_allow_html=True,
    )

    st.markdown("#### Navigation")

    st.markdown(
        """<div style='color: #8b9cbd; font-size: 0.82rem; line-height: 2;'>
Utilisez le menu de pages ci-dessus pour naviguer
entre les modules.
</div>""",
        unsafe_allow_html=True,
    )

    st.divider()


    st.markdown(
        """<div style='font-size:0.78rem; color:#8b9cbd;'>
<b style='color:#00d4ff;'>Réseau couvert</b><br>
10 villes marocaines<br>
Électricité & Eau<br>
2021 – 2024
</div>""",
        unsafe_allow_html=True,
    )

    st.divider()


    st.markdown(
        """<div style='font-size:0.78rem; color:#8b9cbd;'>
<b style='color:#00d4ff;'>Modèles ML</b><br>
Random Forest (Élec & Eau)<br>
XGBoost (Élec)<br>
LightGBM (Élec)<br>
CatBoost (Élec & Eau)
</div>""",
        unsafe_allow_html=True,
    )



st.markdown(
    """<div class="page-header">
<h1> ONEE Predictive System— Prédiction des Pannes</h1>
<p>
Système intelligent de surveillance et de prédiction
des pannes sur le réseau eau &amp; électricité au Maroc
</p>
</div>""",
    unsafe_allow_html=True,
)




col1, col2, col3, col4 = st.columns(4)



cards = [
    ( "722", "Équipements", "+12 ce mois", "up"),
    ("11 774", "Pannes historiques", "−8% vs N−1", "down"),
    ("21 065", "Alertes générées", "+3% vs N−1", "up"),
    ("28 230", "Maintenances", "dont 41% correctives", ""),
]


for col, (val, label, delta, direction) in zip(
    [col1, col2, col3, col4],
    cards,
):
    with col:
        st.markdown(
            metric_card(
                "",
                val,
                label,
                delta,
                direction,
            ),
            unsafe_allow_html=True,
        )


st.markdown("<br>", unsafe_allow_html=True)



c1, c2, c3 = st.columns(3)


with c1:

    st.markdown(
        """<div class="metric-card" style="text-align:left;">
<div style="font-size:1.4rem; margin-bottom:0.6rem;">
 Objectif
</div>
<p style="color:#8b9cbd; font-size:0.88rem; line-height:1.7;">
Prédire les pannes  avant
qu'elles ne surviennent, en exploitant les données
capteurs, météorologiques et historiques de maintenance.
</p>
</div>""",
        unsafe_allow_html=True,
    )




with c2:

    st.markdown(
        """<div class="metric-card" style="text-align:left;">
<div style="font-size:1.4rem; margin-bottom:0.6rem;">
 Données sources
</div>
<p style="color:#8b9cbd; font-size:0.88rem; line-height:1.7;">
Dataset IoT marocain de plus de
<b style="color:#00d4ff;">200 000 mesures</b>
SCADA, couvrant environ 1 200 capteurs sur
10 villes marocaines de 2021 à 2024.
</p>
</div>""",
        unsafe_allow_html=True,
    )


with c3:

    st.markdown(
        """<div class="metric-card" style="text-align:left;">
<div style="font-size:1.4rem; margin-bottom:0.6rem;">
 Modèles ML
</div>
<p style="color:#8b9cbd; font-size:0.88rem; line-height:1.7;">
Ensemble de modèles comprenant Random Forest,
XGBoost, LightGBM et CatBoost, avec optimisation
des seuils de décision afin d'améliorer la détection
des pannes.
</p>
</div>""",
        unsafe_allow_html=True,
    )



st.markdown("<br>", unsafe_allow_html=True)

st.info(
    " **Sélectionnez une page dans la barre latérale** "
    "pour accéder aux différents modules de l'application.",
    
)



st.markdown(
    """<div class="main-footer">
ONEE Predictive System Intelligence Platform
&nbsp;·&nbsp;
Réseau Eau &amp; Électricité Maroc
&nbsp;·&nbsp;
2021–2024
</div>""",
    unsafe_allow_html=True,
)
