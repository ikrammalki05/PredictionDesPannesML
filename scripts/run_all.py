"""
run_all.py
==========
Runs every generate_*.py script in the correct dependency order.

IMPORTANT: this NEVER touches, calls, or regenerates generate_dataset.py /
moroccan_water_electricity_iot_dataset.csv. That file is treated as an
immutable, pre-existing input sitting in ../data/raw/.

Dependency order:
    1. generate_manufacturers.py     (independent)
    2. generate_technicians.py       (independent)
    3. generate_equipments.py        (needs: IoT csv, manufacturers.csv)
    4. generate_sensors.py           (needs: IoT csv, equipments.csv)
    5. generate_failures.py          (needs: IoT csv, equipments.csv)
    6. generate_alerts.py            (needs: IoT csv, failures.csv)
    7. generate_maintenance_history.py (needs: equipments.csv, technicians.csv, failures.csv, IoT csv)
    8. generate_weather.py           (needs: IoT csv)
    9. generate_energy_consumption.py (needs: IoT csv)

Run:
    python3 run_all.py
"""

import subprocess
import sys

SCRIPTS_IN_ORDER = [
    "generate_manufacturers.py",
    "generate_technicians.py",
    "generate_equipments.py",
    "generate_sensors.py",
    "generate_failures.py",
    "generate_alerts.py",
    "generate_maintenance_history.py",
    "generate_weather.py",
    "generate_energy_consumption.py",
]

for script in SCRIPTS_IN_ORDER:
    print(f"\n{'='*70}\nRunning {script}\n{'='*70}")
    result = subprocess.run([sys.executable, script])
    if result.returncode != 0:
        print(f"FAILED: {script}")
        sys.exit(1)

print("\nAll tables generated successfully in ../data/generated/")
