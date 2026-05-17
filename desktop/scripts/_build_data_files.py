"""One-shot helper: reads raw data modules and writes rotors.py, fuels.py, steam_gen.py."""
import sys
sys.path.insert(0, ".")

import gtnh_turbine_calc.data.rotors_raw as r
import gtnh_turbine_calc.data.fuels_raw as f

rotor_repr = repr(r.ROTOR_DATA)
gas_repr = repr(f.GAS_FUELS)
plasma_repr = repr(f.PLASMA_FUELS)
ehe_repr = repr(f.EHE_FUELS)

rotors_py = (
    'SIZE_DATA = {\n'
    '    "Small":  {"dur_mult": 1},\n'
    '    "Normal": {"dur_mult": 2},\n'
    '    "Large":  {"dur_mult": 3},\n'
    '    "Huge":   {"dur_mult": 4},\n'
    '}\n'
    '\n'
    'ROTOR_DATA = ' + rotor_repr + '\n'
    '\n'
    'ROTOR_DISPLAY_NAMES = sorted(ROTOR_DATA.keys(), key=lambda n: ROTOR_DATA[n]["tier"], reverse=True)\n'
)

fuels_py = (
    'STEAM_FUELS = {"Steam": 0.5, "SH Steam": 1.0, "SC Steam": 1.0}\n'
    '\n'
    'GAS_FUELS = ' + gas_repr + '\n'
    '\n'
    'PLASMA_FUELS = ' + plasma_repr + '\n'
    '\n'
    'EHE_FUELS = ' + ehe_repr + '\n'
    '\n'
    'GAS_FUEL_NAMES = sorted(GAS_FUELS.keys(), key=lambda n: GAS_FUELS[n]["eu_per_l"], reverse=True)\n'
    'PLASMA_FUEL_NAMES = sorted(PLASMA_FUELS.keys(), key=lambda n: PLASMA_FUELS[n], reverse=True)\n'
    'EHE_FUEL_NAMES = sorted(\n'
    '    [k for k in EHE_FUELS if EHE_FUELS[k]["max_convert_ls"] is not None],\n'
    '    key=lambda n: EHE_FUELS[n].get("eu_t", 0) or 0, reverse=True\n'
    ')\n'
)

steam_gen_py = (
    'LHE_SOURCES = [\n'
    '    {"name": "Lava",              "threshold_ls": 1000,  "max_ls": 2000,  "below": "Steam",    "above": "SH Steam", "ratio_below": 160, "ratio_above": 80},\n'
    '    {"name": "Hot Coolant",       "threshold_ls": 800,   "max_ls": 1600,  "below": "Steam",    "above": "SH Steam", "ratio_below": 400, "ratio_above": 200},\n'
    '    {"name": "Solar Salt (Hot)",  "threshold_ls": 160,   "max_ls": 320,   "below": "Steam",    "above": "SH Steam", "ratio_below": 1000,"ratio_above": 500},\n'
    ']\n'
    '\n'
    'WWXL_SOURCES = [\n'
    '    {"name": "Lava",              "threshold_ls": 32000, "max_ls": 64000, "below": "Steam",    "above": "SH Steam", "ratio_below": 160, "ratio_above": 80},\n'
    '    {"name": "Hot Coolant",       "threshold_ls": 25600, "max_ls": 51200, "below": "Steam",    "above": "SH Steam", "ratio_below": 400, "ratio_above": 200},\n'
    ']\n'
    '\n'
    'THERMAL_BOILER_SOURCES = [\n'
    '    {"name": "Lava",              "max_ls": 1000,  "steam": "Steam",    "ratio": 16},\n'
    '    {"name": "Pahoehoe Lava",     "max_ls": 1000,  "steam": "Steam",    "ratio": 16},\n'
    '    {"name": "Solar Salt (Hot)",  "max_ls": 100,   "steam": "SH Steam", "ratio": 1000},\n'
    '    {"name": "Hot Coolant",       "max_ls": 500,   "steam": "SH Steam", "ratio": 200},\n'
    ']\n'
)

with open("gtnh_turbine_calc/data/rotors.py", "w", encoding="utf-8") as fh:
    fh.write(rotors_py)
print("Written rotors.py")

with open("gtnh_turbine_calc/data/fuels.py", "w", encoding="utf-8") as fh:
    fh.write(fuels_py)
print("Written fuels.py")

with open("gtnh_turbine_calc/data/steam_gen.py", "w", encoding="utf-8") as fh:
    fh.write(steam_gen_py)
print("Written steam_gen.py")
