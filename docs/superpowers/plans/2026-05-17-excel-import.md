# Excel Import Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `--source excel --file <path>` mode to `scripts/update_web_data.py` to import rotors, fuels, and steam_gen data from the GTNH Excel calculator file into `web/data/<gtnh>/`.

**Architecture:** Extract all Excel parsing into a new `scripts/excel_parser.py` module; extend `update_web_data.py` with a `--source` argument that calls a new `_run_excel()` path using the same diff + confirm + write workflow as the existing Java path.

**Tech Stack:** Python 3.10+, openpyxl, json, pytest

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `scripts/excel_parser.py` | Create | Parse rotors, fuels, steam_gen from .xlsx |
| `scripts/update_web_data.py` | Modify | Add `--source`, `_run_excel()`, `_diff_steam_gen()` |
| `tests/test_excel_parser.py` | Create | Tests against real xlsx file |

---

## Background: Excel Sheet Structure

**Sheet "Rotors"**, data starts at row 4. All values are pre-computed.

Row columns (0-indexed):
- `[8]` display name (e.g. "Carbon (2)")
- `[9]` tier (int)
- `[10]` mining_speed (float)
- `[11]` base_durability (int/float)
- `[12]` overflow_tier (int)

Stats are in groups of 4 (Small, Normal, Large, Huge). The base column index for each stat group (absolute 0-based from col A):
```python
COL_OFFSETS = {
    "steam_tight_eff":       20,   # values at cols 28-31
    "steam_loose_eff":       24,   # values at cols 32-35
    "steam_opt_flow_tight":  28,   # values at cols 36-39
    "steam_opt_flow_loose":  32,   # values at cols 40-43
    "steam_power_tight":     36,   # values at cols 44-47
    "steam_power_loose":     40,   # values at cols 48-51
    "gas_tight_eff":         48,   # values at cols 56-59
    "gas_loose_eff":         52,   # values at cols 60-63
    "gas_opt_flow_tight":    56,   # values at cols 64-67
    "gas_opt_flow_loose":    60,   # values at cols 68-71
    "gas_power_tight":       64,   # values at cols 72-75
    "gas_power_loose":       68,   # values at cols 76-79
    "plasma_tight_eff":      76,   # values at cols 84-87
    "plasma_loose_eff":      80,   # values at cols 88-91
    "plasma_opt_flow_tight": 84,   # values at cols 92-95
    "plasma_opt_flow_loose": 88,   # values at cols 96-99
    "plasma_power_tight":    92,   # values at cols 100-103
    "plasma_power_loose":    96,   # values at cols 104-107
}
```
Formula to get absolute column for a size: `abs_col = base_col + 8 + size_index`
where size_index is 0=Small, 1=Normal, 2=Large, 3=Huge.

**Sheet "Fuels"** (0-indexed columns from col A):
- Steam fuels rows 5-7: `[1]`=name, `[2]`=eu_l
- Gas fuels: `[9]`=name, `[10]`=eu_l, `[11]`=xlgt bool
- Plasma fuels: `[14]`=name, `[15]`=eu_l
- EHE fuels: `[17]`=name, `[18]`=max_convert_ls, `[19]`=threshold_ls, `[20]`=eu_t, `[21]`=coolant, `[22]`=max_coolant_ls, `[23]`=normal_steam, `[24]`=max_normal_steam_ls, `[25]`=hot_steam, `[26]`=max_hot_steam_ls, `[27]`=cooled_fluid, `[28]`=max_cooled_fluid_ls

Steam_gen sections detected by scanning col B (index 1) for header strings, then reading following rows until a blank name:
- `'LHE Conversion'`: cols `[1]`=name, `[2]`=threshold_ls, `[3]`=max_ls, `[4]`=below, `[5]`=above, `[6]`=ratio_below, `[7]`=ratio_above
- `'WWXL Conversion'`: same layout
- `'Thermal Boiler Conversion'`: cols `[1]`=name, `[2]`=max_ls, `[4]`=steam, `[5]`=ratio

---

### Task 1: Create `scripts/excel_parser.py` with `extract_rotors`

**Files:**
- Create: `scripts/excel_parser.py`
- Create: `tests/test_excel_parser.py`

**Excel file path for tests:** `Large Turbine Calculator (2.7.0-2.8.4).xlsx` (repo root)

- [ ] **Step 1: Write the failing test for `extract_rotors`**

Create `tests/test_excel_parser.py`:

```python
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

def test_extract_rotors_carbon_present():
    rotors = extract_rotors(_wb())
    names = [r["name"] for r in rotors]
    assert "Carbon (2)" in names

def test_extract_rotors_carbon_stats():
    rotors = extract_rotors(_wb())
    carbon = next(r for r in rotors if r["name"] == "Carbon (2)")
    assert carbon["tier"] == 2
    assert abs(carbon["mining_speed"] - 1.0) < 1e-6
    assert carbon["base_durability"] == 6400
    assert carbon["overflow_tier"] == 1
    small = carbon["sizes"]["Small"]
    assert abs(small["steam_tight_eff"] - 0.75) < 1e-3
    assert abs(small["gas_tight_eff"] - 0.75) < 1e-3
    assert abs(small["plasma_tight_eff"] - 0.75) < 1e-3

def test_extract_rotors_matches_existing_json():
    """Verify extracted data matches the known-good 2.7 web JSON."""
    rotors = extract_rotors(_wb())
    existing = json.load(open(EXISTING_ROTORS))
    existing_map = {r["name"]: r for r in existing}
    new_map = {r["name"]: r for r in rotors}
    # All names in existing should be present (may have extras in Excel)
    common = set(existing_map) & set(new_map)
    assert len(common) > 100
    for name in list(common)[:10]:  # spot-check 10
        e = existing_map[name]
        n = new_map[name]
        assert e["tier"] == n["tier"], f"{name}: tier mismatch"
        assert abs(e["sizes"]["Small"]["steam_tight_eff"] - n["sizes"]["Small"]["steam_tight_eff"]) < 1e-3, f"{name}: steam_tight_eff Small mismatch"
```

- [ ] **Step 2: Run test to confirm it fails**

```
pytest tests/test_excel_parser.py -v
```

Expected: `ImportError: cannot import name 'extract_rotors' from 'scripts.excel_parser'` (or ModuleNotFoundError)

- [ ] **Step 3: Create `scripts/excel_parser.py` with `extract_rotors`**

```python
import openpyxl

_SIZES = ["Small", "Normal", "Large", "Huge"]
_SIZE_DUR_MULTS = {"Small": 1, "Normal": 2, "Large": 3, "Huge": 4}

# Key: JSON field name. Value: absolute 0-based column of the "Small" value.
# Pattern: stat group header is at col X, Small value is at col X+8.
_COL_SMALL = {
    "steam_tight_eff":       28,
    "steam_loose_eff":       32,
    "steam_opt_flow_tight":  36,
    "steam_opt_flow_loose":  40,
    "steam_power_tight":     44,
    "steam_power_loose":     48,
    "gas_tight_eff":         56,
    "gas_loose_eff":         60,
    "gas_opt_flow_tight":    64,
    "gas_opt_flow_loose":    68,
    "gas_power_tight":       72,
    "gas_power_loose":       76,
    "plasma_tight_eff":      84,
    "plasma_loose_eff":      88,
    "plasma_opt_flow_tight": 92,
    "plasma_opt_flow_loose": 96,
    "plasma_power_tight":    100,
    "plasma_power_loose":    104,
}


def extract_rotors(wb) -> list:
    ws = wb["Rotors"]
    rotors = []
    for row in ws.iter_rows(min_row=4, max_row=1000, values_only=True):
        display_name = row[8]
        if not display_name or not isinstance(display_name, str):
            continue
        tier = row[9]
        if tier is None:
            continue

        sizes_data = {}
        for i, size in enumerate(_SIZES):
            sd = {}
            for key, small_col in _COL_SMALL.items():
                col = small_col + i
                val = row[col] if col < len(row) else None
                sd[key] = round(val, 6) if isinstance(val, float) else val
            sd["dur_mult"] = _SIZE_DUR_MULTS[size]
            sizes_data[size] = sd

        rotors.append({
            "name": display_name,
            "tier": int(tier),
            "mining_speed": row[10],
            "base_durability": int(row[11]) if row[11] is not None else None,
            "overflow_tier": int(row[12]) if row[12] is not None else None,
            "sizes": sizes_data,
        })

    rotors.sort(key=lambda r: -r["tier"])
    return rotors
```

- [ ] **Step 4: Run tests**

```
pytest tests/test_excel_parser.py::test_extract_rotors_returns_list tests/test_excel_parser.py::test_extract_rotors_carbon_present tests/test_excel_parser.py::test_extract_rotors_carbon_stats -v
```

Expected: all PASS. If `test_extract_rotors_matches_existing_json` fails on stat values, examine the mismatch — the `_COL_SMALL` values above are derived from structural analysis; adjust any offset that's off by printing `row[27:32]` for a known rotor to cross-check.

- [ ] **Step 5: Run the full test including JSON comparison**

```
pytest tests/test_excel_parser.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 6: Commit**

```
git add scripts/excel_parser.py tests/test_excel_parser.py
git commit -m "feat: add excel_parser.py with extract_rotors, verified against 2.7 web data"
```

---

### Task 2: Add `extract_fuels` to `scripts/excel_parser.py`

**Files:**
- Modify: `scripts/excel_parser.py`
- Modify: `tests/test_excel_parser.py`

- [ ] **Step 1: Write failing tests for `extract_fuels`**

Append to `tests/test_excel_parser.py`:

```python
from scripts.excel_parser import extract_fuels

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
    # Gas: all names and eu_l should match
    new_gas = {e["name"]: e for e in result["gas"]}
    for entry in existing["gas"]:
        name = entry["name"]
        if name in new_gas:
            assert abs(new_gas[name]["eu_l"] - entry["eu_l"]) < 1e-3, f"gas {name} eu_l mismatch"
    # Plasma: same
    new_plasma = {e["name"]: e["eu_l"] for e in result["plasma"]}
    for entry in existing["plasma"]:
        name = entry["name"]
        if name in new_plasma:
            assert abs(new_plasma[name] - entry["eu_l"]) < 1e-3, f"plasma {name} eu_l mismatch"
```

- [ ] **Step 2: Run tests to confirm failure**

```
pytest tests/test_excel_parser.py::test_extract_fuels_structure -v
```

Expected: `ImportError: cannot import name 'extract_fuels'`

- [ ] **Step 3: Implement `extract_fuels` in `scripts/excel_parser.py`**

Append to `scripts/excel_parser.py`:

```python
def extract_fuels(wb, existing: dict | None = None) -> dict:
    ws = wb["Fuels"]
    steam, gas, plasma, ehe = [], [], [], []

    for row in ws.iter_rows(min_row=5, max_row=1000, values_only=True):
        # Steam: col B (1) = name, col C (2) = eu_l
        if row[1] and isinstance(row[2], (int, float)):
            steam.append({"name": row[1], "eu_l": float(row[2])})

        # Gas: col J (9) = name, col K (10) = eu_l, col L (11) = xlgt
        if row[9] and isinstance(row[10], (int, float)):
            gas.append({
                "name": row[9],
                "eu_l": float(row[10]),
                "xlgt": bool(row[11]) if row[11] is not None else False,
            })

        # Plasma: col O (14) = name, col P (15) = eu_l
        if row[14] and isinstance(row[15], (int, float)):
            plasma.append({"name": row[14], "eu_l": float(row[15])})

        # EHE: col R (17) = name, cols S-AC (18-28) = data
        if row[17] and isinstance(row[17], str) and row[18] is not None:
            ehe.append({
                "name": row[17],
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
            })

    return {"steam": steam, "gas": gas, "plasma": plasma, "ehe": ehe}
```

- [ ] **Step 4: Run all fuels tests**

```
pytest tests/test_excel_parser.py -k "fuels" -v
```

Expected: all 6 fuels tests PASS.

- [ ] **Step 5: Commit**

```
git add scripts/excel_parser.py tests/test_excel_parser.py
git commit -m "feat: add extract_fuels to excel_parser, verified against 2.7 web data"
```

---

### Task 3: Add `extract_steam_gen` to `scripts/excel_parser.py`

**Files:**
- Modify: `scripts/excel_parser.py`
- Modify: `tests/test_excel_parser.py`

- [ ] **Step 1: Write failing tests for `extract_steam_gen`**

Append to `tests/test_excel_parser.py`:

```python
from scripts.excel_parser import extract_steam_gen

EXISTING_STEAM_GEN = os.path.join(os.path.dirname(__file__), "..", "web", "data", "2.7", "steam_gen.json")

def test_extract_steam_gen_structure():
    result = extract_steam_gen(_wb())
    assert set(result.keys()) == {"lhe", "wwxl", "thermal_boiler"}
    assert len(result["lhe"]) >= 2
    assert len(result["wwxl"]) >= 1
    assert len(result["thermal_boiler"]) >= 2

def test_extract_steam_gen_lhe_lava():
    result = extract_steam_gen(_wb())
    lhe = {e["name"]: e for e in result["lhe"]}
    assert "Lava" in lhe
    lava = lhe["Lava"]
    assert abs(lava["threshold_ls"] - 1000.0) < 1e-3
    assert abs(lava["max_ls"] - 2000.0) < 1e-3
    assert lava["below"] == "Steam"
    assert lava["above"] == "SH Steam"
    assert abs(lava["ratio_below"] - 160.0) < 1e-3
    assert abs(lava["ratio_above"] - 80.0) < 1e-3

def test_extract_steam_gen_thermal_boiler_lava():
    result = extract_steam_gen(_wb())
    tb = {e["name"]: e for e in result["thermal_boiler"]}
    assert "Lava" in tb
    lava = tb["Lava"]
    assert abs(lava["max_ls"] - 1000.0) < 1e-3
    assert lava["steam"] == "Steam"
    assert lava["ratio"] == 16

def test_extract_steam_gen_matches_existing_json():
    result = extract_steam_gen(_wb())
    existing = json.load(open(EXISTING_STEAM_GEN))
    for section in ("lhe", "wwxl", "thermal_boiler"):
        new_map = {e["name"]: e for e in result[section]}
        for entry in existing[section]:
            name = entry["name"]
            if name in new_map:
                for key in entry:
                    if key == "name":
                        continue
                    assert abs(float(new_map[name][key]) - float(entry[key])) < 1e-3, \
                        f"{section}/{name}/{key} mismatch: {new_map[name][key]} vs {entry[key]}"
```

- [ ] **Step 2: Run to confirm failure**

```
pytest tests/test_excel_parser.py::test_extract_steam_gen_structure -v
```

Expected: `ImportError: cannot import name 'extract_steam_gen'`

- [ ] **Step 3: Implement `extract_steam_gen` in `scripts/excel_parser.py`**

Append to `scripts/excel_parser.py`:

```python
def extract_steam_gen(wb) -> dict:
    ws = wb["Fuels"]
    lhe, wwxl, thermal_boiler = [], [], []
    current_section = None

    for row in ws.iter_rows(min_row=1, max_row=50, values_only=True):
        label = row[1] if len(row) > 1 else None
        if label == "LHE Conversion":
            current_section = "lhe"
            continue
        if label == "WWXL Conversion":
            current_section = "wwxl"
            continue
        if label == "Thermal Boiler Conversion":
            current_section = "thermal_boiler"
            continue
        if label in (None, "Fluid"):
            continue

        # label is a fluid name
        if current_section in ("lhe", "wwxl"):
            entry = {
                "name": label,
                "threshold_ls": row[2],
                "max_ls": row[3],
                "below": row[4],
                "above": row[5],
                "ratio_below": row[6],
                "ratio_above": row[7],
            }
            if current_section == "lhe":
                lhe.append(entry)
            else:
                wwxl.append(entry)
        elif current_section == "thermal_boiler":
            thermal_boiler.append({
                "name": label,
                "max_ls": row[2],
                "steam": row[4],
                "ratio": row[5],
            })

    return {"lhe": lhe, "wwxl": wwxl, "thermal_boiler": thermal_boiler}
```

- [ ] **Step 4: Run steam_gen tests**

```
pytest tests/test_excel_parser.py -k "steam_gen" -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Run full test suite to check for regressions**

```
pytest tests/test_excel_parser.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```
git add scripts/excel_parser.py tests/test_excel_parser.py
git commit -m "feat: add extract_steam_gen to excel_parser, verified against 2.7 web data"
```

---

### Task 4: Extend `scripts/update_web_data.py` with Excel mode

**Files:**
- Modify: `scripts/update_web_data.py`

- [ ] **Step 1: Add `_diff_steam_gen` and `_run_excel` — read the current file first**

Read `scripts/update_web_data.py` in full before editing.

- [ ] **Step 2: Add `openpyxl` import and Excel parser import at top of `update_web_data.py`**

After the existing imports block, add:

```python
import openpyxl

from scripts.excel_parser import extract_rotors, extract_fuels, extract_steam_gen
```

- [ ] **Step 3: Add `_diff_steam_gen` function**

Add after the `_diff_fuels` function:

```python
def _diff_steam_gen(new_sg: dict, old_sg: dict | None) -> None:
    if old_sg is None:
        print("  New file")
        return

    for section in ("lhe", "wwxl", "thermal_boiler"):
        old_map = {e["name"]: e for e in (old_sg.get(section) or [])}
        new_map = {e["name"]: e for e in (new_sg.get(section) or [])}
        added   = sorted(set(new_map) - set(old_map))
        removed = sorted(set(old_map) - set(new_map))
        changed = []
        for name in sorted(set(new_map) & set(old_map)):
            diffs = [
                f"{k}: {old_map[name][k]} -> {new_map[name][k]}"
                for k in new_map[name]
                if k != "name" and k in old_map[name]
                and abs(float(new_map[name][k]) - float(old_map[name][k])) > 1e-6
            ]
            if diffs:
                changed.append(f"  ~ {name}: {', '.join(diffs)}")
        if added or removed or changed:
            print(f"  [{section}]")
            if added:   print(f"    + {', '.join(added)}")
            if removed: print(f"    - {', '.join(removed)}")
            for line in changed: print(f"   {line}")
        else:
            print(f"  [{section}] no changes")
```

- [ ] **Step 4: Add `_run_excel` function**

Add after `_diff_steam_gen`:

```python
def _run_excel(args) -> None:
    out_dir       = os.path.join(_WEB_DATA_DIR, args.gtnh)
    rotors_path   = os.path.join(out_dir, "rotors.json")
    fuels_path    = os.path.join(out_dir, "fuels.json")
    steam_gen_path = os.path.join(out_dir, "steam_gen.json")

    existing_rotors   = json.load(open(rotors_path))    if os.path.exists(rotors_path)    else None
    existing_fuels    = json.load(open(fuels_path))     if os.path.exists(fuels_path)     else None
    existing_steam_gen = json.load(open(steam_gen_path)) if os.path.exists(steam_gen_path) else None

    print(f"Loading {args.file} ...")
    wb = openpyxl.load_workbook(args.file, data_only=True)

    new_rotors    = extract_rotors(wb)
    new_fuels     = extract_fuels(wb, existing_fuels)
    new_steam_gen = extract_steam_gen(wb)

    print(f"\n=== Rotors: {len(new_rotors)} total ===")
    _diff_rotors(new_rotors, existing_rotors)

    print(f"\n=== Fuels ===")
    _diff_fuels(new_fuels, existing_fuels)

    print(f"\n=== Steam Gen ===")
    _diff_steam_gen(new_steam_gen, existing_steam_gen)

    print()
    answer = input(f"Write to web/data/{args.gtnh}/? [y/N] ").strip().lower()
    if answer != "y":
        print("Aborted.")
        return

    os.makedirs(out_dir, exist_ok=True)
    with open(rotors_path, "w", encoding="utf-8") as fh:
        json.dump(new_rotors, fh, ensure_ascii=False, indent=2)
    with open(fuels_path, "w", encoding="utf-8") as fh:
        json.dump(new_fuels, fh, ensure_ascii=False, indent=2)
    with open(steam_gen_path, "w", encoding="utf-8") as fh:
        json.dump(new_steam_gen, fh, ensure_ascii=False, indent=2)

    # Update versions.json
    versions_path = os.path.join(_WEB_DATA_DIR, "versions.json")
    versions = json.load(open(versions_path)) if os.path.exists(versions_path) else []
    if not any(v["id"] == args.gtnh for v in versions):
        versions.append({"id": args.gtnh, "label": args.gtnh})
        with open(versions_path, "w", encoding="utf-8") as fh:
            json.dump(versions, fh, ensure_ascii=False, indent=2)
        print(f"Added {args.gtnh} to versions.json")

    print(f"Written {rotors_path}")
    print(f"Written {fuels_path}")
    print(f"Written {steam_gen_path}")
```

- [ ] **Step 5: Update `main()` to add `--source` and `--file` arguments, and route to `_run_excel`**

Replace the `main()` function:

```python
def main():
    parser = argparse.ArgumentParser(description="Update web/data from GT5-Unofficial source or Excel file")
    parser.add_argument("--source", choices=["java", "excel"], default="java",
                        help="Data source: 'java' (default) downloads GT5 source, 'excel' reads .xlsx file")
    parser.add_argument("--tag",  help="GT5-Unofficial git tag (required for --source java), e.g. 5.09.44.08")
    parser.add_argument("--file", help="Path to Excel .xlsx file (required for --source excel)")
    parser.add_argument("--gtnh", required=True, help="GTNH version string, e.g. 2.9")
    args = parser.parse_args()

    if args.source == "java":
        if not args.tag:
            parser.error("--tag is required when --source java")
        if args.file:
            parser.error("--file is not used with --source java")
        _run_java(args)
    else:
        if not args.file:
            parser.error("--file is required when --source excel")
        if args.tag:
            parser.error("--tag is not used with --source excel")
        _run_excel(args)
```

- [ ] **Step 6: Rename existing `main()` body to `_run_java(args)`**

The current `main()` logic (after argument parsing) becomes `_run_java(args)`. Extract it:

```python
def _run_java(args) -> None:
    out_dir = os.path.join(_WEB_DATA_DIR, args.gtnh)
    rotors_path = os.path.join(out_dir, "rotors.json")
    fuels_path  = os.path.join(out_dir, "fuels.json")

    existing_rotors = json.load(open(rotors_path)) if os.path.exists(rotors_path) else None
    existing_fuels  = json.load(open(fuels_path))  if os.path.exists(fuels_path)  else None

    zip_bytes = _download_zip(args.tag)

    with tempfile.TemporaryDirectory() as tmp:
        src = _extract_src(zip_bytes, tmp)
        print(f"Parsing from {src} ...")
        rotor_data = build_rotor_data(src)
        gas_fuels, plasma_fuels = build_fuel_data(src)

    new_rotors = _build_rotors_json(rotor_data)
    new_fuels  = _build_fuels_json(gas_fuels, plasma_fuels, existing_fuels)

    print(f"\n=== Rotors: {len(new_rotors)} total ===")
    _diff_rotors(new_rotors, existing_rotors)

    print(f"\n=== Fuels ===")
    _diff_fuels(new_fuels, existing_fuels)

    print()
    answer = input(f"Write to web/data/{args.gtnh}/? [y/N] ").strip().lower()
    if answer != "y":
        print("Aborted.")
        return

    os.makedirs(out_dir, exist_ok=True)
    with open(rotors_path, "w", encoding="utf-8") as fh:
        json.dump(new_rotors, fh, ensure_ascii=False, indent=2)
    with open(fuels_path, "w", encoding="utf-8") as fh:
        json.dump(new_fuels, fh, ensure_ascii=False, indent=2)
    print(f"Written {rotors_path}")
    print(f"Written {fuels_path}")
```

- [ ] **Step 7: Smoke test the Java path is not broken**

```
python scripts/update_web_data.py --gtnh 2.9
```

Expected: `error: the following arguments are required: --gtnh` — wait, no. Expected: something like `error: --tag is required when --source java` (since no --tag given). This confirms argument parsing works.

Also run:

```
python scripts/update_web_data.py --source excel --gtnh 2.7 --file "Large Turbine Calculator (2.7.0-2.8.4).xlsx"
```

Expected: shows diff against existing 2.7 data, then `[y/N]` prompt. Enter `n` to abort without writing.

- [ ] **Step 8: Run full test suite**

```
pytest tests/ -v --ignore=tests/test_rotor_parser.py --ignore=tests/test_fuel_parser.py
```

(Skip rotor_parser and fuel_parser tests as they require the GT5 source checkout.)

Expected: all other tests PASS including the new `test_excel_parser.py` suite.

- [ ] **Step 9: Commit**

```
git add scripts/update_web_data.py
git commit -m "feat: add --source excel mode to update_web_data.py for Excel-based import"
```

---

## Self-Review

**Spec coverage:**
- `--source excel --file <path>` CLI: Task 4 ✓
- `scripts/excel_parser.py` with 3 functions: Tasks 1-3 ✓
- diff + confirm: Task 4 `_run_excel` ✓
- steam_gen extraction: Task 3 ✓
- `versions.json` update: Task 4 `_run_excel` ✓
- `--source java` default (existing behavior preserved): Task 4 `_run_java` ✓

**Placeholder scan:** No TBDs. All code is complete.

**Type consistency:**
- `extract_rotors(wb) -> list` used in Task 4 as `extract_rotors(wb)` ✓
- `extract_fuels(wb, existing_fuels)` matches signature `extract_fuels(wb, existing=None)` ✓
- `extract_steam_gen(wb)` used as `extract_steam_gen(wb)` ✓
- `_diff_steam_gen(new_steam_gen, existing_steam_gen)` matches definition ✓
- `_run_java(args)` and `_run_excel(args)` both take the parsed `args` namespace ✓
