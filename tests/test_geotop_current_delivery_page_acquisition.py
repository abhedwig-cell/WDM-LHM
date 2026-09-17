from pathlib import Path

import pytest

from wdm_lhm.geotop_current_delivery_page_acquisition import (
    CURRENT_DELIVERY_URL,
    GeoTopCurrentDeliveryPageConfig,
    acquire_geotop_current_delivery_page,
)


def test_acquires_only_pinned_current_delivery_page(tmp_path: Path) -> None:
    html = b'''<html><body>
    <a href="/sites/default/files/geotop/reference-lists.zip">refs</a>
    <a href="/modelbestanden-aanvragen">model files</a>
    <a href="https://example.org/not-official.zip">outside</a>
    GeoTOP 1.6.1 referentielijsten REF_GTP_LITHO_CLASS
    </body></html>'''
    calls = []

    def transport(url, headers, timeout_s, max_bytes):
        calls.append(url)
        return html, {"content-type": "text/html; charset=UTF-8"}, CURRENT_DELIVERY_URL

    m = acquire_geotop_current_delivery_page(tmp_path, get_transport=transport)
    assert calls == [CURRENT_DELIVERY_URL]
    assert m["state"] == "OFFICIAL_CURRENT_DELIVERY_PAGE_ACQUIRED_LINKS_NOT_FOLLOWED"
    assert m["request"]["url"] == CURRENT_DELIVERY_URL
    assert len(m["official_links"]) == 2
    assert any(rec["path"].endswith("reference-lists.zip") for rec in m["candidate_authority_links"])
    assert "REF_GTP_LITHO_CLASS" in m["marker_hits"]
    g = m["guardrails"]
    assert g["links_followed"] is False
    assert g["generic_web_search_performed"] is False
    assert g["code_translation_performed"] is False
    assert g["version_compatibility_established"] is False
    assert g["admission_decision_performed"] is False


def test_rejects_unpinned_source(tmp_path: Path) -> None:
    cfg = GeoTopCurrentDeliveryPageConfig(url="https://www.dinoloket.nl/other")
    with pytest.raises(ValueError, match="pinned"):
        acquire_geotop_current_delivery_page(tmp_path, cfg, get_transport=lambda *args: None)


def test_rejects_external_redirect(tmp_path: Path) -> None:
    def transport(url, headers, timeout_s, max_bytes):
        return b"<html>GeoTOP</html>", {"content-type": "text/html"}, "https://example.org/geotop"
    with pytest.raises(ValueError, match="escaped official"):
        acquire_geotop_current_delivery_page(tmp_path, get_transport=transport)


def test_rejects_non_html(tmp_path: Path) -> None:
    def transport(url, headers, timeout_s, max_bytes):
        return b"data", {"content-type": "application/zip"}, CURRENT_DELIVERY_URL
    with pytest.raises(ValueError, match="content type"):
        acquire_geotop_current_delivery_page(tmp_path, get_transport=transport)
