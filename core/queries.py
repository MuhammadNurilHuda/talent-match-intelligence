"""
queries.py
----------
Centralized repository for reusable raw SQL query strings.

Purpose:
Maintain separation between Python business logic and SQL logic.

Includes:
- Q_PERF_ALL, Q_COMP_ALL     : Fetch yearly performance and competency data.
- Q_DIM_COMP_PILLARS         : Retrieve competency pillar labels.
- Q_EMP_ORG                  : Fetch employee metadata (grade, education, years of service).
- Q_PAPI, Q_PSYCH            : Retrieve PAPI and psychometric assessment tables.
"""

# ---------------------------------------------------------------------------
# Performance and Competency Data
# ---------------------------------------------------------------------------
Q_PERF_ALL = """
SELECT employee_id, year, rating
FROM core.performance_yearly;
"""

Q_COMP_ALL = """
SELECT employee_id, pillar_code, year, score
FROM core.competencies_yearly;
"""

# ---------------------------------------------------------------------------
# Competency Pillar Labels
# ---------------------------------------------------------------------------
Q_DIM_COMP_PILLARS = """
SELECT pillar_code, pillar_label
FROM core.dim_competency_pillars;
"""

# ---------------------------------------------------------------------------
# Organizational Context (for future slicing and contextual analysis)
# ---------------------------------------------------------------------------
Q_EMP_ORG = """
SELECT employee_id, fullname, years_of_service_months,
       grade_id, education_id, major_id
FROM core.employees;
"""

# ---------------------------------------------------------------------------
# PAPI Behavioral Scales
# ---------------------------------------------------------------------------
Q_PAPI = """
SELECT employee_id, scale_code, score
FROM core.papi_scores;
"""

# ---------------------------------------------------------------------------
# Psychometric Profiles
# ---------------------------------------------------------------------------
Q_PSYCH = """
SELECT employee_id, pauli, faxtor, disc, mbti, iq, gtq, tiki
FROM core.profiles_psych;
"""