from __future__ import annotations

import io
from collections import deque
from pathlib import Path
from typing import Callable


FOLDER_MIME = "application/vnd.google-apps.folder"
SHORTCUT_MIME = "application/vnd.google-apps.shortcut"
NATIVE_EXPORTS = {
    "application/vnd.google-apps.document": (
        "application/pdf", ".pdf"
    ),
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
    ),
    "application/vnd.google-apps.presentation": (
        "application/pdf", ".pdf"
    ),
}
FILE_FIELDS = (
    "id,name,mimeType,parents,size,md5Checksum,sha1Checksum,sha256Checksum,"
    "createdTime,modifiedTime,webViewLink,driveId,trashed,"
    "shortcutDetails(targetId,targetMimeType),capabilities(canDownload,canCopy)"
)


class ReadOnlyDriveClient:
    """A deliberately read-only facade over Drive API v3.

    Only files.get, files.list, files.get_media and files.export_media are
    exposed. No source mutation method exists in this class.
    """

    def __init__(self, service):
        self.service = service

    def get_metadata(self, file_id: str) -> dict:
        return (
            self.service.files()
            .get(fileId=file_id, fields=FILE_FIELDS, supportsAllDrives=True)
            .execute()
        )

    def resolve_source_root(self, configured_id: str) -> tuple[dict, str]:
        metadata = self.get_metadata(configured_id)
        if metadata.get("mimeType") == SHORTCUT_MIME:
            target_id = metadata.get("shortcutDetails", {}).get("targetId")
            if not target_id:
                raise RuntimeError("Drive shortcut has no targetId")
            target = self.get_metadata(target_id)
            if target.get("mimeType") != FOLDER_MIME:
                raise RuntimeError("Configured shortcut does not target a folder")
            return target, target_id
        if metadata.get("mimeType") != FOLDER_MIME:
            raise RuntimeError("Configured source ID is neither a folder nor folder shortcut")
        return metadata, configured_id

    def list_children(self, folder_id: str) -> list[dict]:
        rows: list[dict] = []
        page_token = None
        while True:
            response = (
                self.service.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    spaces="drive",
                    fields=f"nextPageToken,files({FILE_FIELDS})",
                    pageSize=1000,
                    pageToken=page_token,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True,
                )
                .execute()
            )
            rows.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return rows

    def inventory_tree(
        self,
        root_id: str,
        root_name: str,
        max_depth: int,
        max_items: int,
        progress: Callable[[str], None] | None = None,
    ) -> list[dict]:
        queue = deque([(root_id, root_name, 0)])
        rows: list[dict] = []
        while queue:
            folder_id, folder_path, depth = queue.popleft()
            if depth > max_depth:
                raise RuntimeError(f"Inventory depth exceeded {max_depth}")
            for child in self.list_children(folder_id):
                row = dict(child)
                row["source_path"] = f"{folder_path}/{child.get('name', '')}"
                row["depth"] = depth + 1
                rows.append(row)
                if len(rows) > max_items:
                    raise RuntimeError(f"Inventory item limit exceeded {max_items}")
                if child.get("mimeType") == FOLDER_MIME:
                    queue.append((child["id"], row["source_path"], depth + 1))
            if progress and len(rows) and len(rows) % 250 == 0:
                progress(f"Inventoried {len(rows):,} source items...")
        return rows

    def download(self, metadata: dict, destination: Path) -> dict:
        from googleapiclient.http import MediaIoBaseDownload

        mime_type = metadata.get("mimeType", "")
        export_mime = None
        suffix = destination.suffix
        if mime_type in NATIVE_EXPORTS:
            export_mime, suffix = NATIVE_EXPORTS[mime_type]
            if destination.suffix.casefold() != suffix:
                destination = destination.with_suffix(suffix)
            request = self.service.files().export_media(
                fileId=metadata["id"], mimeType=export_mime
            )
        else:
            request = self.service.files().get_media(
                fileId=metadata["id"], supportsAllDrives=True
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as handle:
            downloader = MediaIoBaseDownload(handle, request, chunksize=1024 * 1024 * 8)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        return {
            "path": str(destination),
            "export_mime_type": export_mime,
            "bytes": destination.stat().st_size,
        }
