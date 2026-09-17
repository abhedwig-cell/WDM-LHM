from pathlib import Path

import pytest

from wdm_lhm.geotop_netcdf_page_acquisition import (
    NETCDF_PAGE_URL,
    GeoTopNetcdfPageConfig,
    acquire_geotop_netcdf_page,
)


def test_inventories_netcdf_page_without_actions(tmp_path: Path) -> None:
    html = b'''<html><body>
    GeoTOP NetCDF referentielijsten OPeNDAP
    <a href="/files/geotop/refs.xlsx">refs</a>
    <form action="/modelbestanden-aanvragen/netcdf" method="post">
      <select name="model"><option>GeoTOP</option></select>
      <input name="bbox" />
    </form>
    </body></html>'''
    calls = []
    def transport(url, headers, timeout_s, max_bytes):
        calls.append(url)
        return html, {"content-type": "text/html"}, NETCDF_PAGE_URL

    m = acquire_geotop_netcdf_page(tmp_path, get_transport=transport)
    assert calls == [NETCDF_PAGE_URL]
    assert m["state"] == "OFFICIAL_NETCDF_PAGE_ACQUIRED_NO_ACTIONS_INVOKED"
    assert len(m["forms"]) == 1
    assert m["forms"][0]["method"] == "post"
    assert any(rec["path"].endswith("refs.xlsx") for rec in m["candidate_authority_links"])
    g = m["guardrails"]
    assert g["links_followed"] is False
    assert g["forms_submitted"] is False
    assert g["data_request_performed"] is False
    assert g["code_translation_performed"] is False


def test_rejects_unpinned_page(tmp_path: Path) -> None:
    cfg = GeoTopNetcdfPageConfig(url="https://www.dinoloket.nl/other")
    with pytest.raises(ValueError, match="pinned"):
        acquire_geotop_netcdf_page(tmp_path, cfg, get_transport=lambda *args: None)


def test_rejects_external_redirect(tmp_path: Path) -> None:
    def transport(url, headers, timeout_s, max_bytes):
        return b"<html>GeoTOP</html>", {"content-type": "text/html"}, "https://example.org/netcdf"
    with pytest.raises(ValueError, match="escaped official"):
        acquire_geotop_netcdf_page(tmp_path, get_transport=transport)


def test_rejects_non_html(tmp_path: Path) -> None:
    def transport(url, headers, timeout_s, max_bytes):
        return b"data", {"content-type": "application/x-netcdf"}, NETCDF_PAGE_URL
    with pytest.raises(ValueError, match="content type"):
        acquire_geotop_netcdf_page(tmp_path, get_transport=transport)
