from __future__ import annotations

import pandas as pd


def head_to_depth_cm(head_mnap: pd.Series, ground_level_mnap: pd.Series) -> pd.Series:
    """Convert hydraulic head [m NAP] to groundwater depth [cm below ground].

    Positive depth means below ground surface; negative values mean water above ground.
    """
    return (ground_level_mnap - head_mnap) * 100.0
