import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import openpyxl
from scripts.excel_parser import extract_rotors

XLSX = os.path.join(os.path.dirname(__file__), "..", "Large Turbine Calculator (2.7.0-2.8.4).xlsx")
EXISTING_ROTORS = os.path.join(os.path.dirname(__file__), "..", "web", "data", "2.7", "rotors.json")

def _wb():
    return openpyxl.load_workbook(XLSX, data_only=True)

def test_extract_rotors_returns_list():
    rotors = extract_rotors(_wb())
    assert isinstance(rotors, list)
    assert len(rotors) > 100

def test_extract_rotors_mithril_present():
    rotors = extract_rotors(_wb())
    names = [r["name"] for r in rotors]
    assert "Mithril (2)" in names

def test_extract_rotors_mithril_stats():
    rotors = extract_rotors(_wb())
    rotor = next(r for r in rotors if r["name"] == "Mithril (2)")
    assert rotor["tier"] == 2
    assert abs(rotor["mining_speed"] - 32.0) < 1e-6
    assert rotor["base_durability"] == 6400
    assert rotor["overflow_tier"] == 1
    small = rotor["sizes"]["Small"]
    assert abs(small["steam_tight_eff"] - 0.75) < 1e-3
    assert abs(small["gas_tight_eff"] - 0.75) < 1e-3
    assert abs(small["plasma_tight_eff"] - 0.75) < 1e-3

def test_extract_rotors_matches_existing_json():
    """Verify extracted data matches the known-good 2.7 web JSON."""
    rotors = extract_rotors(_wb())
    existing = json.load(open(EXISTING_ROTORS))
    existing_map = {r["name"]: r for r in existing}
    new_map = {r["name"]: r for r in rotors}
    common = set(existing_map) & set(new_map)
    assert len(common) > 100
    for name in sorted(common)[:10]:  # spot-check 10
        e = existing_map[name]
        n = new_map[name]
        assert e["tier"] == n["tier"], f"{name}: tier mismatch"
        assert abs(e["sizes"]["Small"]["steam_tight_eff"] - n["sizes"]["Small"]["steam_tight_eff"]) < 1e-3, f"{name}: steam_tight_eff Small mismatch"
        assert abs(e["sizes"]["Small"]["gas_tight_eff"] - n["sizes"]["Small"]["gas_tight_eff"]) < 1e-3, f"{name}: gas_tight_eff Small mismatch"
