-- =============================================================================
-- Recommended PostgreSQL Indexes
-- =============================================================================
-- Rationale is documented inline. Run after create_tables.sql and after the
-- initial bulk load (creating indexes before a large COPY is slower).

-- ---- iot_measurements: the largest table (~201k rows), most frequently
-- filtered by sensor + time range, and by the ML target column -------------
CREATE INDEX idx_iot_sensor_ts        ON iot_measurements (sensor_id, "timestamp");
CREATE INDEX idx_iot_city_ts          ON iot_measurements (city, "timestamp");
CREATE INDEX idx_iot_target_failure   ON iot_measurements (target_failure);
CREATE INDEX idx_iot_network_type     ON iot_measurements (network_type, equipment_type);
CREATE INDEX idx_iot_season           ON iot_measurements (season);

-- ---- equipments: frequently filtered/joined by location and condition ----
CREATE INDEX idx_equipments_city_district ON equipments (city, district);
CREATE INDEX idx_equipments_network_type  ON equipments (network_type, equipment_type);
CREATE INDEX idx_equipments_condition     ON equipments (current_condition);
CREATE INDEX idx_equipments_manufacturer  ON equipments (manufacturer_id);

-- ---- sensors: joins to equipments and manufacturers, filters by status ---
CREATE INDEX idx_sensors_equipment   ON sensors (equipment_id);
CREATE INDEX idx_sensors_manufacturer ON sensors (manufacturer_id);
CREATE INDEX idx_sensors_status      ON sensors (status);

-- ---- failures: joined to equipments constantly, filtered by date/severity
CREATE INDEX idx_failures_equipment      ON failures (equipment_id);
CREATE INDEX idx_failures_date           ON failures (failure_date);
CREATE INDEX idx_failures_severity       ON failures (severity);

-- ---- alerts: time-ordered lookups per equipment, risk-level dashboards ---
CREATE INDEX idx_alerts_equipment   ON alerts (equipment_id);
CREATE INDEX idx_alerts_timestamp   ON alerts (alert_timestamp);
CREATE INDEX idx_alerts_risk_level  ON alerts (risk_level);

-- ---- maintenance_history: joined to equipments and technicians -----------
CREATE INDEX idx_maint_equipment    ON maintenance_history (equipment_id);
CREATE INDEX idx_maint_technician   ON maintenance_history (technician_id);
CREATE INDEX idx_maint_date         ON maintenance_history (maintenance_date);
CREATE INDEX idx_maint_type         ON maintenance_history (maintenance_type);

-- ---- weather / energy_consumption: composite lookup key is (city, date[, hour])
CREATE INDEX idx_weather_city_date       ON weather (city, observation_date);
CREATE INDEX idx_energy_city_date_hour   ON energy_consumption (city, observation_date, hour);

-- ---- Notes ----
-- 1. iot_measurements(sensor_id, timestamp) is the single most important
--    index in the schema: it backs the per-sensor time-series queries that
--    both the LSTM feature pipeline and any BI drill-down will run constantly.
-- 2. Consider PARTITION BY RANGE ("timestamp") on iot_measurements by year
--    if the warehouse grows well beyond the current ~200k rows (e.g. once
--    live SCADA ingestion replaces the synthetic generator) -- keeps each
--    partition index small and prunes old data efficiently.
-- 3. All FK columns (equipment_id, sensor_id, manufacturer_id, technician_id)
--    are indexed either directly or as the leading column of a composite
--    index, since PostgreSQL does not auto-index FK columns the way some
--    other RDBMS do.
