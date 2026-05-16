# Web Version Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pure HTML/CSS/JS static website for the GTNH Turbine Calculator, deployable on GitHub Pages with no build step.

**Architecture:** Single `index.html` shell with a fixed left sidebar and a main content area. All sections are rendered by vanilla JS modules. Game data lives in JSON files (updated independently from code). Turbine formulas are ported verbatim from `gtnh_turbine_calc/calc/turbine.py` and `ehe.py`.

**Tech Stack:** HTML5, CSS3, vanilla ES modules (no framework, no bundler), Python 3.x for one-time data export script, GitHub Actions for deployment.

---

## File Map

| File | Purpose |
|------|---------|
| `web/index.html` | HTML shell: sidebar + main content div, loads all JS modules |
| `web/css/style.css` | Dark theme vars, layout (sidebar + main), scrollbar, sidebar nav items |
| `web/css/components.css` | Cards, toggle buttons, dropdowns, inputs, result rows, sub-tabs |
| `web/js/app.js` | Sidebar router: shows/hides sections, initialises each section on first visit |
| `web/js/utils.js` | `formatNumber`, `findDynamoTier`, `DYNAMO_TIERS` |
| `web/js/table.js` | `SortableTable` class: sortable + searchable table component |
| `web/js/calc.js` | Ported turbine math: `calcRegularTurbine`, `calcXlTurbine`, helpers |
| `web/js/ehe.js` | Ported EHE math: `calcPlasmaEhe`, `calcNonxlEhe`, helpers |
| `web/js/ui/calculator.js` | Calculator section: Large + XL sub-tabs, inputs, result display |
| `web/js/ui/ehe_planner.js` | EHE Planner section: Plasma EHE + Non-XL EHE planners |
| `web/js/ui/fuels.js` | Fuels section: Steam/Gas/Plasma searchable tables |
| `web/js/ui/rotors.js` | Rotors section: size toggle + searchable/sortable table |
| `web/js/ui/steam_gen.js` | Steam Gen section: static reference tables from JSON |
| `web/data/rotors.json` | 136 rotors with all size stats |
| `web/data/fuels.json` | Steam/gas/plasma fuel lists |
| `web/data/steam_gen.json` | LHE / WWXL / Thermal Boiler reference data |
| `scripts/export_data.py` | Dumps Python data dicts to JSON files |
| `.github/workflows/deploy-web.yml` | GitHub Pages deployment on push to main |

---

## Task 1: Data export script

**Files:**
- Create: `scripts/export_data.py`
- Creates: `web/data/rotors.json`, `web/data/fuels.json`, `web/data/steam_gen.json`

- [ ] **Step 1: Create the web/data/ directory**

```bash
mkdir -p web/data
```

- [ ] **Step 2: Write the export script**

Create `scripts/export_data.py`:

```python
"""Export Python game data to JSON files for the web version.

Run from the repo root:
    python scripts/export_data.py

Outputs:
    web/data/rotors.json
    web/data/fuels.json
    web/data/steam_gen.json
"""
import json
import sys
from pathlib import Path

# Allow importing from the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from gtnh_turbine_calc.data.rotors import ROTORS
from gtnh_turbine_calc.data.fuels import STEAM_FUELS, GAS_FUELS, PLASMA_FUELS, EHE_FUELS
from gtnh_turbine_calc.data.steam_gen import STEAM_GEN_DATA

OUT = Path(__file__).parent.parent / "web" / "data"
OUT.mkdir(parents=True, exist_ok=True)


# --- rotors.json ---
# ROTORS is a list of dicts: {name, tier, base_durability, overflow_tier, sizes: {Small/Normal/Large/Huge: {...}}}
(OUT / "rotors.json").write_text(
    json.dumps(ROTORS, indent=2),
    encoding="utf-8",
)
print(f"Wrote {len(ROTORS)} rotors -> web/data/rotors.json")


# --- fuels.json ---
# GAS_FUELS: list of {name, eu_l, xlgt}
# PLASMA_FUELS: list of {name, eu_l}
# STEAM_FUELS: dict {name: eu_l}
# EHE_FUELS: dict {plasma_name: {max_convert_ls, max_hot_steam_ls, ...}}
fuels = {
    "steam": [{"name": k, "eu_l": v} for k, v in STEAM_FUELS.items()],
    "gas": GAS_FUELS,
    "plasma": PLASMA_FUELS,
    "ehe": EHE_FUELS,
}
(OUT / "fuels.json").write_text(
    json.dumps(fuels, indent=2),
    encoding="utf-8",
)
print(f"Wrote fuels -> web/data/fuels.json")


# --- steam_gen.json ---
(OUT / "steam_gen.json").write_text(
    json.dumps(STEAM_GEN_DATA, indent=2),
    encoding="utf-8",
)
print(f"Wrote steam_gen -> web/data/steam_gen.json")
```

- [ ] **Step 3: Inspect the actual data module structure**

Run to see what ROTORS / STEAM_FUELS / GAS_FUELS etc. actually look like:

```bash
python -c "
from gtnh_turbine_calc.data.rotors import ROTORS
from gtnh_turbine_calc.data.fuels import STEAM_FUELS, GAS_FUELS, PLASMA_FUELS
from gtnh_turbine_calc.data.steam_gen import STEAM_GEN_DATA
print('ROTORS[0]:', ROTORS[0])
print('STEAM_FUELS:', STEAM_FUELS)
print('GAS_FUELS[0]:', GAS_FUELS[0])
print('PLASMA_FUELS[0]:', PLASMA_FUELS[0])
print('STEAM_GEN_DATA:', STEAM_GEN_DATA)
"
```

Adjust the export script if the actual structure differs from what the script assumes. The JSON output must preserve all fields used by the web JS.

- [ ] **Step 4: Run the export script**

```bash
python scripts/export_data.py
```

Expected output:
```
Wrote 136 rotors -> web/data/rotors.json
Wrote fuels -> web/data/fuels.json
Wrote steam_gen -> web/data/steam_gen.json
```

- [ ] **Step 5: Verify JSON files are valid and have expected content**

```bash
python -c "
import json
r = json.load(open('web/data/rotors.json'))
f = json.load(open('web/data/fuels.json'))
s = json.load(open('web/data/steam_gen.json'))
print(f'Rotors: {len(r)}, Fuels steam: {len(f[\"steam\"])}, gas: {len(f[\"gas\"])}, plasma: {len(f[\"plasma\"])}')
print('First rotor keys:', list(r[0].keys()))
print('First rotor sizes keys:', list(r[0][\"sizes\"].keys()))
print('First size stat keys:', list(r[0][\"sizes\"][\"Small\"].keys()))
"
```

Expected: 136 rotors, 3 steam fuels, 28 gas fuels, 128 plasma fuels. Each rotor has sizes Small/Normal/Large/Huge with keys like `steam_tight_eff`, `steam_opt_flow_tight`, etc.

- [ ] **Step 6: Commit**

```bash
git add scripts/export_data.py web/data/
git commit -m "add data export script and web JSON data files"
```

---

## Task 2: HTML shell + CSS foundation

**Files:**
- Create: `web/index.html`
- Create: `web/css/style.css`
- Create: `web/css/components.css`

- [ ] **Step 1: Create web/ directory structure**

```bash
mkdir -p web/css web/js/ui
```

- [ ] **Step 2: Write `web/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GTNH Turbine Calculator</title>
  <link rel="stylesheet" href="css/style.css">
  <link rel="stylesheet" href="css/components.css">
</head>
<body>
  <div class="layout">
    <nav class="sidebar">
      <div class="sidebar-logo">GTNH<br><span>Turbines</span></div>
      <ul class="nav-list">
        <li class="nav-item active" data-section="calculator">⚡ Calculator</li>
        <li class="nav-item" data-section="ehe">🔥 EHE Planner</li>
        <li class="nav-item" data-section="steam-gen">💧 Steam Gen</li>
        <li class="nav-item" data-section="fuels">⛽ Fuels</li>
        <li class="nav-item" data-section="rotors">🔩 Rotors</li>
      </ul>
    </nav>
    <main class="main-content">
      <div id="section-calculator" class="section"></div>
      <div id="section-ehe" class="section hidden"></div>
      <div id="section-steam-gen" class="section hidden"></div>
      <div id="section-fuels" class="section hidden"></div>
      <div id="section-rotors" class="section hidden"></div>
    </main>
  </div>
  <script type="module" src="js/app.js"></script>
</body>
</html>
```

- [ ] **Step 3: Write `web/css/style.css`**

```css
:root {
  --bg:        #0d1117;
  --card:      #111827;
  --border:    #1f2937;
  --text:      #d1d5db;
  --muted:     #6b7280;
  --green:     #4ade80;
  --red:       #e94560;
  --yellow:    #facc15;
  --cyan:      #00d4ff;
  --purple:    #c084fc;
  --orange:    #fb923c;
  --blue:      #60a5fa;
  --sidebar-w: 160px;
  --font:      system-ui, -apple-system, sans-serif;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font);
  font-size: 13px;
  height: 100vh;
  overflow: hidden;
}

.layout {
  display: flex;
  height: 100vh;
}

/* Sidebar */
.sidebar {
  width: var(--sidebar-w);
  flex-shrink: 0;
  background: var(--card);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  padding: 16px 0;
}

.sidebar-logo {
  color: var(--red);
  font-size: 14px;
  font-weight: bold;
  padding: 0 16px 16px;
  border-bottom: 1px solid var(--border);
  line-height: 1.3;
}

.sidebar-logo span { color: var(--muted); font-size: 11px; font-weight: normal; }

.nav-list { list-style: none; margin-top: 8px; }

.nav-item {
  padding: 8px 16px;
  cursor: pointer;
  color: var(--muted);
  font-size: 13px;
  border-radius: 0;
  transition: background 0.1s, color 0.1s;
  user-select: none;
}

.nav-item:hover { background: #1f2937; color: var(--text); }

.nav-item.active {
  background: #1e1a2e;
  color: var(--red);
  border-left: 3px solid var(--red);
  padding-left: 13px;
}

/* Main content */
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.section { width: 100%; }
.hidden { display: none !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: #374151; border-radius: 3px; }

/* Section heading */
.section-title {
  font-size: 18px;
  font-weight: bold;
  color: var(--text);
  margin-bottom: 20px;
}
```

- [ ] **Step 4: Write `web/css/components.css`**

```css
/* Sub-tabs (Large / XL Turbo inside Calculator, etc.) */
.sub-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid var(--border);
  margin-bottom: 20px;
}

.sub-tab {
  padding: 6px 18px;
  cursor: pointer;
  color: var(--muted);
  font-size: 13px;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  user-select: none;
  transition: color 0.1s;
}

.sub-tab:hover { color: var(--text); }
.sub-tab.active { color: var(--text); border-bottom-color: var(--red); }

/* Toggle button group */
.toggle-group {
  display: inline-flex;
  background: #1f2937;
  border-radius: 6px;
  padding: 2px;
  gap: 2px;
}

.toggle-btn {
  padding: 4px 12px;
  border: none;
  background: transparent;
  color: var(--muted);
  font-size: 12px;
  border-radius: 4px;
  cursor: pointer;
  font-family: var(--font);
  transition: background 0.1s, color 0.1s;
}

.toggle-btn:hover { background: #374151; color: var(--text); }
.toggle-btn.active { background: #1e40af; color: #93c5fd; }

/* Card */
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px;
}

/* Settings row (label + control) */
.setting-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.setting-label {
  color: var(--muted);
  font-size: 12px;
  min-width: 90px;
}

/* Select / dropdown */
select {
  background: #1f2937;
  color: var(--cyan);
  border: 1px solid #374151;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  font-family: var(--font);
  cursor: pointer;
  outline: none;
  max-width: 240px;
}

select:focus { border-color: #4b5563; }

/* Text input */
input[type="number"], input[type="text"] {
  background: #1f2937;
  color: var(--text);
  border: 1px solid #374151;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  font-family: var(--font);
  outline: none;
  width: 100px;
}

input[type="number"]:focus, input[type="text"]:focus { border-color: #4b5563; }

/* Remove number input arrows */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; }

/* Result row */
.result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 3px 0;
  font-size: 13px;
}

.result-label { color: var(--muted); }
.result-value { font-weight: bold; }
.result-value.green  { color: var(--green); }
.result-value.yellow { color: var(--yellow); }
.result-value.cyan   { color: var(--cyan); }
.result-value.muted  { color: var(--muted); }

/* Divider */
.divider {
  border: none;
  border-top: 1px solid var(--border);
  margin: 10px 0;
}

/* Fuel tabs (Steam / Gas / Plasma inside turbine card) */
.fuel-tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
  margin-bottom: 12px;
}

.fuel-tab {
  padding: 5px 14px;
  cursor: pointer;
  font-size: 12px;
  color: var(--muted);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  user-select: none;
}

.fuel-tab:hover { color: var(--text); }
.fuel-tab.active { color: var(--text); border-bottom-color: #4b5563; }
.fuel-tab.steam.active  { border-bottom-color: var(--blue);   color: var(--blue); }
.fuel-tab.gas.active    { border-bottom-color: var(--orange);  color: var(--orange); }
.fuel-tab.plasma.active { border-bottom-color: var(--purple);  color: var(--purple); }

/* Table */
.table-wrap { overflow-x: auto; }

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.data-table th {
  background: #1f2937;
  color: var(--muted);
  padding: 6px 10px;
  text-align: left;
  font-weight: bold;
  cursor: pointer;
  white-space: nowrap;
  user-select: none;
}

.data-table th.numeric { text-align: center; }
.data-table th .sort-arrow { margin-left: 4px; opacity: 0.4; }
.data-table th.sorted .sort-arrow { opacity: 1; }

.data-table td {
  padding: 5px 10px;
  border-bottom: 1px solid var(--border);
  color: var(--text);
}

.data-table td.numeric { text-align: center; }
.data-table tr:hover td { background: #161d2b; }

/* Search box above table */
.search-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--card);
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
}

.search-input {
  flex: 1;
  background: #1f2937;
  color: var(--text);
  border: 1px solid #374151;
  border-radius: 4px;
  padding: 5px 10px;
  font-size: 12px;
  font-family: var(--font);
  outline: none;
  max-width: 300px;
}

.search-input:focus { border-color: #4b5563; }

/* Grid helpers */
.row { display: flex; gap: 16px; }
.col { flex: 1; }
```

- [ ] **Step 5: Verify HTML renders**

Start a local server from the `web/` directory:

```bash
cd web && python -m http.server 8080
```

Open http://localhost:8080 in browser. Expected: dark page with left sidebar containing 5 nav items, main area empty (no JS yet).

- [ ] **Step 6: Commit**

```bash
git add web/index.html web/css/
git commit -m "add web HTML shell and CSS foundation"
```

---

## Task 3: Utilities + sidebar router

**Files:**
- Create: `web/js/utils.js`
- Create: `web/js/app.js`

- [ ] **Step 1: Write `web/js/utils.js`**

```js
export const DYNAMO_TIERS = [
  ["LV",       32],
  ["MV",       128],
  ["HV",       512],
  ["EV",       2048],
  ["IV",       8192],
  ["LuV",      32768],
  ["ZPM",      131072],
  ["UV",       524288],
  ["UHV",      2097152],
  ["UEV",      8388608],
  ["UIV",      33554432],
  ["UMV",      134217728],
  ["UXV",      536870912],
  ["MAX",      2147483648],
  ["MAX+",     8589934592],
  ["MAX++",    34359738368],
  ["MAX+++",   137438953472],
  ["MAX++++",  549755813888],
];

/**
 * Return the minimum dynamo tier name that can output >= euPerT EU/t at 1 amp.
 * @param {number} euPerT
 * @returns {string}
 */
export function findDynamoTier(euPerT) {
  for (const [name, voltage] of DYNAMO_TIERS) {
    if (voltage > euPerT) return name;
  }
  return "MAX++++";
}

/**
 * Format a number with thousands separators: 1234567 -> "1,234,567".
 * Floats are rounded to 2 decimal places if fractional.
 * @param {number} n
 * @returns {string}
 */
export function formatNumber(n) {
  if (n === null || n === undefined || isNaN(n)) return "—";
  const rounded = Number.isInteger(n) ? n : Math.round(n * 100) / 100;
  return rounded.toLocaleString("en-US");
}

/**
 * Populate a <select> element with options from an array.
 * @param {HTMLSelectElement} sel
 * @param {string[]} items - option text values
 * @param {string} [selected] - which value to select by default
 */
export function populateSelect(sel, items, selected = null) {
  sel.innerHTML = "";
  for (const item of items) {
    const opt = document.createElement("option");
    opt.value = item;
    opt.textContent = item;
    if (item === selected) opt.selected = true;
    sel.appendChild(opt);
  }
}
```

- [ ] **Step 2: Write `web/js/app.js`**

```js
import { initCalculator } from "./ui/calculator.js";
import { initEhePlanner } from "./ui/ehe_planner.js";
import { initSteamGen }   from "./ui/steam_gen.js";
import { initFuels }      from "./ui/fuels.js";
import { initRotors }     from "./ui/rotors.js";

// Map section id -> init function (called once on first visit)
const SECTIONS = {
  "calculator": initCalculator,
  "ehe":        initEhePlanner,
  "steam-gen":  initSteamGen,
  "fuels":      initFuels,
  "rotors":     initRotors,
};

const initialised = new Set();

function showSection(sectionId) {
  // Hide all sections
  document.querySelectorAll(".section").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));

  // Show target section
  const sectionEl = document.getElementById(`section-${sectionId}`);
  if (!sectionEl) return;
  sectionEl.classList.remove("hidden");

  // Mark nav item active
  const navItem = document.querySelector(`.nav-item[data-section="${sectionId}"]`);
  if (navItem) navItem.classList.add("active");

  // Init section on first visit
  if (!initialised.has(sectionId) && SECTIONS[sectionId]) {
    SECTIONS[sectionId](sectionEl);
    initialised.add(sectionId);
  }
}

// Wire up sidebar clicks
document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", () => showSection(item.dataset.section));
});

// Init the default section (calculator)
showSection("calculator");
```

- [ ] **Step 3: Create stub UI modules so app.js doesn't crash**

Create each file with a placeholder that renders a visible heading:

`web/js/ui/calculator.js`:
```js
export function initCalculator(el) {
  el.innerHTML = "<h2 class='section-title'>⚡ Calculator</h2><p style='color:#6b7280'>Coming soon...</p>";
}
```

`web/js/ui/ehe_planner.js`:
```js
export function initEhePlanner(el) {
  el.innerHTML = "<h2 class='section-title'>🔥 EHE Planner</h2><p style='color:#6b7280'>Coming soon...</p>";
}
```

`web/js/ui/steam_gen.js`:
```js
export function initSteamGen(el) {
  el.innerHTML = "<h2 class='section-title'>💧 Steam Gen</h2><p style='color:#6b7280'>Coming soon...</p>";
}
```

`web/js/ui/fuels.js`:
```js
export function initFuels(el) {
  el.innerHTML = "<h2 class='section-title'>⛽ Fuels</h2><p style='color:#6b7280'>Coming soon...</p>";
}
```

`web/js/ui/rotors.js`:
```js
export function initRotors(el) {
  el.innerHTML = "<h2 class='section-title'>🔩 Rotors</h2><p style='color:#6b7280'>Coming soon...</p>";
}
```

- [ ] **Step 4: Verify navigation works**

Refresh http://localhost:8080. Expected:
- Calculator section shows "Coming soon..." by default
- Clicking each sidebar item switches to that section
- Active sidebar item highlighted red with left border
- No console errors

- [ ] **Step 5: Commit**

```bash
git add web/js/
git commit -m "add sidebar router and utility modules"
```

---

## Task 4: SortableTable component

**Files:**
- Create: `web/js/table.js`

- [ ] **Step 1: Write `web/js/table.js`**

```js
/**
 * SortableTable — renders a searchable, sortable HTML table into a container element.
 *
 * Usage:
 *   const t = new SortableTable(containerEl, columns, rows);
 *   t.render();
 *
 * columns: Array of { key: string, label: string, numeric: boolean, width?: string }
 * rows: Array of objects with keys matching column.key values
 */
export class SortableTable {
  constructor(container, columns, rows) {
    this._container = container;
    this._columns = columns;
    this._rows = rows;
    this._filtered = [...rows];
    this._sortCol = null;
    this._sortAsc = true;
    this._query = "";
  }

  render() {
    this._container.innerHTML = "";

    // Search bar
    const searchWrap = document.createElement("div");
    searchWrap.className = "search-wrap";
    searchWrap.innerHTML = `<span style="color:#6b7280">🔍</span>`;
    const input = document.createElement("input");
    input.type = "text";
    input.className = "search-input";
    input.placeholder = "Search...";
    input.value = this._query;
    input.addEventListener("input", e => {
      this._query = e.target.value.toLowerCase();
      this._applyFilter();
      this._renderBody();
    });
    searchWrap.appendChild(input);
    this._container.appendChild(searchWrap);

    // Table wrap
    const wrap = document.createElement("div");
    wrap.className = "table-wrap";
    const table = document.createElement("table");
    table.className = "data-table";

    // Header
    const thead = document.createElement("thead");
    const hrow = document.createElement("tr");
    for (const col of this._columns) {
      const th = document.createElement("th");
      th.textContent = col.label;
      if (col.numeric) th.classList.add("numeric");
      if (col.width) th.style.width = col.width;
      const arrow = document.createElement("span");
      arrow.className = "sort-arrow";
      arrow.textContent = "↕";
      th.appendChild(arrow);
      th.addEventListener("click", () => this._sort(col.key, col.numeric, th, arrow));
      hrow.appendChild(th);
    }
    thead.appendChild(hrow);
    table.appendChild(thead);

    this._tbody = document.createElement("tbody");
    table.appendChild(this._tbody);
    wrap.appendChild(table);
    this._container.appendChild(wrap);

    this._applyFilter();
    this._renderBody();
  }

  _applyFilter() {
    if (!this._query) {
      this._filtered = [...this._rows];
    } else {
      this._filtered = this._rows.filter(row =>
        this._columns.some(col => {
          const val = row[col.key];
          return val != null && String(val).toLowerCase().includes(this._query);
        })
      );
    }
    if (this._sortCol) this._doSort();
  }

  _sort(key, numeric, th, arrow) {
    if (this._sortCol === key) {
      this._sortAsc = !this._sortAsc;
    } else {
      this._sortCol = key;
      this._sortAsc = true;
    }

    // Update header styles
    this._container.querySelectorAll("th").forEach(h => {
      h.classList.remove("sorted");
      h.querySelector(".sort-arrow").textContent = "↕";
    });
    th.classList.add("sorted");
    arrow.textContent = this._sortAsc ? "↑" : "↓";

    this._doSort();
    this._renderBody();
  }

  _doSort() {
    const key = this._sortCol;
    const asc = this._sortAsc;
    this._filtered.sort((a, b) => {
      let av = a[key], bv = b[key];
      const an = parseFloat(String(av).replace(/,/g, ""));
      const bn = parseFloat(String(bv).replace(/,/g, ""));
      if (!isNaN(an) && !isNaN(bn)) {
        av = an; bv = bn;
      }
      if (av < bv) return asc ? -1 : 1;
      if (av > bv) return asc ? 1 : -1;
      return 0;
    });
  }

  _renderBody() {
    this._tbody.innerHTML = "";
    for (const row of this._filtered) {
      const tr = document.createElement("tr");
      for (const col of this._columns) {
        const td = document.createElement("td");
        if (col.numeric) td.classList.add("numeric");
        td.textContent = row[col.key] ?? "—";
        tr.appendChild(td);
      }
      this._tbody.appendChild(tr);
    }
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add web/js/table.js
git commit -m "add SortableTable reusable component"
```

---

## Task 5: Fuels + Steam Gen sections

**Files:**
- Modify: `web/js/ui/fuels.js`
- Modify: `web/js/ui/steam_gen.js`

- [ ] **Step 1: Write `web/js/ui/fuels.js`**

```js
import { SortableTable } from "../table.js";

let _data = null;

async function loadData() {
  if (_data) return _data;
  const res = await fetch("data/fuels.json");
  _data = await res.json();
  return _data;
}

export async function initFuels(el) {
  el.innerHTML = `
    <h2 class="section-title">⛽ Fuels</h2>
    <div class="sub-tabs">
      <div class="sub-tab active" data-tab="steam">💧 Steam</div>
      <div class="sub-tab" data-tab="gas">🔥 Gas</div>
      <div class="sub-tab" data-tab="plasma">⚡ Plasma</div>
    </div>
    <div id="fuels-content"></div>
  `;

  const data = await loadData();
  const contentEl = el.querySelector("#fuels-content");

  // Prepare row data
  const steamRows = data.steam.map(f => ({ name: f.name, eu_l: f.eu_l }));

  const gasRows = data.gas.map(f => ({
    name: f.name,
    eu_l: f.eu_l,
    xlgt: f.xlgt ? "Yes" : "No",
  }));

  const plasmaRows = [...data.plasma]
    .sort((a, b) => b.eu_l - a.eu_l)
    .map(f => ({ name: f.name, eu_l: f.eu_l }));

  const tables = {
    steam: new SortableTable(document.createElement("div"), [
      { key: "name",  label: "Name",   numeric: false, width: "60%" },
      { key: "eu_l",  label: "EU/L",   numeric: true  },
    ], steamRows),
    gas: new SortableTable(document.createElement("div"), [
      { key: "name",  label: "Name",   numeric: false, width: "55%" },
      { key: "eu_l",  label: "EU/L",   numeric: true  },
      { key: "xlgt",  label: "XLGT",   numeric: false },
    ], gasRows),
    plasma: new SortableTable(document.createElement("div"), [
      { key: "name",  label: "Name",   numeric: false, width: "60%" },
      { key: "eu_l",  label: "EU/L",   numeric: true  },
    ], plasmaRows),
  };

  let currentTab = "steam";

  function showTab(tab) {
    currentTab = tab;
    el.querySelectorAll(".sub-tab").forEach(t =>
      t.classList.toggle("active", t.dataset.tab === tab)
    );
    const tableEl = tables[tab]._container;
    tables[tab].render();
    contentEl.innerHTML = "";
    contentEl.appendChild(tableEl);
  }

  el.querySelectorAll(".sub-tab").forEach(t =>
    t.addEventListener("click", () => showTab(t.dataset.tab))
  );

  showTab("steam");
}
```

- [ ] **Step 2: Write `web/js/ui/steam_gen.js`**

Open `web/data/steam_gen.json` and inspect actual structure first:

```bash
python -c "import json; d=json.load(open('web/data/steam_gen.json')); print(type(d)); print(d if isinstance(d, list) else list(d.keys()))"
```

Then write steam_gen.js. The file renders a static reference table from the JSON. Adjust field names below to match actual JSON structure after inspecting it:

```js
let _data = null;

async function loadData() {
  if (_data) return _data;
  const res = await fetch("data/steam_gen.json");
  _data = await res.json();
  return _data;
}

export async function initSteamGen(el) {
  const data = await loadData();

  // Render function — adjust field names to match actual steam_gen.json keys
  function renderSection(title, rows, columns) {
    const div = document.createElement("div");
    div.style.marginBottom = "24px";
    div.innerHTML = `<h3 style="color:#9ca3af;font-size:13px;margin-bottom:10px;">${title}</h3>`;

    const wrap = document.createElement("div");
    wrap.className = "table-wrap";
    const table = document.createElement("table");
    table.className = "data-table";

    const thead = `<thead><tr>${columns.map(c =>
      `<th${c.numeric ? ' class="numeric"' : ""}>${c.label}</th>`
    ).join("")}</tr></thead>`;
    const tbody = `<tbody>${rows.map(row =>
      `<tr>${columns.map(c =>
        `<td${c.numeric ? ' class="numeric"' : ""}>${row[c.key] ?? "—"}</td>`
      ).join("")}</tr>`
    ).join("")}</tbody>`;

    table.innerHTML = thead + tbody;
    wrap.appendChild(table);
    div.appendChild(wrap);
    return div;
  }

  el.innerHTML = `<h2 class="section-title">💧 Steam Gen</h2>`;

  // data is expected to be an array or object — adjust to actual structure
  // If it's an array of {name, threshold_ls, max_flow_ls, ...}:
  const entries = Array.isArray(data) ? data : Object.entries(data).map(([name, v]) => ({name, ...v}));

  const cols = [
    { key: "name",         label: "Generator",    numeric: false },
    { key: "threshold_ls", label: "Threshold L/s", numeric: true },
    { key: "max_flow_ls",  label: "Max Flow L/s",  numeric: true },
  ];
  // Add any extra columns present in the data
  const extraKeys = entries.length > 0
    ? Object.keys(entries[0]).filter(k => !["name","threshold_ls","max_flow_ls"].includes(k))
    : [];
  for (const k of extraKeys) {
    cols.push({ key: k, label: k.replace(/_/g, " "), numeric: !isNaN(entries[0][k]) });
  }

  el.appendChild(renderSection("Steam Generators", entries, cols));
}
```

- [ ] **Step 3: Verify in browser**

Refresh http://localhost:8080. Click Fuels — should show a searchable, sortable table of steam fuels. Click Gas/Plasma tabs to switch. Click Steam Gen — should show a table from the JSON.

- [ ] **Step 4: Commit**

```bash
git add web/js/ui/fuels.js web/js/ui/steam_gen.js
git commit -m "implement Fuels and Steam Gen sections"
```

---

## Task 6: Rotors section

**Files:**
- Modify: `web/js/ui/rotors.js`

- [ ] **Step 1: Write `web/js/ui/rotors.js`**

The size toggle switches which efficiency/flow columns are displayed. `TURBINE_TO_ROTOR_SIZE` maps UI size to data column key (same mapping as Python):

```
Small  -> "Small"   (efficiency from Small col)
Normal -> "Small"   (efficiency from Small col)
Large  -> "Normal"
Huge   -> "Large"
```

Durability uses `_TURBINE_TO_DUR_SIZE`:
```
Small  -> "Normal"
Normal -> "Large"
Large  -> "Large"
Huge   -> "Huge"
```

```js
import { SortableTable } from "../table.js";
import { formatNumber } from "../utils.js";

const TURBINE_TO_ROTOR_SIZE = { Small: "Small", Normal: "Small", Large: "Normal", Huge: "Large" };
const TURBINE_TO_DUR_SIZE   = { Small: "Normal", Normal: "Large", Large: "Large", Huge: "Huge" };

let _rotors = null;

async function loadData() {
  if (_rotors) return _rotors;
  const res = await fetch("data/rotors.json");
  _rotors = await res.json();
  return _rotors;
}

function buildRows(rotors, uiSize) {
  const effKey = TURBINE_TO_ROTOR_SIZE[uiSize];
  const durKey = TURBINE_TO_DUR_SIZE[uiSize];
  return rotors.map(r => {
    const sd = r.sizes[effKey];
    const durMult = r.sizes[durKey]?.dur_mult ?? 1;
    return {
      name:              r.name,
      tier:              r.tier,
      base_dur:          formatNumber(r.base_durability * durMult),
      overflow:          r.overflow_tier,
      steam_tight_eff:   sd ? (sd.steam_tight_eff * 100).toFixed(1) + "%" : "—",
      steam_loose_eff:   sd ? (sd.steam_loose_eff * 100).toFixed(1) + "%" : "—",
      opt_flow_tight:    sd ? formatNumber(sd.steam_opt_flow_tight) : "—",
      opt_flow_loose:    sd ? formatNumber(sd.steam_opt_flow_loose) : "—",
    };
  });
}

const COLUMNS = [
  { key: "name",           label: "Display Name",     numeric: false },
  { key: "tier",           label: "Tier",              numeric: true,  width: "50px" },
  { key: "base_dur",       label: "Base Dur",          numeric: true  },
  { key: "overflow",       label: "Overflow",          numeric: true,  width: "70px" },
  { key: "steam_tight_eff",label: "Eff Tight",         numeric: false, width: "80px" },
  { key: "steam_loose_eff",label: "Eff Loose",         numeric: false, width: "80px" },
  { key: "opt_flow_tight", label: "Flow Tight (L/t)",  numeric: true  },
  { key: "opt_flow_loose", label: "Flow Loose (L/t)",  numeric: true  },
];

export async function initRotors(el) {
  el.innerHTML = `
    <h2 class="section-title">🔩 Rotors</h2>
    <div class="setting-row" style="margin-bottom:16px;">
      <span class="setting-label">Blade Size:</span>
      <div class="toggle-group" id="rotors-size-toggle">
        <button class="toggle-btn active" data-size="Small">Small</button>
        <button class="toggle-btn" data-size="Normal">Normal</button>
        <button class="toggle-btn" data-size="Large">Large</button>
        <button class="toggle-btn" data-size="Huge">Huge</button>
      </div>
    </div>
    <div class="card" style="padding:0;overflow:hidden;" id="rotors-table-wrap"></div>
  `;

  const rotors = await loadData();
  let currentSize = "Small";
  const tableContainer = document.createElement("div");
  let table = null;

  function refresh(size) {
    currentSize = size;
    el.querySelectorAll("#rotors-size-toggle .toggle-btn").forEach(b =>
      b.classList.toggle("active", b.dataset.size === size)
    );
    const rows = buildRows(rotors, size);
    if (!table) {
      table = new SortableTable(tableContainer, COLUMNS, rows);
      table.render();
      el.querySelector("#rotors-table-wrap").appendChild(tableContainer);
    } else {
      table._rows = rows;
      table._applyFilter();
      table._renderBody();
    }
  }

  el.querySelectorAll("#rotors-size-toggle .toggle-btn").forEach(b =>
    b.addEventListener("click", () => refresh(b.dataset.size))
  );

  refresh("Small");
}
```

- [ ] **Step 2: Verify in browser**

Click Rotors. Expected: 136 rows, sortable by any column, searchable. Switching size toggle updates Dur, Eff, Flow columns. Sort by Tier should give 1, 1, 2, 2, ... 22 (numeric).

- [ ] **Step 3: Commit**

```bash
git add web/js/ui/rotors.js
git commit -m "implement Rotors section with size toggle and sortable table"
```

---

## Task 7: Turbine calc formulas (JS port)

**Files:**
- Create: `web/js/calc.js`

This is a direct port of `gtnh_turbine_calc/calc/turbine.py`. Every formula must match exactly.

- [ ] **Step 1: Write `web/js/calc.js`**

```js
/**
 * Turbine calculation formulas — ported from gtnh_turbine_calc/calc/turbine.py.
 * Do NOT change these without verifying against the Python source.
 */
import { findDynamoTier } from "./utils.js";

// Maps UI blade size name to the data column key used for EFFICIENCY stats.
export const TURBINE_TO_ROTOR_SIZE = {
  Small:  "Small",
  Normal: "Small",
  Large:  "Normal",
  Huge:   "Large",
  XL:     "Normal",
};

// Due to data extraction misalignment, durability multiplier is in the NEXT column.
export const TURBINE_TO_DUR_SIZE = {
  Small:  "Normal",
  Normal: "Large",
  Large:  "Large",
  Huge:   "Huge",
  XL:     "Large",
};

function rotorSizeData(rotor, size) {
  const key = TURBINE_TO_ROTOR_SIZE[size] ?? size;
  return rotor.sizes[key];
}

function rotorDurability(rotor, size) {
  const key = TURBINE_TO_DUR_SIZE[size] ?? size;
  return rotor.base_durability * rotor.sizes[key].dur_mult;
}

function lifetimeRegular(durability, output, steamFuelType, mode) {
  if (output <= 0) return 0;
  const damage = Math.min(output / 5, Math.pow(output, 0.6));
  const base = 2 * Math.ceil(durability / damage * 50);
  let mult;
  if (steamFuelType === "SC Steam") {
    mult = mode === "Tight" ? 1.0 : 4.0;
  } else if (steamFuelType === "Steam" || steamFuelType === "SH Steam") {
    mult = mode === "Tight" ? 2.0 : 8 / 3;
  } else {
    mult = 1.0;
  }
  return base * mult;
}

function lifetimeXl(durability, output, turbineType, mode) {
  if (output <= 0) return 0;
  const damage = Math.min(output / 5 / 5, Math.pow(output / 5, 0.6));
  if (turbineType === "steam") {
    const mult = mode === "Tight" ? 1.0 : 4 / 3;
    return Math.ceil(mult * durability / damage * 50);
  } else if (turbineType === "gas") {
    return Math.ceil(4 / 3 * durability / damage * 50);
  } else {
    return Math.ceil(1.25 * durability / damage * 50);
  }
}

function flowEffSteam(effFlow, optFlow, overflowTier, fuelType) {
  if (optFlow <= 0) return 0;
  if (effFlow > optFlow) {
    let mult;
    if (fuelType === "SC Steam") mult = 1.25;
    else if (fuelType === "SH Steam") mult = overflowTier + 2;
    else mult = overflowTier + 1;
    return 1.0 - Math.abs((effFlow - optFlow) / (optFlow * mult));
  }
  return 1.0 - Math.abs((effFlow - optFlow) / optFlow);
}

function flowEffGas(effFlow, optFlow, overflowTier) {
  if (optFlow <= 0) return 0;
  if (effFlow > optFlow) {
    return 1.0 - Math.abs((effFlow - optFlow) / (optFlow * (overflowTier * 3 - 1)));
  }
  return 1.0 - Math.abs((effFlow - optFlow) / optFlow);
}

function flowEffPlasma(effFlow, optFlow, overflowTier) {
  if (optFlow <= 0) return 0;
  if (effFlow > optFlow) {
    return 1.0 - Math.abs((effFlow - optFlow) / (optFlow * (overflowTier * 3 + 1)));
  }
  return 1.0 - Math.abs((effFlow - optFlow) / optFlow);
}

/**
 * Calculate outputs for one regular turbine configuration.
 * @param {"steam"|"gas"|"plasma"} turbineType
 * @param {object} rotor - rotor data object from rotors.json
 * @param {string} size - "Small"|"Normal"|"Large"|"Huge"
 * @param {string} mode - "Tight"|"Loose"
 * @param {string} fuelType - fuel name string
 * @param {number} fuelValue - EU/L (steam/gas) or EU/L (plasma, used /20)
 * @param {number|null} manualFlow - null for optimal
 * @returns {object} result
 */
export function calcRegularTurbine(turbineType, rotor, size, mode, fuelType, fuelValue, manualFlow = null) {
  const sd = rotorSizeData(rotor, size);
  const overflowTier = rotor.overflow_tier;
  const durability = rotorDurability(rotor, size);

  let optFlow, optOutput, maxFlow, effFlow, effOutput, rotor_eff, lifetime;

  if (turbineType === "steam") {
    rotor_eff = mode === "Tight" ? sd.steam_tight_eff : sd.steam_loose_eff;
    optFlow   = mode === "Tight" ? sd.steam_opt_flow_tight : sd.steam_opt_flow_loose;
    optOutput = Math.floor(optFlow * rotor_eff * fuelValue);

    let maxFlowMult;
    if (fuelType === "SC Steam") maxFlowMult = 1.25;
    else if (fuelType === "SH Steam") maxFlowMult = 0.5 * overflowTier + 1.5;
    else maxFlowMult = 0.5 * overflowTier + 1;
    maxFlow = Math.floor(optFlow * maxFlowMult);

    effFlow = manualFlow !== null ? Math.min(maxFlow, manualFlow) : optFlow;
    const fe = flowEffSteam(effFlow, optFlow, overflowTier, fuelType);
    effOutput = Math.max(1, Math.floor(effFlow * fe * rotor_eff * fuelValue));
    lifetime  = lifetimeRegular(durability, effOutput, fuelType, mode);

  } else if (turbineType === "gas") {
    rotor_eff    = mode === "Tight" ? sd.gas_tight_eff : sd.gas_loose_eff;
    const optFlowEuT = mode === "Tight" ? sd.gas_opt_flow_tight : sd.gas_opt_flow_loose;
    optFlow  = Math.max(1, Math.floor(optFlowEuT / fuelValue));
    optOutput = Math.floor(optFlow * rotor_eff * fuelValue);

    maxFlow  = Math.floor(overflowTier * 1.5 * optFlow);
    effFlow  = manualFlow !== null ? Math.min(maxFlow, manualFlow) : optFlow;
    const fe  = flowEffGas(effFlow, optFlow, overflowTier);
    effOutput = Math.floor(effFlow * fe * rotor_eff * fuelValue);
    lifetime  = lifetimeRegular(durability, effOutput, null, mode);

  } else { // plasma
    rotor_eff    = mode === "Tight" ? sd.plasma_tight_eff : sd.plasma_loose_eff;
    const optFlowEuT = mode === "Tight" ? sd.plasma_opt_flow_tight : sd.plasma_opt_flow_loose;
    optFlow  = Math.max(1, Math.ceil(optFlowEuT * 20 / fuelValue));
    optOutput = Math.floor(optFlow * rotor_eff * fuelValue / 20);

    maxFlow  = Math.floor((1.5 * overflowTier + 1) * optFlow);
    effFlow  = manualFlow !== null ? Math.min(maxFlow, manualFlow) : optFlow;
    const fe  = flowEffPlasma(effFlow, optFlow, overflowTier);
    effOutput = Math.max(1, Math.floor(effFlow * fe * rotor_eff * fuelValue / 20));
    lifetime  = lifetimeRegular(durability, effOutput, null, mode);
  }

  return {
    turbineType, mode, fuelType, fuelValue,
    optFlow, optOutput, effFlow, effOutput,
    rotorEff: rotor_eff, maxFlow, overflowTier, lifetime,
    minDynamoTierOpt: findDynamoTier(optOutput),
    minDynamoTierEff: findDynamoTier(effOutput),
  };
}

/**
 * Calculate outputs for one XL turbine (16x flow multiplier).
 * @param {"steam"|"gas"|"plasma"} turbineType
 * @param {object} rotor
 * @param {string} size
 * @param {string} mode
 * @param {string} fuelType
 * @param {number} fuelValue
 * @param {boolean} isDense - for steam: display flow in dense SC units (L/t / 1000)
 * @param {number|null} manualFlow
 * @returns {object} result
 */
export function calcXlTurbine(turbineType, rotor, size, mode, fuelType, fuelValue, isDense = false, manualFlow = null) {
  const sd = rotorSizeData(rotor, size);
  const overflowTier = rotor.overflow_tier;
  const durability = rotorDurability(rotor, size);
  const XL = 16;

  let optFlow, optOutput, maxFlow, effFlow, effOutput, rotor_eff, lifetime;

  if (turbineType === "steam") {
    rotor_eff = mode === "Tight" ? sd.steam_tight_eff : sd.steam_loose_eff;
    const baseOptFlow = mode === "Tight" ? sd.steam_opt_flow_tight : sd.steam_opt_flow_loose;
    const optFlowRaw  = baseOptFlow * XL;
    const displayFlow = isDense ? Math.floor(optFlowRaw / 1000) : optFlowRaw;
    const optFlowCalc = isDense ? displayFlow * 1000 : optFlowRaw;
    optOutput = Math.floor(optFlowCalc * rotor_eff * fuelValue);

    const maxFlowRaw = Math.floor(optFlowRaw * 1.25);
    const effFlowRaw = manualFlow !== null
      ? Math.min(maxFlowRaw, manualFlow * (isDense ? 1000 : 1))
      : optFlowCalc;
    const fe = optFlowCalc ? 1.0 - Math.abs((effFlowRaw - optFlowCalc) / optFlowCalc) : 0;
    effOutput = Math.max(1, Math.floor(effFlowRaw * fe * rotor_eff * fuelValue));
    lifetime  = lifetimeXl(durability, effOutput, "steam", mode);
    optFlow   = displayFlow;
    effFlow   = isDense ? Math.floor(effFlowRaw / 1000) : effFlowRaw;
    maxFlow   = isDense ? Math.floor(maxFlowRaw / 1000) : maxFlowRaw;

  } else if (turbineType === "gas") {
    rotor_eff    = mode === "Tight" ? sd.gas_tight_eff : sd.gas_loose_eff;
    const optFlowEuT = mode === "Tight" ? sd.gas_opt_flow_tight : sd.gas_opt_flow_loose;
    optFlow  = Math.max(1, Math.floor(XL * optFlowEuT / fuelValue));
    optOutput = Math.floor(optFlow * rotor_eff * fuelValue);
    maxFlow  = Math.floor(optFlow * 1.25);
    effFlow  = manualFlow !== null ? Math.min(maxFlow, manualFlow) : optFlow;
    const fe  = optFlow ? 1.0 - Math.abs((effFlow - optFlow) / optFlow) : 0;
    effOutput = Math.floor(effFlow * fe * rotor_eff * fuelValue);
    lifetime  = lifetimeXl(durability, effOutput, "gas", mode);

  } else { // plasma
    rotor_eff    = mode === "Tight" ? sd.plasma_tight_eff : sd.plasma_loose_eff;
    const optFlowEuT = mode === "Tight" ? sd.plasma_opt_flow_tight : sd.plasma_opt_flow_loose;
    optFlow  = Math.max(1, Math.floor(XL * optFlowEuT * 20 / fuelValue));
    const plasmaPowerTight = sd.plasma_power_tight;
    const nerfMult = plasmaPowerTight
      ? Math.min(1.0, Math.pow(fuelValue * 0.005, 2) / plasmaPowerTight)
      : 1.0;
    optOutput = Math.floor(optFlow * rotor_eff * fuelValue / 20 * nerfMult);
    maxFlow  = Math.floor(optFlow * 1.25);
    effFlow  = manualFlow !== null ? Math.min(maxFlow, manualFlow) : optFlow;
    const fe  = optFlow ? 1.0 - Math.abs((effFlow - optFlow) / optFlow) : 0;
    effOutput = Math.floor(optOutput * Math.min(1 + overflowTier * 1.5, effFlow / optFlow) * fe);
    lifetime  = lifetimeXl(durability, effOutput, "plasma", mode);
  }

  return {
    turbineType, mode, fuelType, fuelValue,
    optFlow, optOutput, effFlow, effOutput,
    rotorEff: rotor_eff, maxFlow, overflowTier, lifetime,
    minDynamoTierOpt: findDynamoTier(optOutput),
    minDynamoTierEff: findDynamoTier(effOutput),
  };
}
```

- [ ] **Step 2: Spot-check formula output against the desktop app**

Run the desktop app, note the output for a known combination (e.g. Neutronium rotor, Normal size, Gas, Naquadah, Tight mode). Then verify the JS produces the same result by opening browser console:

```js
// In browser console at http://localhost:8080
// (after loading the page so modules are available)
// This is a manual check — just verify numbers match the desktop app
```

No automated test framework is needed — a manual spot-check of 2-3 combinations is sufficient.

- [ ] **Step 3: Commit**

```bash
git add web/js/calc.js
git commit -m "port turbine calc formulas to JS"
```

---

## Task 8: Calculator section UI

**Files:**
- Modify: `web/js/ui/calculator.js`

- [ ] **Step 1: Write `web/js/ui/calculator.js`**

```js
import { calcRegularTurbine, calcXlTurbine } from "../calc.js";
import { formatNumber, findDynamoTier, DYNAMO_TIERS, populateSelect } from "../utils.js";

let _data = null;

async function loadData() {
  if (_data) return _data;
  const [rotors, fuels] = await Promise.all([
    fetch("data/rotors.json").then(r => r.json()),
    fetch("data/fuels.json").then(r => r.json()),
  ]);
  _data = { rotors, fuels };
  return _data;
}

function makeToggle(options, onChange) {
  const group = document.createElement("div");
  group.className = "toggle-group";
  options.forEach((opt, i) => {
    const btn = document.createElement("button");
    btn.className = "toggle-btn" + (i === 0 ? " active" : "");
    btn.textContent = opt;
    btn.addEventListener("click", () => {
      group.querySelectorAll(".toggle-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      onChange(opt);
    });
    group.appendChild(btn);
  });
  group.getValue = () => group.querySelector(".toggle-btn.active").textContent;
  return group;
}

function makeResultRow(label, colorClass = "green") {
  const row = document.createElement("div");
  row.className = "result-row";
  row.innerHTML = `<span class="result-label">${label}</span><span class="result-value ${colorClass}">—</span>`;
  row.setValue = v => { row.querySelector(".result-value").textContent = v; };
  return row;
}

function makeDivider() {
  const hr = document.createElement("hr");
  hr.className = "divider";
  return hr;
}

// --- Turbine card (one per turbine type: steam / gas / plasma) ---
function makeTurbineCard(turbineTypeLabel, fuelList, calcFn, sharedState) {
  // turbineTypeLabel: "steam" | "gas" | "plasma"
  const type = turbineTypeLabel;
  const colorMap = { steam: "blue", gas: "orange", plasma: "purple" };
  const accentColor = colorMap[type] || "green";

  const wrap = document.createElement("div");

  // Fuel tabs
  const tabBar = document.createElement("div");
  tabBar.className = "fuel-tabs";
  ["steam","gas","plasma"].forEach(t => {
    const tab = document.createElement("div");
    tab.className = `fuel-tab ${t}` + (t === type ? " active" : "");
    tab.textContent = { steam: "💧 Steam", gas: "🔥 Gas", plasma: "⚡ Plasma" }[t];
    tab.dataset.type = t;
    tab.addEventListener("click", () => {
      wrap.dispatchEvent(new CustomEvent("switchtype", { detail: t, bubbles: true }));
    });
    tabBar.appendChild(tab);
  });
  wrap.appendChild(tabBar);

  // Settings
  const settingsDiv = document.createElement("div");
  settingsDiv.style.marginBottom = "12px";

  // Mode toggle
  const modeRow = document.createElement("div");
  modeRow.className = "setting-row";
  modeRow.innerHTML = `<span class="setting-label">Mode:</span>`;
  const modeToggle = makeToggle(["Tight", "Loose"], () => recalc());
  modeRow.appendChild(modeToggle);
  settingsDiv.appendChild(modeRow);

  // Fuel select
  const fuelRow = document.createElement("div");
  fuelRow.className = "setting-row";
  fuelRow.innerHTML = `<span class="setting-label">Fuel:</span>`;
  const fuelSel = document.createElement("select");
  populateSelect(fuelSel, fuelList.map(f => f.name), fuelList[0]?.name);
  fuelSel.addEventListener("change", () => recalc());
  fuelRow.appendChild(fuelSel);
  settingsDiv.appendChild(fuelRow);

  // Flow toggle
  const flowRow = document.createElement("div");
  flowRow.className = "setting-row";
  flowRow.innerHTML = `<span class="setting-label">Flow:</span>`;
  const flowToggle = makeToggle(["Optimal", "Manual"], val => {
    manualInput.style.display = val === "Manual" ? "inline" : "none";
    recalc();
  });
  const manualInput = document.createElement("input");
  manualInput.type = "number";
  manualInput.min = 1;
  manualInput.value = 1000;
  manualInput.style.display = "none";
  manualInput.style.marginLeft = "8px";
  manualInput.addEventListener("input", () => recalc());
  flowRow.appendChild(flowToggle);
  flowRow.appendChild(manualInput);
  settingsDiv.appendChild(flowRow);
  wrap.appendChild(settingsDiv);

  wrap.appendChild(makeDivider());

  // Results
  const resultsDiv = document.createElement("div");
  const rows = {
    optFlow:   makeResultRow("Optimal flow:", "cyan"),
    optOutput: makeResultRow("Output EU/t:", "green"),
    dynamo:    makeResultRow("Dynamo tier:", "muted"),
    effFlow:   makeResultRow("Eff. flow:", "cyan"),
    effOutput: makeResultRow("Eff. output:", "green"),
    rotorEff:  makeResultRow("Rotor eff.:", "muted"),
    lifetime:  makeResultRow("Lifetime (s):", "yellow"),
  };
  Object.values(rows).forEach(r => resultsDiv.appendChild(r));
  wrap.appendChild(resultsDiv);

  function getFuelValue() {
    const name = fuelSel.value;
    const f = fuelList.find(x => x.name === name);
    return f ? f.eu_l : 1;
  }

  function recalc() {
    const rotor = sharedState.rotor;
    if (!rotor) return;
    const size     = sharedState.size;
    const mode     = modeToggle.getValue();
    const fuelType = fuelSel.value;
    const fuelValue = getFuelValue();
    const isManual = flowToggle.getValue() === "Manual";
    const manualFlow = isManual ? parseFloat(manualInput.value) || null : null;

    const r = calcFn(type, rotor, size, mode, fuelType, fuelValue, manualFlow);

    const flowUnit = type === "plasma" ? "L/s" : "L/t";
    rows.optFlow.setValue(`${formatNumber(r.optFlow)} ${flowUnit}`);
    rows.optOutput.setValue(`${formatNumber(r.optOutput)} EU/t`);
    rows.dynamo.setValue(r.minDynamoTierOpt);
    rows.effFlow.setValue(isManual ? `${formatNumber(r.effFlow)} ${flowUnit}` : "—");
    rows.effOutput.setValue(isManual ? `${formatNumber(r.effOutput)} EU/t` : "—");
    rows.rotorEff.setValue(`${(r.rotorEff * 100).toFixed(1)}%`);
    rows.lifetime.setValue(`${formatNumber(Math.round(r.lifetime))} s`);
  }

  wrap.recalc = recalc;
  return wrap;
}

// --- Shared settings (rotor + size + dynamo tier) ---
function makeSharedSettings(rotors, onChange) {
  const state = { rotor: null, size: "Normal" };
  const div = document.createElement("div");
  div.className = "card";
  div.style.marginBottom = "16px";
  div.style.display = "flex";
  div.style.flexWrap = "wrap";
  div.style.gap = "16px";
  div.style.alignItems = "center";

  // Rotor search select
  const rotorWrap = document.createElement("div");
  rotorWrap.className = "setting-row";
  rotorWrap.innerHTML = `<span class="setting-label">Rotor:</span>`;
  const rotorSel = document.createElement("select");
  rotorSel.style.maxWidth = "220px";
  populateSelect(rotorSel, rotors.map(r => r.name), rotors[0]?.name);
  state.rotor = rotors[0] ?? null;
  rotorSel.addEventListener("change", () => {
    state.rotor = rotors.find(r => r.name === rotorSel.value) ?? null;
    onChange(state);
  });
  rotorWrap.appendChild(rotorSel);
  div.appendChild(rotorWrap);

  // Size toggle
  const sizeWrap = document.createElement("div");
  sizeWrap.className = "setting-row";
  sizeWrap.innerHTML = `<span class="setting-label">Blade Size:</span>`;
  const sizeToggle = makeToggle(["Small", "Normal", "Large", "Huge"], val => {
    state.size = val;
    onChange(state);
  });
  sizeToggle.querySelector(".toggle-btn:nth-child(2)").click(); // default Normal
  sizeWrap.appendChild(sizeToggle);
  div.appendChild(sizeWrap);

  return { el: div, state };
}

// --- Large turbines tab ---
async function buildLargeTab(el, data) {
  const steamFuels  = data.fuels.steam;
  const gasFuels    = data.fuels.gas;
  const plasmaFuels = data.fuels.plasma;

  const { el: settingsEl, state } = makeSharedSettings(data.rotors, () => cards.forEach(c => c.recalc()));

  const cardsWrap = document.createElement("div");
  cardsWrap.style.display = "flex";
  cardsWrap.style.gap = "12px";
  cardsWrap.style.flexWrap = "wrap";

  const fuelMap = { steam: steamFuels, gas: gasFuels, plasma: plasmaFuels };
  let visibleType = "steam";

  function makeCardWrap(type) {
    const box = document.createElement("div");
    box.className = "card";
    box.style.flex = "1";
    box.style.minWidth = "240px";
    box.dataset.type = type;

    const card = makeTurbineCard(type, fuelMap[type], (t, rotor, size, mode, fuelType, fuelValue, mf) =>
      calcRegularTurbine(t, rotor, size, mode, fuelType, fuelValue, mf), state);

    card.addEventListener("switchtype", e => {
      const newType = e.detail;
      if (newType !== type) {
        // Switch to sibling card's type — highlight tab, recalc
        cardsWrap.querySelectorAll(".fuel-tab").forEach(tab => {
          tab.classList.toggle("active", tab.dataset.type === newType);
        });
      }
    });

    box.appendChild(card);
    box.recalc = card.recalc;
    return box;
  }

  const cards = ["steam", "gas", "plasma"].map(makeCardWrap);
  cards.forEach(c => cardsWrap.appendChild(c));

  el.appendChild(settingsEl);
  el.appendChild(cardsWrap);

  // Initial calc
  cards.forEach(c => c.recalc());
}

// --- XL turbines tab ---
async function buildXlTab(el, data) {
  const steamFuels  = data.fuels.steam;
  const gasFuels    = data.fuels.gas;
  const plasmaFuels = data.fuels.plasma;

  const { el: settingsEl, state } = makeSharedSettings(data.rotors, () => cards.forEach(c => c.recalc()));

  const cardsWrap = document.createElement("div");
  cardsWrap.style.display = "flex";
  cardsWrap.style.gap = "12px";
  cardsWrap.style.flexWrap = "wrap";

  const fuelMap = { steam: steamFuels, gas: gasFuels, plasma: plasmaFuels };

  function makeCardWrap(type) {
    const box = document.createElement("div");
    box.className = "card";
    box.style.flex = "1";
    box.style.minWidth = "240px";

    const card = makeTurbineCard(type, fuelMap[type], (t, rotor, size, mode, fuelType, fuelValue, mf) =>
      calcXlTurbine(t, rotor, size, mode, fuelType, fuelValue, false, mf), state);

    box.appendChild(card);
    box.recalc = card.recalc;
    return box;
  }

  const cards = ["steam", "gas", "plasma"].map(makeCardWrap);
  cards.forEach(c => cardsWrap.appendChild(c));

  el.appendChild(settingsEl);
  el.appendChild(cardsWrap);

  cards.forEach(c => c.recalc());
}

// --- Main init ---
export async function initCalculator(el) {
  el.innerHTML = `
    <h2 class="section-title">⚡ Calculator</h2>
    <div class="sub-tabs">
      <div class="sub-tab active" data-tab="large">Large Turbines</div>
      <div class="sub-tab" data-tab="xl">XL Turbo Turbines</div>
    </div>
    <div id="calc-large"></div>
    <div id="calc-xl" class="hidden"></div>
  `;

  const data = await loadData();
  const largeEl = el.querySelector("#calc-large");
  const xlEl    = el.querySelector("#calc-xl");

  await buildLargeTab(largeEl, data);

  let xlBuilt = false;

  el.querySelectorAll(".sub-tab").forEach(tab => {
    tab.addEventListener("click", async () => {
      el.querySelectorAll(".sub-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      if (tab.dataset.tab === "large") {
        largeEl.classList.remove("hidden");
        xlEl.classList.add("hidden");
      } else {
        largeEl.classList.add("hidden");
        xlEl.classList.remove("hidden");
        if (!xlBuilt) { await buildXlTab(xlEl, data); xlBuilt = true; }
      }
    });
  });
}
```

- [ ] **Step 2: Verify calculator in browser**

Open http://localhost:8080. Expected:
- Calculator loads with 3 cards (Steam / Gas / Plasma) side by side
- Changing rotor or size updates all 3 cards instantly
- Changing mode / fuel / flow updates individual card
- Numbers match the desktop app for the same inputs
- Switch to XL tab — XL cards load, calculations work

- [ ] **Step 3: Commit**

```bash
git add web/js/ui/calculator.js
git commit -m "implement Calculator section (Large + XL tabs)"
```

---

## Task 9: EHE Planner section

**Files:**
- Create: `web/js/ehe.js`
- Modify: `web/js/ui/ehe_planner.js`

- [ ] **Step 1: Write `web/js/ehe.js`**

Port from `gtnh_turbine_calc/calc/ehe.py`:

```js
/**
 * EHE planner formulas — ported from gtnh_turbine_calc/calc/ehe.py.
 */
import { findDynamoTier } from "./utils.js";

const TURBINE_TO_ROTOR_SIZE = { Small: "Small", Normal: "Small", Large: "Normal", Huge: "Large", XL: "Normal" };

function steamOptFlowXl(rotor, size, mode) {
  const key = TURBINE_TO_ROTOR_SIZE[size] ?? size;
  const sd = rotor.sizes[key];
  const base = mode === "Tight" ? sd.steam_opt_flow_tight : sd.steam_opt_flow_loose;
  return Math.floor(base * 16 / 1000); // dense L/t display
}

function xlPower(rotor, size, mode, fuelValue, flowLt) {
  const key = TURBINE_TO_ROTOR_SIZE[size] ?? size;
  const sd = rotor.sizes[key];
  const rotorEff = mode === "Tight" ? sd.steam_tight_eff : sd.steam_loose_eff;
  const optFlowCalc = steamOptFlowXl(rotor, size, mode) * 1000;
  const effFlow = flowLt * 1000;
  const fe = optFlowCalc ? 1.0 - Math.abs((effFlow - optFlowCalc) / optFlowCalc) : 0;
  return Math.floor(effFlow * fe * rotorEff * fuelValue);
}

function denseSCSteamFromPlasma(plasmaType, plasmaLs, eheMaxLs, eheFuels) {
  const fd = eheFuels[plasmaType];
  if (!fd || eheMaxLs <= 0) return 0;
  const maxHotSteam = fd.max_hot_steam_ls ?? 0;
  const TICKS = 20;
  const capped = Math.min(plasmaLs, eheMaxLs);
  const fullSteamMbt = Math.floor(Math.floor(maxHotSteam * capped / eheMaxLs) / 160) * 160 / TICKS;
  const fullCount = Math.floor(plasmaLs / eheMaxLs);
  const fullTotal = Math.floor(fullSteamMbt) * fullCount;
  const partialFlow = plasmaLs % eheMaxLs;
  const partialSteamMbt = Math.floor(Math.floor(maxHotSteam * partialFlow / eheMaxLs) / 160) * 160 / TICKS;
  return fullTotal + Math.floor(partialSteamMbt);
}

/**
 * @param {string} plasmaType
 * @param {number} recipeOutputL
 * @param {number} recipeTimeS
 * @param {number} parallelCount
 * @param {object} rotor
 * @param {string} size
 * @param {string} mode
 * @param {object} eheFuels - from fuels.json ehe field
 * @param {number} scSteamEuL - EU/L for SC Steam (from fuels.json steam)
 */
export function calcPlasmaEhe(plasmaType, recipeOutputL, recipeTimeS, parallelCount, rotor, size, mode, eheFuels, scSteamEuL) {
  const plasmaOutputLs = recipeOutputL / recipeTimeS * parallelCount;
  const fd = eheFuels[plasmaType] ?? {};
  const eheMaxInputLs = fd.max_convert_ls ?? 0;
  const eheCount = eheMaxInputLs > 0 ? Math.ceil(plasmaOutputLs / eheMaxInputLs) : 0;
  const denseSCSteamLt = denseSCSteamFromPlasma(plasmaType, plasmaOutputLs, eheMaxInputLs, eheFuels);

  const xlOptFlow = steamOptFlowXl(rotor, size, mode);
  const turbineCount = xlOptFlow > 0 && denseSCSteamLt > 0 ? Math.max(1, Math.ceil(denseSCSteamLt / xlOptFlow)) : 0;
  const powerSC = xlPower(rotor, size, mode, scSteamEuL, Math.min(denseSCSteamLt, xlOptFlow));

  return {
    plasmaOutputLs, eheMaxInputLs, eheCount,
    denseSCSteamLt, turbineCount, xlOptFlowLt: xlOptFlow,
    powerPerTurbineSC: powerSC,
    minDynamoTierSC: findDynamoTier(powerSC),
  };
}

const NON_PLASMA_EHE = {
  "Lava":             { max_convert_ls: 160000, threshold_ls: 80000,  max_hot_steam_ls: 12800000, max_normal_steam_ls: 12800000 },
  "IC2 Hot Coolant":  { max_convert_ls: 16000,  threshold_ls: 8000,   max_hot_steam_ls: 3200000,  max_normal_steam_ls: 3200000 },
  "Solar Salt (Hot)": { max_convert_ls: 3200,   threshold_ls: 1600,   max_hot_steam_ls: 3200000,  max_normal_steam_ls: 3200000 },
};

function scSteamFromHotFluid(hotFluid, hotFluidLs) {
  const fd = NON_PLASMA_EHE[hotFluid];
  if (!fd) return [0, 0];
  const { max_convert_ls, threshold_ls, max_hot_steam_ls, max_normal_steam_ls } = fd;
  const capped = Math.min(hotFluidLs, max_convert_ls);
  const fullSteamLs = Math.floor(Math.floor(max_hot_steam_ls * capped / max_convert_ls) / 160) * 160;
  const fullCount = Math.floor(hotFluidLs / max_convert_ls);
  const fullSc = fullSteamLs * fullCount;
  const partialFlow = hotFluidLs % max_convert_ls;
  const partialSteamLs = Math.floor(Math.floor(max_hot_steam_ls * partialFlow / max_convert_ls) / 160) * 160;
  const partialSc = partialFlow >= threshold_ls ? partialSteamLs : 0;
  const scSteamLt = fullSc + partialSc;
  const partialShLs = Math.floor(Math.floor(max_normal_steam_ls * partialFlow / max_convert_ls) / 160) * 160;
  const shSteamLt = partialFlow < threshold_ls ? partialShLs : 0;
  return [scSteamLt, shSteamLt];
}

/**
 * @param {string} hotFluid
 * @param {number} hotFluidInputLs
 * @param {object} rotor
 * @param {string} size
 * @param {string} mode
 * @param {number} scSteamEuL
 * @param {number} steamEuL
 */
export function calcNonxlEhe(hotFluid, hotFluidInputLs, rotor, size, mode, scSteamEuL, steamEuL) {
  const [scSteamLt, shSteamLt] = scSteamFromHotFluid(hotFluid, hotFluidInputLs);
  const key = TURBINE_TO_ROTOR_SIZE[size] ?? size;
  const sd = rotor.sizes[key];
  const rotorEff = mode === "Tight" ? sd.steam_tight_eff : sd.steam_loose_eff;
  const optFlow  = mode === "Tight" ? sd.steam_opt_flow_tight : sd.steam_opt_flow_loose;
  const scTurbineCount = scSteamLt && optFlow ? Math.max(1, Math.ceil(scSteamLt / optFlow)) : 0;
  const shTurbineCount = optFlow ? Math.max(1, Math.ceil((scSteamLt + shSteamLt) / optFlow)) : 0;
  const powerSC  = Math.floor(Math.min(scSteamLt, optFlow) * rotorEff * scSteamEuL);
  const powerReg = Math.floor(Math.min(scSteamLt + shSteamLt, optFlow) * rotorEff * steamEuL);
  const maxConvert = NON_PLASMA_EHE[hotFluid]?.max_convert_ls ?? 1;
  const eheCount = Math.ceil(hotFluidInputLs / maxConvert);
  return {
    totalScSteamLt: scSteamLt, totalShSteamLt: shSteamLt,
    rotorEff, optFlowLt: optFlow,
    scTurbineCount, shTurbineCount,
    powerPerScTurbine: powerSC, powerPerRegTurbine: powerReg,
    minDynamoTierSC:  findDynamoTier(powerSC),
    minDynamoTierReg: findDynamoTier(powerReg),
    eheCount,
  };
}
```

- [ ] **Step 2: Write `web/js/ui/ehe_planner.js`**

```js
import { calcPlasmaEhe, calcNonxlEhe } from "../ehe.js";
import { formatNumber, populateSelect } from "../utils.js";

let _data = null;

async function loadData() {
  if (_data) return _data;
  const [rotors, fuels] = await Promise.all([
    fetch("data/rotors.json").then(r => r.json()),
    fetch("data/fuels.json").then(r => r.json()),
  ]);
  _data = { rotors, fuels };
  return _data;
}

function makeToggle(options, onChange) {
  const group = document.createElement("div");
  group.className = "toggle-group";
  options.forEach((opt, i) => {
    const btn = document.createElement("button");
    btn.className = "toggle-btn" + (i === 0 ? " active" : "");
    btn.textContent = opt;
    btn.addEventListener("click", () => {
      group.querySelectorAll(".toggle-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      onChange(opt);
    });
    group.appendChild(btn);
  });
  group.getValue = () => group.querySelector(".toggle-btn.active").textContent;
  return group;
}

function row(label, id, colorClass = "green") {
  return `<div class="result-row">
    <span class="result-label">${label}</span>
    <span class="result-value ${colorClass}" id="${id}">—</span>
  </div>`;
}

export async function initEhePlanner(el) {
  el.innerHTML = `<h2 class="section-title">🔥 EHE Planner</h2>
    <div class="row">
      <div class="col" id="plasma-ehe-col"></div>
      <div class="col" id="nonxl-ehe-col"></div>
    </div>`;

  const data = await loadData();
  const scSteamEuL = data.fuels.steam.find(f => f.name === "SC Steam")?.eu_l ?? 2;
  const steamEuL   = data.fuels.steam.find(f => f.name === "Steam")?.eu_l ?? 0.5;

  // --- Plasma EHE ---
  const plasmaCol = el.querySelector("#plasma-ehe-col");
  const plasmaTypes = Object.keys(data.fuels.ehe);
  plasmaCol.innerHTML = `
    <div class="card">
      <h3 style="color:#c084fc;font-size:14px;margin-bottom:14px;">Plasma EHE</h3>
      <div class="setting-row"><span class="setting-label">Plasma type:</span>
        <select id="p-plasma-type" style="max-width:200px;"></select></div>
      <div class="setting-row"><span class="setting-label">Recipe output (L):</span>
        <input type="number" id="p-recipe-out" value="1000" min="1"></div>
      <div class="setting-row"><span class="setting-label">Recipe time (s):</span>
        <input type="number" id="p-recipe-time" value="20" min="1"></div>
      <div class="setting-row"><span class="setting-label">Parallels:</span>
        <input type="number" id="p-parallels" value="1" min="1"></div>
      <div class="setting-row"><span class="setting-label">Rotor:</span>
        <select id="p-rotor" style="max-width:200px;"></select></div>
      <div class="setting-row"><span class="setting-label">Blade Size:</span>
        <div id="p-size-toggle"></div></div>
      <div class="setting-row"><span class="setting-label">Mode:</span>
        <div id="p-mode-toggle"></div></div>
      <hr class="divider">
      ${row("Plasma output L/s:", "p-plasma-ls", "purple")}
      ${row("EHE count:", "p-ehe-count", "muted")}
      ${row("Dense SC steam L/t:", "p-sc-steam", "cyan")}
      ${row("XL turbine count:", "p-turb-count", "muted")}
      ${row("Power/turbine EU/t:", "p-power", "green")}
      ${row("Dynamo tier:", "p-dynamo", "muted")}
    </div>`;

  populateSelect(plasmaCol.querySelector("#p-plasma-type"), plasmaTypes, plasmaTypes[0]);
  populateSelect(plasmaCol.querySelector("#p-rotor"), data.rotors.map(r => r.name), data.rotors[0]?.name);

  const pSizeToggle = makeToggle(["Small","Normal","Large","Huge"], () => plasmaRecalc());
  const pModeToggle = makeToggle(["Tight","Loose"], () => plasmaRecalc());
  plasmaCol.querySelector("#p-size-toggle").appendChild(pSizeToggle);
  plasmaCol.querySelector("#p-mode-toggle").appendChild(pModeToggle);

  plasmaCol.querySelectorAll("select, input").forEach(i => i.addEventListener("change", plasmaRecalc));
  plasmaCol.querySelectorAll("input").forEach(i => i.addEventListener("input", plasmaRecalc));

  function plasmaRecalc() {
    const plasmaType    = plasmaCol.querySelector("#p-plasma-type").value;
    const recipeOut     = parseFloat(plasmaCol.querySelector("#p-recipe-out").value) || 0;
    const recipeTime    = parseFloat(plasmaCol.querySelector("#p-recipe-time").value) || 1;
    const parallels     = parseFloat(plasmaCol.querySelector("#p-parallels").value) || 1;
    const rotorName     = plasmaCol.querySelector("#p-rotor").value;
    const rotor         = data.rotors.find(r => r.name === rotorName);
    const size          = pSizeToggle.getValue();
    const mode          = pModeToggle.getValue();
    if (!rotor) return;
    const res = calcPlasmaEhe(plasmaType, recipeOut, recipeTime, parallels, rotor, size, mode, data.fuels.ehe, scSteamEuL);
    plasmaCol.querySelector("#p-plasma-ls").textContent   = formatNumber(res.plasmaOutputLs.toFixed(2));
    plasmaCol.querySelector("#p-ehe-count").textContent   = res.eheCount;
    plasmaCol.querySelector("#p-sc-steam").textContent    = formatNumber(res.denseSCSteamLt);
    plasmaCol.querySelector("#p-turb-count").textContent  = res.turbineCount;
    plasmaCol.querySelector("#p-power").textContent       = `${formatNumber(res.powerPerTurbineSC)} EU/t`;
    plasmaCol.querySelector("#p-dynamo").textContent      = res.minDynamoTierSC;
  }

  plasmaRecalc();

  // --- Non-XL EHE ---
  const nonxlCol = el.querySelector("#nonxl-ehe-col");
  const hotFluids = ["Lava", "IC2 Hot Coolant", "Solar Salt (Hot)"];
  nonxlCol.innerHTML = `
    <div class="card">
      <h3 style="color:#60a5fa;font-size:14px;margin-bottom:14px;">Non-XL EHE</h3>
      <div class="setting-row"><span class="setting-label">Hot fluid:</span>
        <select id="n-fluid"></select></div>
      <div class="setting-row"><span class="setting-label">Flow (L/s):</span>
        <input type="number" id="n-flow" value="10000" min="1"></div>
      <div class="setting-row"><span class="setting-label">Rotor:</span>
        <select id="n-rotor" style="max-width:200px;"></select></div>
      <div class="setting-row"><span class="setting-label">Blade Size:</span>
        <div id="n-size-toggle"></div></div>
      <div class="setting-row"><span class="setting-label">Mode:</span>
        <div id="n-mode-toggle"></div></div>
      <hr class="divider">
      ${row("EHE count:", "n-ehe-count", "muted")}
      ${row("SC steam L/t:", "n-sc-steam", "cyan")}
      ${row("SH steam L/t:", "n-sh-steam", "cyan")}
      ${row("SC turbines:", "n-sc-turb", "muted")}
      ${row("SH turbines:", "n-sh-turb", "muted")}
      ${row("Power/SC turb EU/t:", "n-power-sc", "green")}
      ${row("Power/reg turb EU/t:", "n-power-reg", "green")}
      ${row("Dynamo (SC):", "n-dynamo-sc", "muted")}
      ${row("Dynamo (reg):", "n-dynamo-reg", "muted")}
    </div>`;

  populateSelect(nonxlCol.querySelector("#n-fluid"), hotFluids, hotFluids[0]);
  populateSelect(nonxlCol.querySelector("#n-rotor"), data.rotors.map(r => r.name), data.rotors[0]?.name);

  const nSizeToggle = makeToggle(["Small","Normal","Large","Huge"], () => nonxlRecalc());
  const nModeToggle = makeToggle(["Tight","Loose"], () => nonxlRecalc());
  nonxlCol.querySelector("#n-size-toggle").appendChild(nSizeToggle);
  nonxlCol.querySelector("#n-mode-toggle").appendChild(nModeToggle);

  nonxlCol.querySelectorAll("select, input").forEach(i => i.addEventListener("change", nonxlRecalc));
  nonxlCol.querySelectorAll("input").forEach(i => i.addEventListener("input", nonxlRecalc));

  function nonxlRecalc() {
    const hotFluid = nonxlCol.querySelector("#n-fluid").value;
    const flow     = parseFloat(nonxlCol.querySelector("#n-flow").value) || 0;
    const rotorName = nonxlCol.querySelector("#n-rotor").value;
    const rotor    = data.rotors.find(r => r.name === rotorName);
    const size     = nSizeToggle.getValue();
    const mode     = nModeToggle.getValue();
    if (!rotor) return;
    const res = calcNonxlEhe(hotFluid, flow, rotor, size, mode, scSteamEuL, steamEuL);
    nonxlCol.querySelector("#n-ehe-count").textContent   = res.eheCount;
    nonxlCol.querySelector("#n-sc-steam").textContent    = formatNumber(res.totalScSteamLt);
    nonxlCol.querySelector("#n-sh-steam").textContent    = formatNumber(res.totalShSteamLt);
    nonxlCol.querySelector("#n-sc-turb").textContent     = res.scTurbineCount;
    nonxlCol.querySelector("#n-sh-turb").textContent     = res.shTurbineCount;
    nonxlCol.querySelector("#n-power-sc").textContent    = `${formatNumber(res.powerPerScTurbine)} EU/t`;
    nonxlCol.querySelector("#n-power-reg").textContent   = `${formatNumber(res.powerPerRegTurbine)} EU/t`;
    nonxlCol.querySelector("#n-dynamo-sc").textContent   = res.minDynamoTierSC;
    nonxlCol.querySelector("#n-dynamo-reg").textContent  = res.minDynamoTierReg;
  }

  nonxlRecalc();
}
```

- [ ] **Step 3: Verify EHE Planner in browser**

Click EHE Planner. Expected: two columns (Plasma EHE purple, Non-XL EHE blue). Changing inputs updates results. Cross-check a calculation against the desktop app.

- [ ] **Step 4: Commit**

```bash
git add web/js/ehe.js web/js/ui/ehe_planner.js
git commit -m "implement EHE Planner section"
```

---

## Task 10: GitHub Pages deployment

**Files:**
- Create: `.github/workflows/deploy-web.yml`

- [ ] **Step 1: Enable GitHub Pages in repo settings**

Go to: `Settings > Pages > Source` → set to **GitHub Actions**.

- [ ] **Step 2: Write `.github/workflows/deploy-web.yml`**

```yaml
name: Deploy Web to GitHub Pages

on:
  push:
    branches: ["main"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Pages
        uses: actions/configure-pages@v5

      - name: Upload web/ as Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: web/

      - id: deployment
        name: Deploy to GitHub Pages
        uses: actions/deploy-pages@v4
```

- [ ] **Step 3: Verify the workflow runs**

Push to main. Go to `Actions` tab in GitHub. The deploy workflow should appear and succeed. Open the Pages URL from the workflow output.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/deploy-web.yml
git commit -m "add GitHub Pages deployment workflow"
```

---

## Self-Review

**Spec coverage check:**
- [x] Left sidebar navigation — Task 2 (index.html + style.css) + Task 3 (app.js router)
- [x] Dark theme (#0d1117 bg, green/red/yellow/cyan accents) — Task 2 (CSS variables)
- [x] Calculator: Large + XL sub-tabs, shared settings, fuel tabs — Task 8
- [x] EHE Planner: Plasma + Non-XL side by side — Task 9
- [x] Steam Gen: static reference table — Task 5
- [x] Fuels: Steam/Gas/Plasma searchable tables — Task 5
- [x] Rotors: size toggle + sortable table — Task 6
- [x] Turbine formulas ported verbatim — Task 7
- [x] EHE formulas ported verbatim — Task 9
- [x] Data in JSON files — Task 1
- [x] Export script for JSON — Task 1
- [x] GitHub Pages deploy — Task 10
- [x] SortableTable component numeric sort — Task 4

**No placeholders found.**

**Type consistency:** `calcRegularTurbine` and `calcXlTurbine` signatures used consistently in calculator.js. `calcPlasmaEhe` / `calcNonxlEhe` consistent between ehe.js and ehe_planner.js. `SortableTable` API consistent between table.js and rotors.js / fuels.js.
