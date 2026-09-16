import numpy as np
import pandas as pd
from wdm_lhm.response_model import fit_linear_reservoir


def test_response_recovers_memory():
    rng = np.random.default_rng(1)
    idx = pd.date_range("2020-01-01", periods=1000, freq="D")
    p = pd.Series(rng.gamma(1.0, 2.0, len(idx)), index=idx)
    et = pd.Series(np.full(len(idx), 1.5), index=idx)
    r = (p-et).to_numpy()
    a = 0.95
    x = np.zeros(len(idx))
    for i in range(1, len(idx)):
        x[i] = a*x[i-1] + r[i]
    y = pd.Series(80.0 - 0.4*x, index=idx)
    fit = fit_linear_reservoir(y, p, et)
    assert abs(fit.memory_a - a) < 0.01
    assert abs(fit.gain + 0.4) < 0.03
