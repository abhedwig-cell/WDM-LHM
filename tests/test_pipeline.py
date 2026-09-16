from pathlib import Path
from wdm_lhm.synthetic import make_synthetic
from wdm_lhm.pipeline import run_station


def test_pipeline(tmp_path: Path):
    inp = tmp_path / "input.csv"
    make_synthetic(years=4).to_csv(inp, index=False)
    out = tmp_path / "out"
    result = run_station(inp, out, "test")
    assert (out / "report.html").exists()
    assert (out / "gxg.csv").exists()
    assert len(result["response"]) == 2
