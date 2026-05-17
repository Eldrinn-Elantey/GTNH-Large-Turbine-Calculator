import pytest
from gtnh_turbine_calc.calc.ehe import calc_plasma_ehe, calc_nonxl_ehe
from gtnh_turbine_calc.data.rotors import ROTOR_DATA
from gtnh_turbine_calc.data.fuels import EHE_FUELS

EA = ROTOR_DATA["Energetic Alloy (3)"]

def test_plasma_ehe_helium():
    result = calc_plasma_ehe(
        plasma_type="Helium Plasma",
        recipe_output_l=125,
        recipe_time_s=0.8,
        parallel_count=5,
        rotor=EA,
        size="Normal",
    )
    assert result["plasma_output_ls"] == pytest.approx(781.25, abs=1)
    assert result["dense_sc_steam_lt"] == pytest.approx(2879, abs=50)

def test_nonxl_ehe_ic2_coolant():
    result = calc_nonxl_ehe(
        hot_fluid="IC2 Hot Coolant",
        hot_fluid_input_ls=32000000,
        rotor=EA,
        size="Normal",
    )
    assert result["total_sc_steam_lt"] is not None
