"""Export Python game data to JSON files for the web version.

Run from the repo root:
    python scripts/export_data.py

Outputs:
    web/data/rotors.json
    web/data/fuels.json
    web/data/steam_gen.json
"""
import json
import sys
from pathlib import Path

# Allow importing from the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from gtnh_turbine_calc.data.rotors import ROTOR_DATA, ROTOR_DISPLAY_NAMES
from gtnh_turbine_calc.data.fuels import STEAM_FUELS, GAS_FUELS, PLASMA_FUELS, EHE_FUELS
from gtnh_turbine_calc.data.steam_gen import LHE_SOURCES, THERMAL_BOILER_SOURCES, WWXL_SOURCES

OUT = Path(__file__).parent.parent / "web" / "data"
OUT.mkdir(parents=True, exist_ok=True)


# --- rotors.json ---
# ROTOR_DATA is a dict keyed by rotor name; preserve all fields
rotors = [{"name": name, **stats} for name, stats in ROTOR_DATA.items()]
(OUT / "rotors.json").write_text(
    json.dumps(rotors, indent=2),
    encoding="utf-8",
)
print(f"Wrote {len(rotors)} rotors -> web/data/rotors.json")


# --- fuels.json ---
# STEAM_FUELS: {name: eu_per_l}
# GAS_FUELS:   {name: {eu_per_l, xlgt}}
# PLASMA_FUELS:{name: eu_per_l}
# EHE_FUELS:   {name: {max_convert_ls, ...}}
fuels = {
    "steam": [{"name": k, "eu_l": v} for k, v in STEAM_FUELS.items()],
    "gas": [
        {"name": k, "eu_l": v["eu_per_l"], **{kk: vv for kk, vv in v.items() if kk != "eu_per_l"}}
        for k, v in GAS_FUELS.items()
    ],
    "plasma": [{"name": k, "eu_l": v} for k, v in PLASMA_FUELS.items()],
    "ehe": [{"name": k, **v} for k, v in EHE_FUELS.items()],
}
(OUT / "fuels.json").write_text(
    json.dumps(fuels, indent=2),
    encoding="utf-8",
)
print(
    f"Wrote fuels (steam:{len(fuels['steam'])}, gas:{len(fuels['gas'])}, "
    f"plasma:{len(fuels['plasma'])}, ehe:{len(fuels['ehe'])}) -> web/data/fuels.json"
)


# --- steam_gen.json ---
steam_gen = {
    "lhe": LHE_SOURCES,
    "thermal_boiler": THERMAL_BOILER_SOURCES,
    "wwxl": WWXL_SOURCES,
}
(OUT / "steam_gen.json").write_text(
    json.dumps(steam_gen, indent=2),
    encoding="utf-8",
)
print(
    f"Wrote steam_gen (lhe:{len(LHE_SOURCES)}, thermal:{len(THERMAL_BOILER_SOURCES)}, "
    f"wwxl:{len(WWXL_SOURCES)}) -> web/data/steam_gen.json"
)
