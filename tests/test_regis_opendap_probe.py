from pathlib import Path

from wdm_lhm.regis_opendap_probe import (
    REGIS_OPENDAP_ROOT,
    RegisOpendapProbeConfig,
    normalize_dataset_url,
    probe_regis_opendap,
)


def test_default_root_uses_tls_valid_www_host():
    assert REGIS_OPENDAP_ROOT == "https://www.dinodata.nl/opendap/"
    assert RegisOpendapProbeConfig().root_url == REGIS_OPENDAP_ROOT


def test_normalize_dataset_url_accepts_dap_metadata_links():
    base = "https://www.dinodata.nl/opendap/REGIS/REGIS.nc"
    assert normalize_dataset_url(base) == base
    assert normalize_dataset_url(base + ".html") == base
    assert normalize_dataset_url(base + ".dds") == base
    assert normalize_dataset_url(base + ".das") == base
    assert normalize_dataset_url("https://www.dinodata.nl/opendap/REGIS/") is None


def test_probe_discovers_metadata_without_value_requests(tmp_path: Path):
    root = "https://www.dinodata.nl/opendap/"
    dataset = root + "REGIS/REGIS.nc"
    responses = {
        root: (
            b'<a href="REGIS/">REGIS</a>'
            b'<a href="https://outside.invalid/opendap/REGIS/">outside</a>',
            {"content-type": "text/html"},
            root,
        ),
        root + "REGIS/": (
            b'<a href="REGIS.nc.html">REGIS II</a>',
            {"content-type": "text/html"},
            root + "REGIS/",
        ),
        dataset + ".dds": (
            b"Dataset { Float32 top[layer=132][y=10][x=10]; } REGIS.nc;",
            {"content-type": "text/plain"},
            dataset + ".dds",
        ),
        dataset + ".das": (
            b'Attributes { NC_GLOBAL { String version "v02r2s3"; String crs "EPSG:28992"; } }',
            {"content-type": "text/plain"},
            dataset + ".das",
        ),
    }
    requested: list[str] = []

    def transport(url: str, headers: dict[str, str], timeout_s: int, max_bytes: int):
        requested.append(url)
        payload, response_headers, final_url = responses[url]
        assert len(payload) <= max_bytes
        return payload, response_headers, final_url

    manifest = probe_regis_opendap(
        tmp_path,
        RegisOpendapProbeConfig(max_depth=2, max_pages=10),
        get_transport=transport,
    )

    assert manifest["counts"]["pages"] == 2
    assert manifest["counts"]["dataset_candidates"] == 1
    assert manifest["counts"]["dap2_metadata_candidates"] == 1
    assert manifest["counts"]["v02r2s3_hints"] == 1
    assert manifest["datasets"][0]["dataset_url"] == dataset
    assert all(not flag for flag in manifest["guardrails"].values())
    assert not any(".ascii" in url or ".dods" in url for url in requested)
    assert not any("outside.invalid" in url for url in requested)
    assert (tmp_path / "regis_opendap_probe_manifest.json").is_file()


def test_probe_fails_closed_when_root_is_unavailable(tmp_path: Path):
    def transport(url: str, headers: dict[str, str], timeout_s: int, max_bytes: int):
        raise OSError("synthetic service failure")

    try:
        probe_regis_opendap(tmp_path, get_transport=transport)
    except OSError as exc:
        assert "synthetic service failure" in str(exc)
    else:
        raise AssertionError("root service failure must propagate")
