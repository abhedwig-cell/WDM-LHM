from pathlib import Path

import pytest

from wdm_lhm.geotop_reference_page_acquisition import (
    REFERENCE_URL,
    GeoTopReferencePageConfig,
    acquire_geotop_reference_page,
)


def test_exact_reference_url_and_official_redirect_are_preserved(tmp_path: Path):
    final = "https://www.dinoloket.nl/ondergrondmodellen/geotop"
    payload = b'<html><body>GeoTOP <a href="/download/doc.pdf">download</a><a href="https://example.org/no">no</a></body></html>'

    def transport(url, headers, timeout_s, max_bytes):
        assert url == REFERENCE_URL
        return payload, {"content-type": "text/html; charset=UTF-8"}, final

    m = acquire_geotop_reference_page(tmp_path, get_transport=transport)
    assert m["request"]["dataset_references_url"] == REFERENCE_URL
    assert m["request"]["final_url"] == final
    assert [r["url"] for r in m["official_links"]] == ["https://www.dinoloket.nl/download/doc.pdf"]
    assert m["guardrails"]["discovered_links_followed"] is False
    assert m["guardrails"]["code_translation_performed"] is False
    assert m["guardrails"]["version_compatibility_established"] is False


def test_reference_url_cannot_drift(tmp_path: Path):
    cfg = GeoTopReferencePageConfig(reference_url="https://www.dinoloket.nl/other")
    with pytest.raises(ValueError, match="pinned"):
        acquire_geotop_reference_page(tmp_path, config=cfg)


def test_redirect_to_third_party_fails_closed(tmp_path: Path):
    def transport(url, headers, timeout_s, max_bytes):
        return b"<html>x</html>", {"content-type": "text/html"}, "https://example.org/geotop"

    with pytest.raises(ValueError, match="escaped official"):
        acquire_geotop_reference_page(tmp_path, get_transport=transport)


def test_non_https_final_url_fails_closed(tmp_path: Path):
    def transport(url, headers, timeout_s, max_bytes):
        return b"<html>x</html>", {"content-type": "text/html"}, REFERENCE_URL

    with pytest.raises(ValueError, match="not HTTPS"):
        acquire_geotop_reference_page(tmp_path, get_transport=transport)


def test_non_html_content_fails_closed(tmp_path: Path):
    final = "https://www.dinoloket.nl/geotop"

    def transport(url, headers, timeout_s, max_bytes):
        return b"data", {"content-type": "application/octet-stream"}, final

    with pytest.raises(ValueError, match="content type"):
        acquire_geotop_reference_page(tmp_path, get_transport=transport)


def test_injected_payload_over_guardrail_fails_closed(tmp_path: Path):
    cfg = GeoTopReferencePageConfig(max_response_bytes=3)
    final = "https://www.dinoloket.nl/geotop"

    def transport(url, headers, timeout_s, max_bytes):
        return b"1234", {"content-type": "text/html"}, final

    with pytest.raises(ValueError, match="guardrail"):
        acquire_geotop_reference_page(tmp_path, config=cfg, get_transport=transport)
