"""
ONEE Predictive System — Centralized data loading with caching and error resilience.
All loaders use @st.cache_data to avoid repeated I/O on re-runs.
"""

import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

warnings.filterwarnings("ignore")

# ─── Path resolution ─────────────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent.parent          # project root
DATA_GEN  = _HERE / "data" / "generated"
DATA_PROC = _HERE / "data" / "processed"
MODELS    = _HERE / "models"


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _safe_read(path: Path, **kwargs) -> pd.DataFrame:
    """Read a CSV file gracefully; return empty DataFrame on failure."""
    try:
        return pd.read_csv(path, **kwargs)
    except Exception as exc:
        st.warning(f"️  Could not load `{path.name}`: {exc}", icon="️")
        return pd.DataFrame()


# ─── Generated tables ─────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_failures() -> pd.DataFrame:
    df = _safe_read(DATA_GEN / "failures.csv")
    if not df.empty:
        df["failure_date"] = pd.to_datetime(df["failure_date"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_equipments() -> pd.DataFrame:
    return _safe_read(DATA_GEN / "equipments.csv")


@st.cache_data(show_spinner=False)
def load_sensors() -> pd.DataFrame:
    return _safe_read(DATA_GEN / "sensors.csv")


@st.cache_data(show_spinner=False)
def load_alerts() -> pd.DataFrame:
    df = _safe_read(DATA_GEN / "alerts.csv")
    if not df.empty:
        df["alert_timestamp"] = pd.to_datetime(df["alert_timestamp"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_maintenance() -> pd.DataFrame:
    df = _safe_read(DATA_GEN / "maintenance_history.csv")
    if not df.empty:
        df["maintenance_date"] = pd.to_datetime(df["maintenance_date"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_weather() -> pd.DataFrame:
    df = _safe_read(DATA_GEN / "weather.csv")
    if not df.empty:
        df["observation_date"] = pd.to_datetime(df["observation_date"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_energy(nrows: int = 50_000) -> pd.DataFrame:
    """Load energy consumption — sample to avoid memory issues."""
    return _safe_read(DATA_GEN / "energy_consumption.csv", nrows=nrows)


@st.cache_data(show_spinner=False)
def load_manufacturers() -> pd.DataFrame:
    return _safe_read(DATA_GEN / "manufacturers.csv")


@st.cache_data(show_spinner=False)
def load_technicians() -> pd.DataFrame:
    return _safe_read(DATA_GEN / "technicians.csv")


# ─── Processed ML data (sampled for UI) ──────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_X_test_elec(nrows: int = 5_000) -> pd.DataFrame:
    return _safe_read(DATA_PROC / "X_test_elec.csv", nrows=nrows)


@st.cache_data(show_spinner=False)
def load_y_test_elec() -> pd.Series:
    df = _safe_read(DATA_PROC / "y_test_elec.csv")
    return df.squeeze() if not df.empty else pd.Series(dtype=int)


@st.cache_data(show_spinner=False)
def load_X_test_water(nrows: int = 5_000) -> pd.DataFrame:
    return _safe_read(DATA_PROC / "X_test_water.csv", nrows=nrows)


@st.cache_data(show_spinner=False)
def load_y_test_water() -> pd.Series:
    df = _safe_read(DATA_PROC / "y_test_water.csv")
    return df.squeeze() if not df.empty else pd.Series(dtype=int)


# ─── ML Models ───────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_model(name: str):
    """Load a trained model from models/ directory. Returns None on failure."""
    import joblib
    path = MODELS / name
    if not path.exists():
        st.warning(f"️  Model file not found: `{name}`")
        return None
    try:
        return joblib.load(path)
    except Exception as exc:
        st.error(f" Failed to load model `{name}`: {exc}")
        return None


# ─── Feature column definitions (from X_test exploration) ────────────────────
ELEC_FEATURES = [
    "temperature_c", "humidity_percent", "voltage_v", "current_a",
    "power_factor", "frequency_hz", "energy_consumption_kwh", "vibration_mm_s",
    "noise_db", "equipment_age_years", "maintenance_delay_days", "operating_hours",
    "rainfall_mm", "wind_speed", "dust_level", "ambient_temperature",
    "peak_hour", "weekend", "holiday", "failure_history_last_30_days",
    "failure_history_last_year", "anomaly_score", "maintenance_overdue",
    "usage_intensity", "vibration_age_interaction", "hour", "day_of_week", "month",
    "city_Casablanca", "city_Dakhla", "city_Fès", "city_Laayoune",
    "city_Marrakech", "city_Meknes", "city_Oujda", "city_Rabat", "city_Tangier",
    "district_District_2", "district_District_3", "district_District_4", "district_District_5",
    "equipment_type_smart_meter", "equipment_type_substation", "equipment_type_transformer",
    "season_Spring", "season_Summer", "season_Winter",
]

WATER_FEATURES = [
    "temperature_c", "humidity_percent", "pressure_bar", "water_flow_l_min",
    "vibration_mm_s", "noise_db", "equipment_age_years", "maintenance_delay_days",
    "operating_hours", "rainfall_mm", "wind_speed", "dust_level", "ambient_temperature",
    "peak_hour", "weekend", "holiday", "failure_history_last_30_days",
    "failure_history_last_year", "anomaly_score", "maintenance_overdue",
    "usage_intensity", "vibration_age_interaction", "hour", "day_of_week", "month",
    "city_Casablanca", "city_Dakhla", "city_Fès", "city_Laayoune",
    "city_Marrakech", "city_Meknes", "city_Oujda", "city_Rabat", "city_Tangier",
    "district_District_2", "district_District_3", "district_District_4", "district_District_5",
    "equipment_type_pumping_station", "equipment_type_water_tank",
    "season_Spring", "season_Summer", "season_Winter",
]

# ─── Moroccan city GPS coordinates ───────────────────────────────────────────
CITY_COORDS = {
    "Agadir":      (30.4278, -9.5981),
    "Casablanca":  (33.5731, -7.5898),
    "Fès":         (34.0181, -5.0078),
    "Laayoune":    (27.1536, -13.2033),
    "Marrakech":   (31.6295, -7.9811),
    "Meknes":      (33.8935, -5.5473),
    "Oujda":       (34.6814, -1.9086),
    "Rabat":       (34.0209, -6.8416),
    "Tangier":     (35.7595, -5.8340),
    "Dakhla":      (23.6848, -15.9570),
}
