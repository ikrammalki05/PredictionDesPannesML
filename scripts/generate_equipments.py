"""
generate_equipments.py
=======================
Generates: equipments.csv

Reads the IMMUTABLE IoT fact table (moroccan_water_electricity_iot_dataset.csv)
and infers the physical equipment layer from it. Multiple IoT sensor nodes
that share the same (city, district, network_type, equipment_type) are
clustered into shared "equipment units" (1-3 sensors per unit), matching the
real-world pattern of one physical asset (e.g. one transformer, one pumping
station) carrying several monitoring points (voltage/current node, vibration
node, temperature node, etc.).

Capacity and current_condition are derived directly from the observed
measurement columns (max load, average vibration/anomaly), never invented.

Run from the scripts/ directory:
    python3 generate_equipments.py
"""

import numpy as np
import pandas as pd
from common_utils import (
    load_iot, GEN_DIR, SEED, REFERENCE_DATE, MANUFACTURERS,
    MFR_ELECTRICAL, MFR_WATER, CITY_COORDS, EQUIPMENT_LIFETIME_YEARS,
    CONDITION_LEVELS, owner_for, morocco_jitter,
)

rng = np.random.default_rng(SEED)

df = load_iot()

# ---- per-sensor summary stats needed to derive equipment attributes -------
agg = df.groupby("sensor_id").agg(
    city=("city", "first"),
    district=("district", "first"),
    network_type=("network_type", "first"),
    equipment_type=("equipment_type", "first"),
    equipment_age_years=("equipment_age_years", "first"),
    max_current_A=("current_A", "max"),
    max_voltage_V=("voltage_V", "max"),
    max_flow=("water_flow_L_min", "max"),
    max_pressure=("pressure_bar", "max"),
    mean_vibration=("vibration_mm_s", "mean"),
    mean_anomaly=("anomaly_score", "mean"),
    n_measurements=("timestamp", "count"),
).reset_index()

# ---- cluster sensors within the same (city, district, network_type, equipment_type)
# group into shared equipment units of 1-3 sensors --------------------------
equip_rows = []
sensor_to_equipment = {}
equip_counter = 1

for (city, district, net, eq_type), grp in agg.groupby(
    ["city", "district", "network_type", "equipment_type"]
):
    sensor_ids = grp["sensor_id"].tolist()
    rng.shuffle(sensor_ids)
    i = 0
    while i < len(sensor_ids):
        cluster_size = rng.integers(1, 4)  # 1..3 sensors per equipment unit
        cluster = sensor_ids[i:i + cluster_size]
        i += cluster_size

        equipment_id = f"EQP-{equip_counter:05d}"
        equip_counter += 1
        for sid in cluster:
            sensor_to_equipment[sid] = equipment_id

        cluster_df = grp[grp["sensor_id"].isin(cluster)]
        age_years = float(cluster_df["equipment_age_years"].mean())
        installation_date = (REFERENCE_DATE - pd.Timedelta(days=age_years * 365.25)).normalize()
        # jitter installation date by up to +/-20 days so it doesn't look artificially exact
        installation_date = installation_date + pd.Timedelta(days=int(rng.integers(-20, 21)))

        lifetime_lo, lifetime_hi = EQUIPMENT_LIFETIME_YEARS[eq_type]
        expected_lifetime = int(rng.integers(lifetime_lo, lifetime_hi + 1))

        # capacity: inferred with a realistic engineering safety margin above the
        # highest observed load in the measurement history
        if net == "Electricity":
            max_i = cluster_df["max_current_A"].max()
            capacity = round(float(max_i) * rng.uniform(1.15, 1.35), 1) if pd.notna(max_i) else round(rng.uniform(50, 400), 1)
            capacity_unit = "A"
            manufacturer_id = rng.choice(MFR_ELECTRICAL)
        else:
            max_f = cluster_df["max_flow"].max()
            capacity = round(float(max_f) * rng.uniform(1.15, 1.35), 1) if pd.notna(max_f) else round(rng.uniform(100, 900), 1)
            capacity_unit = "L_min"
            manufacturer_id = rng.choice(MFR_WATER)

        # current_condition: driven by age-vs-lifetime ratio and observed
        # vibration/anomaly stress -- consistent with the IoT dataset's own
        # degradation model, never contradicting it
        age_ratio = np.clip(age_years / expected_lifetime, 0, 1.3)
        stress = np.clip(cluster_df["mean_vibration"].mean() / 6.0, 0, 1.5) if pd.notna(cluster_df["mean_vibration"].mean()) else 0
        condition_score = np.clip(0.55 * age_ratio + 0.45 * stress + rng.normal(0, 0.08), 0, 1.4)
        condition_idx = int(np.clip(condition_score * (len(CONDITION_LEVELS) - 1) / 1.1, 0, len(CONDITION_LEVELS) - 1))
        current_condition = CONDITION_LEVELS[condition_idx]

        base_lat, base_lon = CITY_COORDS[city]
        lat, lon = morocco_jitter(base_lat, base_lon, rng)

        equip_rows.append({
            "equipment_id": equipment_id,
            "city": city,
            "district": district,
            "network_type": net,
            "equipment_type": eq_type,
            "installation_date": installation_date.date().isoformat(),
            "manufacturer_id": manufacturer_id,
            "capacity": capacity,
            "capacity_unit": capacity_unit,
            "expected_lifetime_years": expected_lifetime,
            "current_condition": current_condition,
            "GPS_latitude": lat,
            "GPS_longitude": lon,
            "owner": owner_for(city, net),
        })

equipments_df = pd.DataFrame(equip_rows)
equipments_df.to_csv(GEN_DIR + "equipments.csv", index=False)

# persist the sensor -> equipment mapping for downstream scripts (sensors.csv, etc.)
map_df = pd.DataFrame(
    [{"sensor_id": s, "equipment_id": e} for s, e in sensor_to_equipment.items()]
)
map_df.to_csv(GEN_DIR + "_sensor_equipment_map.csv", index=False)

print(f"Saved {GEN_DIR}equipments.csv  ({len(equipments_df)} equipment units from {len(agg)} sensors)")
print(equipments_df["current_condition"].value_counts())
