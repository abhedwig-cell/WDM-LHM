from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path


OUTER_SHA256 = "1017fa7a76a1f66d09b7aeafe0fc40df226bd29e40767672355e7eddb8906d0e"
MODEL_MEMBER = "Model_HGM000000000062.zip"
MODEL_SHA256 = "ad852235b6ae512f8592c7f59126a7d238bb22580c9ce800cd61de1da7919645"
TERMINAL_MEMBER = "REGIS II_v02r2s3.zip"
TERMINAL_SHA256 = "c983b244d9fa85478fcb7c3df4900b94e8a0282ac1b238b8081ed0f4bc785ea5"
AUTHORITY_MEMBER = "REGIS II_v02r2s3/Toelichting op de bestanden van REGIS II v2.2.3.pdf"
AUTHORITY_CRC32 = "0bb0995f"
AUTHORITY_DECLARED_SIZE = 900_620


def _sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _copy_zip_member_to_temp(
    zf: zipfile.ZipFile,
    member: str,
    *,
    prefix: str,
    chunk_size: int = 16 * 1024 * 1024,
) -> tuple[Path, str, int, str]:
    try:
        info = zf.getinfo(member)
    except KeyError as exc:
        raise ValueError(f"Required archive member not present: {member}") from exc
    if info.is_dir():
        raise ValueError(f"Required archive member is a directory: {member}")
    fd, tmp_name = tempfile.mkstemp(prefix=prefix, suffix=".zip")
    os.close(fd)
    tmp = Path(tmp_name)
    digest = hashlib.sha256()
    copied = 0
    try:
        with zf.open(info, "r") as src, tmp.open("wb") as dst:
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                dst.write(chunk)
                digest.update(chunk)
                copied += len(chunk)
        if copied != info.file_size:
            raise ValueError(
                f"Archive member size mismatch for {member}: copied {copied}, expected {info.file_size}"
            )
        if not zipfile.is_zipfile(tmp):
            raise ValueError(f"Required ZIP member is not a valid ZIP archive: {member}")
        return tmp, digest.hexdigest(), copied, f"{info.CRC:08x}"
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def extract_regis_authority_document(
    outer_zip: str | os.PathLike[str],
    output_dir: str | os.PathLike[str],
    *,
    expected_outer_sha256: str = OUTER_SHA256,
    expected_model_sha256: str = MODEL_SHA256,
    expected_terminal_sha256: str = TERMINAL_SHA256,
    max_document_bytes: int = 5 * 1024 * 1024,
) -> dict:
    """Extract exactly one documented authority PDF from the qualified REGIS delivery.

    The function is deliberately tied to the archive chain admitted by the recursive
    inventory checkpoint. It materialises only the two nested ZIP containers and the
    single authority PDF. No raster, shapefile, XML or spreadsheet member is opened.
    Any archive/hash/member drift fails closed.
    """
    outer_path = Path(outer_zip)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not outer_path.is_file():
        raise FileNotFoundError(outer_path)
    if not zipfile.is_zipfile(outer_path):
        raise ValueError(f"REGIS source is not a ZIP file: {outer_path}")

    outer_sha = _sha256_file(outer_path)
    if outer_sha != expected_outer_sha256:
        raise ValueError(
            f"Outer REGIS SHA-256 drift: {outer_sha}; expected {expected_outer_sha256}"
        )

    model_tmp: Path | None = None
    terminal_tmp: Path | None = None
    document_path: Path | None = None
    try:
        with zipfile.ZipFile(outer_path, "r") as outer:
            model_tmp, model_sha, model_size, model_crc = _copy_zip_member_to_temp(
                outer, MODEL_MEMBER, prefix="wdm_lhm_regis_model_"
            )
        if model_sha != expected_model_sha256:
            raise ValueError(
                f"Model archive SHA-256 drift: {model_sha}; expected {expected_model_sha256}"
            )

        with zipfile.ZipFile(model_tmp, "r") as model:
            terminal_tmp, terminal_sha, terminal_size, terminal_crc = _copy_zip_member_to_temp(
                model, TERMINAL_MEMBER, prefix="wdm_lhm_regis_terminal_"
            )
        if terminal_sha != expected_terminal_sha256:
            raise ValueError(
                f"Terminal archive SHA-256 drift: {terminal_sha}; expected {expected_terminal_sha256}"
            )

        with zipfile.ZipFile(terminal_tmp, "r") as terminal:
            try:
                info = terminal.getinfo(AUTHORITY_MEMBER)
            except KeyError as exc:
                raise ValueError(f"Authority document not present: {AUTHORITY_MEMBER}") from exc
            if info.is_dir():
                raise ValueError("Authority member unexpectedly resolves to a directory")
            if info.file_size > max_document_bytes:
                raise ValueError(
                    f"Authority document exceeds size guardrail: {info.file_size} > {max_document_bytes}"
                )
            if info.file_size != AUTHORITY_DECLARED_SIZE:
                raise ValueError(
                    f"Authority document size drift: {info.file_size}; expected {AUTHORITY_DECLARED_SIZE}"
                )
            crc = f"{info.CRC:08x}"
            if crc != AUTHORITY_CRC32:
                raise ValueError(
                    f"Authority document CRC32 drift: {crc}; expected {AUTHORITY_CRC32}"
                )

            document_path = out / Path(AUTHORITY_MEMBER).name
            digest = hashlib.sha256()
            copied = 0
            with terminal.open(info, "r") as src, document_path.open("wb") as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)
                    digest.update(chunk)
                    copied += len(chunk)
            if copied != info.file_size:
                raise ValueError(
                    f"Authority document size mismatch: copied {copied}, expected {info.file_size}"
                )

        with document_path.open("rb") as fh:
            if fh.read(5) != b"%PDF-":
                raise ValueError("Extracted authority member does not have a PDF header")

        manifest = {
            "status": "EXACT_REGIS_AUTHORITY_DOCUMENT_EXTRACTED",
            "source": {
                "path_name": outer_path.name,
                "size_bytes": outer_path.stat().st_size,
                "sha256": outer_sha,
            },
            "archive_chain": [
                {
                    "member": MODEL_MEMBER,
                    "size_bytes": model_size,
                    "sha256": model_sha,
                    "crc32_hex": model_crc,
                },
                {
                    "member": TERMINAL_MEMBER,
                    "size_bytes": terminal_size,
                    "sha256": terminal_sha,
                    "crc32_hex": terminal_crc,
                },
            ],
            "authority_document": {
                "member": AUTHORITY_MEMBER,
                "output_name": document_path.name,
                "size_bytes": document_path.stat().st_size,
                "crc32_hex": AUTHORITY_CRC32,
                "sha256": digest.hexdigest(),
            },
            "guardrails": {
                "extracted_nonzip_member_count": 1,
                "extracted_nonzip_members": [AUTHORITY_MEMBER],
                "raster_members_opened": 0,
                "hydrogeological_interpretation_performed": False,
                "admission_decision_performed": False,
                "large_nested_archives_retained": False,
            },
        }
        (out / "regis_authority_document_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )
        return manifest
    except Exception:
        if document_path is not None and document_path.exists():
            document_path.unlink()
        raise
    finally:
        for tmp in (terminal_tmp, model_tmp):
            if tmp is not None and tmp.exists():
                tmp.unlink()
