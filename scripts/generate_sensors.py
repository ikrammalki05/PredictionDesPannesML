"""
generate_sensors.py
====================
Generates: sensors.csv

Reads the immutable IoT fact table (for sensor_id / network_type / equipment_type /
timestamp range per sensor) and equipments.csv (for the equipment_id FK,
produced by generate_equipments.py). Each row of sensors.csv corresponds
1:1 to a sensor_id that appears in the IoT measurement file — no sensor is
invented and no sensor_id is dropped.

Run from the scripts/ directory (after generate_equipments.py):
    python3 generate_sensors.py
"""

import numpy as np
import pandas as pd
from common_utils import (
    load_iot, GEN_DIR, SEED, REFERENCE_DATE, MFR_IOT,
    EQUIPMENT_TYPE_SENSOR_LABEL, COMM_PROTOCOLS_ELEC, COMM_PROTOCOLS_WATER,
    SENSOR_EXPECTED_LIFETIME_YEARS,
)

rng = np.random.default_rng(SEED + 1)

df = load_iot()
sensor_map = pd.read_csv(GEN_DIR + "_sensor_equipment_map.csv")

agg = df.groupby("sensor_id").agg(
    network_type=("network_type", "first"),
    equipment_type=("equipment_type", "first"),
    equipment_age_years=("equipment_age_years", "first"),
    first_seen=("timestamp", "min"),
    last_seen=("timestamp", "max"),
).reset_index()
agg["first_seen"] = pd.to_datetime(agg["first_seen"])
agg["last_seen"] = pd.to_datetime(agg["last_seen"])

agg = agg.merge(sensor_map, on="sensor_id", how="left")

rows = []
for r in agg.itertuples(index=False):
    net = r.network_type
    eq_type = r.equipment_type

    # sensor node installed at/near equipment installation; here we use the
    # first timestamp actually observed for that sensor in the IoT data as a
    # lower bound, and back-date slightly for realism
    installation_date = (r.first_seen - pd.Timedelta(days=int(rng.integers(0, 30)))).normalize()

    lifetime_lo, lifetime_hi = SENSOR_EXPECTED_LIFETIME_YEARS
    expected_lifetime = int(rng.integers(lifetime_lo, lifetime_hi + 1))

    # calibration happens periodically after installation, before the last
    # observed reading -- never after last_seen, never before installation
    span_days = max((r.last_seen - installation_date).days, 1)
    last_calibration = installation_date + pd.Timedelta(days=int(rng.integers(0, span_days + 1)))

    battery_level = int(np.clip(rng.normal(70, 20), 3, 100))
    # sensors with very low battery or very old calibration are more likely inactive/faulty
    days_since_cal = (REFERENCE_DATE - last_calibration).days
    inactive_p = np.clip(0.02 + 0.15 * (battery_level < 15) + 0.10 * (days_since_cal > 720), 0, 0.6)
    status = rng.choice(["Active", "Inactive", "Under Maintenance", "Faulty"],
                         p=[1 - inactive_p - 0.03, inactive_p * 0.5, 0.02, inactive_p * 0.5 + 0.01])

    protocol = rng.choice(COMM_PROTOCOLS_ELEC if net == "Electricity" else COMM_PROTOCOLS_WATER)
    firmware = f"v{rng.integers(1,5)}.{rng.integers(0,10)}.{rng.integers(0,10)}"
    model = f"{'ELX' if net=='Electricity' else 'HYD'}-{rng.integers(1000,9999)}"

    rows.append({
        "sensor_id": r.sensor_id,
        "equipment_id": r.equipment_id,
        "sensor_type": EQUIPMENT_TYPE_SENSOR_LABEL[eq_type],
        "manufacturer_id": rng.choice(MFR_IOT),
        "model": model,
        "firmware_version": firmware,
        "installation_date": installation_date.date().isoformat(),
        "last_calibration": last_calibration.date().isoformat(),
        "battery_level": battery_level,
        "status": status,
        "communication_protocol": protocol,
        "sampling_interval_minutes": 10,   # matches the IoT dataset's fixed 10-minute cadence
        "expected_lifetime_years": expected_lifetime,
    })

sensors_df = pd.DataFrame(rows)
sensors_df.to_csv(GEN_DIR + "sensors.csv", index=False)
print(f"Saved {GEN_DIR}sensors.csv  ({len(sensors_df)} rows)")
print(sensors_df["status"].value_counts())
