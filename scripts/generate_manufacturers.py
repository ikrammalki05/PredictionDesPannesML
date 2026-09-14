"""
generate_manufacturers.py
==========================
Generates: manufacturers.csv

Independent reference table — does not need the IoT dataset, since
manufacturer identity doesn't depend on measurement data. Provided here so
equipments.csv / sensors.csv can foreign-key against it.

Run from the scripts/ directory:
    python3 generate_manufacturers.py
"""

from common_utils import MANUFACTURERS, GEN_DIR

out_path = GEN_DIR + "manufacturers.csv"
MANUFACTURERS.to_csv(out_path, index=False)
print(f"Saved {out_path}  ({len(MANUFACTURERS)} rows)")
