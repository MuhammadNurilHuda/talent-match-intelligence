\set ON_ERROR_STOP on

-- ==== DIM ====
\copy staging.dim_companies          (company_id, name)          FROM 'staging_csv/dim_companies.csv'          WITH (FORMAT csv, HEADER true)
\copy staging.dim_areas              (area_id, name)             FROM 'staging_csv/dim_areas.csv'              WITH (FORMAT csv, HEADER true)
\copy staging.dim_positions          (position_id, name)         FROM 'staging_csv/dim_positions.csv'          WITH (FORMAT csv, HEADER true)
\copy staging.dim_departments        (department_id, name)       FROM 'staging_csv/dim_departments.csv'        WITH (FORMAT csv, HEADER true)
\copy staging.dim_divisions          (division_id, name)         FROM 'staging_csv/dim_divisions.csv'          WITH (FORMAT csv, HEADER true)
\copy staging.dim_directorates       (directorate_id, name)      FROM 'staging_csv/dim_directorates.csv'       WITH (FORMAT csv, HEADER true)
\copy staging.dim_grades             (grade_id, name)            FROM 'staging_csv/dim_grades.csv'             WITH (FORMAT csv, HEADER true)
\copy staging.dim_education          (education_id, name)        FROM 'staging_csv/dim_education.csv'          WITH (FORMAT csv, HEADER true)
\copy staging.dim_majors             (major_id, name)            FROM 'staging_csv/dim_majors.csv'             WITH (FORMAT csv, HEADER true)

\copy staging.dim_competency_pillars (pillar_code, pillar_label) FROM 'staging_csv/dim_competency_pillars.csv' WITH (FORMAT csv, HEADER true)

-- ==== EMPLOYEES ====
\copy staging.employees_raw (employee_id, fullname, nip, company_id, area_id, position_id, department_id, division_id, directorate_id, grade_id, education_id, major_id, years_of_service_months) FROM 'staging_csv/employees.csv' WITH (FORMAT csv, HEADER true)

-- ==== FACT & PROFILE ====
\copy staging.profiles_psych     (employee_id, pauli, faxtor, disc, disc_word, mbti, iq, gtq, tiki) FROM 'staging_csv/profiles_psych.csv'     WITH (FORMAT csv, HEADER true)
\copy staging.papi_scores        (employee_id, scale_code, score)                                   FROM 'staging_csv/papi_scores.csv'        WITH (FORMAT csv, HEADER true)
\copy staging.strengths          (employee_id, rank, theme)                                         FROM 'staging_csv/strengths.csv'          WITH (FORMAT csv, HEADER true)
\copy staging.performance_yearly (employee_id, rating, year)                                        FROM 'staging_csv/performance_yearly.csv' WITH (FORMAT csv, HEADER true)
\copy staging.competencies_yearly(employee_id, score, pillar_code, year)                            FROM 'staging_csv/competencies_yearly.csv'WITH (FORMAT csv, HEADER true)

-- ==== TV/TGC isn't used ====
