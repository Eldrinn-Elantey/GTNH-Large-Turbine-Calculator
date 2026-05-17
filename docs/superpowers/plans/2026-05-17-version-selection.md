# Version Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a version selector dropdown to the sidebar that switches the data set (rotors, fuels, steam_gen) between GTNH versions, persisting the choice in localStorage.

**Architecture:** Data files are organized into versioned subfolders (`web/data/2.7/`, `web/data/2.9/`). A new `version.js` module manages the active version. The three data modules (`rotors.js`, `fuels.js`, `steam_gen.js`) read the active version at fetch time. On version change, caches are cleared and the active section is re-rendered.

**Tech Stack:** Vanilla JS (ES modules), HTML, CSS — no build step.

---

### Task 1: Reorganize data files into versioned folders

**Files:**
- Create: `web/data/versions.json`
- Create: `web/data/2.7/rotors.json` (move from `web/data/rotors.json`)
- Create: `web/data/2.7/fuels.json` (move from `web/data/fuels.json`)
- Create: `web/data/2.7/steam_gen.json` (move from `web/data/steam_gen.json`)

- [ ] **Step 1: Create versioned subfolder and move existing files**

```powershell
New-Item -ItemType Directory -Path web/data/2.7
Move-Item web/data/rotors.json web/data/2.7/rotors.json
Move-Item web/data/fuels.json  web/data/2.7/fuels.json
Move-Item web/data/steam_gen.json web/data/2.7/steam_gen.json
```

- [ ] **Step 2: Create `web/data/versions.json`**

```json
[
  { "id": "2.7", "label": "2.7.0-2.8.4" },
  { "id": "2.9", "label": "2.8-2.9" }
]
```

(The `2.9/` folder and its data files will be added in a later task once data is prepared.)

- [ ] **Step 3: Commit**

```bash
git add web/data/
git commit -m "refactor: move data files into versioned subfolders (2.7)"
```

---

### Task 2: Create `js/version.js`

**Files:**
- Create: `web/js/version.js`

- [ ] **Step 1: Write `web/js/version.js`**

```js
const STORAGE_KEY = "gtnh-version";

let _versions = null;

export async function loadVersions() {
  if (_versions) return _versions;
  const res = await fetch("data/versions.json");
  _versions = await res.json();
  return _versions;
}

export function getVersion() {
  return localStorage.getItem(STORAGE_KEY) ?? null;
}

export function setVersion(id) {
  localStorage.setItem(STORAGE_KEY, id);
}

// Returns the version id to use — falls back to first available version.
export async function resolveVersion() {
  const versions = await loadVersions();
  const saved = getVersion();
  if (saved && versions.find(v => v.id === saved)) return saved;
  const fallback = versions[0].id;
  setVersion(fallback);
  return fallback;
}
```

- [ ] **Step 2: Commit**

```bash
git add web/js/version.js
git commit -m "feat: version.js — load versions manifest, persist selection"
```

---

### Task 3: Update data modules to use versioned paths

**Files:**
- Modify: `web/js/ui/rotors.js`
- Modify: `web/js/ui/fuels.js`
- Modify: `web/js/ui/steam_gen.js`

- [ ] **Step 1: Update `rotors.js`**

Add import at the top and update `loadData`. Also export `clearCache`:

```js
import { SortableTable } from "../table.js";
import { formatNumber } from "../utils.js";
import { getVersion } from "../version.js";

const TURBINE_TO_ROTOR_SIZE = { Small: "Small", Normal: "Small", Large: "Normal", Huge: "Large" };
const TURBINE_TO_DUR_SIZE   = { Small: "Normal", Normal: "Large", Large: "Large", Huge: "Huge" };

let _rotors = null;

export function clearCache() { _rotors = null; }

async function loadData() {
  if (_rotors) return _rotors;
  const res = await fetch(`data/${getVersion()}/rotors.json`);
  _rotors = await res.json();
  return _rotors;
}
```

(Rest of the file stays unchanged.)

- [ ] **Step 2: Update `fuels.js`**

```js
import { SortableTable } from "../table.js";
import { getVersion } from "../version.js";

let _data = null;

export function clearCache() { _data = null; }

async function loadData() {
  if (_data) return _data;
  const res = await fetch(`data/${getVersion()}/fuels.json`);
  _data = await res.json();
  return _data;
}
```

(Rest of the file stays unchanged.)

- [ ] **Step 3: Update `steam_gen.js`**

```js
import { formatNumber } from "../utils.js";
import { getVersion } from "../version.js";

let _data = null;

export function clearCache() { _data = null; }

async function loadData() {
  if (_data) return _data;
  const res = await fetch(`data/${getVersion()}/steam_gen.json`);
  _data = await res.json();
  return _data;
}
```

(Rest of the file stays unchanged.)

- [ ] **Step 4: Commit**

```bash
git add web/js/ui/rotors.js web/js/ui/fuels.js web/js/ui/steam_gen.js
git commit -m "feat: data modules read from versioned path"
```

---

### Task 4: Add version selector to the sidebar

**Files:**
- Modify: `web/index.html`
- Modify: `web/css/style.css`
- Modify: `web/js/app.js`

- [ ] **Step 1: Add `<select>` to sidebar in `index.html`**

Replace the existing `.sidebar-logo` block:

```html
<div class="sidebar-logo">
  GTNH<br><span>Turbines</span>
  <select id="version-select" class="version-select"></select>
</div>
```

- [ ] **Step 2: Style the select in `style.css`**

Add after the `.sidebar-logo span` rule:

```css
.version-select {
  display: block;
  width: 100%;
  margin-top: 8px;
  background: var(--bg);
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 3px 6px;
  font-size: 11px;
  cursor: pointer;
}
```

- [ ] **Step 3: Wire up version select in `app.js`**

```js
import { initCalculator } from "./ui/calculator.js";
import { initEhePlanner } from "./ui/ehe_planner.js";
import { initSteamGen }   from "./ui/steam_gen.js";
import { initFuels }      from "./ui/fuels.js";
import { initRotors }     from "./ui/rotors.js";
import { clearCache as clearRotors }   from "./ui/rotors.js";
import { clearCache as clearFuels }    from "./ui/fuels.js";
import { clearCache as clearSteamGen } from "./ui/steam_gen.js";
import { loadVersions, resolveVersion, setVersion } from "./version.js";

const SECTIONS = {
  "calculator": initCalculator,
  "ehe":        initEhePlanner,
  "steam-gen":  initSteamGen,
  "fuels":      initFuels,
  "rotors":     initRotors,
};

const initialised = new Set();
let activeSection = "calculator";

function showSection(sectionId) {
  document.querySelectorAll(".section").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));

  const sectionEl = document.getElementById(`section-${sectionId}`);
  if (!sectionEl) return;
  sectionEl.classList.remove("hidden");

  const navItem = document.querySelector(`.nav-item[data-section="${sectionId}"]`);
  if (navItem) navItem.classList.add("active");

  activeSection = sectionId;

  if (!initialised.has(sectionId) && SECTIONS[sectionId]) {
    SECTIONS[sectionId](sectionEl);
    initialised.add(sectionId);
  }
}

function reloadActiveSection() {
  const sectionEl = document.getElementById(`section-${activeSection}`);
  if (!sectionEl || !SECTIONS[activeSection]) return;
  initialised.delete(activeSection);
  sectionEl.innerHTML = "";
  SECTIONS[activeSection](sectionEl);
  initialised.add(activeSection);
}

async function initVersionSelect() {
  const versions = await loadVersions();
  const current = await resolveVersion();

  const select = document.getElementById("version-select");
  versions.forEach(v => {
    const opt = document.createElement("option");
    opt.value = v.id;
    opt.textContent = v.label;
    if (v.id === current) opt.selected = true;
    select.appendChild(opt);
  });

  select.addEventListener("change", () => {
    setVersion(select.value);
    clearRotors();
    clearFuels();
    clearSteamGen();
    reloadActiveSection();
  });
}

document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", () => showSection(item.dataset.section));
});

await initVersionSelect();
showSection("calculator");
```

- [ ] **Step 4: Verify in browser**

Open `web/index.html` via a local server. Check:
- Version dropdown appears in sidebar under the logo
- Changing version reloads data (open DevTools Network tab — should see fetch to `data/2.X/rotors.json`)
- Refreshing page restores the selected version

- [ ] **Step 5: Commit**

```bash
git add web/index.html web/css/style.css web/js/app.js
git commit -m "feat: version selector dropdown in sidebar"
```

---

### Task 5: Prepare 2.9 data

This task is tracked separately as it requires extracting and transforming data from the xlsx file. It can be done independently once Task 1 is complete.

- [ ] **Step 1: Create `web/data/2.9/` folder**

```powershell
New-Item -ItemType Directory -Path web/data/2.9
```

- [ ] **Step 2: Export rotor data from xlsx**

Run a Python script to extract Rotor Data sheet from `GTNH Power Planner 2.8-2.9.xlsx` and convert to the same JSON schema as `web/data/2.7/rotors.json`. Review the output carefully — field names and structure must match exactly.

- [ ] **Step 3: Export fuel data from xlsx**

Same process for Fuel Data sheet → `web/data/2.9/fuels.json`.

- [ ] **Step 4: Copy steam_gen data**

If steam generator data hasn't changed between versions, copy from 2.7:

```powershell
Copy-Item web/data/2.7/steam_gen.json web/data/2.9/steam_gen.json
```

- [ ] **Step 5: Commit**

```bash
git add web/data/2.9/
git commit -m "feat: add 2.9 data set"
```
