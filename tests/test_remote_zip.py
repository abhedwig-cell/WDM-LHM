import io
import zipfile

from wdm_lhm.remote_zip import RemoteZipIndexConfig, index_remote_zip


def _make_zip() -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt", "hello")
        z.writestr("grids/top_unit.asc", "1 2 3\n")
        z.writestr("grids/bottom_unit.asc", "4 5 6\n")
    return b.getvalue()


def test_index_remote_zip_uses_ranges_only(tmp_path):
    payload = _make_zip()
    calls = []

    def head_transport(url, headers, timeout):
        calls.append(("HEAD", None, None))
        return {
            "content-length": str(len(payload)),
            "content-type": "application/zip",
            "accept-ranges": "bytes",
            "etag": '"abc"',
        }

    def range_transport(url, start, end, headers, timeout):
        calls.append(("RANGE", start, end))
        part = payload[start:end + 1]
        return part, {"content-range": f"bytes {start}-{end}/{len(payload)}"}, 206

    out = index_remote_zip(
        "https://example.test/model.zip",
        tmp_path,
        RemoteZipIndexConfig(tail_bytes=65557),
        head_transport=head_transport,
        range_transport=range_transport,
    )
    assert out["counts"]["files"] == 3
    assert {e["name"] for e in out["entries"]} == {
        "README.txt",
        "grids/top_unit.asc",
        "grids/bottom_unit.asc",
    }
    assert out["remote"]["content_length_bytes"] == len(payload)
    assert len([c for c in calls if c[0] == "RANGE"]) == 2
    assert (tmp_path / "remote_zip_index.json").exists()


def test_index_remote_zip_refuses_non_range_server(tmp_path):
    payload = _make_zip()

    def head_transport(url, headers, timeout):
        return {"content-length": str(len(payload)), "content-type": "application/zip"}

    def range_transport(url, start, end, headers, timeout):
        # Simulate a server ignoring Range and returning the entire object.
        return payload, {"content-type": "application/zip"}, 200

    try:
        index_remote_zip(
            "https://example.test/model.zip",
            tmp_path,
            head_transport=head_transport,
            range_transport=range_transport,
        )
    except ValueError as exc:
        assert "Range" in str(exc)
    else:
        raise AssertionError("Expected fail-closed refusal when server ignores Range")
