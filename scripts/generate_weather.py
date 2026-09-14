"""
generate_weather.py
====================
Generates: weather.csv

Reads the immutable IoT fact table's environmental columns
(rainfall_mm, humidity_percent, wind_speed, ambient_temperature, dust_level)
and aggregates them to one row per (city, date) -- representing what a real
municipal weather station would report, rather than duplicating per-sensor
noise. This keeps weather.csv perfectly consistent with the IoT
measurements (it IS derived from them) while being joinable to any other
table via (city, date).

Run from the scripts/ directory:
    python3 generate_weather.py
"""

import pandas as pd
from common_utils import load_iot, GEN_DIR

df = load_iot()
df["date"] = pd.to_datetime(df["timestamp"]).dt.date

weather = df.groupby(["city", "date"]).agg(
    season=("season", "first"),
    avg_temperature_C=("ambient_temperature", "mean"),
    min_temperature_C=("ambient_temperature", "min"),
    max_temperature_C=("ambient_temperature", "max"),
    total_rainfall_mm=("rainfall_mm", "sum"),
    avg_humidity_percent=("humidity_percent", "mean"),
    avg_wind_speed=("wind_speed", "mean"),
    avg_dust_level=("dust_level", "mean"),
).reset_index()

for col in ["avg_temperature_C", "min_temperature_C", "max_temperature_C",
            "total_rainfall_mm", "avg_humidity_percent", "avg_wind_speed", "avg_dust_level"]:
    weather[col] = weather[col].round(2)

weather.insert(0, "weather_id", ["WTH-" + str(i + 1).zfill(6) for i in range(len(weather))])
weather = weather.rename(columns={"date": "observation_date"})

weather.to_csv(GEN_DIR + "weather.csv", index=False)
print(f"Saved {GEN_DIR}weather.csv  ({len(weather)} rows -- one per city per calendar day, 2021-2024)")
