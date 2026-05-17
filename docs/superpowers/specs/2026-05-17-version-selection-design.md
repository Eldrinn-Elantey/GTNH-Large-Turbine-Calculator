# Version Selection — Design Spec

## Goal

Allow users to select the GTNH game version whose data (rotors, fuels, steam generators) the calculator uses. Selection persists across sessions.

## Data Structure

```
web/data/
  versions.json         — manifest listing available versions
  2.7/
    rotors.json
    fuels.json
    steam_gen.json
  2.9/
    rotors.json
    fuels.json
    steam_gen.json
```

`versions.json` schema:
```json
[
  { "id": "2.7", "label": "2.7.0-2.8.4" },
  { "id": "2.9", "label": "2.8-2.9" }
]
```

Adding a new version = create a new subfolder + append one entry to `versions.json`. No code changes needed.

Current files in `web/data/` (flat) become `web/data/2.7/` — the 2.7 dataset is the existing data.

## New Module: `js/version.js`

Responsibilities:
- `loadVersions()` — fetch `data/versions.json`, return array
- `getVersion()` — return current version id from `localStorage` (default: first entry in versions.json)
- `setVersion(id)` — save to `localStorage`, trigger data reload

## Data Module Changes

`rotors.js`, `fuels.js`, `steam_gen.js` each have a module-level cache variable (`_rotors`, `_fuels`, etc.) and a `loadData()` function. Changes:
- Import `getVersion` from `version.js`
- Change fetch path: `data/rotors.json` → `data/${getVersion()}/rotors.json`
- Export a `clearCache()` function that sets the cache variable to `null`

## UI

In `index.html`, add a `<select id="version-select">` below the sidebar logo. Populated dynamically from `versions.json` on app init. On change: call `setVersion()`, call `clearCache()` on all three data modules, re-render the currently active section.

In `app.js`: on init, load versions, populate select, restore saved selection.

## Persistence

Selected version stored in `localStorage` key `gtnh-version`. Defaults to the first entry in `versions.json` if not set.
