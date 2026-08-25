import inspect

from devoteam_reference_ai.phase2_drive import ReadOnlyDriveClient


def test_drive_facade_exposes_no_mutation_methods():
    public = {name for name, _ in inspect.getmembers(ReadOnlyDriveClient, inspect.isfunction) if not name.startswith("_")}
    assert public == {"download", "get_metadata", "inventory_tree", "list_children", "resolve_source_root"}


def test_source_has_no_drive_mutation_calls():
    source = inspect.getsource(ReadOnlyDriveClient)
    for forbidden in (".create(", ".update(", ".delete(", ".copy(", ".permissions("):
        assert forbidden not in source
