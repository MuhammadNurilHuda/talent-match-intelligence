"""
weight_search.py
----------------
Lightweight grid search for cross-domain weight tuning (w_main) under the constraint sum = 1.

Purpose:
- Explore reasonable combinations of component weights for the Success Score model.
- Used in Step 2 (SQL Logic Design) to validate proportional balance between domains.

Notes:
- The grid is intentionally coarse but computationally light.
- Each generated weight dictionary satisfies 0.05 ≤ context ≤ 0.20.
"""
import itertools
import numpy as np

# ---------------------------------------------------------------------------
# Simple grid generator for w_main combinations
# ---------------------------------------------------------------------------
def grid_weights():
    """
    Generate small grid combinations of domain weights (competency, strengths,
    psychometric, context) where all components sum to 1.0.

    Returns:
        Iterator[dict[str, float]]: Each element is a weight configuration like:
            {"competency": 0.50, "strengths": 0.25, "psychometric": 0.15, "context": 0.10}
    """
    # Iterate over coarse but meaningful ranges for each main component.
    for c in [0.45, 0.50, 0.55]:
        for s in [0.20, 0.25, 0.30]:
            for p in [0.10, 0.15, 0.20]:
                # Ensure total weight equals 1.0 by allocating the remaining share to context.
                rest = 1.0 - (c + s + p)
                # Only yield configurations where context weight falls within [0.05, 0.20].
                if 0.05 <= rest <= 0.20:
                    yield {"competency":c, "strengths":s, "psychometric":p, "context":rest}