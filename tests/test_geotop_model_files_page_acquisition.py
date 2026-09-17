from pathlib import Path

import pytest

from wdm_lhm.geotop_model_files_page_acquisition import (
    MODEL_FILES_URL,
    GeoTopModelFilesPageConfig,
    acquire_geotop_model_files_page,
)


def test_inventories_links_and_forms_without_actions(tmp_path: Path) -> None:
    html = b'''<html><body>
    GeoTOP modelbestanden referentielijsten
    <a href="/files/geotop/reference.zip">download</a>
    <form action="/modelbestanden-aanvragen" method="post" id="request-form">
      <select name="model"><option>GeoTOP</option></select>
      <input name="email" />
      <button name="submit">send</button>
    </form>
    </body></html>'''
    calls = []
    def transport(url, headers, timeout_s, max_bytes):
        calls.append(url)
        return html, {"content-type": "text/html"}, MODEL_FILES_URL

    m = acquire_geotop_model_files_page(tmp_path, get_transport=transport)
    assert calls == [MODEL_FILES_URL]
    assert m["state"] == "OFFICIAL_MODEL_FILES_PAGE_ACQUIRED_NO_ACTIONS_INVOKED"
    assert len(m["forms"]) == 1
    assert m["forms"][0]["method"] == "post"
    assert m["forms"][0]["action_is_official"] is True
    assert m["forms"][0]["input_names"] == ["email", "model", "submit"]
    assert any(rec["path"].endswith("reference.zip") for rec in m["candidate_authority_links"])
    g = m["guardrails"]
    assert g["links_followed"] is False
    assert g["forms_submitted"] is False
    assert g["form_actions_invoked"] is False
    assert g["code_translation_performed"] is False


def test_rejects_unpinned_page(tmp_path: Path) -> None:
    cfg = GeoTopModelFilesPageConfig(url="https://www.dinoloket.nl/other")
    with pytest.raises(ValueError, match="pinned"):
        acquire_geotop_model_files_page(tmp_path, cfg, get_transport=lambda *args: None)


def test_rejects_external_redirect(tmp_path: Path) -> None:
    def transport(url, headers, timeout_s, max_bytes):
        return b"<html>GeoTOP</html>", {"content-type": "text/html"}, "https://example.org/model"
    with pytest.raises(ValueError, match="escaped official"):
        acquire_geotop_model_files_page(tmp_path, get_transport=transport)


def test_rejects_non_html(tmp_path: Path) -> None:
    def transport(url, headers, timeout_s, max_bytes):
        return b"PK", {"content-type": "application/zip"}, MODEL_FILES_URL
    with pytest.raises(ValueError, match="content type"):
        acquire_geotop_model_files_page(tmp_path, get_transport=transport)
