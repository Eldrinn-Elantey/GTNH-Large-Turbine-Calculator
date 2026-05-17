# Excel Import Design

**Date:** 2026-05-17  
**Status:** Approved

## Goal

Add `--source excel --file <path>` mode to `scripts/update_web_data.py` so historical GTNH versions (2.7, 2.8, etc.) can be imported from the Excel calculator file with the same diff + confirm workflow as the Java source mode.

## Usage

```
python scripts/update_web_data.py --source excel --file "Large Turbine Calculator (2.7.0-2.8.4).xlsx" --gtnh 2.7
```

- `--source java` (default): existing behavior, requires `--tag`, forbids `--file`
- `--source excel`: new behavior, requires `--file`, forbids `--tag`

## Components

### `scripts/excel_parser.py` (new)

Refactored from `scripts/extract_data.py`. Three public functions:

**`extract_rotors(wb) -> list`**  
Reads sheet "Rotors", rows from row 4, cols I-M for metadata (display name, tier, mining_speed, base_durability, overflow_tier), then the pre-computed stat columns using the COL_OFFSETS mapping. Returns a list of dicts in the same format as `_build_rotors_json()` output — sorted by tier descending.

**`extract_fuels(wb, existing: dict | None) -> dict`**  
Reads sheet "Fuels". Steam fuels from col B/C, gas fuels from col J/K/L, plasma fuels from col O/P, EHE fuels from col R onwards. Returns `{steam, gas, plasma, ehe}` matching `fuels.json` schema. If `existing` is provided, steam section is preserved from it (same as Java mode).

**`extract_steam_gen(wb, existing: dict | None) -> dict`**  
Reads sheet "Fuels". Detects LHE, WWXL, and Thermal Boiler conversion tables by their header strings. Returns `{lhe, wwxl, thermal_boiler}` matching `steam_gen.json` schema. If `existing` is provided and a section is not found in Excel, it is preserved from existing.

### `scripts/update_web_data.py` (extended)

New function `_run_excel(args)`:
1. Load workbook with `openpyxl.load_workbook(args.file, data_only=True)`
2. Read existing `rotors.json`, `fuels.json`, `steam_gen.json` from `web/data/<gtnh>/` if present
3. Call `extract_rotors`, `extract_fuels`, `extract_steam_gen`
4. Print diff for each file using existing `_diff_rotors`, `_diff_fuels`, and new `_diff_steam_gen`
5. Single `[y/N]` confirm
6. Write all three JSON files + update `versions.json`

`main()` updated: `--source` argument (choices: `java`, `excel`, default `java`), `--file` argument (optional), validation that source/file/tag combination is valid.

## Diff for steam_gen

`_diff_steam_gen(new, old)`: for each section (lhe, wwxl, thermal_boiler), compare entries by fluid name — report added, removed, changed (any field differs).

## versions.json update

After writing data files, add the gtnh version string to `versions.json` list if not already present.

## Column mapping (Rotors sheet)

Excel stores pre-computed values. Row layout (0-indexed):
- `[8]` display name, `[9]` tier, `[10]` mining_speed, `[11]` base_durability, `[12]` overflow_tier
- Stats start at col offset 20 (steam_tight_eff for Small), each group of 4 values = [Small, Normal, Large, Huge]
- See `COL_OFFSETS` in existing `extract_data.py` for full mapping

## Out of scope

- Dense Steam fuels (not in Excel)
- Automatic version detection from filename
- CI automation (manual run only)
