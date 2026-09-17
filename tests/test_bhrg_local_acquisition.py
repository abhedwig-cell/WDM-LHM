import hashlib
import json

import pytest

from wdm_lhm.bhrg_local_acquisition import (
    BHRG_BASE,
    LocalBhrgConfig,
    acquire_local_bhrg,
    build_characteristics_body,
    build_characteristics_url,
    build_object_url,
    parse_characteristics_response,
    rd_to_wgs84,
)


def _characteristics_xml(ids):
    docs = "".join(
        f"<bhrg:dispatchDocument><brocom:broId>{bro_id}</brocom:broId></bhrg:dispatchDocument>"
        for bro_id in ids
    )
    return (
        f'<bhrg:dispatchCharacteristicsResponse xmlns:bhrg="urn:test:bhrg" '
        f'xmlns:brocom="urn:test:brocommon" numberOfDocuments="{len(ids)}">'
        f"<brocom:responseType>dispatch</brocom:responseType>{docs}"
        f"</bhrg:dispatchCharacteristicsResponse>"
    ).encode()


def _object_xml(bro_id):
    return (
        f'<bhrg:BoreholeResearch xmlns:bhrg="urn:test:bhrg" '
        f'xmlns:brocom="urn:test:brocommon">'
        f"<brocom:broId>{bro_id}</brocom:broId>"
        f"<bhrg:dummy>raw-only</bhrg:dummy>"
        f"</bhrg:BoreholeResearch>"
    ).encode()


def test_rd_to_wgs84_target_is_deterministic():
    lon, lat = rd_to_wgs84(172274.997571, 447781.978030)
    assert lon == pytest.approx(5.638863172, abs=1e-9)
    assert lat == pytest.approx(52.018122914, abs=1e-9)


def test_characteristics_request_is_fixed_and_bounded():
    cfg = LocalBhrgConfig()
    url = build_characteristics_url(request_reference=cfg.request_reference)
    body = build_characteristics_body(cfg)
    assert url == (
        f"{BHRG_BASE}/characteristics/searches?"
        "requestReference=wdm-lhm-stage-b-local-bhrg-20774"
    )
    assert body["area"]["enclosingCircle"]["radius"] == 0.5
    assert body["area"]["enclosingCircle"]["center"]["lat"] == pytest.approx(52.018122914)
    assert body["area"]["enclosingCircle"]["center"]["lon"] == pytest.approx(5.638863172)


def test_parse_characteristics_zero_result():
    assert parse_characteristics_response(_characteristics_xml([])) == []


def test_parse_characteristics_rejects_duplicates_and_over_limit():
    with pytest.raises(ValueError, match="Duplicate"):
        parse_characteristics_response(_characteristics_xml(["BHR0001", "BHR0001"]))
    with pytest.raises(ValueError, match="exceeds bounded guardrail"):
        parse_characteristics_response(
            _characteristics_xml(["BHR0001", "BHR0002"]),
            max_results=1,
        )


def test_object_url_is_pinned():
    assert build_object_url("BHR000123") == f"{BHRG_BASE}/objects/BHR000123"
    with pytest.raises(ValueError, match="Unexpected BHR-G BRO-ID"):
        build_object_url("../bad")


def test_acquisition_persists_raw_hashes_without_interpretation(tmp_path):
    ids = ["BHR0001", "BHR0002"]
    char = _characteristics_xml(ids)
    objects = {bro_id: _object_xml(bro_id) for bro_id in ids}
    calls = []

    def transport(method, url, headers, body, timeout_s, max_bytes):
        calls.append((method, url, headers, body, timeout_s, max_bytes))
        if method == "POST":
            sent = json.loads(body.decode())
            assert sent["area"]["enclosingCircle"]["radius"] == 0.5
            return char, {"content-type": "application/xml"}, url, 200
        bro_id = url.rsplit("/", 1)[-1]
        return objects[bro_id], {"content-type": "application/xml"}, url, 200

    manifest = acquire_local_bhrg(tmp_path, transport=transport)
    assert manifest["result"]["state"] == "LOCAL_BHRG_OBJECTS_ACQUIRED"
    assert manifest["result"]["bro_ids"] == ids
    assert manifest["result"]["count"] == 2
    assert manifest["search"]["response_sha256"] == hashlib.sha256(char).hexdigest()
    assert [item["sha256"] for item in manifest["result"]["objects"]] == [
        hashlib.sha256(objects[bro_id]).hexdigest() for bro_id in ids
    ]
    assert manifest["guardrails"]["raw_only"] is True
    assert manifest["guardrails"]["lithology_interpretation_performed"] is False
    assert manifest["guardrails"]["hydraulic_interpretation_performed"] is False
    assert manifest["guardrails"]["admission_decision_performed"] is False
    assert "lithology" not in manifest["result"]
    assert (tmp_path / "bhrg_characteristics_response.xml").read_bytes() == char
    assert (tmp_path / "bhrg_local_manifest.json").is_file()
    assert len(calls) == 3


def test_acquisition_zero_result_is_valid_evidence(tmp_path):
    char = _characteristics_xml([])

    def transport(method, url, headers, body, timeout_s, max_bytes):
        assert method == "POST"
        return char, {"content-type": "application/xml"}, url, 200

    manifest = acquire_local_bhrg(tmp_path, transport=transport)
    assert manifest["result"]["state"] == "NO_LOCAL_BHRG_FOUND"
    assert manifest["result"]["count"] == 0
    assert manifest["result"]["objects"] == []


def test_acquisition_rejects_object_id_mismatch_and_redirect_drift(tmp_path):
    char = _characteristics_xml(["BHR0001"])

    def mismatch(method, url, headers, body, timeout_s, max_bytes):
        if method == "POST":
            return char, {"content-type": "application/xml"}, url, 200
        return _object_xml("BHR9999"), {"content-type": "application/xml"}, url, 200

    with pytest.raises(ValueError, match="BRO-ID mismatch"):
        acquire_local_bhrg(tmp_path / "mismatch", transport=mismatch)

    def redirect(method, url, headers, body, timeout_s, max_bytes):
        if method == "POST":
            return char, {"content-type": "application/xml"}, url, 200
        return _object_xml("BHR0001"), {"content-type": "application/xml"}, "https://example.org/object", 200

    with pytest.raises(ValueError, match="Unexpected BHR-G object final URL"):
        acquire_local_bhrg(tmp_path / "redirect", transport=redirect)
