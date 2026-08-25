from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from devoteam_reference_ai.config import load_project_configuration  # noqa: E402


class ConfigurationTests(unittest.TestCase):
    def test_approved_phase_zero_contract_is_loadable(self) -> None:
        config = load_project_configuration(ROOT)
        self.assertEqual(config["security"]["policy"], "D1")
        self.assertEqual(config["filters"]["catalogue"], "G1")
        self.assertFalse(config["models"]["llm"]["external_calls_enabled"])


if __name__ == "__main__":
    unittest.main()
