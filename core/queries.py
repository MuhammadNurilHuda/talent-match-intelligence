"""
queries.py
-----------
Menyimpan query SQL mentah yang sering dipakai.
Tujuan: menjaga pemisahan antara logika Python dan SQL.

Termasuk:
- Q_PERF_ALL, Q_COMP_ALL   : ambil data performa & kompetensi tahunan.
- Q_DIM_COMP_PILLARS       : label pilar kompetensi.
- Q_EMP_ORG                : metadata karyawan (grade, pendidikan, masa kerja).
"""

# Kompetensi & label performa
Q_PERF_ALL = """
SELECT employee_id, year, rating
FROM core.performance_yearly;
"""

Q_COMP_ALL = """
SELECT employee_id, pillar_code, year, score
FROM core.competencies_yearly;
"""

# Mapping label pilar
Q_DIM_COMP_PILLARS = """
SELECT pillar_code, pillar_label
FROM core.dim_competency_pillars;
"""

# Konteks org (jika dibutuhkan slicing nanti)
Q_EMP_ORG = """
SELECT employee_id, fullname, years_of_service_months,
       grade_id, education_id, major_id
FROM core.employees;
"""

# Ambil tabel PAPI
Q_PAPI = """
SELECT employee_id, scale_code, score
FROM core.papi_scores;
"""

# Ambil tabel profiles_psych
Q_PSYCH = """
SELECT employee_id, pauli, faxtor, disc, mbti, iq, gtq, tiki
FROM core.profiles_psych;
"""