# GTNH Large Turbine Calculator - GUI App Design

**Date:** 2026-05-16
**Stack:** Python + CustomTkinter
**Source data:** Large Turbine Calculator (2.7.0-2.8.4).xlsx

## Overview

Desktop application that replaces the Excel calculator for GTNH turbine planning. Covers all turbine types, EHE setup planning, and reference tables for fuels, rotors, and steam generation. Dark theme, sidebar navigation.

## Features

### Calculator tab

Shared rotor settings at the top (rotor material dropdown, rotor size dropdown). Below that, three turbine cards side by side:

- **Large Steam Turbine** — tight/loose toggle, fuel type dropdown (Steam/SH Steam/SC Steam), effective flow toggle (Optimal/Manual with L/t input). Outputs: optimal flow [L/t] with tier, output [EU/t], dynamo output [Amps + tier], rotor lifetime [days].
- **Large Gas Turbine** — same structure, gas fuels dropdown (Nitrobenzene, Benzene, etc.), flow in L/t.
- **Large Plasma Generator** — same structure, plasma fuels dropdown, flow in L/s (not L/t).

Below the three cards, a collapsible section for XL Turbo variants:
- XL Turbo SC Steam Turbine (has "Is Dense" toggle)
- XL Turbo Gas Turbine
- XL Turbo Plasma Turbine

All calculations update live as the user changes any input.

### EHE Planner tab

Two sub-planners in separate sections:

**Plasma EHE Setup Planner:**
- Inputs: plasma type dropdown, recipe output [L], recipe time [s], EU/t per recipe, parallel count
- Outputs: plasma output [L/s], EHE max input [L/s], total dense SC steam [L/t], rotor fit, rotor efficiency, power per turbine (SC/SH and Reg), dynamo output tier

**Non-XL EHE Setup Planner:**
- Inputs: hot fluid type dropdown, hot fluid input [L/s]
- Outputs: EHE max input [L/s], total SC steam [L/t], total SH steam [L/t], rotor fit, rotor efficiency, power per turbine (SC/SH), dynamo output tier

### Steam Generation tab

Read-only reference table showing conversion ratios for each heat source:
- LHE Conversion: Lava, Hot Coolant, Solar Salt (Hot) — thresholds, max flow, steam type, ratios
- WWXL Conversion: same fluids, higher limits
- Thermal Boiler Conversion: Lava, Pahoehoe Lava, Solar Salt, Hot Coolant — max flow, steam type, ratio

Scrollable table with fixed headers. No inputs — purely informational.

### Fuels tab

Read-only searchable reference table with three sections:
- Steam Turbine Fuels: type, EU/L
- Gas Turbine Fuels: name, EU/L, allowed in XLGT
- Plasma Turbine Fuels: display name, EU/L, and EHE columns (max convert L/s, threshold, EU/t, coolant, steam outputs)

Search field at the top filters rows by name across all sections.

### Rotors tab

Read-only searchable reference table:
- Columns: display name, tier, mining speed, durability, overflow tier, flow multipliers (steam/gas/plasma), efficiency values
- Search field filters by name

## Architecture

```
gtnh_turbine_calc/
├── main.py
├── app.py                  # CTk window, sidebar, frame switching
├── data/
│   ├── fuels.py            # steam/gas/plasma fuel dicts
│   ├── rotors.py           # rotor material dicts
│   └── steam_gen.py        # steam generation conversion tables
├── calc/
│   ├── turbine.py          # all turbine math (EU/t, flow, lifetime, dynamo tier)
│   └── ehe.py              # EHE planner math
└── ui/
    ├── calculator.py       # Calculator tab
    ├── ehe_planner.py      # EHE Planner tab
    ├── steam_gen.py        # Steam Generation tab
    ├── fuels_ref.py        # Fuels reference tab
    ├── rotors_ref.py       # Rotors reference tab
    └── widgets.py          # TurbineCard, ResultRow, SearchableTable, ToggleButton
```

## Calculation Logic

All math is ported from the Excel formulas and the source GT5 Java code referenced in the Rotors sheet. Key formulas:

**Optimal flow (tight mode):** `base_optimal_flow * rotor_speed_multiplier`
**Tight efficiency:** `base_tight_efficiency` from rotor material
**Loose efficiency:** `base_loose_efficiency` from rotor material
**Output EU/t:** `optimal_flow * fuel_value_eu_l * efficiency / 1000` (adjusted per turbine type)
**Rotor lifetime [s]:** `durability / (base_damage + rotor_size_damage) * flow_multiplier`
**Dynamo output [Amps]:** `output_eu_t / dynamo_tier_voltage`
**Min dynamo tier:** smallest tier where 1 amp handles the output

Plasma flows are in L/s; steam and gas flows are in L/t. The UI must clearly label units.

## UI Design

- **Theme:** CustomTkinter dark mode, accent color `#e94560` (red) for active nav item
- **Turbine card colors:** Steam = blue `#3b82f6`, Gas = amber `#f59e0b`, Plasma = purple `#a855f7`
- **Result value colors:** EU/t output = green `#4ade80`, flow = yellow `#facc15`, dynamo = purple `#c084fc`, lifetime = orange `#fb923c`
- **Window size:** 1100x700 minimum, resizable
- **Sidebar width:** 160px fixed
- **Font:** CustomTkinter default (Inter/system)

## Data Extraction

All fuel and rotor data is extracted from the Excel file once during development and stored as Python dicts in `data/`. No runtime dependency on the xlsx file. This makes the app self-contained — users don't need the Excel file.

## Dependencies

- `customtkinter>=5.2.0`
- Python 3.10+
- No other runtime dependencies

## Out of Scope

- Saving/loading user configurations
- Comparing multiple rotor/fuel combinations side by side
- The "2.6 vs 2.7 comparison" and "Misc" Excel sheets
- The "space pumping" Excel sheet
