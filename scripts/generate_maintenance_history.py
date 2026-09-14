"""
generate_maintenance_history.py
================================
Generates: maintenance_history.csv

Reads equipments.csv, technicians.csv, failures.csv, and the immutable IoT
fact table (for per-equipment average `maintenance_delay_days`, which drives
how overdue the simulated maintenance schedule runs).

Two kinds of maintenance events are generated:
1. Preventive maintenance: periodic checkups from installation_date onward
   (interval depends on equipment_type), each scheduled date shifted later by
   the equipment's average observed maintenance_delay_days -- consistent with
   "maintenance decreases failure probability" / delay increases risk.
2. Corrective maintenance: triggered shortly AFTER each failure in
   failures.csv (never before), performed by a technician whose
   specialization matches the network_type.

Run from the scripts/ directory (after generate_failures.py, generate_technicians.py):
    python3 generate_maintenance_history.py
"""

import numpy as np
import pandas as pd
from common_utils import load_iot, GEN_DIR, SEED, REFERENCE_DATE, DATA_END

rng = np.random.default_rng(SEED + 5)

equipments = pd.read_csv(GEN_DIR + "equipments.csv", parse_dates=["installation_date"])
technicians = pd.read_csv(GEN_DIR + "technicians.csv")
failures = pd.read_csv(GEN_DIR + "failures.csv", parse_dates=["failure_date"])
df = load_iot()
sensor_map = pd.read_csv(GEN_DIR + "_sensor_equipment_map.csv")
df = df.merge(sensor_map, on="sensor_id", how="left")

avg_delay = df.groupby("equipment_id")["maintenance_delay_days"].mean()

PREVENTIVE_INTERVAL_DAYS = {
    "transformer": 180, "substation": 180, "distribution_box": 270,
    "smart_meter": 365, "pipeline": 365, "pumping_station": 120, "water_tank": 270,
}

PARTS_BY_TYPE = {
    "transformer": ["cooling oil", "bushings", "gaskets", "cooling fans"],
    "substation": ["circuit breaker", "relay module", "insulators", "busbars"],
    "distribution_box": ["fuses", "terminal blocks", "connectors"],
    "smart_meter": ["battery", "communication module", "display unit"],
    "pipeline": ["gaskets", "valve", "pipe section", "coupling"],
    "pumping_station": ["impeller", "seals", "motor bearings", "pump shaft"],
    "water_tank": ["level sensor", "corrosion coating", "inlet valve"],
}

tech_by_network = {
    "Electricity": technicians[technicians.specialization.str.contains(
        "Transformer|Substation|Metering|Distribution|SCADA & Electrical", regex=True)],
    "Water": technicians[technicians.specialization.str.contains(
        "Pumping|Pipeline|Tanks|Hydraulic|SCADA & Water", regex=True)],
}

rows = []
maint_counter = 1

for eq in equipments.itertuples(index=False):
    interval = PREVENTIVE_INTERVAL_DAYS[eq.equipment_type]
    delay_days = float(avg_delay.get(eq.equipment_id, 10))
    techs_pool = tech_by_network[eq.network_type]
    parts_pool = PARTS_BY_TYPE[eq.equipment_type]

    # ---- preventive maintenance schedule ----
    next_date = eq.installation_date + pd.Timedelta(days=interval)
    while next_date <= min(REFERENCE_DATE, DATA_END + pd.Timedelta(days=30)):
        actual_date = next_date + pd.Timedelta(days=max(0, rng.normal(delay_days * 0.5, delay_days * 0.3 + 1)))
        if actual_date > REFERENCE_DATE:
            break
        tech = techs_pool.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0] if len(techs_pool) else technicians.sample(1).iloc[0]

        cost = round(rng.uniform(1500, 8000), 2)
        duration = round(np.clip(rng.normal(3, 1.2), 0.5, 12), 1)
        result = rng.choice(["OK - No issues found", "Minor issue fixed", "Part replaced"], p=[0.55, 0.30, 0.15])
        parts = rng.choice(parts_pool) if result == "Part replaced" else "None"

        rows.append({
            "maintenance_id": f"MNT-{maint_counter:06d}",
            "equipment_id": eq.equipment_id,
            "technician_id": tech["technician_id"],
            "maintenance_date": actual_date.strftime("%Y-%m-%d"),
            "maintenance_type": "Preventive",
            "maintenance_cost_MAD": cost,
            "duration_hours": duration,
            "parts_replaced": parts,
            "result": result,
            "next_maintenance": (actual_date + pd.Timedelta(days=interval)).strftime("%Y-%m-%d"),
        })
        maint_counter += 1
        next_date = next_date + pd.Timedelta(days=interval)

    # ---- corrective maintenance, always AFTER the failure it responds to ----
    eq_failures = failures[failures.equipment_id == eq.equipment_id]
    for f in eq_failures.itertuples(index=False):
        response_delay_hours = np.clip(rng.normal(18, 12), 1, 96)
        maint_date = pd.Timestamp(f.failure_date) + pd.Timedelta(hours=response_delay_hours)
        tech = techs_pool.sample(1, random_state=int(rng.integers(0, 1_000_000))).iloc[0] if len(techs_pool) else technicians.sample(1).iloc[0]

        severity_mult = {"Low": 0.5, "Medium": 1.0, "High": 1.8, "Critical": 3.0}[f.severity]
        cost = round(rng.uniform(3000, 9000) * severity_mult, 2)
        duration = round(np.clip(rng.normal(4 * severity_mult, 2), 1, 72), 1)

        rows.append({
            "maintenance_id": f"MNT-{maint_counter:06d}",
            "equipment_id": eq.equipment_id,
            "technician_id": tech["technician_id"],
            "maintenance_date": maint_date.strftime("%Y-%m-%d %H:%M:%S"),
            "maintenance_type": "Corrective",
            "maintenance_cost_MAD": cost,
            "duration_hours": duration,
            "parts_replaced": rng.choice(parts_pool),
            "result": "Repaired" if f.resolved else "Temporary fix - monitoring",
            "next_maintenance": (maint_date + pd.Timedelta(days=interval // 2)).strftime("%Y-%m-%d"),
        })
        maint_counter += 1

maintenance_df = pd.DataFrame(rows).sort_values("maintenance_date").reset_index(drop=True)
maintenance_df.to_csv(GEN_DIR + "maintenance_history.csv", index=False)
print(f"Saved {GEN_DIR}maintenance_history.csv  ({len(maintenance_df)} rows)")
print(maintenance_df["maintenance_type"].value_counts())
