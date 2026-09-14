"""
common_utils.py
================
Shared reference data & helper functions used by every generate_*.py script
in this project. This is NOT one of the 9 deliverable tables — it just avoids
duplicating city coordinates / manufacturer lists / lifetime tables across
scripts. Each generate_*.py script remains independently runnable; it simply
imports this module instead of re-declaring the same reference constants.

IMPORTANT: this module never touches or regenerates the IoT measurements file.
"""

import numpy as np
import pandas as pd

SEED = 7
RAW_IOT_PATH = "../data/raw/moroccan_water_electricity_iot_dataset.csv"
GEN_DIR = "../data/generated/"

REFERENCE_DATE = pd.Timestamp("2025-01-15")  # "today" for the simulated warehouse
DATA_START = pd.Timestamp("2021-01-01")
DATA_END = pd.Timestamp("2024-12-31 23:50:00")

# ----------------------------------------------------------------------------
# City geography (real approximate city-center coordinates, all within Morocco
# / Moroccan-administered territory)
# ----------------------------------------------------------------------------
CITY_COORDS = {
    "Casablanca": (33.5731, -7.5898),
    "Rabat":      (34.0209, -6.8416),
    "Marrakech":  (31.6295, -7.9811),
    "Fès":        (34.0331, -5.0003),
    "Tangier":    (35.7595, -5.8340),
    "Agadir":     (30.4278, -9.5981),
    "Oujda":      (34.6814, -1.9086),
    "Meknes":     (33.8935, -5.5473),
    "Laayoune":   (27.1418, -13.1897),
    "Dakhla":     (23.6848, -15.9570),
}

# Delegated/regional operators in Morocco (real-world consistent)
CITY_OWNER = {
    "Casablanca": "Lydec (Groupe Suez)",
    "Rabat":      "Redal (Groupe Veolia)",
    "Tangier":    "Amendis (Groupe Veolia)",
}
DEFAULT_OWNER_WATER = "ONEE - Branche Eau"
DEFAULT_OWNER_ELEC = "ONEE - Branche Électricité"


def owner_for(city: str, network_type: str) -> str:
    if city in CITY_OWNER:
        return CITY_OWNER[city]
    return DEFAULT_OWNER_WATER if network_type == "Water" else DEFAULT_OWNER_ELEC


# ----------------------------------------------------------------------------
# Manufacturers (real, well-known companies in water/electricity/IoT)
# ----------------------------------------------------------------------------
MANUFACTURERS = pd.DataFrame([
    ("MFR-01", "ABB",                     "Switzerland", "abb.com",             "Electrical Equipment"),
    ("MFR-02", "Siemens",                 "Germany",     "siemens.com",         "Electrical Equipment"),
    ("MFR-03", "Schneider Electric",      "France",      "se.com",              "Electrical Equipment"),
    ("MFR-04", "General Electric",        "USA",         "ge.com",              "Electrical Equipment"),
    ("MFR-05", "Hitachi Energy",          "Japan",       "hitachienergy.com",   "Electrical Equipment"),
    ("MFR-06", "Honeywell",               "USA",         "honeywell.com",       "IoT Sensors & Metering"),
    ("MFR-07", "Emerson",                 "USA",         "emerson.com",         "IoT Sensors & Metering"),
    ("MFR-08", "Legrand",                 "France",      "legrand.com",         "Electrical Equipment"),
    ("MFR-09", "Xylem",                   "USA",         "xylem.com",           "Water Equipment"),
    ("MFR-10", "Grundfos",                "Denmark",     "grundfos.com",        "Water Equipment"),
    ("MFR-11", "Itron",                   "USA",         "itron.com",           "IoT Sensors & Metering"),
    ("MFR-12", "Sensus (Xylem)",          "UK",          "sensus.com",          "IoT Sensors & Metering"),
    ("MFR-13", "Mueller Water Products",  "USA",         "muellerwaterproducts.com", "Water Equipment"),
    ("MFR-14", "Endress+Hauser",          "Switzerland", "endress.com",         "IoT Sensors & Metering"),
    ("MFR-15", "Badger Meter",            "USA",         "badgermeter.com",     "IoT Sensors & Metering"),
], columns=["manufacturer_id", "manufacturer_name", "country", "website", "speciality"])

MFR_ELECTRICAL = MANUFACTURERS.loc[MANUFACTURERS.speciality == "Electrical Equipment", "manufacturer_id"].tolist()
MFR_WATER = MANUFACTURERS.loc[MANUFACTURERS.speciality == "Water Equipment", "manufacturer_id"].tolist()
MFR_IOT = MANUFACTURERS.loc[MANUFACTURERS.speciality == "IoT Sensors & Metering", "manufacturer_id"].tolist()

# ----------------------------------------------------------------------------
# Equipment expected lifetime ranges (years) — standard infrastructure
# engineering assumptions
# ----------------------------------------------------------------------------
EQUIPMENT_LIFETIME_YEARS = {
    "transformer":       (25, 35),
    "substation":        (30, 40),
    "pipeline":          (40, 50),
    "pumping_station":   (20, 25),
    "water_tank":        (30, 40),
    "smart_meter":       (10, 15),
    "distribution_box":  (20, 25),
}

SENSOR_EXPECTED_LIFETIME_YEARS = (5, 10)  # IoT sensor nodes wear out faster than the host equipment

EQUIPMENT_TYPE_SENSOR_LABEL = {
    "transformer":      "Electrical Monitoring Node (voltage/current/vibration/temperature)",
    "substation":       "Electrical Monitoring Node (voltage/current/power-factor/temperature)",
    "distribution_box":  "Electrical Monitoring Node (voltage/current/vibration)",
    "smart_meter":      "Smart Metering Node (energy consumption)",
    "pipeline":         "Hydraulic Monitoring Node (pressure/flow/vibration)",
    "pumping_station":  "Hydraulic Monitoring Node (pressure/flow/vibration/temperature)",
    "water_tank":       "Hydraulic Monitoring Node (pressure/level/temperature)",
}

COMM_PROTOCOLS_ELEC = ["Modbus TCP", "IEC 61850", "NB-IoT", "LoRaWAN", "MQTT/4G"]
COMM_PROTOCOLS_WATER = ["LoRaWAN", "NB-IoT", "Modbus RTU", "MQTT/4G"]

CONDITION_LEVELS = ["Excellent", "Good", "Fair", "Poor", "Critical"]


def load_iot():
    df = pd.read_csv(RAW_IOT_PATH, parse_dates=["timestamp"])
    return df


def morocco_jitter(lat, lon, rng, scale=0.06):
    """Small random offset around a city center to place a district-level asset,
    kept tight enough to remain a realistic urban/peri-urban distance (~<7km)."""
    return round(lat + rng.uniform(-scale, scale), 6), round(lon + rng.uniform(-scale, scale), 6)
