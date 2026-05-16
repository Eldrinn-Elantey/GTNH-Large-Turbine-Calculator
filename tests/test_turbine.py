import pytest
from gtnh_turbine_calc.calc.turbine import (
    calc_regular_turbine, calc_xl_turbine, TurbineResult
)
from gtnh_turbine_calc.data.rotors import ROTOR_DATA
from gtnh_turbine_calc.data.fuels import STEAM_FUELS, GAS_FUELS, PLASMA_FUELS

EA = ROTOR_DATA["Energetic Alloy (3)"]

# --- Regular Steam ---
def test_steam_tight_optimal():
    r = calc_regular_turbine("steam", EA, "Normal", "Tight", "Steam", STEAM_FUELS["Steam"])
    assert r.opt_output_eu_t == 1215
    assert r.opt_flow == 1800
    assert r.lifetime_s == pytest.approx(866376, abs=200)

def test_steam_loose_optimal():
    r = calc_regular_turbine("steam", EA, "Normal", "Loose", "Steam", STEAM_FUELS["Steam"])
    assert r.opt_output_eu_t == 6586

# --- Regular Gas ---
def test_gas_tight_benzene():
    r = calc_regular_turbine("gas", EA, "Normal", "Tight", "Benzene", GAS_FUELS["Benzene"]["eu_per_l"])
    assert r.opt_output_eu_t == 2430
    assert r.opt_flow == 5

# --- Regular Plasma ---
def test_plasma_tight_helium():
    # Helium Plasma eu/L = 81920
    r = calc_regular_turbine("plasma", EA, "Normal", "Tight", "Helium Plasma", 81920)
    assert r.opt_output_eu_t == 105062
    assert r.opt_flow == 19  # L/s

# --- XL Steam ---
def test_xl_steam_loose_sc():
    r = calc_xl_turbine("steam", EA, "Normal", "Loose", "SC Steam", STEAM_FUELS["SC Steam"], is_dense=True)
    assert r.opt_output_eu_t == pytest.approx(210330, abs=10)

# --- XL Gas ---
def test_xl_gas_tight_nitrobenzene():
    r = calc_xl_turbine("gas", EA, "Normal", "Tight", "Nitrobenzene", GAS_FUELS["Nitrobenzene"]["eu_per_l"])
    assert r.opt_output_eu_t == pytest.approx(38880, abs=50)
