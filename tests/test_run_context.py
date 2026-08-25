from pathlib import Path
import json
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from devoteam_reference_ai.run_context import new_run_context, write_run_manifest  # noqa: E402


class RunContextTests(unittest.TestCase):
    def test_manifest_contains_config_hashes(self) -> None:
        context = new_run_context("phase1_test", ROOT)
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            output = Path(directory) / "manifest.json"
            write_run_manifest(context, output, ROOT)
            payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["stage"], "phase1_test")
        self.assertIn("project.yaml", payload["config_hashes"])
        self.assertEqual(len(payload["config_hashes"]["project.yaml"]), 64)


if __name__ == "__main__":
    unittest.main()
