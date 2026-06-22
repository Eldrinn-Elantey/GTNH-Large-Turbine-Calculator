# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.5.0] - 2026-05-20

### Added
- Steam Cascade planner inside XL Turbo Turbines tab (new inner sub-tab alongside Single Turbine)
- EHE source block: plasma type, recipe output/time, EU/t per recipe, parallel count; calculates plasma output, EHE count, Dense SC Steam total, and reactor consumption
- Per-stage cards (SC / HP / Reg) with independent rotor and mode; shows full cascade blocks and partial cascade block with EU/t output per block
- Summary block: total turbines, gross power, reactor consumption, net power after reactor costs, dynamo hatches, minimum rotor lifetime

### Changed
- `makeToggle` extracted from calculator.js to utils.js (was duplicated in calculator.js and ehe_planner.js)

## [0.4.0] - 2026-05-17

### Added
- Mobile layout: hamburger menu, slide-in sidebar with overlay, proper scrolling on small screens
- Rotor durability row in calculator card (between rotor efficiency and lifetime)
- Sidebar footer: version badge (links to CHANGELOG) and Issues link to GitHub tracker
- Java extractor scripts: parse rotor stats and fuel values from GT5-Unofficial source (`scripts/update_web_data.py --tag <tag> --gtnh <version>`)
- Excel import mode for `update_web_data.py` (`--source excel --file <path> --gtnh <version>`) with `scripts/excel_parser.py`

### Fixed
- Font size setting now actually scales the UI (was overridden by hardcoded px values)
- Dynamo hatch row now recalculates from effective output in Manual mode

### Changed
- In Optimal mode show Opt. flow / Output rows; in Manual mode show Eff. flow / Eff. output rows instead
- Desktop app moved into `desktop/` subfolder; build CI updated accordingly

## [0.3.0] - 2026-05-17

### Added
- Settings section: font size (Small / Medium / Large) and EN/RU localization
- Version selector (GTNH 2.7.0–2.8.4 / 2.9 data sets)

## [0.2.0] - 2026-05-17

### Added
- Multi-card comparison in Large/XL tabs (add/remove slots)
- Compare Rotors tab with sortable table
- Dynamo hatch count with tier selector
- Lifetime unit toggle (s / min / h / days), default days
- EHE Planner section

### Fixed
- Stable settings layout, fixed-width selects
- Limit calculator card width
- One card with fuel tabs, rotor tier filter

## [0.1.0] - 2026-05-17

### Added
- Web app: sidebar router, Calculator (Large + XL), Fuels, Steam Gen, Rotors sections
- Turbine calc formulas ported to JS (regular + XL, steam/gas/plasma)
- Reusable SortableTable component
- GitHub Pages deployment
