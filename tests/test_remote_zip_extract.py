import io
import zipfile

from wdm_lhm.remote_zip import RemoteZipIndexConfig, index_remote_zip
from wdm_lhm.remote_zip_extract import extract_remote_zip_member


def _make_zip() -> bytes:
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("MetaData_TEST.xml", "<metadata><name>REGIS</name></metadata>")
        z.writestr("large.bin", b"x" * 10000)
    return b.getvalue()


def _transports(payload: bytes):
    def head_transport(url, headers, timeout):
        return {
            "content-length": str(len(payload)),
            "content-type": "application/zip",
            "accept-ranges": "bytes",
        }

    def range_transport(url, start, end, headers, timeout):
        part = payload[start:end + 1]
        return part, {"content-range": f"bytes {start}-{end}/{len(payload)}"}, 206

    return head_transport, range_transport


def test_extract_remote_deflated_member_by_ranges(tmp_path):
    payload = _make_zip()
    head_transport, range_transport = _transports(payload)
    index = index_remote_zip(
        "https://example.test/regis.zip",
        tmp_path / "index",
        RemoteZipIndexConfig(),
        head_transport=head_transport,
        range_transport=range_transport,
    )
    entry = next(e for e in index["entries"] if e["name"] == "MetaData_TEST.xml")
    out = extract_remote_zip_member(
        "https://example.test/regis.zip",
        entry,
        tmp_path / "MetaData_TEST.xml",
        RemoteZipIndexConfig(),
        head_transport=head_transport,
        range_transport=range_transport,
    )
    assert out.read_text() == "<metadata><name>REGIS</name></metadata>"


def test_extract_remote_member_refuses_unbounded_file(tmp_path):
    payload = _make_zip()
    head_transport, range_transport = _transports(payload)
    index = index_remote_zip(
        "https://example.test/regis.zip",
        tmp_path / "index",
        head_transport=head_transport,
        range_transport=range_transport,
    )
    entry = next(e for e in index["entries"] if e["name"] == "large.bin")
    try:
        extract_remote_zip_member(
            "https://example.test/regis.zip",
            entry,
            tmp_path / "large.bin",
            head_transport=head_transport,
            range_transport=range_transport,
            max_uncompressed_bytes=100,
        )
    except ValueError as exc:
        assert "bounded extraction limit" in str(exc)
    else:
        raise AssertionError("Expected bounded extraction refusal")
