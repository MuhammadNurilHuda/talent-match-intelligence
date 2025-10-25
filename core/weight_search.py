"""
weight_search.py
----------------
Grid search sederhana untuk w_main (antar-domain), dengan constraint sum=1.
"""
import itertools
import numpy as np

def grid_weights():
    # grid kasar tapi kecil
    for c in [0.45, 0.50, 0.55]:
        for s in [0.20, 0.25, 0.30]:
            for p in [0.10, 0.15, 0.20]:
                rest = 1.0 - (c + s + p)
                if 0.05 <= rest <= 0.20:
                    yield {"competency":c, "strengths":s, "psychometric":p, "context":rest}