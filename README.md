# Talent Match Intelligence

This repository implements a data-driven **Talent Match Intelligence** pipeline to compute a composite **Success Score** for employees or candidates. The score integrates performance outcomes, competencies, psychometrics, strengths, and contextual factors to support talent evaluation, matching, and decision-making.

---

## Overview

The project combines multiple HR data domains into a unified analytical model:

- Performance ratings (historical, latest-year focus)
- Competency pillars and proficiency levels
- Strengths (e.g. CliftonStrengths top themes)
- Psychometric assessments (e.g. DISC, MBTI)
- PAPI behavioral/workstyle dimensions
- Contextual and organizational attributes (grade, education, tenure, org structure)

The main output is **Success Formula v2**, a normalized score (0–1) with transparent component breakdowns for interpretability.

---

## Architecture

**Data Flow**

`staging_csv/` → `staging` schema → `core` schema → Python analysis & scoring → Success Score

**Database Layers**

- **staging**: raw tables loaded directly from CSV
- **core**: cleaned, deduplicated, analysis-ready tables
- **mart**: reserved for downstream presentation or BI use (optional)

---

## Repository Structure

- `sql/`
  - `01_init_schemas_and_tables.sql`  
    Initializes schemas (`staging`, `core`, `mart`) and base tables.
  - `02_load_staging_from_csv.sql`  
    Loads CSV files from `staging_csv/` into the `staging` schema using `\copy`.
  - `03_transform_to_core.sql`  
    Transforms and standardizes data from `staging` into `core`.

- `staging_csv/`  
  Example and development CSV datasets used by the SQL pipeline.

- `core/`
  - `config.py` – environment configuration and validation
  - `db.py` – SQLAlchemy database engine
  - `queries.py` – centralized SQL query definitions
  - `io.py` – data access layer (DB → pandas DataFrames)
  - `success_formula_v2.py` – Success Score v2 implementation
  - `evaluate.py` – evaluation metrics and utilities
  - `eda_*.py` – exploratory analysis scripts per data domain
  - `weight_search.py` – lightweight weight/grid search utilities

- `notebooks/step1_redthreads.ipynb`  
  Main end-to-end analysis notebook (EDA → insights → scoring).

- `test_connection.py`  
  Database connectivity and environment diagnostics.

---

## Requirements

- Python 3.10+ (3.11 recommended)
- PostgreSQL or Supabase Postgres
- `psql` CLI (required for CSV loading via `\copy`)

---

## Environment Setup

Create a `.env` file in the project root:

```bash
PG_CONN="postgresql+psycopg2://USER:PASSWORD@HOST:5432/DBNAME"
SUPABASE_URL="https://<project-ref>.supabase.co"
SUPABASE_KEY="<service_or_anon_key>"
````

* `PG_CONN` is required for all Python modules and SQLAlchemy connections.
* `SUPABASE_URL` and `SUPABASE_KEY` are used for Supabase connectivity checks.

---

## Python Dependencies

Install dependencies using the provided requirements file:

```bash
pip install -r requirements.txt
```

---

## Database Initialization

Run all SQL scripts from the **repository root** to ensure relative CSV paths resolve correctly.

1. Initialize schemas and tables:

```bash
psql -d <DBNAME> -f sql/01_init_schemas_and_tables.sql
```

2. Load CSV data into staging:

```bash
psql -d <DBNAME> -f sql/02_load_staging_from_csv.sql
```

3. Transform staging data into core tables:

```bash
psql -d <DBNAME> -f sql/03_transform_to_core.sql
```

---

## Connection Test (Optional)

```bash
python test_connection.py
```

This script validates environment variables, checks PostgreSQL connectivity, and verifies the presence of key `core` tables.

---

## Analysis Workflow

The primary analytical workflow is documented in:

* `notebooks/step1_redthreads.ipynb`

The notebook covers:

* Exploratory analysis by data domain
* Feature sanity checks and distributions
* Construction and inspection of Success Formula v2
* Preliminary evaluation and diagnostics

---

## Success Formula v2

Implemented in `core/success_formula_v2.py`.

**Components (default weights):**

* Competency: 50%
* Strengths: 25%
* Psychometric: 20%
* DISC bonus: small, conditional (non-penalizing)

**Outputs:**

* Final normalized success score (`0–1`)
* Component-level breakdown for interpretability and debugging

---

## Model Evaluation

Evaluation utilities are defined in `core/evaluate.py`, including:

* ROC-AUC
* PR-AUC (Average Precision)
* KS statistic
* Precision@K
* Capture@K

These metrics are intended for internal validation and comparative experiments, not for production-grade prediction without further calibration.

---

## Notes

* CSV loading relies on PostgreSQL `\copy`; ensure correct working directory.
* The repository is analysis-focused and not designed as a production API.
* Weights and formulas are intentionally transparent and adjustable.
