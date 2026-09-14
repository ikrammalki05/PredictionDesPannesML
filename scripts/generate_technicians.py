"""
generate_technicians.py
========================
Generates: technicians.csv

Independent reference table (maintenance workforce). Cities are drawn from
the same 10 cities present in the IoT dataset so technician assignment stays
consistent with equipment locations.

Run from the scripts/ directory:
    python3 generate_technicians.py
"""

import numpy as np
import pandas as pd
from common_utils import GEN_DIR, SEED, CITY_COORDS

rng = np.random.default_rng(SEED + 2)

FIRST_NAMES = ["Youssef", "Mohamed", "Ahmed", "Hamza", "Karim", "Omar", "Rachid", "Said",
               "Amine", "Yassine", "Fatima", "Khadija", "Salma", "Imane", "Nadia",
               "Meryem", "Sara", "Zineb", "Hind", "Laila"]
LAST_NAMES = ["El Amrani", "Bennani", "Tazi", "Alaoui", "Fassi", "Idrissi", "Chraibi",
              "Benjelloun", "Ouazzani", "Berrada", "Cherkaoui", "Lahlou", "Sebti",
              "Zouiten", "Bouzid", "Naciri", "Kettani", "Squalli", "El Fassi", "Mansouri"]

SPECIALIZATIONS_ELEC = ["High-Voltage Transformers", "Substation Systems", "Smart Metering",
                         "Distribution Networks", "SCADA & Electrical Instrumentation"]
SPECIALIZATIONS_WATER = ["Water Pumping Systems", "Pipeline & Leak Detection", "Water Tanks & Reservoirs",
                          "Hydraulic Instrumentation", "SCADA & Water Instrumentation"]

COMPANIES = ["ONEE - Direction Régionale", "Lydec Maintenance", "Redal Technique",
             "Amendis Technique", "Schneider Electric Services Maroc", "Siemens Field Services",
             "Veolia Maroc", "GTR Maroc", "Cegelec Maroc"]

N_TECHNICIANS = 180

rows = []
for i in range(1, N_TECHNICIANS + 1):
    network = rng.choice(["Electricity", "Water"], p=[0.52, 0.48])
    spec = rng.choice(SPECIALIZATIONS_ELEC if network == "Electricity" else SPECIALIZATIONS_WATER)
    rows.append({
        "technician_id": f"TCH-{i:04d}",
        "name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
        "specialization": spec,
        "experience_years": int(np.clip(rng.normal(9, 6), 0, 35)),
        "company": rng.choice(COMPANIES),
        "city": rng.choice(list(CITY_COORDS.keys())),
    })

technicians_df = pd.DataFrame(rows)
technicians_df.to_csv(GEN_DIR + "technicians.csv", index=False)
print(f"Saved {GEN_DIR}technicians.csv  ({len(technicians_df)} rows)")
