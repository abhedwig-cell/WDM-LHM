import json

import pytest

from wdm_lhm.bhrg_local_20760 import (
    CAPABILITY,
    REQUEST_REFERENCE,
    TARGET_GMW,
    TARGET_STATION,
    acquire_local_bhrg_20760,
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


def test_20760_adapter_reuses_engine_with_exact_target_and_guardrails(tmp_path):
    calls = []
    response = _characteristics_xml([])

    def transport(method, url, headers, body, timeout_s, max_bytes):
        calls.append((method, url, headers, body, timeout_s, max_bytes))
        assert method == "POST"
        request = json.loads(body.decode())
        circle = request["area"]["enclosingCircle"]
        assert circle["radius"] == 0.5
        assert circle["center"]["lon"] == pytest.approx(5.671091912, abs=1e-9)
        assert circle["center"]["lat"] == pytest.approx(52.005025614, abs=1e-9)
        assert REQUEST_REFERENCE in url
        return response, {"content-type": "application/xml"}, url, 200

    manifest = acquire_local_bhrg_20760(tmp_path, transport=transport)

    assert manifest["capability"] == CAPABILITY
    assert manifest["target"]["gmw"] == TARGET_GMW
    assert manifest["target"]["station"] == TARGET_STATION
    assert manifest["target"]["rd_x_m"] == pytest.approx(174493.0038178011)
    assert manifest["target"]["rd_y_m"] == pytest.approx(446332.9711833446)
    assert manifest["result"]["state"] == "NO_LOCAL_BHRG_FOUND"
    assert manifest["result"]["count"] == 0
    assert manifest["guardrails"]["raw_only"] is True
    assert manifest["guardrails"]["lithology_interpretation_performed"] is False
    assert manifest["guardrails"]["hydraulic_interpretation_performed"] is False
    assert manifest["guardrails"]["screen_correlation_performed"] is False
    assert manifest["guardrails"]["geotop_used"] is False
    assert manifest["guardrails"]["admission_decision_performed"] is False
    assert manifest["guardrails"]["allow_admissible_enabled"] is False
    assert manifest["adapter"]["candidate_specific_network_logic_added"] is False
    assert "GMW000000020760 only" in manifest["qualification_boundary"]
    assert len(calls) == 1

    persisted = json.loads((tmp_path / "bhrg_local_manifest.json").read_text())
    assert persisted["capability"] == CAPABILITY
    assert persisted["target"]["gmw"] == TARGET_GMW
