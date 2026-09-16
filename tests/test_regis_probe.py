from wdm_lhm.regis_probe import RegisProbeConfig, parse_atom_document, probe_regis_delivery


def test_parse_atom_document_links():
    payload = b'''<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <title>BRO REGIS II</title>
      <id>urn:test:regis</id>
      <updated>2026-09-01T00:00:00Z</updated>
      <link rel="section" type="application/atom+xml" href="sub/feed.xml" />
      <link rel="enclosure" type="application/zip" href="downloads/regis.zip" />
    </feed>'''
    doc = parse_atom_document(payload, "https://service.test/root/index.xml")
    assert doc["metadata"]["title"] == "BRO REGIS II"
    assert doc["links"][0]["href"] == "https://service.test/root/sub/feed.xml"
    assert doc["links"][1]["href"] == "https://service.test/root/downloads/regis.zip"


def test_probe_regis_delivery_recurses_without_downloading_archive(tmp_path):
    root = b'''<feed xmlns="http://www.w3.org/2005/Atom">
      <title>REGIS root</title><id>root</id><updated>2026-09-01T00:00:00Z</updated>
      <link rel="section" type="application/atom+xml" href="sub.xml" />
    </feed>'''
    sub = b'''<feed xmlns="http://www.w3.org/2005/Atom">
      <title>REGIS delivery</title><id>delivery</id><updated>2026-09-02T00:00:00Z</updated>
      <link rel="enclosure" type="application/zip" href="model/regis_v223.zip" />
    </feed>'''
    calls = []

    def get_transport(url, headers, timeout):
        calls.append(("GET", url))
        if url == "https://service.test/index.xml":
            return root, {"content-type": "application/atom+xml"}
        if url == "https://service.test/sub.xml":
            return sub, {"content-type": "application/atom+xml"}
        raise AssertionError(url)

    def head_transport(url, headers, timeout):
        calls.append(("HEAD", url))
        assert url == "https://service.test/model/regis_v223.zip"
        return {
            "content-length": "123456",
            "content-type": "application/zip",
            "last-modified": "Wed, 16 Sep 2026 10:00:00 GMT",
        }

    result = probe_regis_delivery(
        tmp_path,
        RegisProbeConfig(atom_url="https://service.test/index.xml", max_depth=2),
        get_transport=get_transport,
        head_transport=head_transport,
    )
    assert result["counts"] == {"feeds": 2, "download_candidates": 1}
    assert result["downloads"][0]["content_length_bytes"] == 123456
    assert (tmp_path / "regis_probe_manifest.json").exists()
    assert not any(method == "GET" and url.endswith(".zip") for method, url in calls)
