import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.fuel_parser import parse_gas_fuels, parse_plasma_fuels

GT5_SRC = r"C:\Users\Eldrinn_Elantey\GitHub\GT5-Unofficial\src"

def test_plasma_aluminium():
    fuels = parse_plasma_fuels(GT5_SRC)
    assert "Aluminium" in fuels
    assert fuels["Aluminium"]["eu_per_l"] == 159744.0

def test_plasma_fuel_count():
    fuels = parse_plasma_fuels(GT5_SRC)
    assert len(fuels) >= 50

def test_gas_fuels_found():
    fuels = parse_gas_fuels(GT5_SRC)
    # At least some gas fuels must be found
    assert len(fuels) >= 5

def test_gas_fuel_structure():
    fuels = parse_gas_fuels(GT5_SRC)
    for name, data in fuels.items():
        assert "eu_per_l" in data
        assert isinstance(data["eu_per_l"], float)
        assert data["eu_per_l"] > 0
