import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.rotor_parser import parse_gt_materials, parse_werkstoff_materials

GT5_SRC = r"C:\Users\Eldrinn_Elantey\GitHub\GT5-Unofficial\src"

def test_adamantium_parsed():
    mats = parse_gt_materials(GT5_SRC)
    # Adamantium: setTool(8_192, 10, 32.0f), setTurbine(1.0f, 5.0f, 1.0f)
    assert "Adamantium" in mats
    m = mats["Adamantium"]
    assert m["tool_quality"] == 10
    assert abs(m["tool_speed"] - 32.0) < 1e-3
    assert m["tool_durability"] == 8192
    assert abs(m["steam_mult"] - 1.0) < 1e-6
    assert abs(m["gas_mult"]   - 5.0) < 1e-6
    assert abs(m["plasma_mult"]- 1.0) < 1e-6

def test_alduorite_has_steam_mult():
    mats = parse_gt_materials(GT5_SRC)
    # Alduorite: setTool(8_192, 1, 32.0f), setTurbine(6.0f, 1.0f, 1.0f)
    assert "Alduorite" in mats
    assert abs(mats["Alduorite"]["steam_mult"] - 6.0) < 1e-6

def test_titanium_default_multipliers():
    mats = parse_gt_materials(GT5_SRC)
    # Titanium has setTool but no setTurbine -> defaults 1/1/1
    assert "Titanium" in mats
    m = mats["Titanium"]
    assert abs(m["steam_mult"]  - 1.0) < 1e-6
    assert abs(m["gas_mult"]    - 1.0) < 1e-6
    assert abs(m["plasma_mult"] - 1.0) < 1e-6

def test_werkstoff_shirabon():
    mats = parse_werkstoff_materials(GT5_SRC)
    # Shirabon in GGMaterial.java: setSpeedOverride(640.0F), setDurOverride(15728640), setQualityOverride((byte) 26)
    assert "Shirabon" in mats
    m = mats["Shirabon"]
    assert abs(m["tool_speed"] - 640.0) < 1e-3
    assert m["tool_durability"] == 15728640
    assert m["tool_quality"] == 26
    assert abs(m["steam_mult"] - 1.0) < 1e-6
