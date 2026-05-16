# GTNH Large Turbine Calculator GUI - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CustomTkinter desktop application that replicates all calculations from the GTNH Large Turbine Calculator Excel spreadsheet (v2.7.0-2.8.4).

**Architecture:** Python package `gtnh_turbine_calc/` with separate modules for data, calculation logic, and UI. All fuel/rotor data is extracted from the Excel file once and stored as Python dicts. The UI calls calculation functions and displays results live as inputs change.

**Tech Stack:** Python 3.10+, customtkinter>=5.2.0, openpyxl>=3.1.0 (extraction only, not runtime)

---

## File Map

```
gtnh_turbine_calc/
├── __init__.py
├── main.py                   # entry point
├── app.py                    # CTkApp window + sidebar + frame switching
├── data/
│   ├── __init__.py
│   ├── fuels.py              # STEAM_FUELS, GAS_FUELS, PLASMA_FUELS, EHE_FUELS
│   ├── rotors.py             # ROTOR_DATA, SIZE_DATA
│   └── steam_gen.py          # STEAM_GEN_DATA (LHE/WWXL/Thermal Boiler tables)
├── calc/
│   ├── __init__.py
│   ├── common.py             # DYNAMO_TIERS, find_dynamo_tier()
│   ├── turbine.py            # regular + XL turbine calculations
│   └── ehe.py                # EHE planner calculations
└── ui/
    ├── __init__.py
    ├── widgets.py             # TurbineCard, ResultRow, ToggleButton, SearchableTable
    ├── calculator.py          # Calculator tab (3 regular + XL section)
    ├── ehe_planner.py         # EHE Planner tab
    ├── steam_gen_tab.py       # Steam Generation tab
    ├── fuels_ref.py           # Fuels reference tab
    └── rotors_ref.py          # Rotors reference tab
scripts/
└── extract_data.py           # one-time script to dump rotor+fuel data from Excel
tests/
├── test_turbine.py
└── test_ehe.py
requirements.txt
```

---

## Task 1: Project Setup

**Files:**
- Create: `gtnh_turbine_calc/__init__.py`
- Create: `gtnh_turbine_calc/main.py`
- Create: `requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```
customtkinter>=5.2.0
openpyxl>=3.1.0
```

- [ ] **Step 2: Create directory structure**

```
mkdir gtnh_turbine_calc gtnh_turbine_calc\data gtnh_turbine_calc\calc gtnh_turbine_calc\ui tests scripts
```

Create `gtnh_turbine_calc/__init__.py` (empty).
Create `gtnh_turbine_calc/data/__init__.py` (empty).
Create `gtnh_turbine_calc/calc/__init__.py` (empty).
Create `gtnh_turbine_calc/ui/__init__.py` (empty).

- [ ] **Step 3: Create main.py**

```python
from gtnh_turbine_calc.app import TurbineCalcApp

if __name__ == "__main__":
    app = TurbineCalcApp()
    app.mainloop()
```

- [ ] **Step 4: Install dependencies**

```
pip install customtkinter openpyxl
```

Expected: both packages install without errors.

- [ ] **Step 5: Verify import works**

```
python -c "import customtkinter; import openpyxl; print('OK')"
```

Expected: `OK`

---

## Task 2: Data Extraction Script

**Files:**
- Create: `scripts/extract_data.py`

This script reads the Excel file and prints Python code for `data/rotors.py` and `data/fuels.py`. Run it once to generate the data files.

- [ ] **Step 1: Create extract_data.py**

```python
import openpyxl
import sys

EXCEL_PATH = "D:/UserData/Eldrinn_Elantey/Downloads/Large Turbine Calculator (2.7.0-2.8.4).xlsx"

def extract_rotors(wb):
    ws = wb["Rotors"]
    sizes = ["Small", "Normal", "Large", "Huge"]
    size_dur_mults = {"Small": 1, "Normal": 2, "Large": 3, "Huge": 4}

    # Column offsets (relative to range start col I=9, 1-indexed in VLOOKUP)
    # These match Rotors!E10..E30 col index bases + size MATCH(1..4)
    COL_OFFSETS = {
        "steam_tight_eff":       20,  # E13
        "steam_loose_eff":       24,  # E14
        "steam_opt_flow_tight":  28,  # E15 [L/t]
        "steam_opt_flow_loose":  32,  # E16 [L/t]
        "steam_power_tight":     36,  # E17 [EU/t]
        "steam_power_loose":     40,  # E18 [EU/t]
        "gas_tight_eff":         48,  # E19
        "gas_loose_eff":         52,  # E20
        "gas_opt_flow_tight":    56,  # E21 [EU/t]
        "gas_opt_flow_loose":    60,  # E22 [EU/t]
        "gas_power_tight":       64,  # E23 [EU/t]
        "gas_power_loose":       68,  # E24 [EU/t]
        "plasma_tight_eff":      76,  # E25
        "plasma_loose_eff":      80,  # E26
        "plasma_opt_flow_tight": 84,  # E27 [EU/t]
        "plasma_opt_flow_loose": 88,  # E28 [EU/t]
        "plasma_power_tight":    92,  # E29 [EU/t]
        "plasma_power_loose":    96,  # E30 [EU/t]
    }

    rotors = {}
    # Material rows start at row 4, col I=9
    for row in ws.iter_rows(min_row=4, max_row=1000, values_only=True):
        display_name = row[8]  # col I = index 8 (0-based)
        if not display_name or not isinstance(display_name, str):
            continue
        tier = row[9]          # col J
        mining_speed = row[10] # col K
        base_dur = row[11]     # col L (Durability ST)
        overflow_tier = row[12]# col M

        if tier is None:
            continue

        sizes_data = {}
        for i, size in enumerate(sizes, start=1):  # 1=Small, 2=Normal, 3=Large, 4=Huge
            sd = {}
            for key, base_col in COL_OFFSETS.items():
                col_idx = base_col + i  # 1-indexed relative to col I
                abs_col = 9 + col_idx - 1  # absolute column (0-indexed)
                val = row[abs_col] if abs_col < len(row) else None
                sd[key] = round(val, 6) if isinstance(val, float) else val
            sd["dur_mult"] = size_dur_mults[size]
            sizes_data[size] = sd

        rotors[display_name] = {
            "tier": int(tier),
            "mining_speed": mining_speed,
            "base_durability": int(base_dur),
            "overflow_tier": int(overflow_tier),
            "sizes": sizes_data,
        }

    return rotors

def extract_fuels(wb):
    ws = wb["Fuels"]
    steam_fuels = {}
    gas_fuels = {}
    plasma_fuels = {}
    ehe_fuels = {}

    for row in ws.iter_rows(min_row=5, max_row=1000, values_only=True):
        # Steam fuels: col B=name, col C=eu_per_l
        if row[1] and row[2] is not None and isinstance(row[2], (int, float)):
            if row[1] in ("Steam", "SH Steam", "SC Steam"):
                steam_fuels[row[1]] = float(row[2])

        # Gas fuels: col J=name, col K=eu_per_l, col L=xlgt
        if row[9] and row[10] is not None and isinstance(row[10], (int, float)):
            gas_fuels[row[9]] = {"eu_per_l": float(row[10]), "xlgt": bool(row[11])}

        # Plasma fuels: col O=name, col P=eu_per_l
        if row[14] and row[15] is not None and isinstance(row[15], (int, float)):
            plasma_fuels[row[14]] = float(row[15])

        # EHE plasma fuels: col R=name, col S..AC = data
        if row[17] and isinstance(row[17], str) and row[18] is not None:
            ehe_fuels[row[17]] = {
                "max_convert_ls": row[18],
                "threshold_ls": row[19],
                "eu_t": row[20],
                "coolant": row[21],
                "max_coolant_ls": row[22],
                "normal_steam": row[23],
                "max_normal_steam_ls": row[24],
                "hot_steam": row[25],
                "max_hot_steam_ls": row[26],
                "cooled_fluid": row[27],
                "max_cooled_fluid_ls": row[28],
            }

    return steam_fuels, gas_fuels, plasma_fuels, ehe_fuels

if __name__ == "__main__":
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

    rotors = extract_rotors(wb)
    steam_fuels, gas_fuels, plasma_fuels, ehe_fuels = extract_fuels(wb)

    if "--rotors" in sys.argv:
        print("ROTOR_DATA =", repr(rotors))
    if "--fuels" in sys.argv:
        print("STEAM_FUELS =", repr(steam_fuels))
        print("GAS_FUELS =", repr(gas_fuels))
        print("PLASMA_FUELS =", repr(plasma_fuels))
        print("EHE_FUELS =", repr(ehe_fuels))
    if len(sys.argv) == 1:
        print(f"Extracted {len(rotors)} rotors, "
              f"{len(steam_fuels)} steam fuels, "
              f"{len(gas_fuels)} gas fuels, "
              f"{len(plasma_fuels)} plasma fuels, "
              f"{len(ehe_fuels)} EHE fuels")
```

- [ ] **Step 2: Run and verify counts**

```
python scripts/extract_data.py
```

Expected: `Extracted N rotors, 3 steam fuels, 28 gas fuels, 65+ plasma fuels, 65+ EHE fuels`
(exact counts depend on version).

- [ ] **Step 3: Generate rotor data file**

```
python scripts/extract_data.py --rotors > gtnh_turbine_calc/data/rotors_raw.py
```

Then open `rotors_raw.py`, copy the `ROTOR_DATA = {...}` dict, and create `gtnh_turbine_calc/data/rotors.py`:

```python
SIZE_DATA = {
    "Small":  {"dur_mult": 1},
    "Normal": {"dur_mult": 2},
    "Large":  {"dur_mult": 3},
    "Huge":   {"dur_mult": 4},
}

ROTOR_DISPLAY_NAMES = [...]  # sorted list of all display names for dropdowns

ROTOR_DATA = { ... }  # paste extracted dict here
```

For `ROTOR_DISPLAY_NAMES`, add after the dict:
```python
ROTOR_DISPLAY_NAMES = sorted(ROTOR_DATA.keys(), key=lambda n: ROTOR_DATA[n]["tier"], reverse=True)
```

- [ ] **Step 4: Generate fuel data file**

```
python scripts/extract_data.py --fuels > gtnh_turbine_calc/data/fuels_raw.py
```

Create `gtnh_turbine_calc/data/fuels.py`:

```python
STEAM_FUELS = {"Steam": 0.5, "SH Steam": 1.0, "SC Steam": 1.0}

GAS_FUELS = { ... }      # paste extracted dict
PLASMA_FUELS = { ... }   # paste extracted dict
EHE_FUELS = { ... }      # paste extracted dict

GAS_FUEL_NAMES = sorted(GAS_FUELS.keys(), key=lambda n: GAS_FUELS[n]["eu_per_l"], reverse=True)
PLASMA_FUEL_NAMES = sorted(PLASMA_FUELS.keys(), key=lambda n: PLASMA_FUELS[n], reverse=True)
EHE_FUEL_NAMES = sorted(
    [k for k in EHE_FUELS if EHE_FUELS[k]["max_convert_ls"] is not None],
    key=lambda n: EHE_FUELS[n].get("eu_t", 0) or 0, reverse=True
)
```

- [ ] **Step 5: Create steam_gen.py**

```python
# Conversion data from Steam Generation sheet
# LHE: Lava/Hot Coolant/Solar Salt → Steam/SH Steam
# WWXL: same fluids, 20x capacity
# Thermal Boiler: Lava/Pahoehoe/Solar Salt/Hot Coolant → Steam

LHE_SOURCES = [
    {"name": "Lava",              "threshold_ls": 1000,  "max_ls": 2000,  "below": "Steam",    "above": "SH Steam", "ratio_below": 160, "ratio_above": 80},
    {"name": "Hot Coolant",       "threshold_ls": 800,   "max_ls": 1600,  "below": "Steam",    "above": "SH Steam", "ratio_below": 400, "ratio_above": 200},
    {"name": "Solar Salt (Hot)",  "threshold_ls": 160,   "max_ls": 320,   "below": "Steam",    "above": "SH Steam", "ratio_below": 1000,"ratio_above": 500},
]

WWXL_SOURCES = [
    {"name": "Lava",              "threshold_ls": 32000, "max_ls": 64000, "below": "Steam",    "above": "SH Steam", "ratio_below": 160, "ratio_above": 80},
    {"name": "Hot Coolant",       "threshold_ls": 25600, "max_ls": 51200, "below": "Steam",    "above": "SH Steam", "ratio_below": 400, "ratio_above": 200},
]

THERMAL_BOILER_SOURCES = [
    {"name": "Lava",              "max_ls": 1000,  "steam": "Steam",    "ratio": 16},
    {"name": "Pahoehoe Lava",     "max_ls": 1000,  "steam": "Steam",    "ratio": 16},
    {"name": "Solar Salt (Hot)",  "max_ls": 100,   "steam": "SH Steam", "ratio": 1000},
    {"name": "Hot Coolant",       "max_ls": 500,   "steam": "SH Steam", "ratio": 200},
]
```

- [ ] **Step 6: Verify imports**

```
python -c "from gtnh_turbine_calc.data.fuels import STEAM_FUELS, GAS_FUELS, PLASMA_FUELS; from gtnh_turbine_calc.data.rotors import ROTOR_DATA; print(len(ROTOR_DATA), 'rotors')"
```

Expected: prints number of rotors > 0.

---

## Task 3: Common Calculation Utilities

**Files:**
- Create: `gtnh_turbine_calc/calc/common.py`
- Create: `tests/test_common.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_common.py
import pytest
from gtnh_turbine_calc.calc.common import find_dynamo_tier

def test_find_dynamo_tier_660():
    assert find_dynamo_tier(660) == "EV"

def test_find_dynamo_tier_58572():
    assert find_dynamo_tier(58572) == "ZPM"

def test_find_dynamo_tier_1188():
    assert find_dynamo_tier(1188) == "EV"
```

- [ ] **Step 2: Run to confirm fail**

```
python -m pytest tests/test_common.py -v
```

Expected: ImportError or NameError.

- [ ] **Step 3: Create calc/common.py**

```python
import math

DYNAMO_TIERS = [
    ("LV",      32),
    ("MV",      128),
    ("HV",      512),
    ("EV",      2048),
    ("IV",      8192),
    ("LuV",     32768),
    ("ZPM",     131072),
    ("UV",      524288),
    ("UHV",     2097152),
    ("UEV",     8388608),
    ("UIV",     33554432),
    ("UMV",     134217728),
    ("UXV",     536870912),
    ("MAX",     2147483648),
    ("MAX+",    8589934592),
    ("MAX++",   34359738368),
    ("MAX+++",  137438953472),
    ("MAX++++", 549755813888),
]

def find_dynamo_tier(eu_per_t: float) -> str:
    """Return the minimum dynamo tier that can output at least eu_per_t EU/t at 1 amp."""
    for name, voltage in DYNAMO_TIERS:
        if voltage > eu_per_t:
            return name
    return "MAX++++"

def dynamo_amps(eu_per_t: float, tier: str) -> float:
    """Return amps needed at the given dynamo tier."""
    voltage = dict(DYNAMO_TIERS).get(tier, 1)
    return round(eu_per_t / voltage, 3)
```

- [ ] **Step 4: Run tests**

```
python -m pytest tests/test_common.py -v
```

Expected: all pass.

- [ ] **Step 5: Commit**

```
git add gtnh_turbine_calc/ tests/test_common.py requirements.txt scripts/
git commit -m "add project skeleton, data extraction script, common calc utils"
```

---

## Task 4: Turbine Calculation Engine

**Files:**
- Create: `gtnh_turbine_calc/calc/turbine.py`
- Create: `tests/test_turbine.py`

All formulas below are derived from the Excel Calculator sheet formulas (rows 4-67).

- [ ] **Step 1: Write failing tests with known-good values from the Excel**

```python
# tests/test_turbine.py
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
    assert r.opt_output_eu_t == 660
    assert r.opt_flow == 1200
    assert r.lifetime_s == pytest.approx(416490, abs=200)

def test_steam_loose_optimal():
    r = calc_regular_turbine("steam", EA, "Normal", "Loose", "Steam", STEAM_FUELS["Steam"])
    assert r.opt_output_eu_t == 2123

# --- Regular Gas ---
def test_gas_tight_benzene():
    r = calc_regular_turbine("gas", EA, "Normal", "Tight", "Benzene", GAS_FUELS["Benzene"]["eu_per_l"])
    assert r.opt_output_eu_t == 1188
    assert r.opt_flow == 3

# --- Regular Plasma ---
def test_plasma_tight_helium():
    # Helium Plasma eu/L = 81920 (not in main plasma list, hardcoded from Excel)
    r = calc_regular_turbine("plasma", EA, "Normal", "Tight", "Helium Plasma", 81920)
    assert r.opt_output_eu_t == 58572
    assert r.opt_flow == 13  # L/s

# --- XL Steam ---
def test_xl_steam_loose_sc():
    # XL Turbo SC Steam: C25*16 = 6377.62*16 = 102041.9 L/t, output ~67904 EU/t
    r = calc_xl_turbine("steam", EA, "Normal", "Loose", "SC Steam", STEAM_FUELS["SC Steam"], is_dense=True)
    assert r.opt_output_eu_t == pytest.approx(67904, abs=10)

# --- XL Gas ---
def test_xl_gas_tight_nitrobenzene():
    r = calc_xl_turbine("gas", EA, "Normal", "Tight", "Nitrobenzene", GAS_FUELS["Nitrobenzene"]["eu_per_l"])
    assert r.opt_output_eu_t == pytest.approx(21120, abs=50)
```

- [ ] **Step 2: Run to confirm fail**

```
python -m pytest tests/test_turbine.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement calc/turbine.py**

```python
import math
from dataclasses import dataclass
from typing import Literal

from gtnh_turbine_calc.calc.common import find_dynamo_tier, dynamo_amps

TurbineType = Literal["steam", "gas", "plasma"]


@dataclass
class TurbineResult:
    turbine_type: str
    mode: str
    fuel_type: str
    fuel_value: float
    opt_flow: float          # L/t for steam/gas, L/s for plasma
    opt_output_eu_t: int     # EU/t at optimal flow, tight efficiency
    eff_flow: float          # same units as opt_flow (capped to max)
    eff_output_eu_t: int     # EU/t at effective flow
    rotor_eff: float
    max_flow: float
    min_dynamo_tier_opt: str
    min_dynamo_tier_eff: str
    lifetime_s: float        # seconds at effective flow
    overflow_tier: int


def _rotor_size(rotor: dict, size: str) -> dict:
    return rotor["sizes"][size]


def _durability(rotor: dict, size: str) -> int:
    return rotor["base_durability"] * rotor["sizes"][size]["dur_mult"]


def _lifetime_regular(durability: int, output: int, steam_mode: str | None, mode: str) -> float:
    """Regular turbine lifetime in seconds. Formula: 2*ceil(dur/min(out/5, out^0.6)*50)*mult."""
    if output <= 0:
        return 0.0
    damage = min(output / 5, output ** 0.6)
    base = 2 * math.ceil(durability / damage * 50)
    if steam_mode == "SC Steam":
        mult = 0.5 if mode == "Tight" else 2.0
    elif steam_mode in ("Steam", "SH Steam"):
        mult = 1.0 if mode == "Tight" else 4 / 3
    else:  # gas, plasma
        mult = 1.0
    return base * mult


def _lifetime_xl(durability: int, output: int, turbine_type: str, mode: str) -> float:
    """XL turbine lifetime in seconds."""
    if output <= 0:
        return 0.0
    damage = min(output / 5 / 5, (output / 5) ** 0.6)
    if turbine_type == "steam":
        mult = 1.0 if mode == "Tight" else 4 / 3
        return math.ceil(mult * durability / damage * 50)
    elif turbine_type == "gas":
        return math.ceil(4 / 3 * durability / damage * 50)
    else:  # plasma
        return math.ceil(1.25 * durability / damage * 50)


def _flow_efficiency_steam(eff_flow: float, opt_flow: float, overflow_tier: int, fuel_type: str) -> float:
    """Steam turbine flow efficiency (0..1). <optimal underflows, >optimal overflows."""
    if opt_flow <= 0:
        return 0.0
    if eff_flow > opt_flow:
        if fuel_type == "SC Steam":
            mult = 1.25
        elif fuel_type == "SH Steam":
            mult = overflow_tier + 2
        else:
            mult = overflow_tier + 1
        return 1.0 - abs((eff_flow - opt_flow) / (opt_flow * mult))
    else:
        return 1.0 - abs((eff_flow - opt_flow) / opt_flow)


def _flow_efficiency_gas(eff_flow: float, opt_flow: float, overflow_tier: int) -> float:
    if opt_flow <= 0:
        return 0.0
    if eff_flow > opt_flow:
        return 1.0 - abs((eff_flow - opt_flow) / (opt_flow * (overflow_tier * 3 - 1)))
    return 1.0 - abs((eff_flow - opt_flow) / opt_flow)


def _flow_efficiency_plasma(eff_flow: float, opt_flow: float, overflow_tier: int) -> float:
    if opt_flow <= 0:
        return 0.0
    if eff_flow > opt_flow:
        return 1.0 - abs((eff_flow - opt_flow) / (opt_flow * (overflow_tier * 3 + 1)))
    return 1.0 - abs((eff_flow - opt_flow) / opt_flow)


def calc_regular_turbine(
    turbine_type: TurbineType,
    rotor: dict,
    size: str,
    mode: str,
    fuel_type: str,
    fuel_value: float,
    manual_flow: float | None = None,
) -> TurbineResult:
    """Calculate all outputs for one regular turbine configuration."""
    sd = _rotor_size(rotor, size)
    overflow_tier = rotor["overflow_tier"]
    durability = _durability(rotor, size)

    if turbine_type == "steam":
        rotor_eff = sd["steam_tight_eff"] if mode == "Tight" else sd["steam_loose_eff"]
        opt_flow = sd["steam_opt_flow_tight"] if mode == "Tight" else sd["steam_opt_flow_loose"]
        opt_output = int(math.floor(opt_flow * rotor_eff * fuel_value))

        if fuel_type == "SC Steam":
            max_flow_mult = 1.25
        elif fuel_type == "SH Steam":
            max_flow_mult = 0.5 * overflow_tier + 1.5
        else:
            max_flow_mult = 0.5 * overflow_tier + 1
        max_flow = int(math.floor(opt_flow * max_flow_mult))

        eff_flow = min(max_flow, manual_flow) if manual_flow is not None else opt_flow
        flow_eff = _flow_efficiency_steam(eff_flow, opt_flow, overflow_tier, fuel_type)
        eff_output = max(1, int(math.floor(eff_flow * flow_eff * rotor_eff * fuel_value)))
        lifetime = _lifetime_regular(durability, eff_output, fuel_type, mode)

    elif turbine_type == "gas":
        rotor_eff = sd["gas_tight_eff"] if mode == "Tight" else sd["gas_loose_eff"]
        opt_flow_eu_t = sd["gas_opt_flow_tight"] if mode == "Tight" else sd["gas_opt_flow_loose"]
        opt_flow = max(1, int(math.floor(opt_flow_eu_t / fuel_value)))
        opt_output = int(math.floor(opt_flow * rotor_eff * fuel_value))

        max_flow_mult = overflow_tier * 1.5
        max_flow = int(math.floor(max_flow_mult * opt_flow))

        eff_flow = min(max_flow, manual_flow) if manual_flow is not None else opt_flow
        flow_eff = _flow_efficiency_gas(eff_flow, opt_flow, overflow_tier)
        eff_output = int(math.floor(eff_flow * flow_eff * rotor_eff * fuel_value))
        lifetime = _lifetime_regular(durability, eff_output, None, mode)

    else:  # plasma
        rotor_eff = sd["plasma_tight_eff"] if mode == "Tight" else sd["plasma_loose_eff"]
        opt_flow_eu_t = sd["plasma_opt_flow_tight"] if mode == "Tight" else sd["plasma_opt_flow_loose"]
        opt_flow = max(1, int(math.ceil(opt_flow_eu_t * 20 / fuel_value)))
        opt_output = int(math.floor(opt_flow * rotor_eff * fuel_value / 20))

        max_flow_mult = 1.5 * overflow_tier + 1
        max_flow = int(math.floor(max_flow_mult * opt_flow))

        eff_flow = min(max_flow, manual_flow) if manual_flow is not None else opt_flow
        flow_eff = _flow_efficiency_plasma(eff_flow, opt_flow, overflow_tier)
        eff_output = int(math.floor(opt_output * min(1 + overflow_tier * 1.5, eff_flow / opt_flow) * flow_eff))
        lifetime = _lifetime_regular(durability, eff_output, None, mode)

    return TurbineResult(
        turbine_type=turbine_type,
        mode=mode,
        fuel_type=fuel_type,
        fuel_value=fuel_value,
        opt_flow=opt_flow,
        opt_output_eu_t=opt_output,
        eff_flow=eff_flow,
        eff_output_eu_t=eff_output,
        rotor_eff=rotor_eff,
        max_flow=max_flow,
        min_dynamo_tier_opt=find_dynamo_tier(opt_output),
        min_dynamo_tier_eff=find_dynamo_tier(eff_output),
        lifetime_s=lifetime,
        overflow_tier=overflow_tier,
    )


def calc_xl_turbine(
    turbine_type: TurbineType,
    rotor: dict,
    size: str,
    mode: str,
    fuel_type: str,
    fuel_value: float,
    is_dense: bool = False,
    manual_flow: float | None = None,
) -> TurbineResult:
    """Calculate all outputs for one XL turbine (16x flow multiplier)."""
    sd = _rotor_size(rotor, size)
    overflow_tier = rotor["overflow_tier"]
    durability = _durability(rotor, size)
    XL = 16  # XL multiplier

    if turbine_type == "steam":
        rotor_eff = sd["steam_tight_eff"] if mode == "Tight" else sd["steam_loose_eff"]
        base_opt_flow = sd["steam_opt_flow_tight"] if mode == "Tight" else sd["steam_opt_flow_loose"]
        opt_flow_raw = base_opt_flow * XL   # L/t (or mB/t when dense)
        display_flow = int(math.floor(opt_flow_raw / 1000)) if is_dense else int(opt_flow_raw)
        opt_flow_calc = display_flow * 1000 if is_dense else opt_flow_raw
        opt_output = int(math.floor(opt_flow_calc * rotor_eff * fuel_value))

        max_flow_raw = int(math.floor(opt_flow_raw * 1.25))
        max_flow_calc = max_flow_raw

        eff_flow_raw = min(max_flow_raw, manual_flow * (1000 if is_dense else 1)) if manual_flow is not None else opt_flow_calc
        flow_eff = 1.0 - abs((eff_flow_raw - opt_flow_calc) / opt_flow_calc) if opt_flow_calc else 0.0
        eff_output = max(1, int(math.floor(eff_flow_raw * flow_eff * rotor_eff * fuel_value)))
        lifetime = _lifetime_xl(durability, eff_output, "steam", mode)
        opt_flow = display_flow

    elif turbine_type == "gas":
        rotor_eff = sd["gas_tight_eff"] if mode == "Tight" else sd["gas_loose_eff"]
        opt_flow_eu_t = sd["gas_opt_flow_tight"] if mode == "Tight" else sd["gas_opt_flow_loose"]
        opt_flow = max(1, int(math.floor(XL * opt_flow_eu_t / fuel_value)))
        opt_output = int(math.floor(opt_flow * rotor_eff * fuel_value))

        max_flow = int(math.floor(opt_flow * 1.25))
        eff_flow = min(max_flow, manual_flow) if manual_flow is not None else opt_flow
        flow_eff = 1.0 - abs((eff_flow - opt_flow) / opt_flow) if opt_flow else 0.0
        eff_output = int(math.floor(eff_flow * flow_eff * rotor_eff * fuel_value))
        lifetime = _lifetime_xl(durability, eff_output, "gas", mode)

    else:  # plasma
        rotor_eff = sd["plasma_tight_eff"] if mode == "Tight" else sd["plasma_loose_eff"]
        opt_flow_eu_t = sd["plasma_opt_flow_tight"] if mode == "Tight" else sd["plasma_opt_flow_loose"]
        opt_flow = max(1, int(math.floor(XL * opt_flow_eu_t * 20 / fuel_value)))
        plasma_power_tight = sd["plasma_power_tight"]
        nerf_mult = min(1.0, (fuel_value * 0.005) ** 2 / plasma_power_tight) if plasma_power_tight else 1.0
        opt_output = int(math.floor(opt_flow * rotor_eff * fuel_value / 20 * nerf_mult))

        max_flow = int(math.floor(opt_flow * 1.25))
        eff_flow = min(max_flow, manual_flow) if manual_flow is not None else opt_flow
        flow_eff = 1.0 - abs((eff_flow - opt_flow) / opt_flow) if opt_flow else 0.0
        eff_output = int(math.floor(opt_output * min(1 + overflow_tier * 1.5, eff_flow / opt_flow) * flow_eff))
        lifetime = _lifetime_xl(durability, eff_output, "plasma", mode)

    return TurbineResult(
        turbine_type=turbine_type,
        mode=mode,
        fuel_type=fuel_type,
        fuel_value=fuel_value,
        opt_flow=opt_flow,
        opt_output_eu_t=opt_output,
        eff_flow=eff_flow,
        eff_output_eu_t=eff_output,
        rotor_eff=rotor_eff,
        max_flow=max_flow if turbine_type != "steam" else int(math.floor(opt_flow * 1.25)),
        min_dynamo_tier_opt=find_dynamo_tier(opt_output),
        min_dynamo_tier_eff=find_dynamo_tier(eff_output),
        lifetime_s=lifetime,
        overflow_tier=overflow_tier,
    )
```

- [ ] **Step 4: Run tests**

```
python -m pytest tests/test_turbine.py -v
```

Expected: all pass. If a value is off by more than the tolerance, compare with the Excel data_only values and adjust the formula.

- [ ] **Step 5: Commit**

```
git add gtnh_turbine_calc/calc/ tests/test_turbine.py
git commit -m "add turbine calculation engine with tests"
```

---

## Task 5: EHE Planner Calculation Engine

**Files:**
- Create: `gtnh_turbine_calc/calc/ehe.py`
- Create: `tests/test_ehe.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_ehe.py
import pytest
from gtnh_turbine_calc.calc.ehe import calc_plasma_ehe, calc_nonxl_ehe
from gtnh_turbine_calc.data.rotors import ROTOR_DATA
from gtnh_turbine_calc.data.fuels import EHE_FUELS

EA = ROTOR_DATA["Energetic Alloy (3)"]

def test_plasma_ehe_helium():
    # Helium Plasma EHE: recipe_output=125L, time=0.8s, parallel=5
    # plasma_output = 125/0.8*5 = 781.25 L/s
    # EHE max input for Helium Plasma from EHE_FUELS
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
```

- [ ] **Step 2: Run to confirm fail**

```
python -m pytest tests/test_ehe.py -v
```

- [ ] **Step 3: Create calc/ehe.py**

```python
import math
from gtnh_turbine_calc.calc.common import find_dynamo_tier
from gtnh_turbine_calc.data.fuels import EHE_FUELS, STEAM_FUELS


def _steam_opt_flow_xl(rotor: dict, size: str, mode: str) -> float:
    """XL turbine optimal steam flow in L/t (dense SC mode, divides by 1000)."""
    sd = rotor["sizes"][size]
    base = sd["steam_opt_flow_tight"] if mode == "Tight" else sd["steam_opt_flow_loose"]
    return math.floor(base * 16 / 1000)  # display L/t (dense)


def _steam_opt_flow_regular(rotor: dict, size: str, mode: str) -> float:
    sd = rotor["sizes"][size]
    return sd["steam_opt_flow_tight"] if mode == "Tight" else sd["steam_opt_flow_loose"]


def _xl_power(rotor: dict, size: str, mode: str, fuel_value: float, flow_lt: float) -> int:
    """XL turbine output EU/t given a steam flow [L/t] (dense units, so multiply by 1000)."""
    sd = rotor["sizes"][size]
    rotor_eff = sd["steam_tight_eff"] if mode == "Tight" else sd["steam_loose_eff"]
    opt_flow_calc = _steam_opt_flow_xl(rotor, size, mode) * 1000  # back to mB/t
    eff_flow = flow_lt * 1000
    flow_eff = 1.0 - abs((eff_flow - opt_flow_calc) / opt_flow_calc) if opt_flow_calc else 0.0
    return int(math.floor(eff_flow * flow_eff * rotor_eff * fuel_value))


def _dense_sc_steam_from_plasma(plasma_type: str, plasma_ls: float, ehe_max_ls: float) -> int:
    """Dense SC Steam [L/t] from plasma EHE.

    Formula (from Excel L77):
    full_ehecount = floor(plasma_ls / ehe_max_ls)
    partial_flow = mod(plasma_ls, ehe_max_ls)
    max_hot_steam = EHE_FUELS[plasma_type]["max_hot_steam_ls"]

    full = floor(floor(floor(max_hot_steam * min(plasma_ls,ehe_max_ls)/ehe_max_ls) / 160) * 160 / 1000)
           * full_ehe_count
    partial = floor(floor(floor(max_hot_steam * partial_flow/ehe_max_ls) / 160) * 160 / 1000)
    """
    if plasma_type not in EHE_FUELS:
        return 0
    fd = EHE_FUELS[plasma_type]
    max_hot_steam = fd.get("max_hot_steam_ls") or 0
    if ehe_max_ls <= 0:
        return 0

    capped = min(plasma_ls, ehe_max_ls)
    full_steam_ls = math.floor(math.floor(max_hot_steam * capped / ehe_max_ls) / 160) * 160
    full_count = math.floor(plasma_ls / ehe_max_ls)
    full_total = math.floor(full_steam_ls / 1000) * full_count

    partial_flow = plasma_ls % ehe_max_ls
    partial_steam_ls = math.floor(math.floor(max_hot_steam * partial_flow / ehe_max_ls) / 160) * 160
    partial_total = math.floor(partial_steam_ls / 1000)

    return int(full_total + partial_total)


def calc_plasma_ehe(
    plasma_type: str,
    recipe_output_l: float,
    recipe_time_s: float,
    parallel_count: float,
    rotor: dict,
    size: str,
    mode: str = "Loose",
) -> dict:
    """Plasma EHE Setup Planner calculation."""
    plasma_output_ls = recipe_output_l / recipe_time_s * parallel_count

    fd = EHE_FUELS.get(plasma_type, {})
    ehe_max_input_ls = fd.get("max_convert_ls") or 0
    ehe_count = math.ceil(plasma_output_ls / ehe_max_input_ls) if ehe_max_input_ls > 0 else 0
    dense_sc_steam_lt = _dense_sc_steam_from_plasma(plasma_type, plasma_output_ls, ehe_max_input_ls)

    sd = rotor["sizes"][size]
    rotor_eff = sd["steam_tight_eff"] if mode == "Tight" else sd["steam_loose_eff"]

    xl_opt_flow = _steam_opt_flow_xl(rotor, size, mode)  # L/t display (dense)
    turbine_count = max(1, math.ceil(dense_sc_steam_lt / xl_opt_flow)) if xl_opt_flow > 0 else 0

    power_sc = _xl_power(rotor, size, mode, STEAM_FUELS["SC Steam"], min(dense_sc_steam_lt, xl_opt_flow))
    power_reg = _xl_power(rotor, size, mode, STEAM_FUELS["Steam"] * 0.5, min(dense_sc_steam_lt, xl_opt_flow))

    return {
        "plasma_output_ls": plasma_output_ls,
        "ehe_max_input_ls": ehe_max_input_ls,
        "ehe_count": ehe_count,
        "dense_sc_steam_lt": dense_sc_steam_lt,
        "rotor_fit": mode,
        "rotor_eff": rotor_eff,
        "turbine_count": turbine_count,
        "xl_opt_flow_lt": xl_opt_flow,
        "power_per_turbine_sc": power_sc,
        "min_dynamo_tier_sc": find_dynamo_tier(power_sc),
    }


def _sc_steam_from_hot_fluid(hot_fluid: str, hot_fluid_ls: float) -> tuple[int, int]:
    """Non-XL EHE: SC Steam [L/t] and SH Steam [L/t] from hot fluid.

    Returns (sc_steam_lt, sh_steam_lt).
    Formula from Excel P73/P74: uses Fuels EHE rows 5-7 (non-plasma fluids).
    """
    NON_PLASMA_EHE = {
        "Lava":             {"max_convert_ls": 160000, "threshold_ls": 80000,  "max_hot_steam_ls": 12800000, "max_normal_steam_ls": 12800000},
        "IC2 Hot Coolant":  {"max_convert_ls": 16000,  "threshold_ls": 8000,   "max_hot_steam_ls": 3200000,  "max_normal_steam_ls": 3200000},
        "Solar Salt (Hot)": {"max_convert_ls": 3200,   "threshold_ls": 1600,   "max_hot_steam_ls": 3200000,  "max_normal_steam_ls": 3200000},
    }
    fd = NON_PLASMA_EHE.get(hot_fluid)
    if not fd:
        return 0, 0

    max_convert = fd["max_convert_ls"]
    threshold = fd["threshold_ls"]
    max_hot = fd["max_hot_steam_ls"]
    max_normal = fd["max_normal_steam_ls"]

    # SC Steam (hot_steam): from full EHEs + partial if above threshold
    capped = min(hot_fluid_ls, max_convert)
    full_steam_ls = math.floor(math.floor(max_hot * capped / max_convert) / 160) * 160
    full_count = math.floor(hot_fluid_ls / max_convert)
    full_sc = full_steam_ls * full_count

    partial_flow = hot_fluid_ls % max_convert
    partial_steam_ls = math.floor(math.floor(max_hot * partial_flow / max_convert) / 160) * 160
    partial_sc = partial_steam_ls if partial_flow >= threshold else 0

    sc_steam_lt = int(full_sc + partial_sc)

    # SH Steam (normal steam): partial EHE below threshold
    partial_sh_ls = math.floor(math.floor(max_normal * partial_flow / max_convert) / 160) * 160
    sh_steam_lt = int(partial_sh_ls if partial_flow < threshold else 0)

    return sc_steam_lt, sh_steam_lt


def calc_nonxl_ehe(
    hot_fluid: str,
    hot_fluid_input_ls: float,
    rotor: dict,
    size: str,
    mode: str = "Loose",
) -> dict:
    """Non-XL EHE Setup Planner calculation."""
    sc_steam_lt, sh_steam_lt = _sc_steam_from_hot_fluid(hot_fluid, hot_fluid_input_ls)

    sd = rotor["sizes"][size]
    rotor_eff = sd["steam_tight_eff"] if mode == "Tight" else sd["steam_loose_eff"]
    opt_flow = sd["steam_opt_flow_tight"] if mode == "Tight" else sd["steam_opt_flow_loose"]

    sc_turbine_count = max(1, math.ceil(sc_steam_lt / opt_flow)) if sc_steam_lt and opt_flow else 0
    sh_turbine_count = max(1, math.ceil((sc_steam_lt + sh_steam_lt) / opt_flow)) if opt_flow else 0

    power_sc = int(math.floor(min(sc_steam_lt, opt_flow) * rotor_eff * STEAM_FUELS["SC Steam"]))
    power_reg = int(math.floor(min(sc_steam_lt + sh_steam_lt, opt_flow) * rotor_eff * STEAM_FUELS["Steam"]))

    ehe_count = math.ceil(hot_fluid_input_ls / {
        "Lava": 160000, "IC2 Hot Coolant": 16000, "Solar Salt (Hot)": 3200
    }.get(hot_fluid, 1))

    return {
        "total_sc_steam_lt": sc_steam_lt,
        "total_sh_steam_lt": sh_steam_lt,
        "rotor_fit": mode,
        "rotor_eff": rotor_eff,
        "opt_flow_lt": opt_flow,
        "sc_turbine_count": sc_turbine_count,
        "sh_turbine_count": sh_turbine_count,
        "power_per_sc_turbine": power_sc,
        "power_per_reg_turbine": power_reg,
        "min_dynamo_tier_sc": find_dynamo_tier(power_sc),
        "min_dynamo_tier_reg": find_dynamo_tier(power_reg),
        "ehe_count": ehe_count,
    }
```

- [ ] **Step 4: Run tests**

```
python -m pytest tests/test_ehe.py -v
```

Expected: all pass (adjust tolerances if needed based on Excel data_only values).

- [ ] **Step 5: Commit**

```
git add gtnh_turbine_calc/calc/ehe.py tests/test_ehe.py
git commit -m "add EHE planner calculation engine"
```

---

## Task 6: Base App Window + Sidebar

**Files:**
- Create: `gtnh_turbine_calc/app.py`

- [ ] **Step 1: Create app.py**

```python
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SIDEBAR_BG = "#111827"
MAIN_BG = "#0d1117"
ACCENT = "#e94560"
SIDEBAR_WIDTH = 160

NAV_ITEMS = [
    ("⚡  Calculator",  "calculator"),
    ("🔥  EHE Planner", "ehe"),
    ("💧  Steam Gen",   "steam_gen"),
    ("⛽  Fuels",       "fuels"),
    ("🔩  Rotors",      "rotors"),
]


class TurbineCalcApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GTNH Large Turbine Calculator")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        self.configure(fg_color=MAIN_BG)

        self._frames: dict[str, ctk.CTkFrame] = {}
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._current_tab = "calculator"

        self._build_sidebar()
        self._build_content_area()
        self._switch_tab("calculator")

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=SIDEBAR_WIDTH, fg_color=SIDEBAR_BG, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        title = ctk.CTkLabel(sidebar, text="GTNH\nTurbines", font=ctk.CTkFont(size=13, weight="bold"),
                              text_color="#e94560")
        title.pack(pady=(20, 16), padx=8)

        for label, key in NAV_ITEMS:
            btn = ctk.CTkButton(
                sidebar, text=label, anchor="w",
                font=ctk.CTkFont(size=12),
                fg_color="transparent", hover_color="#1f2937",
                text_color="#9ca3af", corner_radius=6, height=36,
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_buttons[key] = btn

        version = ctk.CTkLabel(sidebar, text="v2.7.0-2.8.4", font=ctk.CTkFont(size=9),
                                text_color="#374151")
        version.pack(side="bottom", pady=10)

    def _build_content_area(self):
        self._content = ctk.CTkFrame(self, fg_color=MAIN_BG, corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        # Lazy-import tabs to keep startup fast
        from gtnh_turbine_calc.ui.calculator import CalculatorTab
        from gtnh_turbine_calc.ui.ehe_planner import EHEPlannerTab
        from gtnh_turbine_calc.ui.steam_gen_tab import SteamGenTab
        from gtnh_turbine_calc.ui.fuels_ref import FuelsRefTab
        from gtnh_turbine_calc.ui.rotors_ref import RotorsRefTab

        tab_classes = {
            "calculator": CalculatorTab,
            "ehe":        EHEPlannerTab,
            "steam_gen":  SteamGenTab,
            "fuels":      FuelsRefTab,
            "rotors":     RotorsRefTab,
        }
        for key, cls in tab_classes.items():
            frame = cls(self._content)
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._frames[key] = frame

    def _switch_tab(self, key: str):
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg_color=ACCENT, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="#9ca3af")
        self._frames[key].lift()
        self._current_tab = key
```

- [ ] **Step 2: Create placeholder tabs so the app starts**

Create each tab file with a minimal placeholder class:

```python
# gtnh_turbine_calc/ui/calculator.py
import customtkinter as ctk

class CalculatorTab(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        ctk.CTkLabel(self, text="Calculator — coming soon").pack(pady=20)
```

Repeat for `ehe_planner.py`, `steam_gen_tab.py`, `fuels_ref.py`, `rotors_ref.py` (changing class name and label).

- [ ] **Step 3: Run the app and verify sidebar works**

```
python -m gtnh_turbine_calc.main
```

Expected: window opens, sidebar shows 5 nav items, clicking each switches content area.

- [ ] **Step 4: Commit**

```
git add gtnh_turbine_calc/app.py gtnh_turbine_calc/ui/
git commit -m "add base CTk window with sidebar navigation and tab placeholders"
```

---

## Task 7: Reusable UI Widgets

**Files:**
- Create: `gtnh_turbine_calc/ui/widgets.py`

- [ ] **Step 1: Create widgets.py**

```python
import customtkinter as ctk

CARD_BG = "#111827"
RESULT_LABEL_COLOR = "#6b7280"
GREEN = "#4ade80"
YELLOW = "#facc15"
PURPLE = "#c084fc"
ORANGE = "#fb923c"
CYAN = "#00d4ff"


class ResultRow(ctk.CTkFrame):
    """One label=value row inside a turbine card."""
    def __init__(self, master, label: str, value_color: str = GREEN, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._label = ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=11),
                                   text_color=RESULT_LABEL_COLOR, anchor="w")
        self._label.pack(side="left", padx=(0, 8))
        self._value = ctk.CTkLabel(self, text="—", font=ctk.CTkFont(size=11, weight="bold"),
                                   text_color=value_color, anchor="e")
        self._value.pack(side="right")

    def set(self, text: str):
        self._value.configure(text=text)


class ToggleButton(ctk.CTkFrame):
    """Two-option toggle (e.g. Tight/Loose, Optimal/Manual)."""
    def __init__(self, master, options: list[str], command=None, **kwargs):
        super().__init__(master, fg_color="#1f2937", corner_radius=6, **kwargs)
        self._options = options
        self._command = command
        self._selected = options[0]
        self._buttons: dict[str, ctk.CTkButton] = {}
        for opt in options:
            btn = ctk.CTkButton(
                self, text=opt, width=64, height=26,
                font=ctk.CTkFont(size=10),
                fg_color="transparent", hover_color="#374151",
                text_color="#6b7280", corner_radius=4,
                command=lambda o=opt: self._select(o),
            )
            btn.pack(side="left", padx=2, pady=2)
            self._buttons[opt] = btn
        self._select(options[0], notify=False)

    def _select(self, opt: str, notify: bool = True):
        self._selected = opt
        for o, btn in self._buttons.items():
            if o == opt:
                btn.configure(fg_color="#1e40af", text_color="#93c5fd")
            else:
                btn.configure(fg_color="transparent", text_color="#6b7280")
        if notify and self._command:
            self._command(opt)

    def get(self) -> str:
        return self._selected

    def set(self, opt: str):
        self._select(opt, notify=False)


class LabeledDropdown(ctk.CTkFrame):
    """Label + CTkComboBox stacked vertically."""
    def __init__(self, master, label: str, values: list[str], command=None, width=160, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text=label, font=ctk.CTkFont(size=9),
                     text_color="#9ca3af").pack(anchor="w")
        self._combo = ctk.CTkComboBox(
            self, values=values, width=width, height=28,
            font=ctk.CTkFont(size=10),
            fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937",
            text_color=CYAN,
            command=command,
        )
        self._combo.pack(anchor="w", pady=(2, 0))
        if values:
            self._combo.set(values[0])

    def get(self) -> str:
        return self._combo.get()

    def set(self, val: str):
        self._combo.set(val)


class TurbineCard(ctk.CTkFrame):
    """Card for one turbine with inputs and result rows."""
    def __init__(self, master, title: str, accent_color: str, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=8, **kwargs)
        self.configure(border_width=0)
        # Color strip at top
        self._strip = ctk.CTkFrame(self, height=3, fg_color=accent_color, corner_radius=0)
        self._strip.pack(fill="x")
        self._title = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=11, weight="bold"),
                                    text_color=accent_color, anchor="w")
        self._title.pack(anchor="w", padx=10, pady=(8, 4))
        self._inputs_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._inputs_frame.pack(fill="x", padx=10, pady=4)
        self._sep = ctk.CTkFrame(self, height=1, fg_color="#1f2937")
        self._sep.pack(fill="x", padx=10, pady=4)
        self._results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._results_frame.pack(fill="x", padx=10, pady=(0, 10))

    @property
    def inputs(self) -> ctk.CTkFrame:
        return self._inputs_frame

    @property
    def results(self) -> ctk.CTkFrame:
        return self._results_frame


class SearchableTable(ctk.CTkFrame):
    """Scrollable table with a search bar at the top."""
    def __init__(self, master, columns: list[tuple[str, int]], **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        self._columns = columns
        self._all_rows: list[list[str]] = []

        search_bar = ctk.CTkFrame(self, fg_color="#111827")
        search_bar.pack(fill="x", padx=0, pady=(0, 1))
        ctk.CTkLabel(search_bar, text="🔍", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 4))
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._filter())
        entry = ctk.CTkEntry(search_bar, textvariable=self._search_var,
                             placeholder_text="Search...", height=32,
                             fg_color="#1f2937", border_color="#374151",
                             font=ctk.CTkFont(size=11))
        entry.pack(side="left", fill="x", expand=True, padx=8, pady=6)

        # Header
        header = ctk.CTkFrame(self, fg_color="#1f2937", height=30)
        header.pack(fill="x")
        for col_name, col_width in columns:
            ctk.CTkLabel(header, text=col_name, width=col_width,
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color="#9ca3af", anchor="w").pack(side="left", padx=4)

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="#0d1117")
        self._scroll.pack(fill="both", expand=True)
        self._row_frames: list[ctk.CTkFrame] = []

    def load(self, rows: list[list[str]]):
        self._all_rows = rows
        self._filter()

    def _filter(self):
        query = self._search_var.get().lower()
        for f in self._row_frames:
            f.destroy()
        self._row_frames.clear()
        for row_data in self._all_rows:
            if query and not any(query in str(v).lower() for v in row_data):
                continue
            row_frame = ctk.CTkFrame(self._scroll, fg_color="transparent", height=26)
            row_frame.pack(fill="x", pady=1)
            for i, (_, width) in enumerate(self._columns):
                val = row_data[i] if i < len(row_data) else ""
                ctk.CTkLabel(row_frame, text=str(val), width=width,
                             font=ctk.CTkFont(size=10),
                             text_color="#d1d5db", anchor="w").pack(side="left", padx=4)
            self._row_frames.append(row_frame)
```

- [ ] **Step 2: Verify widgets import without errors**

```
python -c "from gtnh_turbine_calc.ui.widgets import TurbineCard, ResultRow, ToggleButton, SearchableTable; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```
git add gtnh_turbine_calc/ui/widgets.py
git commit -m "add reusable UI widgets: TurbineCard, ResultRow, ToggleButton, SearchableTable"
```

---

## Task 8: Calculator Tab

**Files:**
- Modify: `gtnh_turbine_calc/ui/calculator.py`

- [ ] **Step 1: Replace calculator.py with full implementation**

```python
import math
import customtkinter as ctk

from gtnh_turbine_calc.data.rotors import ROTOR_DATA, ROTOR_DISPLAY_NAMES, SIZE_DATA
from gtnh_turbine_calc.data.fuels import (
    STEAM_FUELS, GAS_FUELS, GAS_FUEL_NAMES, PLASMA_FUELS, PLASMA_FUEL_NAMES
)
from gtnh_turbine_calc.calc.turbine import calc_regular_turbine, calc_xl_turbine
from gtnh_turbine_calc.calc.common import dynamo_amps
from gtnh_turbine_calc.ui.widgets import (
    TurbineCard, ResultRow, ToggleButton, LabeledDropdown, YELLOW, GREEN, PURPLE, ORANGE
)

CARD_BG = "#111827"
SECTION_BG = "#0d1117"

STEAM_COLORS = {"Steam": "#3b82f6", "SH Steam": "#60a5fa", "SC Steam": "#93c5fd"}
GAS_COLOR = "#f59e0b"
PLASMA_COLOR = "#a855f7"


def _fmt_flow(flow: float, unit: str) -> str:
    return f"{flow:,.0f} {unit}"


def _fmt_lifetime(seconds: float) -> str:
    days = seconds / 3600 / 24
    if days >= 1:
        return f"{days:.2f} days"
    hours = seconds / 3600
    return f"{hours:.1f} h"


def _fmt_dynamo(eu_t: float, tier: str) -> str:
    from gtnh_turbine_calc.calc.common import DYNAMO_TIERS
    voltage = dict(DYNAMO_TIERS).get(tier, 1)
    amps = round(eu_t / voltage, 3)
    return f"{amps} A [{tier}]"


class RegularTurbineCard(ctk.CTkFrame):
    def __init__(self, master, turbine_type: str, accent: str, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=8, **kwargs)
        self._type = turbine_type
        self._accent = accent
        self._rotor_ref: list[dict] = [{}]  # reference to shared rotor data
        self._size_ref: list[str] = ["Normal"]
        self._build()

    def _build(self):
        strip = ctk.CTkFrame(self, height=3, fg_color=self._accent, corner_radius=0)
        strip.pack(fill="x")
        icons = {"steam": "💨", "gas": "🔥", "plasma": "⚛"}
        titles = {"steam": "Large Steam Turbine", "gas": "Large Gas Turbine", "plasma": "Large Plasma Gen"}
        ctk.CTkLabel(self, text=f"{icons[self._type]}  {titles[self._type]}",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self._accent, anchor="w").pack(anchor="w", padx=10, pady=(8, 6))

        # Mode toggle
        mode_row = ctk.CTkFrame(self, fg_color="transparent")
        mode_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(mode_row, text="Mode", font=ctk.CTkFont(size=9),
                     text_color="#6b7280", width=60, anchor="w").pack(side="left")
        self._mode_toggle = ToggleButton(mode_row, ["Tight", "Loose"], command=self._recalc)
        self._mode_toggle.pack(side="left")

        # Fuel dropdown
        fuel_row = ctk.CTkFrame(self, fg_color="transparent")
        fuel_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(fuel_row, text="Fuel", font=ctk.CTkFont(size=9),
                     text_color="#6b7280", width=60, anchor="w").pack(side="left")
        fuel_names = {"steam": list(STEAM_FUELS), "gas": GAS_FUEL_NAMES, "plasma": PLASMA_FUEL_NAMES}
        self._fuel_combo = ctk.CTkComboBox(
            fuel_row, values=fuel_names[self._type], width=170, height=26,
            font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937", text_color="#00d4ff",
            command=lambda _: self._recalc(),
        )
        self._fuel_combo.pack(side="left")
        self._fuel_combo.set(fuel_names[self._type][0])

        # Effective flow mode toggle
        eff_row = ctk.CTkFrame(self, fg_color="transparent")
        eff_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(eff_row, text="Flow", font=ctk.CTkFont(size=9),
                     text_color="#6b7280", width=60, anchor="w").pack(side="left")
        self._flow_toggle = ToggleButton(eff_row, ["Optimal", "Manual"], command=self._on_flow_mode)
        self._flow_toggle.pack(side="left")

        self._manual_entry = ctk.CTkEntry(self, width=100, height=24,
                                          placeholder_text="L/t or L/s",
                                          font=ctk.CTkFont(size=10),
                                          fg_color="#1f2937", border_color="#374151")
        # Hidden by default
        self._manual_visible = False

        # Separator
        ctk.CTkFrame(self, height=1, fg_color="#1f2937").pack(fill="x", padx=10, pady=6)

        # Results
        unit = "L/s" if self._type == "plasma" else "L/t"
        self._row_opt_flow  = self._make_result(f"Opt. Flow [{unit}]", YELLOW)
        self._row_output    = self._make_result("Output [EU/t]", GREEN)
        self._row_dynamo    = self._make_result("Dynamo (Opt)", PURPLE)
        self._row_eff_flow  = self._make_result(f"Eff. Flow [{unit}]", YELLOW)
        self._row_eff_out   = self._make_result("Eff. Output [EU/t]", GREEN)
        self._row_eff_dyn   = self._make_result("Dynamo (Eff)", PURPLE)
        self._row_lifetime  = self._make_result("Rotor Lifetime", ORANGE)

    def _make_result(self, label: str, color: str) -> ResultRow:
        from gtnh_turbine_calc.ui.widgets import ResultRow
        row = ResultRow(self, label=label, value_color=color)
        row.pack(fill="x", padx=10, pady=1)
        return row

    def _on_flow_mode(self, mode: str):
        if mode == "Manual" and not self._manual_visible:
            self._manual_entry.pack(padx=10, pady=(0, 4))
            self._manual_entry.bind("<KeyRelease>", lambda _: self._recalc())
            self._manual_visible = True
        elif mode == "Optimal" and self._manual_visible:
            self._manual_entry.pack_forget()
            self._manual_visible = False
        self._recalc()

    def set_rotor(self, rotor: dict, size: str):
        self._rotor_ref[0] = rotor
        self._size_ref[0] = size
        self._recalc()

    def _recalc(self, *_):
        rotor = self._rotor_ref[0]
        if not rotor:
            return
        size = self._size_ref[0]
        mode = self._mode_toggle.get()
        fuel_type = self._fuel_combo.get()

        if self._type == "steam":
            fuel_val = STEAM_FUELS.get(fuel_type, 0.5)
        elif self._type == "gas":
            fuel_val = GAS_FUELS.get(fuel_type, {}).get("eu_per_l", 1)
        else:
            fuel_val = PLASMA_FUELS.get(fuel_type, 81920)

        manual_flow = None
        if self._flow_toggle.get() == "Manual":
            try:
                manual_flow = float(self._manual_entry.get())
            except ValueError:
                manual_flow = None

        try:
            r = calc_regular_turbine(self._type, rotor, size, mode, fuel_type, fuel_val, manual_flow)
        except Exception:
            return

        unit = "L/s" if self._type == "plasma" else "L/t"
        self._row_opt_flow.set(f"{r.opt_flow:,.0f} {unit}")
        self._row_output.set(f"{r.opt_output_eu_t:,} EU/t")
        self._row_dynamo.set(_fmt_dynamo(r.opt_output_eu_t, r.min_dynamo_tier_opt))
        self._row_eff_flow.set(f"{r.eff_flow:,.0f} {unit}")
        self._row_eff_out.set(f"{r.eff_output_eu_t:,} EU/t")
        self._row_eff_dyn.set(_fmt_dynamo(r.eff_output_eu_t, r.min_dynamo_tier_eff))
        self._row_lifetime.set(_fmt_lifetime(r.lifetime_s))


class XLTurbineCard(ctk.CTkFrame):
    """XL Turbo turbine card."""
    def __init__(self, master, turbine_type: str, accent: str, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=8, **kwargs)
        self._type = turbine_type
        self._accent = accent
        self._rotor_ref: list[dict] = [{}]
        self._size_ref: list[str] = ["Normal"]
        self._build()

    def _build(self):
        strip = ctk.CTkFrame(self, height=3, fg_color=self._accent, corner_radius=0)
        strip.pack(fill="x")
        titles = {
            "steam": "XL Turbo SC Steam Turbine",
            "gas":   "XL Turbo Gas Turbine",
            "plasma":"XL Turbo Plasma Turbine",
        }
        ctk.CTkLabel(self, text=titles[self._type],
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=self._accent, anchor="w").pack(anchor="w", padx=10, pady=(8, 6))

        mode_row = ctk.CTkFrame(self, fg_color="transparent")
        mode_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(mode_row, text="Mode", font=ctk.CTkFont(size=9),
                     text_color="#6b7280", width=60, anchor="w").pack(side="left")
        self._mode_toggle = ToggleButton(mode_row, ["Tight", "Loose"], command=self._recalc)
        self._mode_toggle.pack(side="left")

        fuel_row = ctk.CTkFrame(self, fg_color="transparent")
        fuel_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(fuel_row, text="Fuel", font=ctk.CTkFont(size=9),
                     text_color="#6b7280", width=60, anchor="w").pack(side="left")

        if self._type == "steam":
            fuel_names = ["SC Steam"]
            self._dense_var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(fuel_row, text="Dense", variable=self._dense_var,
                            font=ctk.CTkFont(size=9), command=self._recalc).pack(side="right")
        elif self._type == "gas":
            fuel_names = [k for k, v in GAS_FUELS.items() if v["xlgt"]]
        else:
            fuel_names = PLASMA_FUEL_NAMES

        self._fuel_combo = ctk.CTkComboBox(
            fuel_row, values=fuel_names, width=140, height=26,
            font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937", text_color="#00d4ff",
            command=lambda _: self._recalc(),
        )
        self._fuel_combo.pack(side="left")
        self._fuel_combo.set(fuel_names[0])

        ctk.CTkFrame(self, height=1, fg_color="#1f2937").pack(fill="x", padx=10, pady=6)

        unit = "L/s" if self._type == "plasma" else "L/t"
        self._row_flow    = self._make_result(f"Opt. Flow [{unit}]", YELLOW)
        self._row_output  = self._make_result("Output [EU/t]", GREEN)
        self._row_dynamo  = self._make_result("Dynamo", PURPLE)
        self._row_life    = self._make_result("Rotor Lifetime", ORANGE)

    def _make_result(self, label: str, color: str) -> ResultRow:
        from gtnh_turbine_calc.ui.widgets import ResultRow
        row = ResultRow(self, label=label, value_color=color)
        row.pack(fill="x", padx=10, pady=1)
        return row

    def set_rotor(self, rotor: dict, size: str):
        self._rotor_ref[0] = rotor
        self._size_ref[0] = size
        self._recalc()

    def _recalc(self, *_):
        rotor = self._rotor_ref[0]
        if not rotor:
            return
        size = self._size_ref[0]
        mode = self._mode_toggle.get()
        fuel_type = self._fuel_combo.get()
        is_dense = getattr(self, "_dense_var", None)
        is_dense = is_dense.get() if is_dense else False

        if self._type == "steam":
            fuel_val = STEAM_FUELS.get(fuel_type, 1.0)
        elif self._type == "gas":
            fuel_val = GAS_FUELS.get(fuel_type, {}).get("eu_per_l", 1)
        else:
            fuel_val = PLASMA_FUELS.get(fuel_type, 81920)

        try:
            r = calc_xl_turbine(self._type, rotor, size, mode, fuel_type, fuel_val, is_dense)
        except Exception:
            return

        unit = "L/s" if self._type == "plasma" else "L/t"
        self._row_flow.set(f"{r.opt_flow:,.0f} {unit}")
        self._row_output.set(f"{r.opt_output_eu_t:,} EU/t")
        self._row_dynamo.set(_fmt_dynamo(r.opt_output_eu_t, r.min_dynamo_tier_opt))
        self._row_life.set(_fmt_lifetime(r.lifetime_s))


class CalculatorTab(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        self._xl_visible = False
        self._build()

    def _build(self):
        # Shared rotor settings
        shared = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8)
        shared.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(shared, text="SHARED ROTOR SETTINGS",
                     font=ctk.CTkFont(size=9), text_color="#6b7280").pack(anchor="w", padx=12, pady=(10, 4))

        rotor_row = ctk.CTkFrame(shared, fg_color="transparent")
        rotor_row.pack(fill="x", padx=12, pady=(0, 10))

        self._rotor_combo = ctk.CTkComboBox(
            rotor_row, values=ROTOR_DISPLAY_NAMES, width=220, height=30,
            font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937", text_color="#00d4ff",
            command=lambda _: self._on_rotor_change(),
        )
        self._rotor_combo.pack(side="left", padx=(0, 12))
        self._rotor_combo.set(ROTOR_DISPLAY_NAMES[0])

        self._size_toggle = ToggleButton(rotor_row, ["Small", "Normal", "Large", "Huge"],
                                         command=lambda _: self._on_rotor_change())
        self._size_toggle.pack(side="left", padx=(0, 12))
        self._size_toggle.set("Normal")

        self._lbl_eff = ctk.CTkLabel(rotor_row, text="Eff: —", font=ctk.CTkFont(size=10),
                                      text_color=GREEN)
        self._lbl_eff.pack(side="left", padx=8)
        self._lbl_dur = ctk.CTkLabel(rotor_row, text="Dur: —", font=ctk.CTkFont(size=10),
                                      text_color=YELLOW)
        self._lbl_dur.pack(side="left", padx=8)

        # Regular turbine cards
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=16, pady=4)
        cards_frame.columnconfigure((0, 1, 2), weight=1, uniform="card")

        self._steam_card  = RegularTurbineCard(cards_frame, "steam",  "#3b82f6")
        self._gas_card    = RegularTurbineCard(cards_frame, "gas",    "#f59e0b")
        self._plasma_card = RegularTurbineCard(cards_frame, "plasma", "#a855f7")
        self._steam_card.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self._gas_card.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        self._plasma_card.grid(row=0, column=2, sticky="nsew", padx=4, pady=4)

        # XL section toggle
        xl_header = ctk.CTkButton(
            self, text="▶  XL Turbo Turbines  (click to expand)",
            font=ctk.CTkFont(size=11), fg_color="#111827", hover_color="#1f2937",
            text_color="#9ca3af", corner_radius=6, height=36, anchor="w",
            command=self._toggle_xl,
        )
        xl_header.pack(fill="x", padx=16, pady=(8, 0))
        self._xl_header_btn = xl_header

        # XL cards (hidden initially)
        self._xl_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._xl_frame.columnconfigure((0, 1, 2), weight=1, uniform="xl")
        self._xl_steam  = XLTurbineCard(self._xl_frame, "steam",  "#93c5fd")
        self._xl_gas    = XLTurbineCard(self._xl_frame, "gas",    "#fcd34d")
        self._xl_plasma = XLTurbineCard(self._xl_frame, "plasma", "#c084fc")
        self._xl_steam.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self._xl_gas.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        self._xl_plasma.grid(row=0, column=2, sticky="nsew", padx=4, pady=4)

        self._on_rotor_change()

    def _toggle_xl(self):
        if self._xl_visible:
            self._xl_frame.pack_forget()
            self._xl_header_btn.configure(text="▶  XL Turbo Turbines  (click to expand)")
            self._xl_visible = False
        else:
            self._xl_frame.pack(fill="x", padx=16, pady=(0, 16))
            self._xl_header_btn.configure(text="▼  XL Turbo Turbines")
            self._xl_visible = True

    def _on_rotor_change(self, *_):
        name = self._rotor_combo.get()
        size = self._size_toggle.get()
        rotor = ROTOR_DATA.get(name, {})
        if not rotor:
            return
        sd = rotor["sizes"][size]
        dur = rotor["base_durability"] * sd["dur_mult"]
        self._lbl_eff.configure(text=f"Eff (tight): {sd['steam_tight_eff']:.3f}")
        self._lbl_dur.configure(text=f"Dur: {dur:,}")

        for card in [self._steam_card, self._gas_card, self._plasma_card,
                     self._xl_steam, self._xl_gas, self._xl_plasma]:
            card.set_rotor(rotor, size)
```

- [ ] **Step 2: Run the app and test Calculator tab**

```
python -m gtnh_turbine_calc.main
```

Expected:
- Calculator tab shows 3 turbine cards.
- Changing rotor material updates all cards.
- Changing mode/fuel shows updated EU/t values.
- XL section expands on click.
- Values match the Excel defaults: Steam Tight = 660 EU/t, Gas Benzene = 1188 EU/t.

- [ ] **Step 3: Commit**

```
git add gtnh_turbine_calc/ui/calculator.py
git commit -m "implement Calculator tab with regular and XL turbine cards"
```

---

## Task 9: EHE Planner Tab

**Files:**
- Modify: `gtnh_turbine_calc/ui/ehe_planner.py`

- [ ] **Step 1: Replace ehe_planner.py**

```python
import customtkinter as ctk
from gtnh_turbine_calc.data.rotors import ROTOR_DATA, ROTOR_DISPLAY_NAMES
from gtnh_turbine_calc.data.fuels import EHE_FUEL_NAMES
from gtnh_turbine_calc.calc.ehe import calc_plasma_ehe, calc_nonxl_ehe
from gtnh_turbine_calc.ui.widgets import ResultRow, LabeledDropdown, YELLOW, GREEN, PURPLE, ORANGE

CARD_BG = "#111827"

NON_XL_HOT_FLUIDS = ["Lava", "IC2 Hot Coolant", "Solar Salt (Hot)"]


class EHEPlannerTab(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        self._build()

    def _build(self):
        # Shared rotor selector
        shared = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8)
        shared.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(shared, text="Rotor (shared with Calculator tab)",
                     font=ctk.CTkFont(size=9), text_color="#6b7280").pack(anchor="w", padx=12, pady=(8, 2))
        rotor_row = ctk.CTkFrame(shared, fg_color="transparent")
        rotor_row.pack(fill="x", padx=12, pady=(0, 10))
        self._rotor_combo = ctk.CTkComboBox(
            rotor_row, values=ROTOR_DISPLAY_NAMES, width=220, height=30,
            font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937", text_color="#00d4ff",
            command=lambda _: self._recalc_all(),
        )
        self._rotor_combo.pack(side="left", padx=(0, 12))
        self._rotor_combo.set(ROTOR_DISPLAY_NAMES[0])

        self._size_var = ctk.StringVar(value="Normal")
        for s in ["Small", "Normal", "Large", "Huge"]:
            ctk.CTkRadioButton(rotor_row, text=s, variable=self._size_var, value=s,
                               font=ctk.CTkFont(size=10), command=self._recalc_all).pack(side="left", padx=4)

        two_cols = ctk.CTkFrame(self, fg_color="transparent")
        two_cols.pack(fill="x", padx=16, pady=4)
        two_cols.columnconfigure((0, 1), weight=1, uniform="ehe")

        # Plasma EHE planner (left)
        self._build_plasma_ehe(two_cols, column=0)
        # Non-XL EHE planner (right)
        self._build_nonxl_ehe(two_cols, column=1)

        self._recalc_all()

    def _make_input_row(self, parent, label: str, default: str = "") -> ctk.CTkEntry:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(row, text=label, width=160, font=ctk.CTkFont(size=10),
                     text_color="#9ca3af", anchor="w").pack(side="left")
        entry = ctk.CTkEntry(row, width=100, height=26,
                             font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151")
        entry.pack(side="right")
        if default:
            entry.insert(0, default)
        entry.bind("<KeyRelease>", lambda _: self._recalc_all())
        return entry

    def _build_plasma_ehe(self, parent, column: int):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=8)
        card.grid(row=0, column=column, sticky="nsew", padx=4, pady=4)
        ctk.CTkFrame(card, height=3, fg_color="#a855f7", corner_radius=0).pack(fill="x")
        ctk.CTkLabel(card, text="⚛  Plasma EHE Setup Planner",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#a855f7", anchor="w").pack(anchor="w", padx=10, pady=(8, 6))

        # Fuel dropdown
        fuel_row = ctk.CTkFrame(card, fg_color="transparent")
        fuel_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(fuel_row, text="Plasma Type", width=120, font=ctk.CTkFont(size=10),
                     text_color="#9ca3af", anchor="w").pack(side="left")
        self._plasma_fuel_combo = ctk.CTkComboBox(
            fuel_row, values=EHE_FUEL_NAMES, width=170, height=26,
            font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937", text_color="#00d4ff",
            command=lambda _: self._recalc_all(),
        )
        self._plasma_fuel_combo.pack(side="right")
        if EHE_FUEL_NAMES:
            self._plasma_fuel_combo.set(EHE_FUEL_NAMES[0])

        self._plasma_output_l  = self._make_input_row(card, "Recipe Output [L]", "125")
        self._plasma_time_s    = self._make_input_row(card, "Recipe Time [s]", "0.8")
        self._plasma_eu_t      = self._make_input_row(card, "EU/t per Recipe", "32720")
        self._plasma_parallels = self._make_input_row(card, "Parallel Count", "5")

        ctk.CTkFrame(card, height=1, fg_color="#1f2937").pack(fill="x", padx=10, pady=6)

        self._plasma_r_output   = self._make_result(card, "Plasma Output [L/s]", YELLOW)
        self._plasma_r_ehe_max  = self._make_result(card, "EHE Max Input [L/s]", "#9ca3af")
        self._plasma_r_ehe_cnt  = self._make_result(card, "EHE Count", "#9ca3af")
        self._plasma_r_steam    = self._make_result(card, "Dense SC Steam [L/t]", YELLOW)
        self._plasma_r_fit      = self._make_result(card, "Rotor Fit", "#9ca3af")
        self._plasma_r_eff      = self._make_result(card, "Rotor Efficiency", "#9ca3af")
        self._plasma_r_turbs    = self._make_result(card, "Turbine Count", "#9ca3af")
        self._plasma_r_power    = self._make_result(card, "Power/Turbine [EU/t]", GREEN)
        self._plasma_r_dynamo   = self._make_result(card, "Min Dynamo", PURPLE)

    def _build_nonxl_ehe(self, parent, column: int):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=8)
        card.grid(row=0, column=column, sticky="nsew", padx=4, pady=4)
        ctk.CTkFrame(card, height=3, fg_color="#3b82f6", corner_radius=0).pack(fill="x")
        ctk.CTkLabel(card, text="💧  Non-XL EHE Setup Planner",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#3b82f6", anchor="w").pack(anchor="w", padx=10, pady=(8, 6))

        fluid_row = ctk.CTkFrame(card, fg_color="transparent")
        fluid_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(fluid_row, text="Hot Fluid", width=120, font=ctk.CTkFont(size=10),
                     text_color="#9ca3af", anchor="w").pack(side="left")
        self._hot_fluid_combo = ctk.CTkComboBox(
            fluid_row, values=NON_XL_HOT_FLUIDS, width=170, height=26,
            font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937", text_color="#00d4ff",
            command=lambda _: self._recalc_all(),
        )
        self._hot_fluid_combo.pack(side="right")
        self._hot_fluid_combo.set(NON_XL_HOT_FLUIDS[1])  # IC2 Hot Coolant

        self._hot_input_ls = self._make_input_row(card, "Hot Fluid Input [L/s]", "32000000")

        ctk.CTkFrame(card, height=1, fg_color="#1f2937").pack(fill="x", padx=10, pady=6)

        self._nonxl_r_ehe_max  = self._make_result(card, "EHE Max Input [L/s]", "#9ca3af")
        self._nonxl_r_sc       = self._make_result(card, "Total SC Steam [L/t]", YELLOW)
        self._nonxl_r_sh       = self._make_result(card, "Total SH Steam [L/t]", YELLOW)
        self._nonxl_r_fit      = self._make_result(card, "Rotor Fit", "#9ca3af")
        self._nonxl_r_eff      = self._make_result(card, "Rotor Efficiency", "#9ca3af")
        self._nonxl_r_opt_flow = self._make_result(card, "Opt. Flow/Turbine [L/t]", YELLOW)
        self._nonxl_r_sc_cnt   = self._make_result(card, "SC Turbine Count", "#9ca3af")
        self._nonxl_r_sh_cnt   = self._make_result(card, "SH/Reg Turbine Count", "#9ca3af")
        self._nonxl_r_power_sc = self._make_result(card, "Power/SC Turbine [EU/t]", GREEN)
        self._nonxl_r_power_r  = self._make_result(card, "Power/Reg Turbine [EU/t]", GREEN)
        self._nonxl_r_dynamo   = self._make_result(card, "Min Dynamo (Reg)", PURPLE)

    def _make_result(self, parent, label: str, color: str) -> ResultRow:
        row = ResultRow(parent, label=label, value_color=color)
        row.pack(fill="x", padx=10, pady=1)
        return row

    def _get_rotor(self):
        name = self._rotor_combo.get()
        size = self._size_var.get()
        rotor = ROTOR_DATA.get(name, {})
        return rotor, size

    def _recalc_all(self, *_):
        rotor, size = self._get_rotor()
        if not rotor:
            return

        # Plasma EHE
        try:
            ptype = self._plasma_fuel_combo.get()
            r_out = float(self._plasma_output_l.get() or 125)
            r_time = float(self._plasma_time_s.get() or 0.8)
            r_par = float(self._plasma_parallels.get() or 5)
            pr = calc_plasma_ehe(ptype, r_out, r_time, r_par, rotor, size)
            self._plasma_r_output.set(f"{pr['plasma_output_ls']:.2f} L/s")
            self._plasma_r_ehe_max.set(f"{pr['ehe_max_input_ls']:,} L/s")
            self._plasma_r_ehe_cnt.set(str(pr['ehe_count']))
            self._plasma_r_steam.set(f"{pr['dense_sc_steam_lt']:,} L/t")
            self._plasma_r_fit.set(pr['rotor_fit'])
            self._plasma_r_eff.set(f"{pr['rotor_eff']:.3f}")
            self._plasma_r_turbs.set(str(pr['turbine_count']))
            self._plasma_r_power.set(f"{pr['power_per_turbine_sc']:,} EU/t")
            self._plasma_r_dynamo.set(pr['min_dynamo_tier_sc'])
        except Exception:
            pass

        # Non-XL EHE
        try:
            hf = self._hot_fluid_combo.get()
            hf_ls = float(self._hot_input_ls.get() or 32000000)
            nr = calc_nonxl_ehe(hf, hf_ls, rotor, size)
            self._nonxl_r_ehe_max.set(f"{nr.get('ehe_max_input_ls', '—')}")
            self._nonxl_r_sc.set(f"{nr['total_sc_steam_lt']:,} L/t")
            self._nonxl_r_sh.set(f"{nr['total_sh_steam_lt']:,} L/t")
            self._nonxl_r_fit.set(nr['rotor_fit'])
            self._nonxl_r_eff.set(f"{nr['rotor_eff']:.3f}")
            self._nonxl_r_opt_flow.set(f"{nr['opt_flow_lt']:,} L/t")
            self._nonxl_r_sc_cnt.set(str(nr['sc_turbine_count']))
            self._nonxl_r_sh_cnt.set(str(nr['sh_turbine_count']))
            self._nonxl_r_power_sc.set(f"{nr['power_per_sc_turbine']:,} EU/t")
            self._nonxl_r_power_r.set(f"{nr['power_per_reg_turbine']:,} EU/t")
            self._nonxl_r_dynamo.set(nr['min_dynamo_tier_reg'])
        except Exception:
            pass
```

- [ ] **Step 2: Run and test EHE tab**

```
python -m gtnh_turbine_calc.main
```

Click "EHE Planner" in sidebar. Both planners should show calculated values. Verify Plasma EHE default output with Helium Plasma shows ~2879 Dense SC Steam L/t (±50).

- [ ] **Step 3: Commit**

```
git add gtnh_turbine_calc/ui/ehe_planner.py
git commit -m "implement EHE Planner tab with plasma and non-XL sections"
```

---

## Task 10: Steam Generation Tab

**Files:**
- Modify: `gtnh_turbine_calc/ui/steam_gen_tab.py`

- [ ] **Step 1: Replace steam_gen_tab.py**

```python
import customtkinter as ctk
from gtnh_turbine_calc.data.steam_gen import LHE_SOURCES, WWXL_SOURCES, THERMAL_BOILER_SOURCES

CARD_BG = "#111827"


def _steam_row(parent, name: str, data: dict, is_thermal: bool = False):
    row = ctk.CTkFrame(parent, fg_color="#1f2937", corner_radius=4, height=28)
    row.pack(fill="x", pady=1)
    row.pack_propagate(False)
    cols = [
        (name, 160),
    ]
    if is_thermal:
        cols += [
            (f"{data['max_ls']:,} L/s", 100),
            (data["steam"], 80),
            (f"×{data['ratio']}", 60),
        ]
    else:
        cols += [
            (f"{data['threshold_ls']:,}", 100),
            (f"{data['max_ls']:,}", 100),
            (data["below"], 70),
            (data["above"], 80),
            (f"×{data['ratio_below']}", 60),
            (f"×{data['ratio_above']}", 60),
        ]
    for text, width in cols:
        ctk.CTkLabel(row, text=text, width=width, font=ctk.CTkFont(size=10),
                     text_color="#d1d5db", anchor="w").pack(side="left", padx=4)


def _section(parent, title: str, color: str, headers: list, sources: list, is_thermal: bool = False):
    card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=8)
    card.pack(fill="x", padx=16, pady=6)
    ctk.CTkFrame(card, height=3, fg_color=color, corner_radius=0).pack(fill="x")
    ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=color, anchor="w").pack(anchor="w", padx=10, pady=(8, 4))
    # Header row
    hdr = ctk.CTkFrame(card, fg_color="#374151", corner_radius=4, height=26)
    hdr.pack(fill="x", padx=10, pady=(0, 2))
    hdr.pack_propagate(False)
    for text, width in headers:
        ctk.CTkLabel(hdr, text=text, width=width, font=ctk.CTkFont(size=9, weight="bold"),
                     text_color="#9ca3af", anchor="w").pack(side="left", padx=4)
    for src in sources:
        _steam_row(card, src["name"], src, is_thermal)
    ctk.CTkFrame(card, height=4, fg_color="transparent").pack()


class SteamGenTab(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Steam Generation Reference",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#e94560").pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(self, text="All flows in L/s. Steam output = input × ratio.",
                     font=ctk.CTkFont(size=10), text_color="#6b7280").pack(anchor="w", padx=16, pady=(0, 12))

        lhe_hdrs = [("Source", 160), ("Threshold L/s", 100), ("Max L/s", 100),
                    ("Below thr.", 70), ("Above thr.", 80), ("Ratio↓", 60), ("Ratio↑", 60)]
        _section(self, "Large Heat Exchanger (LHE)", "#3b82f6", lhe_hdrs, LHE_SOURCES)
        _section(self, "Whakawhiti Wera XL (WWXL)", "#60a5fa", lhe_hdrs, WWXL_SOURCES)

        th_hdrs = [("Source", 160), ("Max L/s", 100), ("Steam Type", 80), ("Ratio", 60)]
        _section(self, "Thermal Boiler", "#f59e0b", th_hdrs, THERMAL_BOILER_SOURCES, is_thermal=True)
```

- [ ] **Step 2: Run and check Steam Gen tab shows tables**

```
python -m gtnh_turbine_calc.main
```

Click "Steam Gen". Three tables should appear for LHE, WWXL, and Thermal Boiler.

- [ ] **Step 3: Commit**

```
git add gtnh_turbine_calc/ui/steam_gen_tab.py
git commit -m "implement Steam Generation reference tab"
```

---

## Task 11: Fuels Reference Tab

**Files:**
- Modify: `gtnh_turbine_calc/ui/fuels_ref.py`

- [ ] **Step 1: Replace fuels_ref.py**

```python
import customtkinter as ctk
from gtnh_turbine_calc.data.fuels import STEAM_FUELS, GAS_FUELS, PLASMA_FUELS
from gtnh_turbine_calc.ui.widgets import SearchableTable

CARD_BG = "#111827"


class FuelsRefTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Fuel Reference",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#e94560").pack(anchor="w", padx=16, pady=(16, 8))

        tabs = ctk.CTkTabview(self, fg_color="#111827", segmented_button_fg_color="#111827",
                              segmented_button_selected_color="#e94560",
                              segmented_button_selected_hover_color="#c03050")
        tabs.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Steam Fuels
        steam_tab = tabs.add("Steam")
        steam_tbl = SearchableTable(steam_tab,
                                    columns=[("Type", 200), ("EU/L", 120)])
        steam_tbl.pack(fill="both", expand=True)
        steam_tbl.load([[k, f"{v:.1f}"] for k, v in STEAM_FUELS.items()])

        # Gas Fuels
        gas_tab = tabs.add("Gas")
        gas_tbl = SearchableTable(gas_tab,
                                  columns=[("Name", 220), ("EU/L", 100), ("XLGT", 60)])
        gas_tbl.pack(fill="both", expand=True)
        gas_rows = sorted(
            [[k, f"{v['eu_per_l']:.0f}", "✓" if v["xlgt"] else "✗"]
             for k, v in GAS_FUELS.items()],
            key=lambda r: float(r[1]), reverse=True,
        )
        gas_tbl.load(gas_rows)

        # Plasma Fuels
        plasma_tab = tabs.add("Plasma")
        plasma_tbl = SearchableTable(plasma_tab,
                                     columns=[("Name", 260), ("EU/L", 120)])
        plasma_tbl.pack(fill="both", expand=True)
        plasma_rows = sorted(
            [[k, f"{v:,.0f}"] for k, v in PLASMA_FUELS.items()],
            key=lambda r: float(r[1].replace(",", "")), reverse=True,
        )
        plasma_tbl.load(plasma_rows)
```

- [ ] **Step 2: Run and check Fuels tab**

```
python -m gtnh_turbine_calc.main
```

Click "Fuels". Three sub-tabs (Steam/Gas/Plasma) with searchable tables.

- [ ] **Step 3: Commit**

```
git add gtnh_turbine_calc/ui/fuels_ref.py
git commit -m "implement Fuels reference tab with searchable tables"
```

---

## Task 12: Rotors Reference Tab

**Files:**
- Modify: `gtnh_turbine_calc/ui/rotors_ref.py`

- [ ] **Step 1: Replace rotors_ref.py**

```python
import customtkinter as ctk
from gtnh_turbine_calc.data.rotors import ROTOR_DATA, ROTOR_DISPLAY_NAMES
from gtnh_turbine_calc.ui.widgets import SearchableTable


class RotorsRefTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Rotor Reference",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#e94560").pack(anchor="w", padx=16, pady=(16, 8))

        size_frame = ctk.CTkFrame(self, fg_color="#111827", corner_radius=6)
        size_frame.pack(anchor="w", padx=16, pady=(0, 8))
        ctk.CTkLabel(size_frame, text="Size:", font=ctk.CTkFont(size=10),
                     text_color="#9ca3af").pack(side="left", padx=(10, 4))
        self._size_var = ctk.StringVar(value="Normal")
        for s in ["Small", "Normal", "Large", "Huge"]:
            ctk.CTkRadioButton(size_frame, text=s, variable=self._size_var, value=s,
                               font=ctk.CTkFont(size=10),
                               command=self._reload).pack(side="left", padx=6, pady=6)

        self._table = SearchableTable(self, columns=[
            ("Display Name", 240),
            ("Tier",         50),
            ("Base Dur",     90),
            ("Overflow",     70),
            ("St.Tight Eff", 90),
            ("St.Loose Eff", 90),
            ("St.Opt Flow",  90),
            ("Gas Tight",    80),
            ("Pla Tight",    80),
        ])
        self._table.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self._reload()

    def _reload(self):
        size = self._size_var.get()
        rows = []
        for name in ROTOR_DISPLAY_NAMES:
            rd = ROTOR_DATA[name]
            sd = rd["sizes"][size]
            dur = rd["base_durability"] * sd["dur_mult"]
            rows.append([
                name,
                str(rd["tier"]),
                f"{dur:,}",
                str(rd["overflow_tier"]),
                f"{sd['steam_tight_eff']:.3f}",
                f"{sd['steam_loose_eff']:.3f}",
                f"{sd['steam_opt_flow_tight']:,.0f}",
                f"{sd['gas_tight_eff']:.3f}",
                f"{sd['plasma_tight_eff']:.3f}",
            ])
        self._table.load(rows)
```

- [ ] **Step 2: Run and check Rotors tab**

```
python -m gtnh_turbine_calc.main
```

Click "Rotors". Searchable table with all materials. Size radio buttons change the displayed values.

- [ ] **Step 3: Commit**

```
git add gtnh_turbine_calc/ui/rotors_ref.py
git commit -m "implement Rotors reference tab"
```

---

## Task 13: Final Polish + Packaging

**Files:**
- Create: `gtnh_turbine_calc.bat` (Windows launcher)

- [ ] **Step 1: Verify all tests pass**

```
python -m pytest tests/ -v
```

Expected: all pass.

- [ ] **Step 2: Run the full app and smoke-test every tab**

```
python -m gtnh_turbine_calc.main
```

Check:
- Calculator: steam tight Energetic Alloy Normal = 660 EU/t, gas tight Benzene = 1188 EU/t
- Calculator: XL section expands and shows values
- EHE Planner: both sections populate
- Steam Gen: three tables visible
- Fuels: all three sub-tabs work, search filters results
- Rotors: table loads, size buttons reload

- [ ] **Step 3: Create Windows launcher**

```batch
@echo off
python -m gtnh_turbine_calc.main
pause
```

Save as `run.bat` in project root.

- [ ] **Step 4: Final commit**

```
git add .
git commit -m "complete GTNH Large Turbine Calculator GUI - all tabs implemented"
```

---

## Notes on Verification

After Task 4, compare these values against the Excel (data_only) to confirm the math is correct:

| Config | Expected Output |
|---|---|
| Energetic Alloy Normal, Steam, Tight, Steam fuel | 660 EU/t |
| Energetic Alloy Normal, Gas, Tight, Benzene | 1188 EU/t |
| Energetic Alloy Normal, Plasma, Tight, Helium Plasma (81920 EU/L) | 58572 EU/t |
| Energetic Alloy Normal, XL SC Steam, Loose, Dense | ~67904 EU/t |

If any value differs by more than 1%, re-read the corresponding Excel formula from the Calculator sheet and adjust `calc/turbine.py`.
