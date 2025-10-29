/*
  File: 03_transform_to_core.sql
  ------------------------------
  Purpose:
    Transform and migrate data from the staging schema to the core schema.

  Responsibilities:
    - Clean and standardize data loaded from CSV staging tables.
    - Deduplicate records using DISTINCT and ROW_NUMBER().
    - Populate all dimension and fact tables in the core schema.
    - Maintain referential integrity by ensuring IDs and text fields are valid.
    - Update existing records on conflict (upsert behavior).

  Workflow:
    1. Seed all dimension tables (dim_*).
    2. Load employees with organization hierarchy references.
    3. Insert psychometric, PAPI, strengths, performance, and competency data.
    4. Run quick row count summary and orphan key validation at the end.

  Usage:
    Run this after executing 02_load_staging_from_csv.sql.
    Example:
        psql -U postgres -d your_database -f sql/03_transform_to_core.sql

  Notes:
    - Uses TRIM, NULLIF, and UPPER for normalization.
    - Uses ON CONFLICT DO UPDATE to avoid duplicate inserts.
    - The orphan check at the end should return all zeros.
*/
\set ON_ERROR_STOP on

BEGIN;

-- =========================
-- Seed DIM (id & name from CSV)
-- =========================
INSERT INTO core.dim_companies(company_id, name)
SELECT DISTINCT TRIM(company_id), TRIM(name)
FROM staging.dim_companies
WHERE NULLIF(TRIM(company_id),'') IS NOT NULL
  AND NULLIF(TRIM(name),'') IS NOT NULL
ON CONFLICT (company_id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO core.dim_areas(area_id, name)
SELECT DISTINCT TRIM(area_id), TRIM(name)
FROM staging.dim_areas
WHERE NULLIF(TRIM(area_id),'') IS NOT NULL
  AND NULLIF(TRIM(name),'') IS NOT NULL
ON CONFLICT (area_id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO core.dim_positions(position_id, name)
SELECT DISTINCT TRIM(position_id), TRIM(name)
FROM staging.dim_positions
WHERE NULLIF(TRIM(position_id),'') IS NOT NULL
  AND NULLIF(TRIM(name),'') IS NOT NULL
ON CONFLICT (position_id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO core.dim_departments(department_id, name)
SELECT DISTINCT TRIM(department_id), TRIM(name)
FROM staging.dim_departments
WHERE NULLIF(TRIM(department_id),'') IS NOT NULL
  AND NULLIF(TRIM(name),'') IS NOT NULL
ON CONFLICT (department_id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO core.dim_divisions(division_id, name)
SELECT DISTINCT TRIM(division_id), TRIM(name)
FROM staging.dim_divisions
WHERE NULLIF(TRIM(division_id),'') IS NOT NULL
  AND NULLIF(TRIM(name),'') IS NOT NULL
ON CONFLICT (division_id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO core.dim_directorates(directorate_id, name)
SELECT DISTINCT TRIM(directorate_id), TRIM(name)
FROM staging.dim_directorates
WHERE NULLIF(TRIM(directorate_id),'') IS NOT NULL
  AND NULLIF(TRIM(name),'') IS NOT NULL
ON CONFLICT (directorate_id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO core.dim_grades(grade_id, name)
SELECT DISTINCT TRIM(grade_id), TRIM(name)
FROM staging.dim_grades
WHERE NULLIF(TRIM(grade_id),'') IS NOT NULL
  AND NULLIF(TRIM(name),'') IS NOT NULL
ON CONFLICT (grade_id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO core.dim_education(education_id, name)
SELECT DISTINCT TRIM(education_id), TRIM(name)
FROM staging.dim_education
WHERE NULLIF(TRIM(education_id),'') IS NOT NULL
  AND NULLIF(TRIM(name),'') IS NOT NULL
ON CONFLICT (education_id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO core.dim_majors(major_id, name)
SELECT DISTINCT TRIM(major_id), TRIM(name)
FROM staging.dim_majors
WHERE NULLIF(TRIM(major_id),'') IS NOT NULL
  AND NULLIF(TRIM(name),'') IS NOT NULL
ON CONFLICT (major_id) DO UPDATE SET name = EXCLUDED.name;

INSERT INTO core.dim_competency_pillars(pillar_code, pillar_label)
SELECT DISTINCT UPPER(TRIM(pillar_code)), TRIM(pillar_label)
FROM staging.dim_competency_pillars
WHERE NULLIF(TRIM(pillar_code),'') IS NOT NULL
ON CONFLICT (pillar_code) DO UPDATE SET pillar_label = EXCLUDED.pillar_label;

-- =========================
-- EMPLOYEES
-- =========================
WITH se_raw AS (
  SELECT
    TRIM(employee_id) AS employee_id,
    TRIM(fullname) AS fullname,
    TRIM(nip) AS nip,
    NULLIF(TRIM(company_id),'')     AS company_id,
    NULLIF(TRIM(area_id),'')        AS area_id,
    NULLIF(TRIM(position_id),'')    AS position_id,
    NULLIF(TRIM(department_id),'')  AS department_id,
    NULLIF(TRIM(division_id),'')    AS division_id,
    NULLIF(TRIM(directorate_id),'') AS directorate_id,
    NULLIF(TRIM(grade_id),'')       AS grade_id,
    NULLIF(TRIM(education_id),'')   AS education_id,
    NULLIF(TRIM(major_id),'')       AS major_id,
    NULLIF(TRIM(years_of_service_months),'')::NUMERIC::INT AS yos
  FROM staging.employees_raw
  WHERE NULLIF(TRIM(employee_id),'') IS NOT NULL
),
se AS (
  -- Dedup if there're double employee
  SELECT *, ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY employee_id) AS rn
  FROM se_raw
)
INSERT INTO core.employees(
  employee_id, fullname, nip,
  company_id, area_id, position_id, department_id, division_id,
  directorate_id, grade_id, education_id, major_id,
  years_of_service_months
)
SELECT
  employee_id, fullname, nip,
  company_id, area_id, position_id, department_id, division_id,
  directorate_id, grade_id, education_id, major_id,
  yos
FROM se
WHERE rn = 1
ON CONFLICT (employee_id) DO UPDATE SET
  fullname    = EXCLUDED.fullname,
  nip         = EXCLUDED.nip,
  company_id  = EXCLUDED.company_id,
  area_id     = EXCLUDED.area_id,
  position_id = EXCLUDED.position_id,
  department_id  = EXCLUDED.department_id,
  division_id    = EXCLUDED.division_id,
  directorate_id = EXCLUDED.directorate_id,
  grade_id       = EXCLUDED.grade_id,
  education_id   = EXCLUDED.education_id,
  major_id       = EXCLUDED.major_id,
  years_of_service_months = EXCLUDED.years_of_service_months;

-- =========================
-- PROFILES
-- =========================
WITH src AS (
  SELECT DISTINCT ON (TRIM(employee_id))
    TRIM(employee_id) AS employee_id,
    NULLIF(pauli,'')::NUMERIC           AS pauli,
    NULLIF(faxtor,'')::NUMERIC          AS faxtor,
    NULLIF(disc,'')                     AS disc,
    NULLIF(disc_word,'')                AS disc_word,
    NULLIF(mbti,'')                     AS mbti,
    NULLIF(TRIM(iq),'')::NUMERIC        AS iq,
    NULLIF(TRIM(gtq),'')::NUMERIC::INT  AS gtq,
    NULLIF(TRIM(tiki),'')::NUMERIC::INT AS tiki
  FROM staging.profiles_psych
  WHERE NULLIF(TRIM(employee_id),'') IS NOT NULL
  ORDER BY TRIM(employee_id)
)
INSERT INTO core.profiles_psych(employee_id, pauli, faxtor, disc, disc_word, mbti, iq, gtq, tiki)
SELECT employee_id, pauli, faxtor, disc, disc_word, mbti, iq, gtq, tiki
FROM src
ON CONFLICT (employee_id) DO UPDATE SET
  pauli = EXCLUDED.pauli,
  faxtor = EXCLUDED.faxtor,
  disc = EXCLUDED.disc,
  disc_word = EXCLUDED.disc_word,
  mbti = EXCLUDED.mbti,
  iq = EXCLUDED.iq,
  gtq = EXCLUDED.gtq,
  tiki = EXCLUDED.tiki;

-- =========================
-- PAPI
-- =========================
WITH src AS (
  SELECT DISTINCT ON (TRIM(employee_id), TRIM(scale_code))
    TRIM(employee_id) AS employee_id,
    TRIM(scale_code)  AS scale_code,
    NULLIF(TRIM(score),'')::NUMERIC::INT AS score
  FROM staging.papi_scores
  WHERE NULLIF(TRIM(employee_id),'') IS NOT NULL AND NULLIF(TRIM(scale_code),'') IS NOT NULL
  ORDER BY TRIM(employee_id), TRIM(scale_code)
)
INSERT INTO core.papi_scores(employee_id, scale_code, score)
SELECT employee_id, scale_code, score
FROM src
ON CONFLICT (employee_id, scale_code) DO UPDATE SET score = EXCLUDED.score;

-- =========================
-- STRENGTHS
-- =========================
WITH src AS (
  SELECT DISTINCT ON (TRIM(employee_id), NULLIF(TRIM(rank),''))
    TRIM(employee_id) AS employee_id,
    NULLIF(TRIM(rank),'')::NUMERIC::INT AS rank,
    TRIM(theme) AS theme
  FROM staging.strengths
  WHERE NULLIF(TRIM(employee_id),'') IS NOT NULL AND NULLIF(TRIM(theme),'') IS NOT NULL
  ORDER BY TRIM(employee_id), NULLIF(TRIM(rank),'')
)
INSERT INTO core.strengths(employee_id, rank, theme)
SELECT employee_id, rank, theme
FROM src
ON CONFLICT (employee_id, rank) DO UPDATE SET theme = EXCLUDED.theme;

-- =========================
-- PERFORMANCE
-- =========================
WITH src AS (
  SELECT DISTINCT ON (TRIM(employee_id), NULLIF(TRIM(year),'') )
    TRIM(employee_id) AS employee_id,
    NULLIF(TRIM(year),'')::NUMERIC::INT   AS year,
    NULLIF(TRIM(rating),'')::NUMERIC::INT AS rating
  FROM staging.performance_yearly
  WHERE NULLIF(TRIM(employee_id),'') IS NOT NULL
  ORDER BY TRIM(employee_id), NULLIF(TRIM(year),'')
)
INSERT INTO core.performance_yearly(employee_id, year, rating)
SELECT employee_id, year, rating
FROM src
ON CONFLICT (employee_id, year) DO UPDATE SET rating = EXCLUDED.rating;

-- =========================
-- COMPETENCIES
-- =========================
WITH src AS (
  SELECT DISTINCT ON (TRIM(employee_id), UPPER(TRIM(pillar_code)), NULLIF(TRIM(year),'') )
    TRIM(employee_id) AS employee_id,
    UPPER(TRIM(pillar_code)) AS pillar_code,
    NULLIF(TRIM(year),'')::NUMERIC::INT  AS year,
    NULLIF(TRIM(score),'')::NUMERIC::INT AS score
  FROM staging.competencies_yearly
  WHERE NULLIF(TRIM(employee_id),'') IS NOT NULL AND NULLIF(TRIM(pillar_code),'') IS NOT NULL
  ORDER BY TRIM(employee_id), UPPER(TRIM(pillar_code)), NULLIF(TRIM(year),'')
)
INSERT INTO core.competencies_yearly(employee_id, pillar_code, year, score)
SELECT employee_id, pillar_code, year, score
FROM src
ON CONFLICT (employee_id, pillar_code, year) DO UPDATE SET score = EXCLUDED.score;

COMMIT;

-- Quick report: total core rows
SELECT 'dim_companies' tbl, COUNT(*) n FROM core.dim_companies
UNION ALL SELECT 'dim_areas', COUNT(*) FROM core.dim_areas
UNION ALL SELECT 'dim_positions', COUNT(*) FROM core.dim_positions
UNION ALL SELECT 'dim_departments', COUNT(*) FROM core.dim_departments
UNION ALL SELECT 'dim_divisions', COUNT(*) FROM core.dim_divisions
UNION ALL SELECT 'dim_directorates', COUNT(*) FROM core.dim_directorates
UNION ALL SELECT 'dim_grades', COUNT(*) FROM core.dim_grades
UNION ALL SELECT 'dim_education', COUNT(*) FROM core.dim_education
UNION ALL SELECT 'dim_majors', COUNT(*) FROM core.dim_majors
UNION ALL SELECT 'dim_competency_pillars', COUNT(*) FROM core.dim_competency_pillars
UNION ALL SELECT 'employees', COUNT(*) FROM core.employees
UNION ALL SELECT 'profiles_psych', COUNT(*) FROM core.profiles_psych
UNION ALL SELECT 'papi_scores', COUNT(*) FROM core.papi_scores
UNION ALL SELECT 'strengths', COUNT(*) FROM core.strengths
UNION ALL SELECT 'performance_yearly', COUNT(*) FROM core.performance_yearly
UNION ALL SELECT 'competencies_yearly', COUNT(*) FROM core.competencies_yearly
ORDER BY 1;

-- Orphan check (must 0 all)
WITH x AS (
  SELECT
    SUM((company_id     IS NULL)::int) AS miss_company,
    SUM((area_id        IS NULL)::int) AS miss_area,
    SUM((position_id    IS NULL)::int) AS miss_position,
    SUM((department_id  IS NULL)::int) AS miss_department,
    SUM((division_id    IS NULL)::int) AS miss_division,
    SUM((directorate_id IS NULL)::int) AS miss_directorate,
    SUM((grade_id       IS NULL)::int) AS miss_grade,
    SUM((education_id   IS NULL)::int) AS miss_education,
    SUM((major_id       IS NULL)::int) AS miss_major
  FROM core.employees
)
SELECT * FROM x;