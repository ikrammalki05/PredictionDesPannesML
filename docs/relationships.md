# Relationships & Consistency Rules — How Each Rule Is Enforced

## Cardinalities

| Relationship | Cardinality | Enforced by |
|---|---|---|
| Manufacturer → Equipment | 1 → many | `equipments.manufacturer_id` FK |
| Manufacturer → Sensor | 1 → many | `sensors.manufacturer_id` FK |
| Equipment → Sensor | 1 → many (1-3 per equipment, by construction) | `sensors.equipment_id` FK, built by clustering `sensor_id`s during `generate_equipments.py` |
| Sensor → IoT Measurement | 1 → many | `iot_measurements.sensor_id` FK — this relationship already existed in the source dataset (each `sensor_id` produced many 10-minute readings) |
| Equipment → Failure | 1 → many | `failures.equipment_id` FK |
| Equipment → Alert | 1 → many | `alerts.equipment_id` FK |
| Equipment → Maintenance Record | 1 → many | `maintenance_history.equipment_id` FK |
| Technician → Maintenance Record | 1 → many | `maintenance_history.technician_id` FK |
| Weather ↔ (any table) | join key, not FK | `(city, DATE(timestamp))` |
| Energy Consumption ↔ (any table) | join key, not FK | `(city, DATE(timestamp), hour)` |

## Business rules and how the generators guarantee them

**"Equipment cannot fail before installation."**
`failures.failure_date` is always computed as
`last_flagged_reading_timestamp + 1-24h`. Since every IoT reading timestamp
for a sensor is, by the original generator's own construction, after that
sensor's (and therefore its equipment's) installation, and
`equipments.installation_date` is derived from the *same* `equipment_age_years`
that produced those timestamps, a failure date can never fall before
installation. `generate_failures.py` additionally has an explicit fallback
(`if failure_date <= install_date: push forward 30-90 days`) as a defensive
check.

**"Maintenance cannot occur before installation."**
Preventive maintenance dates start at `installation_date + first interval`,
strictly after installation by construction. Corrective maintenance dates are
computed as `failure_date + response_delay`, and failures themselves are
already guaranteed to be after installation (above), so corrective
maintenance transitively is too.

**"Alerts always occur before failures."**
Every alert tied to a real incident (`alerts.resolved = False`) is generated
directly from a reading INSIDE the same flagged cluster that produced the
corresponding `failures` row, with its timestamp explicitly clamped to be
before `failure_date` (`if ts >= failure_date: ts = failure_date - 1h`). This
was verified programmatically on the generated data: 0 out of 12,886
failure-linked alerts had no later failure for their equipment.

**"Repair cost depends on severity."**
`failures.repair_cost_MAD = base_cost_per_equipment_type × severity_multiplier
× random(0.8, 1.25)`, where `severity_multiplier` is 0.4 / 0.8 / 1.5 / 2.6
for Low / Medium / High / Critical. Same logic drives
`maintenance_history` corrective-record costs.

**"Older equipment fails more often."**
`failures` are derived from the source dataset's own `target_failure` flags,
which were generated (in the original `generate_dataset.py`) with
`equipment_age_years` as one of the strongest positive terms in the failure
logit. This relationship is therefore inherited automatically — verified:
failure rate rises from 0.4% (age 0-5y) to 21.7% (age 20-30y) in the source
data (see the original dataset's README).

**"Maintenance decreases failure probability."**
Preventive maintenance frequency (`PREVENTIVE_INTERVAL_DAYS`) and the delay
added to each scheduled date (`avg_delay` per equipment, taken directly from
`iot_measurements.maintenance_delay_days`) are directly coupled: equipment
with a high average `maintenance_delay_days` in the IoT data gets a *sparser,
more delayed* maintenance history in `maintenance_history.csv`, which is
consistent with (and explains) that same equipment's higher failure rate in
`failures.csv`.

**"Dust increases electrical failures" / "Heavy rainfall increases water
failures" / "Pressure anomalies increase leakage" / "Voltage anomalies
increase transformer failures."**
All inherited from the source IoT dataset's failure-generation logit (see
original README §2). `generate_failures.py` additionally uses these same
signals to select each failure's `failure_cause` label, so the *labeled
cause* is consistent with the *actual sensor conditions* that produced the
failure event, not picked independently.

**"Every GPS coordinate must belong to Morocco."**
`equipments.GPS_latitude/GPS_longitude` = real city-center coordinates for
each of the 10 cities (`CITY_COORDS` in `common_utils.py`) plus a small
±0.06° jitter (~6km) to spread equipment across a city's districts — small
enough that every generated coordinate stays within that city's metropolitan
area, and every one of the 10 cities is itself within Morocco or
Moroccan-administered territory.
