"""
generate_failures.py
=====================
Generates: failures.csv

Reads the immutable IoT fact table's `target_failure`, `failure_probability`,
`anomaly_score`, `vibration_mm_s`, `temperature_C`, `pressure_bar`, `voltage_V`
columns plus equipments.csv. A run of consecutive `target_failure = 1`
readings on the same equipment (gap < 3 days) is treated as ONE real-world
failure incident (since the source dataset flags every 10-minute reading in
the 24h risk window, not one row per incident) -- this avoids inventing
hundreds of duplicate "failures" out of a single physical event.

The failure date is placed strictly AFTER the equipment's installation_date
(guaranteed, since IoT measurement timestamps only start after installation)
and after the flagged degradation readings, satisfying the
"equipment cannot fail before installation" rule.

Run from the scripts/ directory (after generate_equipments.py):
    python3 generate_failures.py
"""

import numpy as np
import pandas as pd
from common_utils import load_iot, GEN_DIR, SEED

rng = np.random.default_rng(SEED + 3)

df = load_iot()
sensor_map = pd.read_csv(GEN_DIR + "_sensor_equipment_map.csv")
equipments = pd.read_csv(GEN_DIR + "equipments.csv", parse_dates=["installation_date"])

df = df.merge(sensor_map, on="sensor_id", how="left")
df["timestamp"] = pd.to_datetime(df["timestamp"])

flagged = df[df["target_failure"] == 1].sort_values(["equipment_id", "timestamp"]).copy()

FAILURE_TYPES = {
    "transformer": ["Transformer Overheating", "Insulation Breakdown", "Overload Trip"],
    "substation": ["Voltage Surge", "Overload Trip", "Protection Relay Failure"],
    "distribution_box": ["Overload Trip", "Short Circuit", "Connector Failure"],
    "smart_meter": ["Metering Fault", "Communication Failure", "Power Factor Failure"],
    "pipeline": ["Pipe Burst", "Leakage", "Blockage"],
    "pumping_station": ["Pump Failure", "Pressure Drop", "Motor Overheating"],
    "water_tank": ["Leakage", "Level Sensor Fault", "Structural Corrosion"],
}

failure_rows = []
failure_counter = 1

for equipment_id, grp in flagged.groupby("equipment_id"):
    grp = grp.sort_values("timestamp")
    gaps = grp["timestamp"].diff().dt.total_seconds().div(86400).fillna(0)
    cluster_id = (gaps > 3).cumsum()
    grp = grp.assign(cluster_id=cluster_id)

    eq_type = grp["equipment_type"].iloc[0]
    net_type = grp["network_type"].iloc[0]
    install_date = equipments.loc[equipments.equipment_id == equipment_id, "installation_date"].iloc[0]

    for _, cluster in grp.groupby("cluster_id"):
        last_ts = cluster["timestamp"].max()
        failure_date = last_ts + pd.Timedelta(hours=int(rng.integers(1, 24)))
        if failure_date <= install_date:
            failure_date = install_date + pd.Timedelta(days=int(rng.integers(30, 90)))

        mean_vib = cluster["vibration_mm_s"].mean()
        mean_anom = cluster["anomaly_score"].mean()
        mean_prob = cluster["failure_probability"].mean()
        mean_pressure = cluster["pressure_bar"].mean()
        mean_voltage = cluster["voltage_V"].mean()

        severity_score = np.clip(
            0.4 * (mean_anom if pd.notna(mean_anom) else 0.5)
            + 0.4 * (mean_prob if pd.notna(mean_prob) else 0.5)
            + 0.2 * np.clip((mean_vib if pd.notna(mean_vib) else 2) / 6, 0, 1.5),
            0, 1.4)
        if severity_score < 0.45:
            severity = "Low"
        elif severity_score < 0.7:
            severity = "Medium"
        elif severity_score < 0.95:
            severity = "High"
        else:
            severity = "Critical"

        # cause attribution -- pick the dominant contributing factor observed
        # in the flagged cluster, consistent with the dataset's own risk drivers
        causes = []
        if pd.notna(mean_vib) and mean_vib > 3.2:
            causes.append("Mechanical wear / vibration")
        if net_type == "Water" and pd.notna(mean_pressure) and mean_pressure < 1.4:
            causes.append("Leak / low pressure")
        if net_type == "Water" and pd.notna(mean_pressure) and mean_pressure > 7:
            causes.append("Pressure surge / possible burst")
        if net_type == "Electricity" and pd.notna(mean_voltage) and (mean_voltage < 210 or mean_voltage > 240):
            causes.append("Voltage instability")
        if cluster["maintenance_delay_days"].mean() > 25:
            causes.append("Deferred maintenance")
        if cluster["equipment_age_years"].iloc[0] > 18:
            causes.append("Equipment aging")
        if net_type == "Electricity" and cluster["dust_level"].mean() > 0.5:
            causes.append("Dust contamination")
        if net_type == "Water" and cluster["rainfall_mm"].mean() > 8:
            causes.append("Heavy rainfall stress")
        if not causes:
            causes.append("Undetermined sensor-flagged anomaly")
        failure_cause = causes[0]

        failure_type = rng.choice(FAILURE_TYPES[eq_type])

        base_cost = {"transformer": 45000, "substation": 60000, "distribution_box": 12000,
                     "smart_meter": 2500, "pipeline": 25000, "pumping_station": 30000,
                     "water_tank": 15000}[eq_type]
        severity_mult = {"Low": 0.4, "Medium": 0.8, "High": 1.5, "Critical": 2.6}[severity]
        repair_cost = round(base_cost * severity_mult * rng.uniform(0.8, 1.25), 2)  # MAD

        repair_duration = round(np.clip(rng.normal(4 + 10 * severity_mult, 3), 1, 96), 1)  # hours
        downtime = round(repair_duration + max(0, rng.normal(3, 4)), 1)  # includes response/queue delay

        days_since_failure = (pd.Timestamp("2025-01-15") - failure_date).days
        resolved = bool(days_since_failure > 10 or rng.random() < 0.9)

        failure_rows.append({
            "failure_id": f"FLR-{failure_counter:06d}",
            "equipment_id": equipment_id,
            "failure_date": failure_date.strftime("%Y-%m-%d %H:%M:%S"),
            "failure_type": failure_type,
            "failure_cause": failure_cause,
            "severity": severity,
            "repair_cost_MAD": repair_cost,
            "repair_duration_hours": repair_duration,
            "downtime_hours": downtime,
            "resolved": resolved,
        })
        failure_counter += 1

failures_df = pd.DataFrame(failure_rows).sort_values("failure_date").reset_index(drop=True)
failures_df.to_csv(GEN_DIR + "failures.csv", index=False)
print(f"Saved {GEN_DIR}failures.csv  ({len(failures_df)} rows from {len(flagged)} flagged 10-min readings)")
print(failures_df["severity"].value_counts())
