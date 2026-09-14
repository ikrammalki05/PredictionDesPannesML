# Data Dictionary

## 1. `iot_measurements` (pre-existing fact table — NOT regenerated)
Source file: `moroccan_water_electricity_iot_dataset.csv`. Full column-by-column
documentation already lives in the original project's `README.md` (delivered
previously). Summary: 201,000 rows, 10-minute cadence, 2021–2024, 10 cities,
Water/Electricity network types, `target_failure` label (~6.8% positive rate).

## 2. `manufacturers.csv`
| Column | Type | Description |
|---|---|---|
| manufacturer_id | PK, varchar | Unique manufacturer code (`MFR-01` …) |
| manufacturer_name | varchar | Real-world company name (ABB, Siemens, Xylem, …) |
| country | varchar | Country of headquarters |
| website | varchar | Public domain |
| speciality | varchar | `Electrical Equipment` / `Water Equipment` / `IoT Sensors & Metering` |

## 3. `equipments.csv`
| Column | Type | Description |
|---|---|---|
| equipment_id | PK, varchar | Unique physical asset code (`EQP-00001` …) |
| city / district | varchar | Location, taken directly from the IoT dataset's sensors clustered into this asset |
| network_type | varchar | `Water` / `Electricity` |
| equipment_type | varchar | transformer / substation / pipeline / pumping_station / water_tank / smart_meter / distribution_box |
| installation_date | date | Derived from the fixed `equipment_age_years` of the sensors clustered onto this asset |
| manufacturer_id | FK → manufacturers | Manufacturer assignment, biased by network type |
| capacity | numeric | Rated capacity, inferred as ~1.15–1.35× the highest current/flow ever observed on this equipment's sensors in the IoT data (realistic engineering safety margin) |
| capacity_unit | varchar | `A` (Electricity) or `L_min` (Water) |
| expected_lifetime_years | smallint | Standard infrastructure-engineering lifetime range per equipment type |
| current_condition | varchar | Excellent / Good / Fair / Poor / Critical — derived from age-vs-lifetime ratio **and** average observed vibration/anomaly score for this equipment's sensors |
| GPS_latitude / GPS_longitude | numeric | Real city-center coordinates + small jitter, always within Morocco / Moroccan-administered territory |
| owner | varchar | ONEE (default) or the real delegated operator for Casablanca (Lydec), Rabat (Redal), Tangier (Amendis) |

**Sensor→equipment clustering rule**: sensors sharing the same
`(city, district, network_type, equipment_type)` are grouped into clusters of
1–3 sensors, each cluster becoming one `equipment_id`. This directly
implements "one equipment can have multiple sensors" without ever inventing a
city/type/age combination not already present in the IoT dataset.

## 4. `sensors.csv`
| Column | Type | Description |
|---|---|---|
| sensor_id | PK, varchar | **Identical** to the `sensor_id` values already present in `iot_measurements` — 1:1, none invented, none dropped |
| equipment_id | FK → equipments | From the clustering above |
| sensor_type | varchar | Descriptive label of what the multi-parameter IoT node measures, based on `equipment_type` |
| manufacturer_id | FK → manufacturers | IoT/metering specialists |
| model / firmware_version | varchar | Synthetic but realistic device identifiers |
| installation_date | date | ≤ the first timestamp this sensor_id appears in `iot_measurements` |
| last_calibration | date | Between installation_date and the sensor's last observed reading |
| battery_level | smallint | 0–100 |
| status | varchar | Active / Inactive / Under Maintenance / Faulty — biased by battery level and calibration age |
| communication_protocol | varchar | Modbus TCP, IEC 61850, NB-IoT, LoRaWAN, MQTT/4G (Electricity) or LoRaWAN, NB-IoT, Modbus RTU, MQTT/4G (Water) |
| sampling_interval_minutes | smallint | Fixed at 10, matching the IoT dataset's actual sampling cadence |
| expected_lifetime_years | smallint | 5–10 years, standard IoT sensor node lifespan |

## 5. `technicians.csv`
| Column | Type | Description |
|---|---|---|
| technician_id | PK, varchar | `TCH-0001` … |
| name | varchar | Realistic Moroccan names |
| specialization | varchar | Electrical or Water sub-specialty |
| experience_years | smallint | 0–35 |
| company | varchar | ONEE or a real delegated/contracted operator (Lydec, Redal, Amendis, Schneider Electric Services Maroc, Siemens Field Services, Veolia Maroc, GTR Maroc, Cegelec Maroc) |
| city | varchar | Base city, from the same 10-city list as the IoT dataset |

## 6. `failures.csv`
| Column | Type | Description |
|---|---|---|
| failure_id | PK, varchar | `FLR-000001` … |
| equipment_id | FK → equipments | |
| failure_date | timestamp | Always strictly after `equipments.installation_date` |
| failure_type | varchar | Equipment-type-specific failure mode |
| failure_cause | varchar | The dominant risk factor observed in the pre-failure readings (mechanical wear, leak/low pressure, voltage instability, deferred maintenance, equipment aging, dust contamination, heavy rainfall stress) |
| severity | varchar | Low / Medium / High / Critical — from a weighted combination of `anomaly_score`, `failure_probability`, and `vibration_mm_s` in the pre-failure IoT readings |
| repair_cost_MAD | numeric | Base cost per equipment type × severity multiplier, in Moroccan Dirhams |
| repair_duration_hours | numeric | Scales with severity |
| downtime_hours | numeric | ≥ repair_duration_hours (includes response/queue delay) |
| resolved | boolean | False for most recent failures (still open), True otherwise |

**Generation rule**: consecutive `target_failure = 1` readings (gap < 3 days)
on the same equipment are merged into ONE failure incident, since the source
dataset flags every 10-minute reading within a 24h risk window rather than
logging one row per real-world incident.

## 7. `alerts.csv`
| Column | Type | Description |
|---|---|---|
| alert_id | PK, varchar | `ALT-000001` … |
| equipment_id | FK → equipments | |
| alert_timestamp | timestamp | Always strictly before the related `failures.failure_date` for that equipment (verified programmatically) |
| predicted_failure_probability | numeric | Taken directly from `iot_measurements.failure_probability` (or `anomaly_score` as fallback) at that reading |
| recommended_action | varchar | Mapped from risk_level |
| risk_level | varchar | Low / Medium / High / Critical, thresholded on predicted_failure_probability |
| resolved | boolean | False = led to an actual failure; True = false alarm, investigated with no failure |

## 8. `maintenance_history.csv`
| Column | Type | Description |
|---|---|---|
| maintenance_id | PK, varchar | `MNT-000001` … |
| equipment_id | FK → equipments | |
| technician_id | FK → technicians | Chosen from technicians whose specialization matches the equipment's network_type |
| maintenance_date | timestamp/date | Preventive: installation_date + periodic interval (per equipment type) + delay derived from the equipment's average observed `maintenance_delay_days`. Corrective: always AFTER the related `failures.failure_date` |
| maintenance_type | varchar | Preventive / Corrective |
| maintenance_cost_MAD | numeric | Corrective costs scale with the triggering failure's severity |
| duration_hours | numeric | |
| parts_replaced | varchar (nullable) | NULL when no part was replaced |
| result | varchar | OK - No issues found / Minor issue fixed / Part replaced / Repaired / Temporary fix |
| next_maintenance | date | Scheduled follow-up |

## 9. `weather.csv`
One row per `(city, observation_date)`, aggregated directly from the IoT
dataset's own `rainfall_mm`, `humidity_percent`, `wind_speed`,
`ambient_temperature`, `dust_level` columns — so it can never contradict the
measurements it's joined against.

## 10. `energy_consumption.csv`
One row per `(city, observation_date, hour)`, aggregated directly from the
IoT dataset's `energy_consumption_kWh` (Electricity sensors) and
`water_flow_L_min` (Water sensors, converted to m³), preserving `season`,
`peak_hour`, `weekend`, `holiday` context flags.
