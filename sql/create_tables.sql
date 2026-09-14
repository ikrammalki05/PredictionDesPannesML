-- =============================================================================
-- ONEE Smart Water & Electricity Predictive Maintenance -- Relational Schema
-- =============================================================================
-- Target: PostgreSQL (also Oracle-compatible with minor type substitutions,
-- noted inline where relevant).
--
-- Load order (respects FK dependencies):
--   manufacturers -> technicians -> equipments -> sensors -> iot_measurements
--   -> failures -> alerts -> maintenance_history -> weather -> energy_consumption
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. MANUFACTURERS (independent reference table)
-- -----------------------------------------------------------------------------
CREATE TABLE manufacturers (
    manufacturer_id     VARCHAR(10)   PRIMARY KEY,
    manufacturer_name   VARCHAR(100)  NOT NULL,
    country              VARCHAR(60)   NOT NULL,
    website              VARCHAR(120),
    speciality           VARCHAR(60)   NOT NULL
);

-- -----------------------------------------------------------------------------
-- 2. TECHNICIANS (independent reference table)
-- -----------------------------------------------------------------------------
CREATE TABLE technicians (
    technician_id     VARCHAR(10)   PRIMARY KEY,
    name               VARCHAR(120)  NOT NULL,
    specialization     VARCHAR(80)   NOT NULL,
    experience_years   SMALLINT      NOT NULL CHECK (experience_years >= 0),
    company            VARCHAR(80)   NOT NULL,
    city               VARCHAR(40)   NOT NULL
);

-- -----------------------------------------------------------------------------
-- 3. EQUIPMENTS (core physical-asset dimension)
-- -----------------------------------------------------------------------------
CREATE TABLE equipments (
    equipment_id            VARCHAR(12)   PRIMARY KEY,
    city                     VARCHAR(40)   NOT NULL,
    district                 VARCHAR(40)   NOT NULL,
    network_type             VARCHAR(15)   NOT NULL CHECK (network_type IN ('Water','Electricity')),
    equipment_type           VARCHAR(30)   NOT NULL,
    installation_date        DATE          NOT NULL,
    manufacturer_id          VARCHAR(10)   NOT NULL REFERENCES manufacturers(manufacturer_id),
    capacity                 NUMERIC(10,2) NOT NULL,
    capacity_unit             VARCHAR(10)   NOT NULL,
    expected_lifetime_years  SMALLINT      NOT NULL,
    current_condition         VARCHAR(15)   NOT NULL CHECK (current_condition IN ('Excellent','Good','Fair','Poor','Critical')),
    GPS_latitude              NUMERIC(9,6)  NOT NULL,
    GPS_longitude             NUMERIC(9,6)  NOT NULL,
    owner                     VARCHAR(60)   NOT NULL
);

-- -----------------------------------------------------------------------------
-- 4. SENSORS (IoT device dimension; many sensors -> one equipment)
-- -----------------------------------------------------------------------------
CREATE TABLE sensors (
    sensor_id                    VARCHAR(12)   PRIMARY KEY,
    equipment_id                 VARCHAR(12)   NOT NULL REFERENCES equipments(equipment_id),
    sensor_type                  VARCHAR(120)  NOT NULL,
    manufacturer_id               VARCHAR(10)   NOT NULL REFERENCES manufacturers(manufacturer_id),
    model                         VARCHAR(20)   NOT NULL,
    firmware_version              VARCHAR(20)   NOT NULL,
    installation_date             DATE          NOT NULL,
    last_calibration              DATE          NOT NULL,
    battery_level                 SMALLINT      NOT NULL CHECK (battery_level BETWEEN 0 AND 100),
    status                        VARCHAR(20)   NOT NULL CHECK (status IN ('Active','Inactive','Under Maintenance','Faulty')),
    communication_protocol        VARCHAR(20)   NOT NULL,
    sampling_interval_minutes     SMALLINT      NOT NULL,
    expected_lifetime_years       SMALLINT      NOT NULL
);

-- -----------------------------------------------------------------------------
-- 5. IOT_MEASUREMENTS  (the pre-existing fact table -- NEVER regenerated)
-- File: moroccan_water_electricity_iot_dataset.csv
-- Loaded as-is; sensor_id is the FK into sensors(sensor_id).
-- -----------------------------------------------------------------------------
CREATE TABLE iot_measurements (
    measurement_id                  BIGSERIAL     PRIMARY KEY,   -- surrogate key added at load time (source CSV has no PK column)
    "timestamp"                     TIMESTAMP     NOT NULL,
    city                            VARCHAR(40)   NOT NULL,
    district                        VARCHAR(40)   NOT NULL,
    sensor_id                       VARCHAR(12)   NOT NULL REFERENCES sensors(sensor_id),
    network_type                    VARCHAR(15)   NOT NULL,
    equipment_type                  VARCHAR(30)   NOT NULL,
    temperature_C                   NUMERIC(6,2),
    humidity_percent                NUMERIC(5,2),
    pressure_bar                    NUMERIC(6,3),
    water_flow_L_min                NUMERIC(8,2),
    voltage_V                       NUMERIC(6,2),
    current_A                       NUMERIC(8,3),
    power_factor                    NUMERIC(5,3),
    frequency_Hz                    NUMERIC(6,3),
    energy_consumption_kWh          NUMERIC(8,3),
    vibration_mm_s                  NUMERIC(7,3),
    noise_dB                        NUMERIC(6,2),
    equipment_age_years             NUMERIC(5,2),
    maintenance_delay_days          NUMERIC(6,1),
    operating_hours                 NUMERIC(10,1),
    rainfall_mm                     NUMERIC(6,2),
    wind_speed                      NUMERIC(5,2),
    dust_level                      NUMERIC(5,3),
    ambient_temperature             NUMERIC(6,2),
    peak_hour                       SMALLINT,
    weekend                         SMALLINT,
    holiday                         SMALLINT,
    season                          VARCHAR(10),
    failure_history_last_30_days    SMALLINT,
    failure_history_last_year       SMALLINT,
    anomaly_score                   NUMERIC(6,4),
    failure_probability              NUMERIC(6,4),
    target_failure                  SMALLINT      NOT NULL CHECK (target_failure IN (0,1))
);

-- -----------------------------------------------------------------------------
-- 6. FAILURES
-- -----------------------------------------------------------------------------
CREATE TABLE failures (
    failure_id               VARCHAR(12)   PRIMARY KEY,
    equipment_id              VARCHAR(12)   NOT NULL REFERENCES equipments(equipment_id),
    failure_date               TIMESTAMP     NOT NULL,
    failure_type                VARCHAR(60)   NOT NULL,
    failure_cause                VARCHAR(80)   NOT NULL,
    severity                     VARCHAR(10)   NOT NULL CHECK (severity IN ('Low','Medium','High','Critical')),
    repair_cost_MAD              NUMERIC(12,2) NOT NULL,
    repair_duration_hours        NUMERIC(6,1)  NOT NULL,
    downtime_hours                NUMERIC(6,1)  NOT NULL,
    resolved                     BOOLEAN       NOT NULL
);

-- -----------------------------------------------------------------------------
-- 7. ALERTS  (must precede their related failure -- enforced at ETL time,
-- see docs/relationships.md; not expressible as a pure SQL CHECK across tables)
-- -----------------------------------------------------------------------------
CREATE TABLE alerts (
    alert_id                          VARCHAR(12)   PRIMARY KEY,
    equipment_id                       VARCHAR(12)   NOT NULL REFERENCES equipments(equipment_id),
    alert_timestamp                    TIMESTAMP     NOT NULL,
    predicted_failure_probability       NUMERIC(6,4)  NOT NULL,
    recommended_action                  VARCHAR(80)   NOT NULL,
    risk_level                         VARCHAR(10)   NOT NULL CHECK (risk_level IN ('Low','Medium','High','Critical')),
    resolved                           BOOLEAN       NOT NULL
);

-- -----------------------------------------------------------------------------
-- 8. MAINTENANCE_HISTORY
-- -----------------------------------------------------------------------------
CREATE TABLE maintenance_history (
    maintenance_id          VARCHAR(12)    PRIMARY KEY,
    equipment_id              VARCHAR(12)    NOT NULL REFERENCES equipments(equipment_id),
    technician_id              VARCHAR(10)    NOT NULL REFERENCES technicians(technician_id),
    maintenance_date            TIMESTAMP      NOT NULL,
    maintenance_type             VARCHAR(15)    NOT NULL CHECK (maintenance_type IN ('Preventive','Corrective')),
    maintenance_cost_MAD         NUMERIC(12,2)  NOT NULL,
    duration_hours                NUMERIC(6,1)   NOT NULL,
    parts_replaced                 VARCHAR(60),
    result                         VARCHAR(60)    NOT NULL,
    next_maintenance                DATE
);

-- -----------------------------------------------------------------------------
-- 9. WEATHER  (one row per city per calendar day; derived from IoT columns)
-- -----------------------------------------------------------------------------
CREATE TABLE weather (
    weather_id             VARCHAR(12)   PRIMARY KEY,
    city                    VARCHAR(40)   NOT NULL,
    observation_date         DATE          NOT NULL,
    season                   VARCHAR(10)   NOT NULL,
    avg_temperature_C        NUMERIC(6,2),
    min_temperature_C        NUMERIC(6,2),
    max_temperature_C        NUMERIC(6,2),
    total_rainfall_mm        NUMERIC(7,2),
    avg_humidity_percent     NUMERIC(5,2),
    avg_wind_speed           NUMERIC(5,2),
    avg_dust_level           NUMERIC(5,3),
    UNIQUE (city, observation_date)
);

-- -----------------------------------------------------------------------------
-- 10. ENERGY_CONSUMPTION  (one row per city/day/hour; derived from IoT columns)
-- -----------------------------------------------------------------------------
CREATE TABLE energy_consumption (
    consumption_id                     VARCHAR(14)   PRIMARY KEY,
    city                                 VARCHAR(40)   NOT NULL,
    observation_date                     DATE          NOT NULL,
    hour                                 SMALLINT      NOT NULL CHECK (hour BETWEEN 0 AND 23),
    season                               VARCHAR(10)   NOT NULL,
    peak_hour                            SMALLINT      NOT NULL,
    weekend                              SMALLINT      NOT NULL,
    holiday                              SMALLINT      NOT NULL,
    total_electricity_demand_kWh          NUMERIC(12,3),
    avg_voltage_V                         NUMERIC(6,2),
    n_electricity_sensors_reporting        SMALLINT,
    avg_pressure_bar                      NUMERIC(6,3),
    n_water_sensors_reporting              SMALLINT,
    total_water_consumption_m3             NUMERIC(12,3),
    UNIQUE (city, observation_date, hour)
);
