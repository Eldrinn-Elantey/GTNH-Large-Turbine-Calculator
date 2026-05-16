# GTNH Large Turbine Calculator

Desktop calculator for Large and XL Turbo turbines from **GregTech: New Horizons** (GT5-Unofficial).

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![PySide6](https://img.shields.io/badge/UI-PySide6-green)
![GTNH](https://img.shields.io/badge/GTNH-2.7.0--2.8.4-orange)

## Download

Grab the latest `GTNH-Turbine-Calc.exe` from [Releases](../../releases) — no Python required.

## Features

### ⚡ Calculator

Two sub-tabs — **Large Turbines** and **XL Turbo Turbines** — each with:

- Shared settings: rotor tier filter, material (136 rotors), blade size (Small / Normal / Large / Huge), dynamo hatch tier
- Three cards side by side: **Steam**, **Gas**, **Plasma**
- Per-card: Tight/Loose mode, fuel selector, Optimal/Manual flow
- Results: optimal flow, output EU/t, dynamo hatch count, effective flow/output, rotor lifetime

### 🔥 EHE Planner

Two planners on one screen:

- **Plasma EHE** — input recipe parameters, get EHE count, SC steam output, turbine count and power
- **Non-XL EHE** — input hot fluid flow, get SC/SH steam split and turbine count

### 💧 Steam Gen

Reference table for Large Heat Exchanger, Whakawhiti Wera XL, and Thermal Boiler — threshold, max flow, ratios.

### ⛽ Fuels

Searchable reference tables:
- Steam (3 types)
- Gas (28 fuels, XLGT flag)
- Plasma (128 fuels, sorted by EU/L)

### 🔩 Rotors

Full rotor database — 136 rotors, 9 columns, filterable by blade size and searchable. Shows efficiency, durability, optimal flow for all sizes.

## Running from source

```bash
pip install PySide6
python -m gtnh_turbine_calc.main
```

## Building the exe

```bash
pip install PySide6 pyinstaller
python build_slim.py
# output: dist/GTNH-Turbine-Calc.exe (~47 MB)
```

Or push a version tag to trigger GitHub Actions:

```bash
git tag v2.7.0
git push origin v2.7.0
```

## Tests

```bash
pip install pytest
python -m pytest tests/ -q
```

## Data sources

Rotor stats and turbine formulas verified against GT5-Unofficial source and cross-checked with community Excel sheets.
GTNH versions 2.7.0 – 2.8.4.
