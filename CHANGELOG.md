# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.5.1] - 2026-08-23

### Fixed
- 2.9.X steam fuel values were divided by 1000 along with gas and plasma, so steam turbines reported 0 EU/t and an absurd rotor lifetime
- EHE Planner had no data on the 2.9.X set: the ehe section was missing from its fuels.json

## [0.5.0] - 2026-08-23

### Added
- Tight/Loose mode explanation as a tooltip next to the mode toggle, with a link to the GTNH wiki (EN/RU)
- GoatCounter analytics beacon on the web page

### Changed
- README: three data sets instead of two, Settings section documented, rotor and fuel counts no longer hardcoded to one data set

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
