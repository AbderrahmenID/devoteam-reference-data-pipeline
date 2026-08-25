from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from devoteam_reference_ai.paths import UnsafePathError, assert_safe_write_path  # noqa: E402


class PathSafetyTests(unittest.TestCase):
    def test_write_inside_project_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "reports" / "result.json"
            self.assertEqual(assert_safe_write_path(target, root), target.resolve())

    def test_write_outside_project_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "project"
            root.mkdir()
            with self.assertRaises(UnsafePathError):
                assert_safe_write_path(Path(directory) / "source" / "file.txt", root)


if __name__ == "__main__":
    unittest.main()
