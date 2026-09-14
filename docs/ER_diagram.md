# Entity-Relationship Diagram

```mermaid
erDiagram
    MANUFACTURERS ||--o{ EQUIPMENTS : "manufactures"
    MANUFACTURERS ||--o{ SENSORS : "manufactures"
    EQUIPMENTS ||--o{ SENSORS : "hosts"
    SENSORS ||--o{ IOT_MEASUREMENTS : "records"
    EQUIPMENTS ||--o{ FAILURES : "experiences"
    EQUIPMENTS ||--o{ ALERTS : "triggers"
    EQUIPMENTS ||--o{ MAINTENANCE_HISTORY : "undergoes"
    TECHNICIANS ||--o{ MAINTENANCE_HISTORY : "performs"
    FAILURES ||--o| MAINTENANCE_HISTORY : "resolved by (corrective)"

    MANUFACTURERS {
        varchar manufacturer_id PK
        varchar manufacturer_name
        varchar country
        varchar website
        varchar speciality
    }

    EQUIPMENTS {
        varchar equipment_id PK
        varchar city
        varchar district
        varchar network_type
        varchar equipment_type
        date installation_date
        varchar manufacturer_id FK
        numeric capacity
        varchar capacity_unit
        smallint expected_lifetime_years
        varchar current_condition
        numeric GPS_latitude
        numeric GPS_longitude
        varchar owner
    }

    SENSORS {
        varchar sensor_id PK
        varchar equipment_id FK
        varchar sensor_type
        varchar manufacturer_id FK
        varchar model
        varchar firmware_version
        date installation_date
        date last_calibration
        smallint battery_level
        varchar status
        varchar communication_protocol
        smallint sampling_interval_minutes
        smallint expected_lifetime_years
    }

    IOT_MEASUREMENTS {
        bigint measurement_id PK
        timestamp timestamp
        varchar city
        varchar district
        varchar sensor_id FK
        varchar network_type
        varchar equipment_type
        numeric temperature_C
        numeric pressure_bar
        numeric voltage_V
        numeric vibration_mm_s
        smallint target_failure
        "... (33 columns total, see docs/data_dictionary.md)"
    }

    FAILURES {
        varchar failure_id PK
        varchar equipment_id FK
        timestamp failure_date
        varchar failure_type
        varchar failure_cause
        varchar severity
        numeric repair_cost_MAD
        numeric repair_duration_hours
        numeric downtime_hours
        boolean resolved
    }

    ALERTS {
        varchar alert_id PK
        varchar equipment_id FK
        timestamp alert_timestamp
        numeric predicted_failure_probability
        varchar recommended_action
        varchar risk_level
        boolean resolved
    }

    MAINTENANCE_HISTORY {
        varchar maintenance_id PK
        varchar equipment_id FK
        varchar technician_id FK
        timestamp maintenance_date
        varchar maintenance_type
        numeric maintenance_cost_MAD
        numeric duration_hours
        varchar parts_replaced
        varchar result
        date next_maintenance
    }

    TECHNICIANS {
        varchar technician_id PK
        varchar name
        varchar specialization
        smallint experience_years
        varchar company
        varchar city
    }

    WEATHER {
        varchar weather_id PK
        varchar city
        date observation_date
        varchar season
        numeric avg_temperature_C
        numeric total_rainfall_mm
        numeric avg_humidity_percent
        numeric avg_dust_level
    }

    ENERGY_CONSUMPTION {
        varchar consumption_id PK
        varchar city
        date observation_date
        smallint hour
        numeric total_electricity_demand_kWh
        numeric total_water_consumption_m3
    }
```

## Non-FK joins (documented, not enforced by SQL foreign keys)

- **`weather` ↔ any other table**: join on `(city, DATE(timestamp))` /
  `(city, observation_date)`. Not a formal FK because weather is a daily
  city-level aggregate, not a per-row reference.
- **`energy_consumption` ↔ any other table**: join on
  `(city, DATE(timestamp), hour)`. Same reasoning as weather.
- **`alerts` → `failures`**: not a declared FK (an alert doesn't always lead
  to a failure — many are false alarms), but every alert with `resolved =
  false` corresponds to a genuine pre-failure warning window and its
  `alert_timestamp` is guaranteed to fall strictly before the matching row in
  `failures.failure_date` for the same `equipment_id` (verified at
  generation time — see `docs/relationships.md`).
