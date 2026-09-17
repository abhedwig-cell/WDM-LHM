from pathlib import Path

import pytest

from wdm_lhm.geotop_codebook_authority_discovery import (
    DATASET_URL,
    GeoTopAuthorityDiscoveryConfig,
    acquire_geotop_authority_discovery,
)


def test_acquires_only_exact_service_resources_and_does_not_follow_links(tmp_path: Path):
    html_url = f"{DATASET_URL}.html"
    info_url = f"{DATASET_URL}.info"
    html = b'<html><body><a href="https://www.dinoloket.nl/foo">GeoTOP</a><a href="https://example.org/nope">third</a></body></html>'
    info = b"GeoTOP dataset information"
    seen = []

    def transport(url, headers, timeout_s, max_bytes):
        seen.append(url)
        if url == html_url:
            return html, {"content-type": "text/html; charset=UTF-8"}, url
        if url == info_url:
            return info, {"content-type": "text/plain; charset=UTF-8"}, url
        raise AssertionError(url)

    manifest = acquire_geotop_authority_discovery(tmp_path, get_transport=transport)
    assert seen == [html_url, info_url]
    assert manifest["official_links"] == ["https://www.dinoloket.nl/foo"]
    assert manifest["guardrails"]["discovered_links_followed"] is False
    assert manifest["guardrails"]["third_party_resources_requested"] is False
    assert manifest["guardrails"]["code_translation_performed"] is False
    assert manifest["guardrails"]["version_compatibility_established"] is False


def test_dataset_drift_fails_closed(tmp_path: Path):
    cfg = GeoTopAuthorityDiscoveryConfig(dataset_url="https://example.org/geotop.nc")
    with pytest.raises(ValueError, match="official host"):
        acquire_geotop_authority_discovery(tmp_path, config=cfg)


def test_redirect_drift_fails_closed(tmp_path: Path):
    def transport(url, headers, timeout_s, max_bytes):
        return b"x", {"content-type": "text/plain"}, "https://example.org/geotop.nc.info"

    with pytest.raises(ValueError, match="redirect escaped"):
        acquire_geotop_authority_discovery(tmp_path, get_transport=transport)


def test_empty_resource_fails_closed(tmp_path: Path):
    html_url = f"{DATASET_URL}.html"

    def transport(url, headers, timeout_s, max_bytes):
        if url == html_url:
            return b"", {"content-type": "text/html"}, url
        return b"info", {"content-type": "text/plain"}, url

    with pytest.raises(ValueError, match="empty"):
        acquire_geotop_authority_discovery(tmp_path, get_transport=transport)


def test_size_guardrail_preserved_for_injected_transport(tmp_path: Path):
    cfg = GeoTopAuthorityDiscoveryConfig(max_resource_bytes=3)

    def transport(url, headers, timeout_s, max_bytes):
        return b"1234", {"content-type": "text/plain"}, url

    # Real transport enforces this before return; injected transport is still
    # bounded by the acquisition layer through the configured size check.
    with pytest.raises(ValueError, match="guardrail"):
        acquire_geotop_authority_discovery(tmp_path, config=cfg, get_transport=transport)
