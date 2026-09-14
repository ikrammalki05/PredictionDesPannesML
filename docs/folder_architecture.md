# Project Folder Architecture

```
onee_smart_grid_database/
│
├── data/
│   ├── raw/
│   │   ├── moroccan_water_electricity_iot_dataset.csv   # IMMUTABLE fact table — never touched
│   │   └── generate_dataset.py                          # original generator — never re-run by this project
│   │
│   └── generated/                                        # all 9 derived tables land here
│       ├── manufacturers.csv
│       ├── equipments.csv
│       ├── sensors.csv
│       ├── technicians.csv
│       ├── failures.csv
│       ├── alerts.csv
│       ├── maintenance_history.csv
│       ├── weather.csv
│       ├── energy_consumption.csv
│       └── _sensor_equipment_map.csv     # internal helper artifact (sensor_id -> equipment_id), not a deliverable table
│
├── scripts/
│   ├── common_utils.py                 # shared reference data (manufacturers, cities, lifetimes) + helpers
│   ├── generate_manufacturers.py
│   ├── generate_equipments.py
│   ├── generate_sensors.py
│   ├── generate_technicians.py
│   ├── generate_failures.py
│   ├── generate_alerts.py
│   ├── generate_maintenance_history.py
│   ├── generate_weather.py
│   ├── generate_energy_consumption.py
│   └── run_all.py                      # orchestrator: runs all 9 in correct dependency order
│
├── sql/
│   ├── create_tables.sql               # DDL: all 10 tables, PKs, FKs, CHECK constraints
│   └── indexes.sql                     # recommended PostgreSQL indexes
│
└── docs/
    ├── ER_diagram.md                   # Mermaid ER diagram
    ├── data_dictionary.md              # column-by-column reference for all 10 tables
    ├── star_snowflake_schema.md        # star schema, snowflake schema, DWH layering, Power BI model
    ├── relationships.md                # every business rule and how it's enforced
    └── folder_architecture.md          # this file
```

## Reproducing the database from scratch

```bash
cd scripts/
python3 run_all.py                      # regenerates all 9 derived tables into ../data/generated/
```

Then load into PostgreSQL:

```bash
psql -d onee_dwh -f ../sql/create_tables.sql
# load moroccan_water_electricity_iot_dataset.csv into iot_measurements via \copy or a COPY command
# load each generated CSV into its matching table (same order as run_all.py) via \copy
psql -d onee_dwh -f ../sql/indexes.sql
```

## Design principle behind this layout

`data/raw/` is treated as read-only, version-controlled input — nothing in
`scripts/` ever writes into it. Every script writes only into
`data/generated/`, so the whole derived database can be wiped and rebuilt
(`rm data/generated/*.csv && python3 run_all.py`) without any risk to the
original IoT dataset, matching the requirement that
`moroccan_water_electricity_iot_dataset.csv` remain the single, untouched
source of truth for the entire project.
