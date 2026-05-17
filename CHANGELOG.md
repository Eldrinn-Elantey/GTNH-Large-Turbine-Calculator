# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Fixed
- Font size setting now actually scales the UI (was overridden by hardcoded px values)
- Dynamo hatch row now recalculates from effective output in Manual mode

### Changed
- In Optimal mode show Opt. flow / Output rows; in Manual mode show Eff. flow / Eff. output rows instead

## [0.3.0] - 2026-05-17

### Added
- Settings section: font size (Small / Medium / Large) and EN/RU localization
- Version selector (GTNH 2.7 / 2.9 data sets)

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
