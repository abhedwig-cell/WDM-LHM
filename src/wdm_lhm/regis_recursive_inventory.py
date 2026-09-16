from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
import zipfile
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class RecursiveInventoryEntry:
    archive_depth: int
    archive_chain: str
    archive_sha256: str
    member_name: str
    member_basename: str
    is_dir: bool
    is_zip_container: bool
    extension: str
    compressed_size: int
    uncompressed_size: int
    compression_type: int
    crc32_hex: str


@dataclass(frozen=True)
class ArchiveContainer:
    archive_depth: int
    archive_chain: str
    archive_name: str
    size_bytes: int
    sha256: str
    member_count: int
    zip_child_count: int
    nonzip_file_count: int


def _sha256_file(path: Path, chunk_size: int = 16 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _extension(name: str) -> str:
    suffix = Path(name.rstrip("/")).suffix.lower()
    return suffix if suffix else "<none>"


def _is_zip_member(info: zipfile.ZipInfo) -> bool:
    return (not info.is_dir()) and info.filename.lower().endswith(".zip")


def _copy_zip_member(
    parent: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    destination: Path,
    *,
    chunk_size: int = 16 * 1024 * 1024,
) -> tuple[int, str]:
    """Materialise one ZIP-valued member and return (bytes, sha256).

    Reading to EOF lets ``zipfile`` validate the member CRC. No non-ZIP member
    is ever passed to this function.
    """
    digest = hashlib.sha256()
    copied = 0
    try:
        with parent.open(info, "r") as src, destination.open("wb") as dst:
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                dst.write(chunk)
                digest.update(chunk)
                copied += len(chunk)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"CRC/decompression failure while reading ZIP member {info.filename}") from exc

    if copied != int(info.file_size):
        raise ValueError(
            f"ZIP member size mismatch for {info.filename}: copied {copied}, expected {info.file_size}"
        )
    if not zipfile.is_zipfile(destination):
        raise ValueError(f"Member named *.zip is not a valid ZIP archive: {info.filename}")
    return copied, digest.hexdigest()


def build_recursive_regis_inventory(
    outer_zip: str | os.PathLike[str],
    output_dir: str | os.PathLike[str],
    *,
    max_depth: int = 6,
    max_containers: int = 32,
    max_total_materialized_zip_bytes: int = 8 * 1024**3,
) -> dict:
    """Recursively inventory nested ZIP containers without extracting model files.

    ``outer_zip`` itself is treated as archive depth 0. A member is materialised
    only when its filename ends in ``.zip``. Non-ZIP members are represented only
    by central-directory metadata and are never opened or extracted.

    The function fails closed when recursion depth, number of containers, or total
    materialised nested-ZIP bytes exceed the configured limits. Temporary nested
    ZIPs are removed automatically when the function exits.
    """
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")
    if max_containers < 1:
        raise ValueError("max_containers must be >= 1")
    if max_total_materialized_zip_bytes < 1:
        raise ValueError("max_total_materialized_zip_bytes must be >= 1")

    source = Path(outer_zip)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if not source.is_file():
        raise FileNotFoundError(source)
    if not zipfile.is_zipfile(source):
        raise ValueError(f"REGIS source is not a ZIP file: {source}")

    outer_sha256 = _sha256_file(source)
    entries: list[RecursiveInventoryEntry] = []
    containers: list[ArchiveContainer] = []
    terminal_archives: list[str] = []
    depth_limited_zip_members: list[str] = []
    materialized_zip_bytes = 0
    zip_members_materialized = 0

    with tempfile.TemporaryDirectory(prefix="wdm_lhm_regis_recursive_") as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)

        def walk(archive_path: Path, chain: str, depth: int, archive_sha256: str) -> None:
            nonlocal materialized_zip_bytes, zip_members_materialized
            if len(containers) >= max_containers:
                raise ValueError(f"Archive container limit exceeded ({max_containers})")

            with zipfile.ZipFile(archive_path, "r") as zf:
                infos = zf.infolist()
                zip_children = [i for i in infos if _is_zip_member(i)]
                nonzip_files = [i for i in infos if (not i.is_dir()) and not _is_zip_member(i)]

                containers.append(
                    ArchiveContainer(
                        archive_depth=depth,
                        archive_chain=chain,
                        archive_name=Path(chain.split("!/")[-1]).name,
                        size_bytes=int(archive_path.stat().st_size),
                        sha256=archive_sha256,
                        member_count=len(infos),
                        zip_child_count=len(zip_children),
                        nonzip_file_count=len(nonzip_files),
                    )
                )

                for info in infos:
                    entries.append(
                        RecursiveInventoryEntry(
                            archive_depth=depth,
                            archive_chain=chain,
                            archive_sha256=archive_sha256,
                            member_name=info.filename,
                            member_basename=Path(info.filename.rstrip("/")).name,
                            is_dir=info.is_dir(),
                            is_zip_container=_is_zip_member(info),
                            extension=_extension(info.filename),
                            compressed_size=int(info.compress_size),
                            uncompressed_size=int(info.file_size),
                            compression_type=int(info.compress_type),
                            crc32_hex=f"{info.CRC:08x}",
                        )
                    )

                if not zip_children:
                    terminal_archives.append(chain)
                    return

                if depth >= max_depth:
                    depth_limited_zip_members.extend(f"{chain}!/{i.filename}" for i in zip_children)
                    return

                for child_index, info in enumerate(zip_children):
                    projected = materialized_zip_bytes + int(info.file_size)
                    if projected > max_total_materialized_zip_bytes:
                        raise ValueError(
                            "Nested ZIP materialisation byte budget exceeded: "
                            f"would reach {projected} > {max_total_materialized_zip_bytes}"
                        )
                    child_path = tmp_dir / f"depth{depth + 1:02d}_{len(containers):03d}_{child_index:03d}.zip"
                    copied, child_sha = _copy_zip_member(zf, info, child_path)
                    materialized_zip_bytes += copied
                    zip_members_materialized += 1
                    child_chain = f"{chain}!/{info.filename}"
                    try:
                        walk(child_path, child_chain, depth + 1, child_sha)
                    finally:
                        child_path.unlink(missing_ok=True)

        walk(source, source.name, 0, outer_sha256)

        leaked = list(tmp_dir.iterdir())
        if leaked:
            raise RuntimeError(f"Temporary nested ZIP cleanup failed: {[p.name for p in leaked]}")

    entry_fields = list(asdict(entries[0]).keys()) if entries else [
        "archive_depth", "archive_chain", "archive_sha256", "member_name", "member_basename",
        "is_dir", "is_zip_container", "extension", "compressed_size", "uncompressed_size",
        "compression_type", "crc32_hex",
    ]
    entries_csv = out / "regis_recursive_inventory.csv"
    with entries_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=entry_fields)
        writer.writeheader()
        for row in entries:
            writer.writerow(asdict(row))

    container_fields = list(asdict(containers[0]).keys()) if containers else [
        "archive_depth", "archive_chain", "archive_name", "size_bytes", "sha256",
        "member_count", "zip_child_count", "nonzip_file_count",
    ]
    containers_csv = out / "regis_recursive_containers.csv"
    with containers_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=container_fields)
        writer.writeheader()
        for row in containers:
            writer.writerow(asdict(row))

    leaf_entries = [e for e in entries if not e.is_dir and not e.is_zip_container]
    extension_counts = Counter(e.extension for e in leaf_entries)
    depth_counts = Counter(str(e.archive_depth) for e in entries)
    terminal_depths = [c.archive_depth for c in containers if c.archive_chain in terminal_archives]

    manifest = {
        "status": "RECURSIVE_INVENTORY_ONLY_NO_NONZIP_MEMBERS_EXTRACTED",
        "source": {
            "path_name": source.name,
            "size_bytes": int(source.stat().st_size),
            "sha256": outer_sha256,
        },
        "limits": {
            "max_depth": int(max_depth),
            "max_containers": int(max_containers),
            "max_total_materialized_zip_bytes": int(max_total_materialized_zip_bytes),
        },
        "inventory": {
            "container_count": len(containers),
            "entry_count": len(entries),
            "leaf_nonzip_file_count": len(leaf_entries),
            "zip_members_materialized": zip_members_materialized,
            "materialized_zip_bytes": materialized_zip_bytes,
            "max_archive_depth_reached": max((c.archive_depth for c in containers), default=0),
            "terminal_archive_count": len(terminal_archives),
            "terminal_archive_depths": sorted(terminal_depths),
            "depth_limited_zip_member_count": len(depth_limited_zip_members),
            "depth_limited_zip_members": depth_limited_zip_members,
            "leaf_extensions": dict(sorted(extension_counts.items())),
            "entry_counts_by_archive_depth": dict(sorted(depth_counts.items(), key=lambda kv: int(kv[0]))),
            "entries_csv": entries_csv.name,
            "containers_csv": containers_csv.name,
        },
        "guardrails": {
            "nonzip_members_extracted": 0,
            "interpretation_performed": False,
            "admission_decision_performed": False,
            "large_nested_archives_retained": False,
        },
    }
    (out / "regis_recursive_inventory_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    return manifest
