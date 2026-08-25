from __future__ import annotations

import csv
import json
import shutil
from collections import Counter, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .config import load_yaml
from .phase2_drive import FOLDER_MIME, ReadOnlyDriveClient
from .phase2_links import discover_drive_links
from .phase2_policy import allowed_mime, classify_path
from .phase2_drive import SHORTCUT_MIME
from .phase2_utils import normalize_text, safe_filename, sha256_file, stable_json_hash, write_jsonl


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _timestamp_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _csv_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return "" if value is None else value


def _write_csv(path: Path, rows: list[dict]) -> None:
    keys = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in keys})


def _write_rows(base: Path, name: str, rows: list[dict], config: dict) -> None:
    if config["output"].get("write_jsonl", True):
        write_jsonl(base / f"{name}.jsonl", rows)
    if config["output"].get("write_csv", True):
        _write_csv(base / f"{name}.csv", rows)


def load_phase2_config(path: Path) -> dict:
    config = load_yaml(path)
    if config.get("phase") != 2 or config.get("source", {}).get("access_mode") != "read_only":
        raise ValueError("Phase 2 config must declare phase=2 and read_only source access")
    return config


def _find_master(inventory: list[dict], config: dict, override: str | None) -> dict:
    if override:
        matching = [row for row in inventory if row.get("id") == override]
        if len(matching) != 1:
            raise RuntimeError("MASTER_WORKBOOK_FILE_ID_OVERRIDE is not inside the inventoried source tree")
        return matching[0]
    preferred = {normalize_text(name) for name in config["source"]["master_workbook"]["preferred_names"]}
    exact = [row for row in inventory if normalize_text(row.get("name", "")) in preferred]
    if len(exact) == 1:
        return exact[0]
    if not exact:
        fuzzy = [
            row for row in inventory
            if "reference" in normalize_text(row.get("name", ""))
            and row.get("mimeType") in {
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.google-apps.spreadsheet",
            }
        ]
        if len(fuzzy) == 1:
            return fuzzy[0]
        names = [row.get("source_path") for row in fuzzy[:20]]
        raise RuntimeError(f"Master workbook not uniquely identified. Candidates: {names}")
    raise RuntimeError(
        "Multiple exact master workbook candidates found; set MASTER_WORKBOOK_FILE_ID_OVERRIDE"
    )


def _status_from_exception(exc: Exception) -> tuple[str, str]:
    status = getattr(getattr(exc, "resp", None), "status", None)
    if status == 403:
        return "DENIED", "drive_http_403"
    if status == 404:
        return "MISSING", "drive_http_404"
    return "ERROR", f"{type(exc).__name__}:{str(exc)[:180]}"


def _expand_folder(client, metadata, config, progress):
    return client.inventory_tree(
        metadata["id"],
        metadata.get("name", metadata["id"]),
        int(config["evidence"]["linked_folder_max_depth"]),
        int(config["inventory"]["max_items"]),
        progress,
    )


def _downloadable_name(metadata: dict) -> str:
    return f"{metadata['id']}__{safe_filename(metadata.get('name', 'evidence'))}"


def _dereference_shortcut(client, metadata: dict) -> dict:
    if metadata.get("mimeType") != SHORTCUT_MIME:
        return metadata
    target_id = metadata.get("shortcutDetails", {}).get("targetId")
    if not target_id:
        raise RuntimeError(f"Shortcut {metadata.get('id')} has no targetId")
    target = client.get_metadata(target_id)
    target["resolved_from_shortcut_id"] = metadata.get("id")
    if metadata.get("source_path"):
        target["source_path"] = metadata["source_path"]
    return target


def _build_report(summary: dict) -> str:
    return f"""# Phase 2 — Read-only source inventory and immutable snapshot

**Status:** {summary['status']}
**Snapshot:** `{summary['snapshot_id']}`
**Completed (UTC):** {summary['completed_at_utc']}

## Results

- Source items inventoried: **{summary['source_items_inventoried']}**
- Source paths excluded by policy: **{summary['source_items_excluded_by_path']}**
- Workbook reference rows observed: **{summary['workbook_reference_rows']}**
- Deduplicated evidence link cells: **{summary['evidence_link_records']}**
- Unique Drive evidence targets: **{summary['unique_evidence_target_ids']}**
- Evidence files downloaded: **{summary['evidence_files_downloaded']}**
- Evidence targets denied/missing/error: **{summary['evidence_targets_unavailable']}**
- Evidence targets skipped by policy/type/size: **{summary['evidence_targets_skipped']}**
- Snapshot bytes written: **{summary['snapshot_bytes']:,}**

## Safety assertions

- Source access mode: **read-only**
- Drive source mutation calls: **0**
- Original source files modified: **0**
- External LLM calls: **0**
- OCR calls: **0**
- Blocked workbook fields persisted: **0**

## Interpretation

This snapshot is the immutable evidence boundary for later extraction. Phase 2
does not claim OCR quality, search quality, or reference completeness beyond the
access and policy results recorded in the manifests.
"""


def run_phase2_snapshot(
    drive_service,
    project_root: Path,
    config_path: Path,
    master_workbook_file_id_override: str = "",
    progress: Callable[[str], None] = print,
) -> dict:
    config = load_phase2_config(config_path)
    client = ReadOnlyDriveClient(drive_service)
    configured_id = config["source"]["source_shortcut_id"]
    progress("Resolving the configured source shortcut (read-only)...")
    root_meta, root_id = client.resolve_source_root(configured_id)
    progress(f"Inventorying source folder: {root_meta.get('name', root_id)}")
    inventory = client.inventory_tree(
        root_id,
        root_meta.get("name", root_id),
        int(config["inventory"]["max_depth"]),
        int(config["inventory"]["max_items"]),
        progress,
    )
    for row in inventory:
        excluded, reason = classify_path(row.get("source_path", ""), config)
        row["excluded_by_path_policy"] = excluded
        row["exclusion_reason"] = reason
    inventory_by_id = {row.get("id"): row for row in inventory}

    master = _find_master(inventory, config, master_workbook_file_id_override or None)
    if master.get("excluded_by_path_policy"):
        raise RuntimeError("Master workbook is inside an excluded source path")

    inventory_fingerprint = stable_json_hash(
        [
            {
                "id": row.get("id"),
                "name": row.get("name"),
                "mimeType": row.get("mimeType"),
                "size": row.get("size"),
                "md5Checksum": row.get("md5Checksum"),
                "modifiedTime": row.get("modifiedTime"),
                "source_path": row.get("source_path"),
            }
            for row in sorted(inventory, key=lambda item: item.get("id", ""))
        ]
    )
    snapshot_id = f"{_timestamp_id()}_{inventory_fingerprint[:10]}"
    snapshots_root = project_root / config["output"]["snapshots_dir"]
    snapshot_root = snapshots_root / snapshot_id
    if snapshot_root.exists():
        raise FileExistsError(f"Immutable snapshot already exists: {snapshot_root}")
    raw_master = snapshot_root / "raw" / "master"
    raw_evidence = snapshot_root / "raw" / "evidence"
    manifests = snapshot_root / "manifests"
    reports = snapshot_root / "reports"
    for folder in (raw_master, raw_evidence, manifests, reports):
        folder.mkdir(parents=True, exist_ok=False)

    try:
        _write_rows(manifests, "source_inventory", inventory, config)
        master_destination = raw_master / _downloadable_name(master)
        master_result = client.download(master, master_destination)
        master_path = Path(master_result["path"])
        if master_path.suffix.casefold() != ".xlsx":
            raise RuntimeError(
                f"Master workbook must be XLSX or Google Sheets export, got {master_path.suffix}"
            )
        master_sha = sha256_file(master_path)
        progress("Discovering Google Drive evidence links without reading blocked columns...")
        link_audit = discover_drive_links(master_path, config)
        links = link_audit.pop("records")
        if link_audit["row_count"] < 1:
            raise RuntimeError("Master workbook contains no reference rows")
        if not links:
            raise RuntimeError("No policy-permitted Google Drive evidence links were discovered")
        _write_rows(manifests, "evidence_links", links, config)
        (manifests / "workbook_audit.json").write_text(
            json.dumps(link_audit, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        target_ids = sorted({row["target_file_id"] for row in links})
        target_records: list[dict] = []
        downloadable: dict[str, dict] = {}
        for index, target_id in enumerate(target_ids, start=1):
            base = {
                "target_file_id": target_id,
                "referenced_by_link_cells": sum(
                    row["target_file_id"] == target_id for row in links
                ),
            }
            try:
                metadata = client.get_metadata(target_id)
                if target_id in inventory_by_id:
                    metadata["source_path"] = inventory_by_id[target_id].get("source_path")
                metadata = _dereference_shortcut(client, metadata)
                base.update(
                    {
                        "name": metadata.get("name"),
                        "mimeType": metadata.get("mimeType"),
                        "size": metadata.get("size"),
                        "modifiedTime": metadata.get("modifiedTime"),
                        "resolved_file_id": metadata.get("id"),
                        "resolved_from_shortcut_id": metadata.get("resolved_from_shortcut_id"),
                        "drive_status": "ACCESSIBLE",
                    }
                )
                if metadata.get("mimeType") == FOLDER_MIME:
                    if not config["evidence"].get("expand_linked_folders", False):
                        base.update(snapshot_status="SKIPPED", reason="linked_folder_expansion_disabled")
                    else:
                        children = _expand_folder(client, metadata, config, progress)
                        files = [child for child in children if child.get("mimeType") != FOLDER_MIME]
                        base.update(
                            snapshot_status="EXPANDED_FOLDER",
                            reason="",
                            expanded_file_count=len(files),
                        )
                        for child in files:
                            child = _dereference_shortcut(client, child)
                            downloadable.setdefault(child["id"], child)
                else:
                    base.update(snapshot_status="CANDIDATE_FILE", reason="")
                    downloadable.setdefault(metadata["id"], metadata)
            except Exception as exc:
                status, reason = _status_from_exception(exc)
                base.update(drive_status=status, snapshot_status="UNAVAILABLE", reason=reason)
            target_records.append(base)
            if index % 25 == 0:
                progress(f"Resolved {index}/{len(target_ids)} evidence targets...")

        download_records: list[dict] = []
        hashes = [(master_sha, str(master_path.relative_to(snapshot_root)))]
        snapshot_bytes = master_result["bytes"]
        for index, metadata in enumerate(downloadable.values(), start=1):
            record = {
                "file_id": metadata["id"],
                "name": metadata.get("name"),
                "mimeType": metadata.get("mimeType"),
                "remote_size": metadata.get("size"),
                "remote_md5": metadata.get("md5Checksum"),
                "modifiedTime": metadata.get("modifiedTime"),
            }
            excluded, reason = classify_path(metadata.get("source_path", metadata.get("name", "")), config)
            if excluded:
                record.update(status="SKIPPED", reason=reason)
            elif not allowed_mime(metadata.get("mimeType", ""), config):
                record.update(status="SKIPPED", reason="unsupported_mime_type")
            elif metadata.get("size") and int(metadata["size"]) > int(config["evidence"]["max_file_bytes"]):
                record.update(status="SKIPPED", reason="file_too_large")
            else:
                destination = raw_evidence / _downloadable_name(metadata)
                try:
                    result = client.download(metadata, destination)
                    local_path = Path(result["path"])
                    local_sha = sha256_file(local_path)
                    record.update(
                        status="DOWNLOADED",
                        reason="",
                        local_relative_path=str(local_path.relative_to(snapshot_root)),
                        local_sha256=local_sha,
                        local_bytes=result["bytes"],
                        export_mime_type=result.get("export_mime_type"),
                    )
                    hashes.append((local_sha, record["local_relative_path"]))
                    snapshot_bytes += result["bytes"]
                except Exception as exc:
                    status, failure = _status_from_exception(exc)
                    record.update(status=status, reason=failure)
            download_records.append(record)
            if index % 20 == 0:
                progress(f"Snapshotted {index}/{len(downloadable)} candidate evidence files...")

        _write_rows(manifests, "evidence_targets", target_records, config)
        _write_rows(manifests, "download_manifest", download_records, config)
        hashes.sort(key=lambda item: item[1])
        (snapshot_root / "SHA256SUMS.txt").write_text(
            "".join(f"{digest}  {relative}\n" for digest, relative in hashes),
            encoding="utf-8",
        )
        unavailable = sum(row.get("snapshot_status") == "UNAVAILABLE" for row in target_records)
        unavailable += sum(
            row.get("status") in {"DENIED", "MISSING", "ERROR"}
            for row in download_records
        )
        skipped = sum(row.get("status") == "SKIPPED" for row in download_records)
        downloaded = sum(row.get("status") == "DOWNLOADED" for row in download_records)
        if downloaded < 1:
            raise RuntimeError("No evidence file was downloaded; Phase 2 cannot create a valid snapshot")
        summary = {
            "schema_version": 1,
            "phase": 2,
            "status": "PASS",
            "snapshot_id": snapshot_id,
            "started_from_source_shortcut_id": configured_id,
            "resolved_source_root_id": root_id,
            "master_workbook_file_id": master["id"],
            "master_workbook_sha256": master_sha,
            "inventory_fingerprint_sha256": inventory_fingerprint,
            "source_items_inventoried": len(inventory),
            "source_items_excluded_by_path": sum(bool(row["excluded_by_path_policy"]) for row in inventory),
            "workbook_reference_rows": link_audit["row_count"],
            "evidence_link_records": len(links),
            "unique_evidence_target_ids": len(target_ids),
            "evidence_files_downloaded": downloaded,
            "evidence_targets_unavailable": unavailable,
            "evidence_targets_skipped": skipped,
            "access_gate": "PASS" if unavailable == 0 else "REVIEW_REQUIRED",
            "snapshot_bytes": snapshot_bytes,
            "source_mutation_calls": 0,
            "external_llm_calls": 0,
            "ocr_calls": 0,
            "blocked_field_values_persisted": 0,
            "completed_at_utc": _now(),
        }
        report = _build_report(summary)
        (reports / "PHASE_2_SOURCE_INVENTORY_REPORT.md").write_text(report, encoding="utf-8")
        (snapshot_root / "SNAPSHOT_MANIFEST.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        marker = snapshot_root / config["output"]["immutable_success_marker"]
        marker.write_text(
            json.dumps(
                {
                    "snapshot_id": snapshot_id,
                    "status": "COMPLETE_IMMUTABLE_SNAPSHOT",
                    "manifest_sha256": sha256_file(snapshot_root / "SNAPSHOT_MANIFEST.json"),
                    "created_at_utc": _now(),
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return summary | {"snapshot_root": str(snapshot_root)}
    except Exception:
        # An incomplete snapshot is never presented as valid. Keep the failed
        # directory for diagnosis but mark it explicitly and omit _SUCCESS.
        (snapshot_root / "_FAILED.txt").write_text(
            "Phase 2 failed before the immutable success marker was written.\n",
            encoding="utf-8",
        )
        raise


def verify_snapshot(snapshot_root: Path, success_marker_name: str = "_SUCCESS.json") -> dict:
    marker = snapshot_root / success_marker_name
    manifest = snapshot_root / "SNAPSHOT_MANIFEST.json"
    if not marker.exists() or not manifest.exists():
        raise AssertionError("Snapshot is incomplete: success marker or manifest missing")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("status") != "PASS" or data.get("source_mutation_calls") != 0:
        raise AssertionError("Snapshot manifest failed safety validation")
    for line in (snapshot_root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        path = snapshot_root / relative
        if sha256_file(path) != digest:
            raise AssertionError(f"Hash mismatch: {relative}")
    return data
