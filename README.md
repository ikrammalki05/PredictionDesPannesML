# ONEE Smart Water & Electricity — Relational Database & Data Warehouse

Built **around** the existing, immutable dataset
`moroccan_water_electricity_iot_dataset.csv` (200k+ IoT/SCADA readings across
10 Moroccan cities, 2021–2024). That file and its generator
(`generate_dataset.py`) are **never modified or regenerated** by this
project — every table here is derived from it.

## What's inside

| Folder | Contents |
|---|---|
| `data/raw/` | The original IoT dataset + its generator (read-only input) |
| `data/generated/` | The 9 derived relational tables (CSV) |
| `scripts/` | One Python script per table + `run_all.py` orchestrator |
| `sql/` | PostgreSQL DDL (`create_tables.sql`) + recommended indexes |
| `docs/` | ER diagram, data dictionary, star/snowflake schema, relationship rules, folder architecture |

## Quick start

```bash
cd scripts/
python3 run_all.py
```

Regenerates all 9 tables into `data/generated/` from the untouched IoT
dataset. Every referential-integrity relationship (equipment → sensor →
measurement, equipment → failure/alert/maintenance, technician →
maintenance) was verified after generation:

```
equip.manufacturer_id ⊆ manufacturers   ✓
sens.equipment_id     ⊆ equipments      ✓
sens.manufacturer_id  ⊆ manufacturers   ✓
fail.equipment_id     ⊆ equipments      ✓
alert.equipment_id    ⊆ equipments      ✓
maint.equipment_id    ⊆ equipments      ✓
maint.technician_id   ⊆ technicians     ✓
All 1,200 IoT sensor_ids present in sensors.csv  ✓
0 / 12,886 failure-linked alerts occur after their failure  ✓
```

## Generated tables at a glance

| Table | Rows | Grain |
|---|---|---|
| `manufacturers.csv` | 15 | one per company |
| `equipments.csv` | 722 | one per physical asset (clustered from 1,200 sensors) |
| `sensors.csv` | 1,200 | 1:1 with the IoT dataset's `sensor_id` |
| `technicians.csv` | 180 | one per maintenance staff member |
| `failures.csv` | 11,774 | one per real failure incident (clustered from 13,713 flagged readings) |
| `alerts.csv` | 21,065 | pre-failure warnings + false alarms |
| `maintenance_history.csv` | 28,230 | preventive (16,456) + corrective (11,774) events |
| `weather.csv` | 14,610 | one per city per calendar day |
| `energy_consumption.csv` | 151,911 | one per city per day per hour |

## Where to read more

- **Read first**: `docs/ER_diagram.md` and `docs/data_dictionary.md`
- **Modeling for Power BI / a data warehouse**: `docs/star_snowflake_schema.md`
- **Why every business rule holds**: `docs/relationships.md`
- **Full folder layout & reproduction steps**: `docs/folder_architecture.md`
- **SQL**: `sql/create_tables.sql`, `sql/indexes.sql`

## Deploy the Streamlit application

The dashboard entry point is `app.py`. All required dashboard data and ML
models are versioned in this project; do not exclude `data/generated/`,
`data/processed/`, or `models/` from the deployment source.

### Streamlit Community Cloud

1. Push this folder to a GitHub repository (without the local `venv/`). The
   deployment ignore rules omit training-only datasets and model artefacts.
2. Install and initialize Git LFS before the first push, because the retained
   ML model binaries are tracked through LFS:

   ```bash
   git lfs install
   ```

   Streamlit Community Cloud supports Git LFS repositories.
3. In [Streamlit Community Cloud](https://share.streamlit.io/), choose
   **Create app** and select that repository.
4. Set **Main file path** to `app.py`, then deploy.

The committed `requirements.txt`, `runtime.txt`, and `.streamlit/config.toml`
configure the cloud build automatically.

### Run locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
