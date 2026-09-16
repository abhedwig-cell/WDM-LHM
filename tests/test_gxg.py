import numpy as np
import pandas as pd
from wdm_lhm.gxg import calculate_gxg


def test_gxg_constant_series():
    idx = pd.date_range("2010-01-01", "2014-12-31", freq="D")
    s = pd.Series(75.0, index=idx)
    gxg = calculate_gxg(s)
    assert np.isclose(gxg.ghg_cm, 75.0)
    assert np.isclose(gxg.gvg_cm, 75.0)
    assert np.isclose(gxg.glg_cm, 75.0)
    assert gxg.n_hydro_years_ghg_glg >= 4
