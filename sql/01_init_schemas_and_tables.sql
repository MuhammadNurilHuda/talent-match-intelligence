/*
  File: 01_init_schemas_and_tables.sql
  ------------------------------------
  Purpose:
    Initialize schemas and create all base tables for the Talent Match Intelligence project.

  Responsibilities:
    - Drop existing schemas (mart, core, staging) to ensure a clean setup.
    - Recreate staging, core, and mart schemas.
    - Define dimension and fact tables across the core schema.
    - Create staging tables mirroring the core structure for raw data ingestion.
    - Provide sanity check query at the end to confirm successful creation.

  Usage:
    Run this script once after connecting to your Supabase/PostgreSQL instance.
    Example:
        psql -U postgres -d your_database -f sql/01_init_schemas_and_tables.sql

  Notes:
    - Uses `\set ON_ERROR_STOP on` to ensure the script stops on any error.
    - Compatible with PostgreSQL on Supabase; no engine-specific syntax.
    - Intended for Step 0 (Data Preparation) before running analytic steps.
*/

\set ON_ERROR_STOP on

BEGIN;

-- 1) Drop all schema if exists
DROP SCHEMA IF EXISTS mart CASCADE;
DROP SCHEMA IF EXISTS core CASCADE;
DROP SCHEMA IF EXISTS staging CASCADE;

-- 2) make new schema
CREATE SCHEMA staging;
CREATE SCHEMA core;
CREATE SCHEMA mart;

-- ==================================================
-- 3) CORE TABLES
-- ==================================================

CREATE TABLE core.dim_companies (
  company_id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE core.dim_areas (
  area_id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE core.dim_positions (
  position_id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE core.dim_departments (
  department_id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE core.dim_divisions (
  division_id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE core.dim_directorates (
  directorate_id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE core.dim_grades (
  grade_id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE core.dim_education (
  education_id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE core.dim_majors (
  major_id TEXT PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);

CREATE TABLE core.dim_competency_pillars (
  pillar_code VARCHAR(3) PRIMARY KEY,
  pillar_label TEXT NOT NULL
);

-- Employees
CREATE TABLE core.employees (
  employee_id TEXT PRIMARY KEY,
  fullname TEXT,
  nip TEXT,

  company_id TEXT REFERENCES core.dim_companies(company_id),
  area_id TEXT REFERENCES core.dim_areas(area_id),
  position_id TEXT REFERENCES core.dim_positions(position_id),
  department_id TEXT REFERENCES core.dim_departments(department_id),
  division_id TEXT REFERENCES core.dim_divisions(division_id),
  directorate_id TEXT REFERENCES core.dim_directorates(directorate_id),
  grade_id TEXT REFERENCES core.dim_grades(grade_id),
  education_id TEXT REFERENCES core.dim_education(education_id),
  major_id TEXT REFERENCES core.dim_majors(major_id),

  years_of_service_months INT
);

CREATE TABLE core.profiles_psych (
  employee_id TEXT PRIMARY KEY REFERENCES core.employees(employee_id),
  pauli NUMERIC,
  faxtor NUMERIC,
  disc TEXT,
  disc_word TEXT,
  mbti TEXT,
  iq NUMERIC,
  gtq INT,
  tiki INT
);

CREATE TABLE core.papi_scores (
  employee_id TEXT REFERENCES core.employees(employee_id),
  scale_code TEXT,
  score INT,
  PRIMARY KEY (employee_id, scale_code)
);

CREATE TABLE core.strengths (
  employee_id TEXT REFERENCES core.employees(employee_id),
  rank INT,
  theme TEXT,
  PRIMARY KEY (employee_id, rank)
);

CREATE TABLE core.performance_yearly (
  employee_id TEXT REFERENCES core.employees(employee_id),
  year INT,
  rating INT,
  PRIMARY KEY (employee_id, year)
);
CREATE INDEX idx_core_performance_yearly_year ON core.performance_yearly(year);

CREATE TABLE core.competencies_yearly (
  employee_id TEXT REFERENCES core.employees(employee_id),
  pillar_code VARCHAR(3) REFERENCES core.dim_competency_pillars(pillar_code),
  year  INT,
  score INT,
  PRIMARY KEY (employee_id, pillar_code, year)
);
CREATE INDEX idx_core_comp_yearly_pillar_year ON core.competencies_yearly(pillar_code, year);

-- ==================================================
-- 4) STAGING TABLES
-- ==================================================

-- dim 
CREATE TABLE staging.dim_companies    (company_id TEXT,    name TEXT);
CREATE TABLE staging.dim_areas        (area_id TEXT,       name TEXT);
CREATE TABLE staging.dim_positions    (position_id TEXT,   name TEXT);
CREATE TABLE staging.dim_departments  (department_id TEXT, name TEXT);
CREATE TABLE staging.dim_divisions    (division_id TEXT,   name TEXT);
CREATE TABLE staging.dim_directorates (directorate_id TEXT,name TEXT);
CREATE TABLE staging.dim_grades       (grade_id TEXT,      name TEXT);
CREATE TABLE staging.dim_education    (education_id TEXT,  name TEXT);
CREATE TABLE staging.dim_majors       (major_id TEXT,      name TEXT);
CREATE TABLE staging.dim_competency_pillars (pillar_code TEXT, pillar_label TEXT);

-- employees_raw
CREATE TABLE staging.employees_raw (
  employee_id TEXT,
  fullname TEXT,
  nip TEXT,
  company_id TEXT,
  area_id TEXT,
  position_id TEXT,
  department_id TEXT,
  division_id TEXT,
  directorate_id TEXT,
  grade_id TEXT,
  education_id TEXT,
  major_id TEXT,
  years_of_service_months TEXT
);

-- fact and profile
CREATE TABLE staging.profiles_psych (
  employee_id TEXT, pauli TEXT, faxtor TEXT, disc TEXT, disc_word TEXT, mbti TEXT,
  iq TEXT, gtq TEXT, tiki TEXT
);

CREATE TABLE staging.papi_scores (employee_id TEXT, scale_code TEXT, score TEXT);
CREATE TABLE staging.strengths   (employee_id TEXT, rank TEXT, theme TEXT);
CREATE TABLE staging.performance_yearly (employee_id TEXT, rating TEXT, year TEXT);
CREATE TABLE staging.competencies_yearly (employee_id TEXT, score TEXT, pillar_code TEXT, year TEXT);

-- TV/TGV
CREATE TABLE staging.talent_variable_tv_talent_g (
  test_as_talent_variable_tv TEXT,
  subtest TEXT,
  meaning TEXT,
  behavior_example TEXT,
  talent_group_variable_tgv TEXT,
  note TEXT
);

COMMIT;

-- 5) Sanity check
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema IN ('core','staging')
ORDER BY table_schema, table_name;