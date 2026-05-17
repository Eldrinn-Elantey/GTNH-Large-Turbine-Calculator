import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import openpyxl
from scripts.excel_parser import extract_rotors, extract_fuels

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

EXISTING_FUELS = os.path.join(os.path.dirname(__file__), "..", "web", "data", "2.7", "fuels.json")

def test_extract_fuels_structure():
    result = extract_fuels(_wb())
    assert set(result.keys()) == {"steam", "gas", "plasma", "ehe"}
    assert len(result["steam"]) >= 3
    assert len(result["gas"]) >= 20
    assert len(result["plasma"]) >= 50
    assert len(result["ehe"]) >= 50

def test_extract_fuels_steam_values():
    result = extract_fuels(_wb())
    steam = {e["name"]: e["eu_l"] for e in result["steam"]}
    assert abs(steam["Steam"] - 0.5) < 1e-6
    assert abs(steam["SH Steam"] - 1.0) < 1e-6
    assert abs(steam["SC Steam"] - 1.0) < 1e-6

def test_extract_fuels_gas_nitrobenzene():
    result = extract_fuels(_wb())
    gas = {e["name"]: e for e in result["gas"]}
    assert "Nitrobenzene" in gas
    assert abs(gas["Nitrobenzene"]["eu_l"] - 1600.0) < 1e-6
    assert gas["Nitrobenzene"]["xlgt"] is True

def test_extract_fuels_plasma_celestial_tungsten():
    result = extract_fuels(_wb())
    plasma = {e["name"]: e["eu_l"] for e in result["plasma"]}
    assert "Celestial Tungsten Plasma" in plasma
    assert abs(plasma["Celestial Tungsten Plasma"] - 720000.0) < 1e-3

def test_extract_fuels_ehe_lava():
    result = extract_fuels(_wb())
    ehe = {e["name"]: e for e in result["ehe"]}
    assert "Lava" in ehe
    lava = ehe["Lava"]
    assert abs(lava["max_convert_ls"] - 160000.0) < 1e-3
    assert abs(lava["eu_t"] - 640000.0) < 1e-3
    assert lava["coolant"] == "Distilled Water"

def test_extract_fuels_matches_existing_json():
    result = extract_fuels(_wb())
    existing = json.load(open(EXISTING_FUELS))
    new_gas = {e["name"]: e for e in result["gas"]}
    for entry in existing["gas"]:
        name = entry["name"]
        if name in new_gas:
            assert abs(new_gas[name]["eu_l"] - entry["eu_l"]) < 1e-3, f"gas {name} eu_l mismatch"
    new_plasma = {e["name"]: e["eu_l"] for e in result["plasma"]}
    for entry in existing["plasma"]:
        name = entry["name"]
        if name in new_plasma:
            assert abs(new_plasma[name] - entry["eu_l"]) < 1e-3, f"plasma {name} eu_l mismatch"
