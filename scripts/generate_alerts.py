"""
generate_alerts.py
===================
Generates: alerts.csv

Reads the immutable IoT fact table plus equipments.csv and failures.csv
(produced by generate_equipments.py / generate_failures.py).

Two kinds of alerts are generated, both derived strictly from
`failure_probability` / `anomaly_score` in the IoT measurements:

1. "True" alerts: raised from the degradation readings that precede an actual
   failure incident (1-3 alerts per failure, always timestamped BEFORE
   failures.csv's failure_date -> satisfies "alerts always occur before
   failures").
2. "False-alarm" alerts: raised from readings with elevated risk
   (failure_probability above a threshold) that did NOT lead to a failure --
   a realistic feature of any real monitoring system (not every alert is a
   true positive).

Run from the scripts/ directory (after generate_failures.py):
    python3 generate_alerts.py
"""

import numpy as np
import pandas as pd
from common_utils import load_iot, GEN_DIR, SEED

rng = np.random.default_rng(SEED + 4)

df = load_iot()
sensor_map = pd.read_csv(GEN_DIR + "_sensor_equipment_map.csv")
failures = pd.read_csv(GEN_DIR + "failures.csv", parse_dates=["failure_date"])

df = df.merge(sensor_map, on="sensor_id", how="left")
df["timestamp"] = pd.to_datetime(df["timestamp"])


def risk_level_of(p):
    if p < 0.3:
        return "Low"
    elif p < 0.55:
        return "Medium"
    elif p < 0.8:
        return "High"
    return "Critical"


ACTION_BY_RISK = {
    "Low": "Monitor - no immediate action required",
    "Medium": "Schedule inspection within 7 days",
    "High": "Dispatch technician within 48 hours",
    "Critical": "Immediate intervention required",
}

alert_rows = []
alert_counter = 1

# ---- 1. Alerts tied to real failure incidents ------------------------------
flagged = df[df["target_failure"] == 1].sort_values(["equipment_id", "timestamp"])
for equipment_id, grp in flagged.groupby("equipment_id"):
    grp = grp.sort_values("timestamp")
    gaps = grp["timestamp"].diff().dt.total_seconds().div(86400).fillna(0)
    cluster_id = (gaps > 3).cumsum()
    grp = grp.assign(cluster_id=cluster_id)

    eq_failures = failures[failures.equipment_id == equipment_id].sort_values("failure_date").reset_index(drop=True)
    if eq_failures.empty:
        continue

    for i, (_, cluster) in enumerate(grp.groupby("cluster_id")):
        if i >= len(eq_failures):
            break
        failure_date = eq_failures.loc[i, "failure_date"]
        cluster = cluster.sort_values("timestamp")
        # pick up to 3 alert points within the cluster's lead-up window
        n_alerts = min(len(cluster), rng.integers(1, 4))
        picks = cluster.iloc[np.linspace(0, len(cluster) - 1, n_alerts).astype(int)]
        for _, reading in picks.iterrows():
            ts = reading["timestamp"]
            if ts >= failure_date:
                ts = failure_date - pd.Timedelta(hours=1)
            prob = reading["failure_probability"] if pd.notna(reading["failure_probability"]) else reading["anomaly_score"]
            alert_rows.append({
                "alert_id": f"ALT-{alert_counter:06d}",
                "equipment_id": equipment_id,
                "alert_timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "predicted_failure_probability": round(float(prob), 4),
                "recommended_action": ACTION_BY_RISK[risk_level_of(prob)],
                "risk_level": risk_level_of(prob),
                "resolved": False,   # led to an actual failure -- not successfully preempted
            })
            alert_counter += 1

# ---- 2. False-alarm alerts (elevated risk, no resulting failure) ----------
non_flagged = df[(df["target_failure"] == 0) & (df["failure_probability"] > 0.22)].copy()
# sample down to a realistic false-alarm volume
sample_frac = 0.35
false_alarms = non_flagged.sample(frac=sample_frac, random_state=SEED)

for _, reading in false_alarms.iterrows():
    prob = reading["failure_probability"]
    alert_rows.append({
        "alert_id": f"ALT-{alert_counter:06d}",
        "equipment_id": reading["equipment_id"],
        "alert_timestamp": pd.Timestamp(reading["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
        "predicted_failure_probability": round(float(prob), 4),
        "recommended_action": ACTION_BY_RISK[risk_level_of(prob)],
        "risk_level": risk_level_of(prob),
        "resolved": True,  # investigated, no failure materialized
    })
    alert_counter += 1

alerts_df = pd.DataFrame(alert_rows).sort_values("alert_timestamp").reset_index(drop=True)
alerts_df.to_csv(GEN_DIR + "alerts.csv", index=False)
print(f"Saved {GEN_DIR}alerts.csv  ({len(alerts_df)} rows)")
print(alerts_df["risk_level"].value_counts())
print("Resolved (false alarm) share:", alerts_df["resolved"].mean().round(3))
