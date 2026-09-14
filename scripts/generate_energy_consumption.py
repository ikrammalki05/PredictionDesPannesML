"""
generate_energy_consumption.py
===============================
Generates: energy_consumption.csv

Reads the immutable IoT fact table and aggregates:
- `energy_consumption_kWh` (from Electricity-network sensors) into city-level
  hourly electricity demand
- `water_flow_L_min` (from Water-network sensors) into city-level hourly
  water consumption (m3)

grouped by (city, date, hour, season, peak_hour, weekend, holiday) -- so the
demand curve is guaranteed consistent with the source dataset's own seasonal
and daily patterns (summer peaks, morning/evening peaks, weekend dip), since
it IS the source dataset's own numbers, aggregated to city level.

Run from the scripts/ directory:
    python3 generate_energy_consumption.py
"""

import pandas as pd
from common_utils import load_iot, GEN_DIR

df = load_iot()
df["date"] = pd.to_datetime(df["timestamp"]).dt.date
df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour

elec = df[df.network_type == "Electricity"]
water = df[df.network_type == "Water"]

elec_agg = elec.groupby(["city", "date", "hour", "season", "peak_hour", "weekend", "holiday"]).agg(
    total_electricity_demand_kWh=("energy_consumption_kWh", "sum"),
    avg_voltage_V=("voltage_V", "mean"),
    n_electricity_sensors_reporting=("sensor_id", "nunique"),
).reset_index()

# water_flow_L_min is an instantaneous flow rate (L/min); approximate volume
# per 10-min reading as flow * 10, then sum per hour and convert to m3
water_tmp = water.copy()
water_tmp["volume_L"] = water_tmp["water_flow_L_min"] * 10
water_agg = water_tmp.groupby(["city", "date", "hour", "season", "peak_hour", "weekend", "holiday"]).agg(
    total_water_consumption_L=("volume_L", "sum"),
    avg_pressure_bar=("pressure_bar", "mean"),
    n_water_sensors_reporting=("sensor_id", "nunique"),
).reset_index()
water_agg["total_water_consumption_m3"] = (water_agg["total_water_consumption_L"] / 1000).round(3)
water_agg = water_agg.drop(columns=["total_water_consumption_L"])

energy_df = elec_agg.merge(
    water_agg, on=["city", "date", "hour", "season", "peak_hour", "weekend", "holiday"], how="outer"
)
for col in ["total_electricity_demand_kWh", "avg_voltage_V", "avg_pressure_bar", "total_water_consumption_m3"]:
    energy_df[col] = energy_df[col].round(3)

energy_df.insert(0, "consumption_id", ["ENR-" + str(i + 1).zfill(7) for i in range(len(energy_df))])
energy_df = energy_df.rename(columns={"date": "observation_date"})

energy_df.to_csv(GEN_DIR + "energy_consumption.csv", index=False)
print(f"Saved {GEN_DIR}energy_consumption.csv  ({len(energy_df)} rows -- one per city/day/hour)")
