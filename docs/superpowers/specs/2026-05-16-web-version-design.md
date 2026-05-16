# Web Version Design

## Overview

Static website deployable on GitHub Pages. Pure HTML + CSS + JS, no frameworks, no build tools.
All game logic is ported from Python (`calc/turbine.py`, `calc/ehe.py`, `calc/common.py`) to JavaScript.
Game data lives in separate JSON files so it can be updated independently when GTNH releases new versions.

---

## File Structure

```
web/
  index.html              # single HTML shell, all sections rendered by JS
  css/
    style.css             # global dark theme, layout, sidebar
    components.css        # cards, tables, tabs, toggle buttons, inputs
  js/
    app.js                # router: sidebar navigation, section switching
    calc.js               # ported turbine formulas (calc_regular_turbine, calc_xl_turbine)
    ehe.js                # ported EHE formulas (calc_plasma_ehe, calc_nonxl_ehe)
    ui/
      calculator.js       # Calculator section: Large + XL sub-tabs
      ehe_planner.js      # EHE Planner section
      steam_gen.js        # Steam Gen section
      fuels.js            # Fuels section
      rotors.js           # Rotors section
    table.js              # reusable sortable/searchable table component
    utils.js              # formatNumber, findDynamoTier, DYNAMO_TIERS
  data/
    rotors.json           # 136 rotors with all size stats
    fuels.json            # steam (3), gas (28), plasma (128) fuels
    steam_gen.json        # LHE / WWXL / Thermal Boiler reference data
  scripts/
    export_data.py        # one-time script: dumps Python data dicts to JSON files
```

---

## Visual Design

**Theme:** Dark. Background `#0d1117`, cards `#111827`, borders `#1f2937`.
- Green `#4ade80` — result numbers
- Red `#e94560` — active sidebar item, accents
- Yellow `#facc15` — warnings (lifetime)
- Cyan `#00d4ff` — fuel/flow values
- Purple `#c084fc` — plasma accents
- Orange `#fb923c` — gas accents
- Blue `#60a5fa` — steam accents

**Typography:** system-ui, 13px base. Numbers bold. Labels `#6b7280`.

---

## Layout

```
+--160px sidebar--+------------- main content ---------------+
| GTNH logo       |  section header                          |
|                 |                                           |
| ⚡ Calculator   |  section body (scrollable)               |
| 🔥 EHE Planner  |                                           |
| 💧 Steam Gen    |                                           |
| ⛽ Fuels        |                                           |
| 🔩 Rotors       |                                           |
+-----------------+-------------------------------------------+
```

Sidebar is fixed-width, full-height. Active item highlighted red. Main area scrolls independently.

---

## Sections

### 1. Calculator

Two sub-tabs: **Large Turbines** and **XL Turbo Turbines**.

**Shared settings (above the card):**
- Rotor: searchable dropdown, all 136 rotors
- Blade Size: toggle (Small / Normal / Large / Huge)
- Dynamo Tier: dropdown (LV … MAX++++)

**Turbine card — tabs inside:**
- Tabs: Steam | Gas | Plasma
- Per tab:
  - Mode toggle: Tight / Loose
  - Fuel: dropdown (filtered by tab type)
  - Flow: toggle Optimal / Manual; if Manual, numeric input
  - Results displayed below:
    - Optimal flow (L/t or L/s for plasma)
    - Output EU/t (optimal)
    - Dynamo hatch count
    - Effective flow / output (only shown when Manual)
    - Rotor efficiency %
    - Rotor lifetime (s)

Results recalculate on any input change. XL tab additionally has Dense toggle for steam.

Port formulas from `calc/turbine.py` verbatim:
- `calcRegularTurbine(type, rotor, size, mode, fuelType, fuelValue, manualFlow)`
- `calcXlTurbine(type, rotor, size, mode, fuelType, fuelValue, isDense, manualFlow)`
- Helper functions: `_flowEfficiencySteam`, `_flowEfficiencyGas`, `_flowEfficiencyPlasma`, `_lifetimeRegular`, `_lifetimeXl`
- Constants: `TURBINE_TO_ROTOR_SIZE`, `TURBINE_TO_DUR_SIZE` (must match Python exactly)

### 2. EHE Planner

Two planners side by side:

**Plasma EHE** (left):
- Inputs: plasma type dropdown, recipe output (L), recipe time (s), parallel count
- Rotor + size + mode (shared with calculator or independent — same controls)
- Results: plasma output L/s, EHE count, dense SC steam L/t, XL turbine count, power/turbine, dynamo tier

**Non-XL EHE** (right):
- Inputs: hot fluid dropdown (Lava / IC2 Hot Coolant / Solar Salt Hot), flow L/s
- Rotor + size + mode
- Results: SC steam L/t, SH steam L/t, turbine count (SC / SH), power/turbine, EHE count

Port from `calc/ehe.py`.

### 3. Steam Gen

Static reference table. Three sub-sections (LHE / Whakawhiti Wera XL / Thermal Boiler).
Each shows threshold, max flow, steam ratios. No interactivity needed — render from `steam_gen.json`.

### 4. Fuels

Three sub-tabs: Steam | Gas | Plasma.
Each tab is a searchable + sortable table.

- Steam: Name, EU/L (3 rows)
- Gas: Name, EU/L, XLGT flag (28 rows)
- Plasma: Name, EU/L sorted descending (128 rows)

### 5. Rotors

Single searchable + sortable table. 136 rotors.
Size toggle (Small / Normal / Large / Huge) switches which size columns are shown.
Columns: Display Name, Tier, Base Dur, Overflow, Eff (Tight/Loose), Opt Flow (Tight/Loose).

---

## Reusable Components (JS)

### `table.js` — SortableTable

```js
new SortableTable(containerEl, columns, rows)
// columns: [{key, label, numeric, width}]
// rows: array of objects
// Features: click header to sort (numeric-aware), search input filters all columns
```

### `utils.js`

```js
formatNumber(n)           // "1,024,000" with thousands separators
findDynamoTier(euPerT)    // returns tier name string
DYNAMO_TIERS              // [{name, voltage}] array
```

---

## Data Files

### `rotors.json`

```json
[
  {
    "name": "Neutronium (6)",
    "tier": 6,
    "base_durability": 131072000,
    "overflow_tier": 3,
    "sizes": {
      "Small":  {"steam_tight_eff": ..., "steam_loose_eff": ..., "steam_opt_flow_tight": ..., ...},
      "Normal": {...},
      "Large":  {...},
      "Huge":   {...}
    }
  }
]
```

### `fuels.json`

```json
{
  "steam": {"Steam": 0.5, "SH Steam": 1.0, "SC Steam": 2.0},
  "gas":   [{"name": "Naquadah", "eu_l": 640000, "xlgt": false}, ...],
  "plasma": [{"name": "Naquadah (Nq+)", "eu_l": 6553600}, ...]
}
```

### `steam_gen.json`

```json
[
  {
    "name": "Large Heat Exchanger",
    "threshold_ls": 80000,
    "max_flow_ls": 160000,
    "ratios": "..."
  }
]
```

---

## Data Export Script

`scripts/export_data.py` reads existing Python data modules and writes JSON files:

```python
# Usage: python scripts/export_data.py
# Writes: web/data/rotors.json, web/data/fuels.json, web/data/steam_gen.json
```

Run once after any data change. JSON files are committed to repo — no runtime Python needed.

---

## Deployment

GitHub Actions workflow (`.github/workflows/deploy-web.yml`) triggers on push to `main`.
Copies `web/` directory to GitHub Pages via `actions/deploy-pages`.
No build step needed — pure static files.

---

## Out of Scope

- Mobile layout (desktop-first, sidebar always visible)
- Dark/light theme toggle
- Saving/loading configurations
- Friend's suggestion (all-sizes-per-fuel table) — potential future enhancement
