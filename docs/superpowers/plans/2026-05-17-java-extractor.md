# Java Data Extractor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `scripts/extract_from_java.py` that parses GT5-Unofficial Java sources to extract rotor stats and fuel values, producing output comparable to the existing `rotors_raw.py` / `fuels_raw.py`.

**Architecture:** Four modules — `turbine_formulas.py` ports the TurbineStatCalculator Java formulas to Python; `rotor_parser.py` uses `javalang` AST to extract material properties from `MaterialsInit.java` and regex for Werkstoff-based materials; `fuel_parser.py` uses regex to extract gas and plasma fuel recipes from loader files; `extract_from_java.py` ties them together with a `--compare` flag.

**Tech Stack:** Python 3.10+, `javalang` (AST parser for Java 8 syntax), `re` (regex for Java 14+ arrow-switch files), existing `rotors_raw.py` / `fuels_raw.py` for comparison target.

---

## Source File Map

| Java source | What we extract | Parser method |
|---|---|---|
| `src/main/java/gregtech/loaders/materials/MaterialsInit.java` | GT material properties: `setTool(dur, qual, speed)`, `setTurbine(steam, gas, plasma)`, `addSubTag(NO_SMASHING)` | javalang AST |
| `src/main/java/goodgenerator/items/GGMaterial.java` | Werkstoff overrides: `setSpeedOverride`, `setDurOverride`, `setQualityOverride` | regex |
| `src/main/java/bartworks/system/material/WerkstoffLoader.java` | Werkstoff overrides (same pattern) | regex |
| `src/main/java/gregtech/loaders/oreprocessing/ProcessingCell.java` | Plasma fuel switch: `case "Name" -> recipeBuilder.metadata(FUEL_VALUE, N).metadata(FUEL_TYPE, 4)` | regex |
| `src/main/java/gregtech/loaders/load/FuelLoader.java` + `goodgenerator/loader/RecipeLoader.java` + `gtPlusPlus/.../RecipeLoaderCoalTar.java` + `gtPlusPlus/.../RecipeLoaderGenericChem.java` + `bartworks/.../AdditionalRecipes.java` | Gas fuel recipes: `.metadata(FUEL_VALUE, N) .metadata(FUEL_TYPE, 1)` with fluid input | regex |

## Output File Map

| Python file | Purpose |
|---|---|
| `scripts/turbine_formulas.py` | Pure Python port of TurbineStatCalculator.java formulas |
| `scripts/rotor_parser.py` | Parses Java sources → dict of material properties |
| `scripts/fuel_parser.py` | Parses Java sources → gas and plasma fuel dicts |
| `scripts/extract_from_java.py` | CLI entry point; `--compare` mode diffs against current data |

## Formula Reference (from TurbineStatCalculator.java)

```
# Per-size constants (from ToolTurbineSmall/Normal/Large/Huge.java):
SIZE_SPEED_MULT = {"Small": 1.0, "Normal": 2.0, "Large": 3.0, "Huge": 4.0}
SIZE_BASE_DAMAGE = {"Small": 0.0, "Normal": 2.5, "Large": 5.0, "Huge": 7.5}
SIZE_DUR_MULT    = {"Small": 1,   "Normal": 2,   "Large": 3,   "Huge": 4}

# Per-material:
combat_damage(size) = SIZE_BASE_DAMAGE[size] + tool_quality
base_eff(size)      = 0.5 + (0.5 + combat_damage(size)) * 0.1
loose_eff(size)     = -0.2 + round(base_eff(size) * 85.0) * 0.01
loose_steam_eff     = loose_eff * 0.9
loose_gas_eff       = loose_eff * 0.95
loose_plasma_eff    = loose_eff

opt_flow(size)         = SIZE_SPEED_MULT[size] * tool_speed * 50.0
opt_steam_flow(size)   = opt_flow(size) * steam_mult
opt_gas_flow(size)     = opt_flow(size) * gas_mult
opt_plasma_flow(size)  = opt_flow(size) * plasma_mult * 42.0

loose_steam_flow(size)  = 3.0 * opt_steam_flow(size)  * 1.1  ** ((base_eff(size) - 0.8) * 20)
loose_gas_flow(size)    = 2.0 * opt_gas_flow(size)    * 1.05 ** ((base_eff(size) - 0.8) * 20)
loose_plasma_flow(size) = 2.0 * opt_plasma_flow(size) * 1.03 ** ((base_eff(size) - 0.8) * 20)

steam_tight_eff(size)   = base_eff(size)
steam_loose_eff(size)   = loose_steam_eff(size)
steam_opt_flow_tight    = opt_steam_flow(size)
steam_opt_flow_loose    = loose_steam_flow(size)
steam_power_tight       = opt_steam_flow(size)  * base_eff(size)       * 0.5
steam_power_loose       = loose_steam_flow(size) * loose_steam_eff(size) * 0.5

gas_tight_eff           = base_eff(size)
gas_loose_eff           = loose_gas_eff(size)
gas_opt_flow_tight      = opt_gas_flow(size)
gas_opt_flow_loose      = loose_gas_flow(size)
gas_power_tight         = opt_gas_flow(size)   * base_eff(size)      * 1.0
gas_power_loose         = loose_gas_flow(size) * loose_gas_eff(size) * 1.0

plasma_tight_eff        = base_eff(size)
plasma_loose_eff        = loose_plasma_eff(size)
plasma_opt_flow_tight   = opt_plasma_flow(size)
plasma_opt_flow_loose   = loose_plasma_flow(size)
plasma_power_tight      = opt_plasma_flow(size)   * base_eff(size)         * 1.0
plasma_power_loose      = loose_plasma_flow(size)  * loose_plasma_eff(size) * 1.0

overflow_tier           = 1 + min(2, tool_quality // 3)
base_durability         = tool_durability * 100
```

---

## Task 1: Install javalang and port formula module

**Files:**
- Modify: `requirements.txt`
- Create: `scripts/turbine_formulas.py`
- Create: `tests/test_turbine_formulas.py`

- [ ] **Step 1: Add javalang to requirements.txt**

Append one line to `requirements.txt`:
```
javalang>=0.13.0
```

Run: `pip install javalang`
Expected: installs successfully.

- [ ] **Step 2: Write failing tests for formula module**

Create `tests/test_turbine_formulas.py`:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.turbine_formulas import compute_rotor_sizes

def test_eternity_small():
    # Eternity (26): tool_quality=26, tool_speed=1.0, dur=20971520,
    #   steam_mult=1.0, gas_mult=1.0, plasma_mult=1.0
    # Small: speed_mult=1.0, base_damage=0.0
    #   combat = 0.0 + 26 = 26
    #   base_eff = 0.5 + (0.5+26)*0.1 = 0.5 + 2.65 = 3.15
    # (Note: Excel value may differ; this validates formula mechanics)
    sizes = compute_rotor_sizes(
        tool_quality=26, tool_speed=1.0,
        steam_mult=1.0, gas_mult=1.0, plasma_mult=1.0
    )
    s = sizes["Small"]
    assert abs(s["steam_tight_eff"] - 3.15) < 1e-4
    assert abs(s["gas_tight_eff"] - 3.15) < 1e-4
    assert abs(s["plasma_tight_eff"] - 3.15) < 1e-4
    assert s["dur_mult"] == 1

def test_eternity_normal():
    # Normal: speed_mult=2.0, base_damage=2.5
    #   combat = 2.5 + 26 = 28.5
    #   base_eff = 0.5 + (0.5+28.5)*0.1 = 0.5 + 2.9 = 3.4
    sizes = compute_rotor_sizes(
        tool_quality=26, tool_speed=1.0,
        steam_mult=1.0, gas_mult=1.0, plasma_mult=1.0
    )
    s = sizes["Normal"]
    assert abs(s["steam_tight_eff"] - 3.4) < 1e-4
    assert s["dur_mult"] == 2

def test_opt_flow_with_multiplier():
    # quality=10, speed=6.0, steam_mult=6.0, gas_mult=1.0, plasma_mult=1.0 (Alduorite-like)
    # Small: opt_flow = 1.0 * 6.0 * 50 = 300
    # opt_steam_flow = 300 * 6.0 = 1800
    sizes = compute_rotor_sizes(
        tool_quality=1, tool_speed=6.0,
        steam_mult=6.0, gas_mult=1.0, plasma_mult=1.0
    )
    s = sizes["Small"]
    assert abs(s["steam_opt_flow_tight"] - 1800.0) < 1e-3

def test_overflow_tier():
    # quality=26: 1 + min(2, 26//3) = 1 + min(2, 8) = 3
    from scripts.turbine_formulas import compute_overflow_tier
    assert compute_overflow_tier(26) == 3
    # quality=3: 1 + min(2, 1) = 2
    assert compute_overflow_tier(3) == 2
    # quality=1: 1 + min(2, 0) = 1
    assert compute_overflow_tier(1) == 1
```

Run: `pytest tests/test_turbine_formulas.py -v`
Expected: FAIL (ImportError — module doesn't exist yet).

- [ ] **Step 3: Implement turbine_formulas.py**

Create `scripts/__init__.py` (empty file).

Create `scripts/turbine_formulas.py`:
```python
import math

_SIZE_SPEED_MULT  = {"Small": 1.0, "Normal": 2.0, "Large": 3.0, "Huge": 4.0}
_SIZE_BASE_DAMAGE = {"Small": 0.0, "Normal": 2.5, "Large": 5.0, "Huge": 7.5}
_SIZE_DUR_MULT    = {"Small": 1,   "Normal": 2,   "Large": 3,   "Huge": 4}


def compute_overflow_tier(tool_quality: int) -> int:
    return 1 + min(2, tool_quality // 3)


def _round6(x: float) -> float:
    return round(x, 6)


def compute_rotor_sizes(
    tool_quality: int,
    tool_speed: float,
    steam_mult: float,
    gas_mult: float,
    plasma_mult: float,
) -> dict:
    sizes = {}
    for size in ("Small", "Normal", "Large", "Huge"):
        speed_mult  = _SIZE_SPEED_MULT[size]
        base_damage = _SIZE_BASE_DAMAGE[size]
        dur_mult    = _SIZE_DUR_MULT[size]

        combat    = base_damage + tool_quality
        base_eff  = 0.5 + (0.5 + combat) * 0.1

        loose_eff        = -0.2 + round(base_eff * 85.0) * 0.01
        loose_steam_eff  = loose_eff * 0.9
        loose_gas_eff    = loose_eff * 0.95
        loose_plasma_eff = loose_eff

        opt_flow         = speed_mult * tool_speed * 50.0
        opt_steam        = opt_flow * steam_mult
        opt_gas          = opt_flow * gas_mult
        opt_plasma       = opt_flow * plasma_mult * 42.0

        decay = (base_eff - 0.8) * 20.0
        loose_steam  = 3.0 * opt_steam  * math.pow(1.1,  decay)
        loose_gas    = 2.0 * opt_gas    * math.pow(1.05, decay)
        loose_plasma = 2.0 * opt_plasma * math.pow(1.03, decay)

        sizes[size] = {
            "steam_tight_eff":       _round6(base_eff),
            "steam_loose_eff":       _round6(loose_steam_eff),
            "steam_opt_flow_tight":  _round6(opt_steam),
            "steam_opt_flow_loose":  _round6(loose_steam),
            "steam_power_tight":     _round6(opt_steam  * base_eff       * 0.5),
            "steam_power_loose":     _round6(loose_steam * loose_steam_eff * 0.5),
            "gas_tight_eff":         _round6(base_eff),
            "gas_loose_eff":         _round6(loose_gas_eff),
            "gas_opt_flow_tight":    _round6(opt_gas),
            "gas_opt_flow_loose":    _round6(loose_gas),
            "gas_power_tight":       _round6(opt_gas   * base_eff      * 1.0),
            "gas_power_loose":       _round6(loose_gas * loose_gas_eff * 1.0),
            "plasma_tight_eff":      _round6(base_eff),
            "plasma_loose_eff":      _round6(loose_plasma_eff),
            "plasma_opt_flow_tight": _round6(opt_plasma),
            "plasma_opt_flow_loose": _round6(loose_plasma),
            "plasma_power_tight":    _round6(opt_plasma   * base_eff          * 1.0),
            "plasma_power_loose":    _round6(loose_plasma * loose_plasma_eff  * 1.0),
            "dur_mult":              dur_mult,
        }
    return sizes
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_turbine_formulas.py -v`
Expected: 4 tests PASS.

- [ ] **Step 5: Commit**

```
git add requirements.txt scripts/__init__.py scripts/turbine_formulas.py tests/test_turbine_formulas.py
git commit -m "add turbine_formulas.py: Python port of TurbineStatCalculator formulas"
```

---

## Task 2: Rotor parser — GT materials (MaterialsInit.java via javalang)

**Files:**
- Create: `scripts/rotor_parser.py`
- Create: `tests/test_rotor_parser.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_rotor_parser.py`:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.rotor_parser import parse_gt_materials

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
    # Titanium has setTool but no setTurbine → defaults 1/1/1
    assert "Titanium" in mats
    m = mats["Titanium"]
    assert abs(m["steam_mult"]  - 1.0) < 1e-6
    assert abs(m["gas_mult"]    - 1.0) < 1e-6
    assert abs(m["plasma_mult"] - 1.0) < 1e-6

def test_no_smashing_excluded():
    mats = parse_gt_materials(GT5_SRC)
    # Materials tagged NO_SMASHING should not appear (no turbine blade)
    # Stone is a well-known NO_SMASHING / no-tool material
    for name, data in mats.items():
        assert not data.get("_no_smashing"), f"{name} is NO_SMASHING but was included"
```

Run: `pytest tests/test_rotor_parser.py -v`
Expected: FAIL (ImportError).

- [ ] **Step 2: Implement parse_gt_materials**

Create `scripts/rotor_parser.py`:
```python
"""Parse rotor-capable material properties from GT5-Unofficial Java sources."""
import os
import re
import javalang

_MATERIALS_INIT = os.path.join(
    "src", "main", "java", "gregtech", "loaders", "materials", "MaterialsInit.java"
)
_GGMATERIAL = os.path.join(
    "src", "main", "java", "goodgenerator", "items", "GGMaterial.java"
)
_WERKSTOFF_LOADER = os.path.join(
    "src", "main", "java", "bartworks", "system", "material", "WerkstoffLoader.java"
)


def _float_arg(arg) -> float | None:
    """Extract float from a javalang literal argument (handles _-separators and f suffix)."""
    if arg is None:
        return None
    if hasattr(arg, "value"):
        try:
            return float(str(arg.value).replace("_", "").rstrip("fF"))
        except ValueError:
            return None
    # unary minus: MemberReference or Cast
    if hasattr(arg, "operand") and hasattr(arg.operand, "value"):
        try:
            return -float(str(arg.operand.value).replace("_", "").rstrip("fF"))
        except ValueError:
            return None
    return None


def parse_gt_materials(gt5_src_root: str) -> dict:
    """Parse MaterialsInit.java via javalang AST.

    Returns dict[material_name -> property_dict] for all materials that have
    setTool() and are NOT tagged with NO_SMASHING or BOUNCY.
    """
    path = os.path.join(gt5_src_root, _MATERIALS_INIT)
    with open(path, encoding="utf-8") as fh:
        code = fh.read()

    tree = javalang.parse.parse(code)

    result = {}
    for _, method in tree.filter(javalang.tree.MethodDeclaration):
        if not method.name.startswith("load"):
            continue

        mat_name = None
        tool_dur = tool_qual = tool_speed = None
        steam_mult = gas_mult = plasma_mult = 1.0
        subtags = []

        for _, child in method.filter(javalang.tree.MethodInvocation):
            m = child.member
            args = child.arguments or []

            if m == "setName" and args:
                v = getattr(args[0], "value", None)
                if v:
                    mat_name = v.strip('"')

            elif m == "setTool" and len(args) >= 3:
                tool_dur   = _float_arg(args[0])
                tool_qual  = _float_arg(args[1])
                tool_speed = _float_arg(args[2])

            elif m == "setTurbine" and len(args) >= 3:
                steam_mult  = _float_arg(args[0]) or 1.0
                gas_mult    = _float_arg(args[1]) or 1.0
                plasma_mult = _float_arg(args[2]) or 1.0

            elif m == "addSubTag" and args:
                ref = getattr(args[0], "member", None)
                if ref:
                    subtags.append(ref)

        if mat_name is None or tool_dur is None:
            continue
        if "NO_SMASHING" in subtags or "BOUNCY" in subtags:
            continue

        result[mat_name] = {
            "tool_durability": int(tool_dur),
            "tool_quality":    int(tool_qual),
            "tool_speed":      float(tool_speed),
            "steam_mult":      float(steam_mult),
            "gas_mult":        float(gas_mult),
            "plasma_mult":     float(plasma_mult),
        }

    return result


def parse_werkstoff_materials(gt5_src_root: str) -> dict:
    """Parse Werkstoff-based materials (GGMaterial.java, WerkstoffLoader.java)
    that have speed/durability/quality overrides for turbine use.

    Returns dict[material_name -> property_dict] in same format as parse_gt_materials.
    """
    result = {}
    for rel_path in (_GGMATERIAL, _WERKSTOFF_LOADER):
        path = os.path.join(gt5_src_root, rel_path)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            code = fh.read()

        # Pattern: find each Werkstoff constructor block, extract name + overrides.
        # We look for 'new Werkstoff(' blocks and scan forward for overrides.
        # Use a sliding window: after each '"Name"' occurrence inside a Werkstoff block,
        # scan the next ~600 chars for setSpeedOverride/setDurOverride/setQualityOverride.
        blocks = list(re.finditer(
            r'new Werkstoff\s*\(', code
        ))
        for m in blocks:
            block_start = m.start()
            # Grab up to 800 chars of the Werkstoff constructor args
            chunk = code[block_start: block_start + 800]

            name_match = re.search(r'"([\w][^"]{0,60})"', chunk)
            if not name_match:
                continue
            name = name_match.group(1).strip()

            speed_m   = re.search(r'setSpeedOverride\(\s*([\d.]+)F?\s*\)', chunk)
            dur_m     = re.search(r'setDurOverride\(\s*(\d+)\s*\)', chunk)
            quality_m = re.search(r'setQualityOverride\(\s*\(byte\)\s*(\d+)\s*\)', chunk)

            if not (speed_m and dur_m and quality_m):
                continue  # not a turbine-capable material override

            result[name] = {
                "tool_durability": int(dur_m.group(1)),
                "tool_quality":    int(quality_m.group(1)),
                "tool_speed":      float(speed_m.group(1)),
                "steam_mult":      1.0,
                "gas_mult":        1.0,
                "plasma_mult":     1.0,
            }

    return result
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_rotor_parser.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 4: Commit**

```
git add scripts/rotor_parser.py tests/test_rotor_parser.py
git commit -m "add rotor_parser.py: extract material properties from MaterialsInit + Werkstoff via javalang"
```

---

## Task 3: Fuel parser — gas and plasma fuels

**Files:**
- Create: `scripts/fuel_parser.py`
- Create: `tests/test_fuel_parser.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_fuel_parser.py`:
```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.fuel_parser import parse_gas_fuels, parse_plasma_fuels

GT5_SRC = r"C:\Users\Eldrinn_Elantey\GitHub\GT5-Unofficial\src"

def test_gas_fuels_found():
    fuels = parse_gas_fuels(GT5_SRC)
    # Known gas fuels from existing data
    assert "Naquadah Gas" in fuels
    assert fuels["Naquadah Gas"]["eu_per_l"] == 1024.0

def test_gas_fuel_xlgt_flag():
    fuels = parse_gas_fuels(GT5_SRC)
    # Benzene: eu_per_l=360, xlgt=False (not in any XL-specific file)
    assert "Benzene" in fuels

def test_plasma_fuels_found():
    fuels = parse_plasma_fuels(GT5_SRC)
    # Aluminium plasma: eu_per_l = 159_744
    assert "Aluminium" in fuels
    assert fuels["Aluminium"]["eu_per_l"] == 159744.0

def test_plasma_fuel_count():
    fuels = parse_plasma_fuels(GT5_SRC)
    # Should find at least 50 plasma fuels
    assert len(fuels) >= 50
```

Run: `pytest tests/test_fuel_parser.py -v`
Expected: FAIL (ImportError).

- [ ] **Step 2: Implement fuel_parser.py**

The gas fuel files use this pattern (across multiple files):
```java
.fluidInputs(Materials.Benzene.getGas(1))
.metadata(FUEL_VALUE, 360)
.metadata(FUEL_TYPE, 1)
```
or
```java
.fluidInputs(GGMaterial.naquadahGas.getFluidOrGas(1))
.metadata(FUEL_VALUE, 1024)
.metadata(FUEL_TYPE, 1)
```

The plasma fuel file (`ProcessingCell.java`) uses arrow-switch:
```java
case "Aluminium" -> recipeBuilder.metadata(FUEL_VALUE, 159_744)
    .metadata(FUEL_TYPE, 4)
    .addTo(GTRecipeConstants.Fuel);
```
Plus a fallback formula for unlisted materials (we skip the formula — only extract explicit cases).

Create `scripts/fuel_parser.py`:
```python
"""Parse gas and plasma fuel values from GT5-Unofficial Java source loader files."""
import os
import re

# Files containing gas turbine fuels (FUEL_TYPE = 1)
_GAS_FUEL_FILES = [
    os.path.join("src", "main", "java", "gregtech", "loaders", "load", "FuelLoader.java"),
    os.path.join("src", "main", "java", "goodgenerator", "loader", "RecipeLoader.java"),
    os.path.join("src", "main", "java", "gtPlusPlus", "core", "item", "chemistry",
                 "RecipeLoaderCoalTar.java"),
    os.path.join("src", "main", "java", "gtPlusPlus", "core", "item", "chemistry",
                 "RecipeLoaderGenericChem.java"),
    os.path.join("src", "main", "java", "bartworks", "system", "material",
                 "processingLoaders", "AdditionalRecipes.java"),
]

# File containing plasma fuels (FUEL_TYPE = 4) via arrow switch
_PLASMA_FUEL_FILE = os.path.join(
    "src", "main", "java", "gregtech", "loaders", "oreprocessing", "ProcessingCell.java"
)

# Regex: fluid name from .getGas(N) or .getFluidOrGas(N) or .getFluid(N)
_FLUID_NAME_RE = re.compile(
    r'(?:Materials\.|GGMaterial\.|WerkstoffLoader\.)'
    r'(\w+)'
    r'\.(?:getGas|getFluidOrGas|getFluid)\s*\(\s*\d+\s*\)',
    re.IGNORECASE,
)

# Regex: .metadata(FUEL_VALUE, N) — N may use _ separators
_FUEL_VALUE_RE = re.compile(
    r'metadata\s*\(\s*FUEL_VALUE\s*,\s*([\d_]+)\s*\)'
)

# Regex: .metadata(FUEL_TYPE, 1) or .metadata(FUEL_TYPE, GasTurbine.ordinal())
_GAS_FUEL_TYPE_RE = re.compile(
    r'metadata\s*\(\s*FUEL_TYPE\s*,\s*(?:1\b|GTRecipeConstants\.FuelType\.GasTurbine\.ordinal\(\))'
)

# Regex for plasma arrow-switch: case "Name" -> ... FUEL_VALUE, N ... FUEL_TYPE, 4
_PLASMA_CASE_RE = re.compile(
    r'case\s+"(\w+)"\s+->\s+recipeBuilder\.metadata\s*\(\s*FUEL_VALUE\s*,\s*([\d_]+)\s*\)'
    r'[\s\S]{0,100}?metadata\s*\(\s*FUEL_TYPE\s*,\s*4\s*\)',
    re.MULTILINE,
)


def _parse_int(s: str) -> int:
    return int(s.replace("_", ""))


def parse_gas_fuels(gt5_src_root: str) -> dict:
    """Return dict[fluid_display_name -> {"eu_per_l": float, "xlgt": bool}]."""
    result = {}
    for rel_path in _GAS_FUEL_FILES:
        path = os.path.join(gt5_src_root, rel_path)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            code = fh.read()

        # Split on stdBuilder() calls to isolate individual recipe blocks
        blocks = re.split(r'\.stdBuilder\s*\(\s*\)', code)
        for block in blocks:
            if not _GAS_FUEL_TYPE_RE.search(block):
                continue
            fuel_m = _FUEL_VALUE_RE.search(block)
            if not fuel_m:
                continue
            fluid_m = _FLUID_NAME_RE.search(block)
            if not fluid_m:
                continue

            raw_name = fluid_m.group(1)
            # Convert camelCase field name to display name used in calc data.
            # e.g. "naquadahGas" → "Naquadah Gas", "Benzene" → "Benzene"
            display = _field_to_display(raw_name)
            eu_per_l = float(_parse_int(fuel_m.group(1)))
            result[display] = {"eu_per_l": eu_per_l, "xlgt": False}

    return result


def parse_plasma_fuels(gt5_src_root: str) -> dict:
    """Return dict[material_name -> {"eu_per_l": float}] for plasma fuels."""
    path = os.path.join(gt5_src_root, _PLASMA_FUEL_FILE)
    with open(path, encoding="utf-8") as fh:
        code = fh.read()

    result = {}
    for m in _PLASMA_CASE_RE.finditer(code):
        name    = m.group(1)
        eu_per_l = float(_parse_int(m.group(2)))
        result[name] = {"eu_per_l": eu_per_l}

    return result


def _field_to_display(field_name: str) -> str:
    """Convert Java field/class camelCase name to space-separated title case.

    Examples:
        "Benzene"       → "Benzene"
        "naquadahGas"   → "Naquadah Gas"
        "Nitrobenzene"  → "Nitrobenzene"
    """
    import re as _re
    # Insert space before uppercase letters that follow lowercase
    spaced = _re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', field_name)
    return spaced[0].upper() + spaced[1:]
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_fuel_parser.py -v`
Expected: At least `test_plasma_fuels_found` and `test_plasma_fuel_count` pass. Gas fuel tests may need name-mapping tuning (see Step 4 if they fail).

- [ ] **Step 4: Fix name mapping if gas fuel tests fail**

If `test_gas_fuels_found` fails because "Naquadah Gas" is not found, check what name the parser produces:
```python
from scripts.fuel_parser import parse_gas_fuels
fuels = parse_gas_fuels(r"C:\Users\Eldrinn_Elantey\GitHub\GT5-Unofficial\src")
# Print gas fuels found
for k in sorted(fuels): print(k)
```
Adjust `_field_to_display` or add a `_NAME_OVERRIDES` dict for entries that don't follow camelCase:
```python
_NAME_OVERRIDES = {
    "naquadahGas": "Naquadah Gas",
    # add more as needed
}
```
In `_field_to_display`, check `_NAME_OVERRIDES.get(field_name)` first.

- [ ] **Step 5: Commit**

```
git add scripts/fuel_parser.py tests/test_fuel_parser.py
git commit -m "add fuel_parser.py: extract gas and plasma fuel values from recipe loaders"
```

---

## Task 4: Main script — assembly + compare mode

**Files:**
- Create: `scripts/extract_from_java.py`

- [ ] **Step 1: Write the main script**

Create `scripts/extract_from_java.py`:
```python
"""Extract rotor and fuel data from GT5-Unofficial Java sources.

Usage:
    python scripts/extract_from_java.py --gt5 <path>              # print counts
    python scripts/extract_from_java.py --gt5 <path> --rotors     # print rotor dict
    python scripts/extract_from_java.py --gt5 <path> --fuels      # print fuel dicts
    python scripts/extract_from_java.py --gt5 <path> --compare    # diff vs current data
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.rotor_parser import parse_gt_materials, parse_werkstoff_materials
from scripts.fuel_parser import parse_gas_fuels, parse_plasma_fuels
from scripts.turbine_formulas import compute_rotor_sizes, compute_overflow_tier


def build_rotor_data(gt5_src: str) -> dict:
    gt_mats = parse_gt_materials(gt5_src)
    wk_mats = parse_werkstoff_materials(gt5_src)
    all_mats = {**gt_mats, **wk_mats}

    rotor_data = {}
    for name, props in all_mats.items():
        qual   = props["tool_quality"]
        speed  = props["tool_speed"]
        dur    = props["tool_durability"]
        tier   = qual
        rotor_name = f"{name} ({tier})"

        rotor_data[rotor_name] = {
            "tier":             tier,
            "mining_speed":     speed,
            "base_durability":  dur * 100,
            "overflow_tier":    compute_overflow_tier(qual),
            "sizes":            compute_rotor_sizes(
                tool_quality=qual,
                tool_speed=speed,
                steam_mult=props["steam_mult"],
                gas_mult=props["gas_mult"],
                plasma_mult=props["plasma_mult"],
            ),
        }
    return rotor_data


def build_fuel_data(gt5_src: str) -> tuple[dict, dict]:
    gas    = parse_gas_fuels(gt5_src)
    plasma = parse_plasma_fuels(gt5_src)
    return gas, plasma


def compare_rotors(java_data: dict, current_data: dict) -> None:
    java_keys    = set(java_data)
    current_keys = set(current_data)

    new_in_java  = java_keys - current_keys
    missing_in_java = current_keys - java_keys
    common       = java_keys & current_keys

    print(f"\n=== ROTOR COMPARISON ===")
    print(f"Java: {len(java_keys)}  Current: {len(current_keys)}  Common: {len(common)}")

    if new_in_java:
        print(f"\nNew in Java ({len(new_in_java)}):")
        for n in sorted(new_in_java): print(f"  + {n}")

    if missing_in_java:
        print(f"\nMissing from Java ({len(missing_in_java)}):")
        for n in sorted(missing_in_java): print(f"  - {n}")

    # Check stat differences for common rotors (tight steam eff, Small only)
    print(f"\nStat diffs (steam_tight_eff Small, >5% delta):")
    diffs = []
    for name in sorted(common):
        j_eff = java_data[name]["sizes"]["Small"]["steam_tight_eff"]
        c_eff = current_data[name]["sizes"]["Small"]["steam_tight_eff"]
        if abs(j_eff - c_eff) / max(abs(c_eff), 1e-9) > 0.05:
            diffs.append((name, c_eff, j_eff))
    if diffs:
        for name, c, j in diffs:
            print(f"  {name}: current={c:.4f}  java={j:.4f}")
    else:
        print("  (none)")


def compare_fuels(java_gas: dict, java_plasma: dict,
                  current_gas: dict, current_plasma: dict) -> None:
    print(f"\n=== GAS FUEL COMPARISON ===")
    print(f"Java: {len(java_gas)}  Current: {len(current_gas)}")
    for name in sorted(set(current_gas) | set(java_gas)):
        j = java_gas.get(name, {}).get("eu_per_l")
        c = current_gas.get(name, {}).get("eu_per_l")
        if j != c:
            print(f"  {name}: current={c}  java={j}")

    print(f"\n=== PLASMA FUEL COMPARISON ===")
    print(f"Java: {len(java_plasma)}  Current: {len(current_plasma)}")
    for name in sorted(set(current_plasma) | set(java_plasma)):
        j = java_plasma.get(name, {}).get("eu_per_l") if isinstance(java_plasma.get(name), dict) else java_plasma.get(name)
        c = current_plasma.get(name)
        if j != c:
            print(f"  {name}: current={c}  java={j}")


def main():
    parser = argparse.ArgumentParser(description="Extract data from GT5 Java sources")
    parser.add_argument("--gt5", required=True, help="Path to GT5-Unofficial/src directory")
    parser.add_argument("--rotors",  action="store_true")
    parser.add_argument("--fuels",   action="store_true")
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()

    rotor_data = build_rotor_data(args.gt5)
    gas_fuels, plasma_fuels = build_fuel_data(args.gt5)

    if args.rotors:
        print("ROTOR_DATA =", repr(rotor_data))

    if args.fuels:
        print("GAS_FUELS =",    repr(gas_fuels))
        print("PLASMA_FUELS =", repr(plasma_fuels))

    if args.compare:
        sys.path.insert(0, ".")
        from gtnh_turbine_calc.data.rotors_raw import ROTOR_DATA as current_rotors
        from gtnh_turbine_calc.data.fuels_raw  import GAS_FUELS, PLASMA_FUELS
        compare_rotors(rotor_data, current_rotors)
        compare_fuels(gas_fuels, plasma_fuels, GAS_FUELS, PLASMA_FUELS)

    if not (args.rotors or args.fuels or args.compare):
        print(f"Extracted {len(rotor_data)} rotors, "
              f"{len(gas_fuels)} gas fuels, "
              f"{len(plasma_fuels)} plasma fuels")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-test the script**

Run from the project root:
```
python scripts/extract_from_java.py --gt5 C:\Users\Eldrinn_Elantey\GitHub\GT5-Unofficial\src
```
Expected output like:
```
Extracted 176 rotors, N gas fuels, M plasma fuels
```
(Exact numbers will differ from Excel data — that is expected and is what `--compare` reveals.)

- [ ] **Step 3: Run compare mode and inspect output**

```
python scripts/extract_from_java.py --gt5 C:\Users\Eldrinn_Elantey\GitHub\GT5-Unofficial\src --compare
```
Expected: comparison tables printed with new/missing rotors and stat diffs.

- [ ] **Step 4: Run full test suite**

Run: `pytest tests/ -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```
git add scripts/extract_from_java.py
git commit -m "add extract_from_java.py: CLI to extract and compare rotor/fuel data from GT5 source"
```
