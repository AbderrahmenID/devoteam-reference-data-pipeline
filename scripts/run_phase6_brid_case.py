from pathlib import Path
import hashlib, json, os, shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "human_inputs/phase6/OPPORTUNITY_INPUT_BRID_SYNTHETIC.pdf"
OUTPUT = ROOT / "data/opportunities/OPP-2098dd1874292d22/phase6_brid_controlled_case_v2"

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

if not SOURCE.is_file():
    raise FileNotFoundError(SOURCE)
if sha(SOURCE) != "2098dd1874292d2218e271bd3c0ac9d5f5b44c871de48ad24adf74bd08f335ff":
    raise AssertionError("Synthetic BRID input hash changed")
if not OUTPUT.is_dir():
    raise FileNotFoundError("Release outputs missing; restore them from the package")
for line in (OUTPUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
    expected, name = line.split("  ", 1)
    if sha(OUTPUT / name) != expected:
        raise AssertionError(f"Output changed: {name}")
manifest = json.loads((OUTPUT / "PHASE_6_BRID_MANIFEST.json").read_text(encoding="utf-8"))
if manifest["status"] != "TECHNICAL_PASS_READY_FOR_HUMAN_REVIEW":
    raise AssertionError("Unexpected status")
print(json.dumps({"status": manifest["status"], "opportunity_id": manifest["opportunity_id"],
    "requirements": manifest["requirements"], "eligibility_rules": manifest["eligibility_rules"],
    "filter_proposals": manifest["filter_proposals"]}, indent=2))
