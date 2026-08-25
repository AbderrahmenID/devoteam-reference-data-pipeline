from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable


DRIVE_ID_RE = re.compile(
    r"(?:/d/|/folders/|[?&]id=)([A-Za-z0-9_-]{20,})"
)
RAW_ID_RE = re.compile(r"^[A-Za-z0-9_-]{20,}$")


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text.casefold())
    return " ".join(text.split())


def parse_drive_id(value: Any) -> str | None:
    text = str(value or "").strip()
    if RAW_ID_RE.fullmatch(text):
        return text
    match = DRIVE_ID_RE.search(text)
    return match.group(1) if match else None


def safe_filename(name: str, fallback: str = "file") -> str:
    name = Path(str(name or "")).name
    name = unicodedata.normalize("NFKC", name)
    name = re.sub(r"[\\/:*?\"<>|\x00-\x1f]+", "_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return (name or fallback)[:180]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json_hash(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
