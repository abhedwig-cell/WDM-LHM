from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class InventoryEntry:
    name: str
    is_dir: bool
    extension: str
    compressed_size: int
    uncompressed_size: int
    compression_type: int
    crc32_hex: str


def _sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _member_extension(name: str) -> str:
    suffix = Path(name.rstrip("/")).suffix.lower()
    return suffix if suffix else "<none>"


def _select_model_member(zf: zipfile.ZipFile, requested_member: str | None) -> zipfile.ZipInfo:
    infos = [info for info in zf.infolist() if not info.is_dir()]
    if requested_member:
        try:
            info = zf.getinfo(requested_member)
        except KeyError as exc:
            raise ValueError(f"Requested model member not present: {requested_member}") from exc
        if info.is_dir():
            raise ValueError(f"Requested model member is a directory: {requested_member}")
        return info

    candidates = [info for info in infos if Path(info.filename).name.lower().startswith("model_") and info.filename.lower().endswith(".zip")]
    if len(candidates) != 1:
        names = [info.filename for info in candidates]
        raise ValueError(f"Expected exactly one Model_*.zip member, found {len(candidates)}: {names}")
    return candidates[0]


def build_regis_model_inventory(
    outer_zip: str | os.PathLike[str],
    output_dir: str | os.PathLike[str],
    *,
    model_member: str | None = None,
    retain_inner_zip: bool = False,
    copy_chunk_size: int = 16 * 1024 * 1024,
) -> dict:
    """Inventory the nested REGIS model ZIP without extracting model files.

    The outer delivery ZIP is assumed to be available locally. The selected nested
    model ZIP is streamed to a temporary local file because Python's ``zipfile``
    needs random access to the nested ZIP central directory. Only that nested ZIP
    file is materialised; its members are never extracted.

    The default is fail-closed cleanup: the temporary nested ZIP is removed after
    the inventory is written. ``retain_inner_zip`` exists for controlled debugging
    only and should stay false in qualification workflows.
    """
    outer_path = Path(outer_zip)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if not outer_path.is_file():
        raise FileNotFoundError(outer_path)
    if not zipfile.is_zipfile(outer_path):
        raise ValueError(f"Outer REGIS delivery is not a ZIP file: {outer_path}")

    outer_size = outer_path.stat().st_size
    outer_sha256 = _sha256_file(outer_path)

    tmp_path: Path | None = None
    selected: zipfile.ZipInfo | None = None
    inner_sha256 = hashlib.sha256()
    copied = 0
    try:
        with zipfile.ZipFile(outer_path, "r") as outer:
            selected = _select_model_member(outer, model_member)
            fd, tmp_name = tempfile.mkstemp(prefix="wdm_lhm_regis_model_", suffix=".zip")
            os.close(fd)
            tmp_path = Path(tmp_name)
            with outer.open(selected, "r") as src, tmp_path.open("wb") as dst:
                while True:
                    chunk = src.read(copy_chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    inner_sha256.update(chunk)
                    copied += len(chunk)

        if selected is None or tmp_path is None:
            raise RuntimeError("Internal error: model member extraction did not initialise")
        if copied != selected.file_size:
            raise ValueError(
                f"Nested model ZIP size mismatch: copied {copied} bytes, expected {selected.file_size}"
            )
        if not zipfile.is_zipfile(tmp_path):
            raise ValueError("Extracted Model_*.zip member is not a valid ZIP archive")

        entries: list[InventoryEntry] = []
        with zipfile.ZipFile(tmp_path, "r") as inner:
            bad = inner.testzip()
            if bad is not None:
                raise ValueError(f"Nested REGIS ZIP CRC validation failed at member: {bad}")
            for info in inner.infolist():
                entries.append(
                    InventoryEntry(
                        name=info.filename,
                        is_dir=info.is_dir(),
                        extension=_member_extension(info.filename),
                        compressed_size=int(info.compress_size),
                        uncompressed_size=int(info.file_size),
                        compression_type=int(info.compress_type),
                        crc32_hex=f"{info.CRC:08x}",
                    )
                )

        csv_path = out / "regis_inner_inventory.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(asdict(entries[0]).keys()) if entries else [
                "name", "is_dir", "extension", "compressed_size", "uncompressed_size", "compression_type", "crc32_hex"
            ])
            writer.writeheader()
            for entry in entries:
                writer.writerow(asdict(entry))

        extension_counts = Counter(e.extension for e in entries if not e.is_dir)
        top_level_counts = Counter(
            (e.name.split("/", 1)[0] if "/" in e.name else "<root>") for e in entries
        )
        manifest = {
            "status": "INVENTORY_ONLY_NO_MODEL_MEMBERS_EXTRACTED",
            "outer_zip": {
                "path_name": outer_path.name,
                "size_bytes": outer_size,
                "sha256": outer_sha256,
            },
            "nested_model_zip": {
                "member": selected.filename,
                "outer_member_compressed_size": int(selected.compress_size),
                "outer_member_uncompressed_size": int(selected.file_size),
                "outer_member_crc32_hex": f"{selected.CRC:08x}",
                "sha256": inner_sha256.hexdigest(),
            },
            "inventory": {
                "entry_count": len(entries),
                "file_count": sum(not e.is_dir for e in entries),
                "directory_count": sum(e.is_dir for e in entries),
                "sum_member_compressed_bytes": sum(e.compressed_size for e in entries if not e.is_dir),
                "sum_member_uncompressed_bytes": sum(e.uncompressed_size for e in entries if not e.is_dir),
                "extensions": dict(sorted(extension_counts.items())),
                "top_level": dict(sorted(top_level_counts.items())),
                "csv": csv_path.name,
            },
            "guardrails": {
                "inner_members_extracted": 0,
                "retain_inner_zip": bool(retain_inner_zip),
                "interpretation_performed": False,
                "admission_decision_performed": False,
            },
        }
        (out / "regis_full_inventory_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

        if retain_inner_zip:
            retained = out / Path(selected.filename).name
            shutil.move(str(tmp_path), retained)
            tmp_path = None
            manifest["nested_model_zip"]["retained_path"] = retained.name
            (out / "regis_full_inventory_manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
            )
        return manifest
    finally:
        if tmp_path is not None and tmp_path.exists():
            tmp_path.unlink()
