from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from .phase2_pipeline import verify_snapshot
from .phase2_utils import sha256_file, write_jsonl
from .phase3_extraction import process_document


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_phase3_config(path: Path) -> dict:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    if config.get("phase") != 3:
        raise ValueError("Expected Phase 3 configuration")
    if config.get("security", {}).get("external_llm_enabled"):
        raise ValueError("External LLM must remain disabled during extraction")
    return config


def _atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temporary, path)


def _atomic_jsonl(path: Path, rows: list[dict]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    write_jsonl(temporary, rows)
    os.replace(temporary, path)


def _checkpoint_valid(path: Path, source_sha256: str, pipeline_version: str) -> bool:
    if not path.exists():
        return False
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return (
        value.get("source_sha256") == source_sha256
        and value.get("pipeline_version") == pipeline_version
        and value.get("status") == "COMPLETE"
    )


def _jsonable_records(frame: pd.DataFrame) -> list[dict]:
    return json.loads(frame.to_json(orient="records", force_ascii=False))


def _build_missing_evidence(snapshot_root: Path) -> pd.DataFrame:
    targets = pd.read_csv(snapshot_root / "manifests" / "evidence_targets.csv", dtype=str, keep_default_na=False)
    links = pd.read_csv(snapshot_root / "manifests" / "evidence_links.csv", dtype=str, keep_default_na=False)
    missing = targets.loc[targets["snapshot_status"].eq("UNAVAILABLE")].copy()
    columns = ["target_file_id", "row_number", "cell_coordinate", "source_header", "channels"]
    joined = missing.merge(links[columns], on="target_file_id", how="left")
    return joined.sort_values(["row_number", "cell_coordinate", "target_file_id"], kind="stable")


def _build_report(summary: dict) -> str:
    return f"""# Phase 3 — Multilingual document extraction

**Status:** {summary['status']}
**QA gate:** {summary['qa_gate']}
**Input snapshot:** `{summary['snapshot_id']}`
**Completed (UTC):** {summary['completed_at_utc']}

## Results

- Evidence documents expected: **{summary['documents_expected']}**
- Evidence documents completed: **{summary['documents_completed']}**
- Document processing failures: **{summary['document_failures']}**
- Pages extracted: **{summary['pages_total']}**
- Digital-text pages: **{summary['digital_pages']}**
- OCR pages: **{summary['ocr_pages']}**
- Blank pages: **{summary['blank_pages']}**
- Pages requiring review: **{summary['review_pages']}**
- Failed pages: **{summary['failed_pages']}**
- Missing evidence targets preserved: **{summary['missing_evidence_targets']}**

## Safety

- Source snapshot mutations: **0**
- External LLM calls: **0**
- Raw text classification: **INTERNAL**
- Deterministically redacted text created for downstream use: **yes**

## Interpretation

`REVIEW_REQUIRED` does not invalidate the extraction run. It identifies pages
that need targeted inspection before they are allowed to support generated
claims. No blanket manual transcription checkpoint is required.
"""


def _hash_outputs(run_root: Path, paths: list[Path]) -> Path:
    lines = []
    for path in sorted(paths, key=lambda item: str(item.relative_to(run_root))):
        lines.append(f"{sha256_file(path)}  {path.relative_to(run_root)}\n")
    sums = run_root / "SHA256SUMS.txt"
    sums.write_text("".join(lines), encoding="utf-8")
    return sums


def run_phase3(project_root: Path, config_path: Path, progress=print) -> dict:
    config = load_phase3_config(config_path)
    snapshot_id = config["input"]["snapshot_id"]
    snapshot_root = project_root / "data" / "snapshots" / snapshot_id
    verified_snapshot = verify_snapshot(snapshot_root)
    if verified_snapshot["snapshot_id"] != snapshot_id:
        raise AssertionError("Pinned snapshot ID mismatch")
    actual_manifest_hash = sha256_file(snapshot_root / "SNAPSHOT_MANIFEST.json")
    if actual_manifest_hash != config["input"]["expected_manifest_sha256"]:
        raise AssertionError("Pinned Phase 2 manifest hash mismatch")

    run_root = project_root / config["output"]["root"] / snapshot_id / config["output"]["run_name"]
    success_path = run_root / config["output"]["success_marker"]
    if success_path.exists():
        result = verify_phase3(run_root)
        progress("Existing completed Phase 3 run verified; no documents were reprocessed.")
        return result | {"run_root": str(run_root), "resumed": True}

    document_parts = run_root / "checkpoints" / "documents"
    page_parts = run_root / "checkpoints" / "pages"
    reports = run_root / "reports"
    for folder in (document_parts, page_parts, reports):
        folder.mkdir(parents=True, exist_ok=True)

    downloads = pd.read_csv(
        snapshot_root / "manifests" / "download_manifest.csv",
        dtype=str,
        keep_default_na=False,
    )
    downloads = downloads.loc[downloads["status"].eq("DOWNLOADED")].copy()
    expected = int(config["input"]["expected_downloaded_documents"])
    if len(downloads) != expected:
        raise AssertionError(f"Expected {expected} downloaded documents, found {len(downloads)}")

    for index, document in enumerate(_jsonable_records(downloads), start=1):
        document_id = document["file_id"]
        summary_path = document_parts / f"{document_id}.json"
        pages_path = page_parts / f"{document_id}.jsonl"
        if _checkpoint_valid(summary_path, document["local_sha256"], config["pipeline_version"]) and pages_path.exists():
            progress(f"[{index}/{expected}] Resume: {document['name']}")
            continue
        progress(f"[{index}/{expected}] Extracting: {document['name']}")
        source_path = snapshot_root / document["local_relative_path"]
        if sha256_file(source_path) != document["local_sha256"]:
            raise AssertionError(f"Source hash mismatch before extraction: {document_id}")
        summary, pages = process_document(source_path, document, config)
        _atomic_jsonl(pages_path, pages)
        _atomic_json(summary_path, summary)

    document_rows = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(document_parts.glob("*.json"))
    ]
    page_rows: list[dict] = []
    for path in sorted(page_parts.glob("*.jsonl")):
        page_rows.extend(
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    documents = pd.DataFrame(document_rows)
    pages = pd.DataFrame(page_rows)
    if len(documents) != expected:
        raise AssertionError("Document checkpoint count does not match pinned input")

    if not documents.empty:
        for column in ("method_counts", "qa_counts"):
            documents[column] = documents[column].apply(
                lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True)
            )
    if not pages.empty:
        pages["qa_reasons"] = pages["qa_reasons"].apply(
            lambda value: json.dumps(value, ensure_ascii=False)
        )
        pages["redaction_counts"] = pages["redaction_counts"].apply(
            lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True)
        )

    documents_parquet = run_root / "documents.parquet"
    pages_parquet = run_root / "pages.parquet"
    documents.to_parquet(documents_parquet, index=False)
    pages.to_parquet(pages_parquet, index=False)
    documents_csv = run_root / "documents.csv"
    documents.to_csv(documents_csv, index=False, encoding="utf-8-sig")

    safe_review_columns = [
        "document_id", "source_file_name", "page_number_1_based", "extraction_method",
        "ocr_confidence", "character_count", "word_count", "line_count", "qa_status", "qa_reasons",
        "source_sha256", "source_relative_path",
    ]
    review_csv = run_root / "qa_review_queue.csv"
    if pages.empty:
        pd.DataFrame(columns=safe_review_columns).to_csv(review_csv, index=False, encoding="utf-8-sig")
    else:
        review_queue = pages.loc[pages["qa_status"].isin(["REVIEW", "FAILED"])].copy()
        review_queue[safe_review_columns].to_csv(review_csv, index=False, encoding="utf-8-sig")

    missing = _build_missing_evidence(snapshot_root)
    missing_csv = run_root / "missing_evidence.csv"
    missing.to_csv(missing_csv, index=False, encoding="utf-8-sig")

    failures = documents.loc[documents["status"].eq("FAILED")]
    errors_jsonl = run_root / "processing_errors.jsonl"
    write_jsonl(errors_jsonl, _jsonable_records(failures))
    qa_counts = Counter(pages["qa_status"].tolist()) if not pages.empty else Counter()
    method_counts = Counter(pages["extraction_method"].tolist()) if not pages.empty else Counter()
    document_failures = int(len(failures))
    review_pages = int(qa_counts.get("REVIEW", 0))
    failed_pages = int(qa_counts.get("FAILED", 0))
    summary = {
        "schema_version": 1,
        "phase": 3,
        "pipeline_version": config["pipeline_version"],
        "snapshot_id": snapshot_id,
        "snapshot_manifest_sha256": actual_manifest_hash,
        "status": "PASS" if document_failures == 0 else "PARTIAL",
        "qa_gate": "PASS" if review_pages == 0 and failed_pages == 0 else "REVIEW_REQUIRED",
        "documents_expected": expected,
        "documents_completed": int((documents["status"] == "COMPLETE").sum()),
        "document_failures": document_failures,
        "pages_total": int(len(pages)),
        "digital_pages": int(method_counts.get("digital_pdf", 0)),
        "ocr_pages": int(method_counts.get("tesseract_ocr", 0)),
        "native_fallback_pages": int(
            method_counts.get("docx_native_fallback", 0) + method_counts.get("pptx_native_fallback", 0)
        ),
        "blank_pages": int(qa_counts.get("BLANK", 0)),
        "review_pages": review_pages,
        "failed_pages": failed_pages,
        "missing_evidence_targets": int(missing["target_file_id"].nunique()),
        "source_snapshot_mutation_calls": 0,
        "external_llm_calls": 0,
        "completed_at_utc": _now(),
    }
    manifest_path = run_root / "PHASE_3_MANIFEST.json"
    _atomic_json(manifest_path, summary)
    report_path = reports / "PHASE_3_EXTRACTION_REPORT.md"
    report_path.write_text(_build_report(summary), encoding="utf-8")
    sums_path = _hash_outputs(
        run_root,
        [documents_parquet, pages_parquet, documents_csv, review_csv, missing_csv, errors_jsonl, manifest_path, report_path],
    )
    success = {
        "status": "COMPLETE_REPRODUCIBLE_EXTRACTION",
        "snapshot_id": snapshot_id,
        "pipeline_version": config["pipeline_version"],
        "manifest_sha256": sha256_file(manifest_path),
        "sha256sums_sha256": sha256_file(sums_path),
        "created_at_utc": _now(),
    }
    if summary["status"] == "PASS":
        partial_path = run_root / "_PARTIAL.json"
        if partial_path.exists():
            partial_path.unlink()
        _atomic_json(success_path, success)
    else:
        _atomic_json(run_root / "_PARTIAL.json", success | {"status": "PARTIAL_RETRY_REQUIRED"})
    return summary | {"run_root": str(run_root), "resumed": False}


def verify_phase3(run_root: Path) -> dict:
    success_path = run_root / "_SUCCESS.json"
    manifest_path = run_root / "PHASE_3_MANIFEST.json"
    sums_path = run_root / "SHA256SUMS.txt"
    if not all(path.exists() for path in (success_path, manifest_path, sums_path)):
        raise AssertionError("Incomplete Phase 3 output")
    success = json.loads(success_path.read_text(encoding="utf-8"))
    if sha256_file(manifest_path) != success["manifest_sha256"]:
        raise AssertionError("Phase 3 manifest hash mismatch")
    if sha256_file(sums_path) != success["sha256sums_sha256"]:
        raise AssertionError("Phase 3 checksum-list hash mismatch")
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        if sha256_file(run_root / relative) != expected:
            raise AssertionError(f"Phase 3 output hash mismatch: {relative}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("source_snapshot_mutation_calls") != 0 or manifest.get("external_llm_calls") != 0:
        raise AssertionError("Phase 3 safety assertion failed")
    return manifest
