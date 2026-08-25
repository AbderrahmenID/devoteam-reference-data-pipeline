from pathlib import Path

from devoteam_reference_ai.phase2_utils import parse_drive_id, safe_filename, stable_json_hash


def test_parse_common_drive_links():
    file_id = "1AbCdEfGhIjKlMnOpQrStUvWxYz12"
    assert parse_drive_id(f"https://drive.google.com/file/d/{file_id}/view") == file_id
    assert parse_drive_id(f"https://drive.google.com/open?id={file_id}") == file_id
    assert parse_drive_id(f"https://drive.google.com/drive/folders/{file_id}") == file_id


def test_safe_filename_blocks_traversal():
    value = safe_filename("../../bad:name?.pdf")
    assert value == "bad_name_.pdf"
    assert "/" not in value and "\\" not in value


def test_stable_json_hash_is_order_independent_for_keys():
    assert stable_json_hash({"a": 1, "b": 2}) == stable_json_hash({"b": 2, "a": 1})
