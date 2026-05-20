# XL Steam Cascade Planner — Design Spec

## Overview

Add a "Steam Cascade" sub-tab inside the existing "XL Turbo Turbines" calculator tab. The planner covers the full SC→HP→Reg turbine chain driven by plasma EHEs, including net power after reactor consumption.

## Placement

Inside `Calculator → XL Turbo Turbines`, two inner sub-tabs:
- **Single Turbine** — existing view (unchanged)
- **Steam Cascade** — new planner

EHE Planner remains in the main navigation unchanged. The cascade planner has its own embedded EHE source block.

## User Inputs (green cells concept)

### EHE Source block
- Plasma type (select, from fuels.json ehe list)
- Recipe output in L (number)
- Recipe time in seconds (number)
- EU/t per recipe (number, manual — not in data files)
- Parallel count / reactor count (number)

### Shared settings block
- Blade size: Small / Normal / Large / Huge (toggle)
- Dynamo tier (select)

### Per-stage settings (SC / HP / Reg — each independent)
- Rotor (searchable combobox, from rotors.json)
- Mode: Tight / Loose (toggle)

## Calculated Outputs

### EHE Source block
- Plasma output [L/s] = recipe_output × parallels / recipe_time
- SC Steam per EHE [L/s] — from EHE calc (existing ehe.js logic)
- EHE count = ceil(plasma_output / sc_steam_per_ehe)
- SC Steam total [L/t] — converted from L/s to L/t (×50)
- Reactor consumption [EU/t] = eu_per_recipe × parallels

### Per-stage cards (SC Steam / HP Steam / Steam)
Steam flow through all stages is identical (1:1 volumetric cascade).

For each stage:
- Optimal flow per turbine [L/t] — from calcXlTurbine with the stage's rotor/mode
- Full cascades = floor(sc_steam_total / optimal_flow)
- Partial cascade flow = sc_steam_total mod optimal_flow
- For each full cascade block: flow = optimal_flow, output = optOutput
- For partial cascade block (if remainder > 0): output via calcXlTurbine with manualFlow = remainder
- Stage total EU/t = sum of all cascade blocks
- Dynamo hatches for stage total
- Rotor lifetime shown per block (full and partial differ)

Note: SC and HP stages use eu_l = 1.0, Reg stage uses eu_l = 0.5 (Steam fuel). All three stages use the same steam volume (1:1 cascade), so cascade counts per stage may differ if rotors differ across stages.

### Summary block
- Full cascades count (from SC stage, as reference)
- Partial cascade: yes/no + flow
- Total turbine count = (full_sc + partial_sc ? 1 : 0) + (full_hp + partial_hp ? 1 : 0) + (full_reg + partial_reg ? 1 : 0)
- Gross power [EU/t] = SC stage total + HP stage total + Reg stage total
- Reactor consumption [EU/t]
- Net power [EU/t] = gross − reactor consumption
- Total dynamo hatches
- Minimum rotor lifetime (across all blocks)

## Key Logic Notes

- XL turbines accept all 4 blade sizes (Small / Normal / Large / Huge) — blade size is a real parameter that affects rotor stats, same as Large turbines
- Fuel values: SC Steam eu_l=1.0, SH Steam (HP) eu_l=1.0, Steam eu_l=0.5
- Cascade is a fundamental unit: N full cascades means N×3 turbines total (one of each type per cascade)
- EHE count is always calculated, never user-entered

## Implementation Files

- New: `web/js/ui/xl_cascade.js` — cascade planner component
- Modified: `web/js/ui/calculator.js` — add inner sub-tabs to XL section
- Modified: `web/js/i18n.js` — add translation strings for new UI
- Reuses: `web/js/calc.js` (`calcXlTurbine`), `web/js/ehe.js` (`calcPlasmaEhe`), existing utils
