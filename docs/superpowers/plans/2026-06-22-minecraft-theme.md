# Minecraft Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current dark developer-style CSS with an authentic Minecraft GUI aesthetic (grey inventory palette, Press Start 2P font, raised/sunken pixel borders).

**Architecture:** All changes are CSS-only — `style.css` (layout, sidebar, base) and `components.css` (cards, inputs, tables, buttons). No HTML structure changes, no JS changes. The existing class names and DOM stay identical.

**Tech Stack:** Pure CSS, Google Fonts (Press Start 2P via `<link>` in HTML)

---

### Task 1: Add Google Font and reset CSS variables

**Files:**
- Modify: `web/index.html` (add font link in `<head>`)
- Modify: `web/css/style.css:1-17` (replace `:root` variables and base font)

- [ ] **Step 1: Add Press Start 2P font to HTML**

In `web/index.html`, add inside `<head>` before the CSS links:

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
```

- [ ] **Step 2: Replace CSS variables in style.css**

Replace the entire `:root` block (lines 1–17) with:

```css
:root {
  --mc-bg:      #c6c6c6;
  --mc-panel:   #8b8b8b;
  --mc-sidebar: #555555;
  --mc-dark:    #373737;
  --mc-light:   #ffffff;
  --mc-text:    #ffffff;
  --mc-text-bg: #1a1a1a;
  --mc-green:   #7ec850;
  --mc-yellow:  #f6c90e;
  --mc-red:     #e05c5c;
  --mc-cyan:    #7ec8c8;
  --mc-muted:   #aaaaaa;
  --sidebar-w:  150px;
  --font:       'Press Start 2P', monospace;
  --font-size:  10px;
}
```

- [ ] **Step 3: Verify the page loads without errors**

Open `web/index.html` in a browser (or the running dev server). No console errors expected. The page will look broken — that's fine, we haven't rewritten the rest yet.

- [ ] **Step 4: Commit**

```bash
git add web/index.html web/css/style.css
git commit -m "theme: add Press Start 2P font and Minecraft CSS variables"
```

---

### Task 2: Rewrite base layout and body styles

**Files:**
- Modify: `web/css/style.css:19-192` (everything after `:root`)

- [ ] **Step 1: Replace base reset and body styles**

Replace lines 19–32 in `web/css/style.css`:

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { font-size: var(--font-size); }

body {
  background: var(--mc-bg);
  color: var(--mc-text-bg);
  font-family: var(--font);
  font-size: 1rem;
  height: 100vh;
  overflow: hidden;
  image-rendering: pixelated;
}

.layout {
  display: flex;
  height: 100vh;
}
```

- [ ] **Step 2: Replace sidebar styles**

Replace lines 39–112 (sidebar section) with:

```css
/* Sidebar */
.sidebar {
  width: var(--sidebar-w);
  flex-shrink: 0;
  background: var(--mc-sidebar);
  border-right: 3px solid var(--mc-dark);
  display: flex;
  flex-direction: column;
}

.sidebar-logo {
  background: var(--mc-dark);
  color: var(--mc-text);
  font-size: 0.9rem;
  padding: 10px 8px;
  line-height: 2;
  border-bottom: 3px solid var(--mc-dark);
  text-shadow: 1px 1px #000;
}

.sidebar-logo span { color: var(--mc-muted); font-size: 0.7rem; }

.version-select {
  display: block;
  width: 100%;
  margin-top: 6px;
  background: var(--mc-dark);
  color: var(--mc-text);
  font-family: var(--font);
  font-size: 0.7rem;
  padding: 3px 4px;
  border-top: 2px solid #222;
  border-left: 2px solid #222;
  border-right: 2px solid #999;
  border-bottom: 2px solid #999;
  cursor: pointer;
  outline: none;
}

.nav-list { list-style: none; }

.nav-item {
  padding: 10px 8px;
  cursor: pointer;
  color: var(--mc-muted);
  font-size: 0.7rem;
  user-select: none;
  border-bottom: 1px solid #444;
  text-shadow: 1px 1px #000;
  line-height: 1.8;
}

.nav-item:hover { background: #666; color: var(--mc-text); }

.nav-item.active {
  background: var(--mc-panel);
  color: var(--mc-text);
  border-top: 2px solid var(--mc-light);
  border-left: 2px solid var(--mc-light);
  border-right: 2px solid var(--mc-dark);
  border-bottom: 2px solid var(--mc-dark);
}

.sidebar-footer {
  margin-top: auto;
  padding: 8px;
  border-top: 2px solid var(--mc-dark);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar-footer-version,
.sidebar-footer-issues {
  color: var(--mc-muted);
  font-size: 0.65rem;
  text-decoration: none;
  text-shadow: 1px 1px #000;
}

.sidebar-footer-version:hover,
.sidebar-footer-issues:hover { color: var(--mc-text); }
```

- [ ] **Step 3: Replace main content and utility styles**

Replace lines 114–192 (main-content through section-title) with:

```css
/* Main content */
.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: var(--mc-bg);
}

.section { width: 100%; }
.hidden { display: none !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--mc-bg); }
::-webkit-scrollbar-thumb { background: var(--mc-dark); }

/* Hamburger button (mobile only) */
.hamburger {
  display: none;
  position: fixed;
  top: 10px;
  left: 10px;
  z-index: 200;
  background: var(--mc-panel);
  color: var(--mc-text);
  font-family: var(--font);
  font-size: 1rem;
  width: 36px;
  height: 36px;
  border-top: 3px solid var(--mc-light);
  border-left: 3px solid var(--mc-light);
  border-right: 3px solid var(--mc-dark);
  border-bottom: 3px solid var(--mc-dark);
  cursor: pointer;
  line-height: 1;
}

/* Overlay behind sidebar on mobile */
.sidebar-overlay {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  z-index: 150;
}

.sidebar-overlay.active { display: block; }

@media (max-width: 640px) {
  body { overflow: auto; height: auto; }

  .layout { display: block; }

  .hamburger { display: flex; align-items: center; justify-content: center; }

  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100%;
    z-index: 160;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
  }

  .sidebar.open { transform: translateX(0); }

  .main-content {
    padding: 16px;
    padding-top: 56px;
    overflow-y: visible;
    min-height: 100vh;
  }
}

/* Section heading */
.section-title {
  font-size: 1rem;
  color: var(--mc-text-bg);
  margin-bottom: 16px;
  text-shadow: 1px 1px #fff;
}
```

- [ ] **Step 4: Verify sidebar and layout render correctly**

Reload the page. Expected: grey sidebar visible, nav items readable, main area light grey. Font may still be wrong in some places — that's fine.

- [ ] **Step 5: Commit**

```bash
git add web/css/style.css
git commit -m "theme: rewrite base layout and sidebar styles"
```

---

### Task 3: Rewrite components — cards, inputs, selects

**Files:**
- Modify: `web/css/components.css:1-160` (tabs through combobox)

- [ ] **Step 1: Replace sub-tabs and toggle-group**

Replace lines 1–45 with:

```css
/* Sub-tabs */
.sub-tabs {
  display: flex;
  gap: 0;
  border-bottom: 3px solid var(--mc-dark);
  margin-bottom: 16px;
}

.sub-tab {
  padding: 6px 14px;
  cursor: pointer;
  color: var(--mc-muted);
  font-size: 0.8rem;
  border-bottom: 3px solid transparent;
  margin-bottom: -3px;
  user-select: none;
  text-shadow: 1px 1px #000;
}

.sub-tab:hover { color: var(--mc-text-bg); }
.sub-tab.active {
  color: var(--mc-text-bg);
  border-bottom-color: var(--mc-dark);
  background: var(--mc-panel);
  border-top: 2px solid var(--mc-light);
  border-left: 2px solid var(--mc-light);
  border-right: 2px solid var(--mc-dark);
}

/* Toggle button group */
.toggle-group {
  display: inline-flex;
  background: var(--mc-dark);
  padding: 2px;
  gap: 2px;
  border-top: 2px solid #222;
  border-left: 2px solid #222;
  border-right: 2px solid #999;
  border-bottom: 2px solid #999;
}

.toggle-btn {
  padding: 4px 10px;
  border: none;
  background: transparent;
  color: var(--mc-muted);
  font-size: 0.8rem;
  cursor: pointer;
  font-family: var(--font);
  text-shadow: 1px 1px #000;
}

.toggle-btn:hover { background: #555; color: var(--mc-text); }
.toggle-btn.active {
  background: var(--mc-panel);
  color: var(--mc-text);
  border-top: 2px solid var(--mc-light);
  border-left: 2px solid var(--mc-light);
  border-right: 2px solid var(--mc-dark);
  border-bottom: 2px solid var(--mc-dark);
}
```

- [ ] **Step 2: Replace card and setting-row**

Replace lines 47–72 with:

```css
/* Card */
.card {
  background: var(--mc-panel);
  border-top: 3px solid var(--mc-light);
  border-left: 3px solid var(--mc-light);
  border-right: 3px solid var(--mc-dark);
  border-bottom: 3px solid var(--mc-dark);
  padding: 12px;
}

.card-narrow { max-width: 520px; }

/* Settings row */
.setting-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.setting-label {
  color: var(--mc-muted);
  font-size: 0.8rem;
  min-width: 90px;
  text-shadow: 1px 1px #000;
}
```

- [ ] **Step 3: Replace select, input, combobox styles**

Replace lines 74–160 with:

```css
/* Select / dropdown */
select {
  background: var(--mc-dark);
  color: var(--mc-text);
  font-family: var(--font);
  font-size: 0.8rem;
  padding: 4px 6px;
  border-top: 2px solid #222;
  border-left: 2px solid #222;
  border-right: 2px solid #999;
  border-bottom: 2px solid #999;
  cursor: pointer;
  outline: none;
  max-width: 240px;
}

/* Custom combobox */
.combobox {
  position: relative;
  display: inline-block;
}

.combobox-input {
  width: 100%;
  background: var(--mc-dark);
  color: var(--mc-text);
  border-top: 2px solid #222;
  border-left: 2px solid #222;
  border-right: 2px solid #999;
  border-bottom: 2px solid #999;
  padding: 4px 6px;
  font-size: 0.8rem;
  font-family: var(--font);
  outline: none;
  box-sizing: border-box;
}

.combobox-dropdown {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--mc-dark);
  border: 2px solid #222;
  border-top: none;
  max-height: 220px;
  overflow-y: auto;
  z-index: 100;
}

.combobox-dropdown.open { display: block; }

.combobox-option {
  padding: 5px 8px;
  font-size: 0.8rem;
  font-family: var(--font);
  color: var(--mc-text);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.combobox-option:hover,
.combobox-option.active { background: #555; color: var(--mc-text); }

/* Text input */
input[type="number"], input[type="text"] {
  background: var(--mc-dark);
  color: var(--mc-text);
  border-top: 2px solid #222;
  border-left: 2px solid #222;
  border-right: 2px solid #999;
  border-bottom: 2px solid #999;
  padding: 4px 6px;
  font-size: 0.8rem;
  font-family: var(--font);
  outline: none;
  width: 100px;
}

/* Remove number input arrows */
input[type="number"]::-webkit-inner-spin-button,
input[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; }
```

- [ ] **Step 4: Verify inputs and cards look correct**

Reload page. Cards should have raised grey border. Inputs/selects should have dark background with sunken border.

- [ ] **Step 5: Commit**

```bash
git add web/css/components.css
git commit -m "theme: rewrite cards, inputs, selects to Minecraft style"
```

---

### Task 4: Rewrite components — result rows, divider, fuel tabs, table

**Files:**
- Modify: `web/css/components.css:160-265`

- [ ] **Step 1: Replace result-row, divider, fuel-tabs**

Replace lines 160–205 with:

```css
/* Result row */
.result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 0.8rem;
  border-bottom: 1px solid #666;
}

.result-row:last-child { border-bottom: none; }

.result-label { color: var(--mc-muted); display: flex; align-items: center; gap: 6px; text-shadow: 1px 1px #000; }
.result-value { font-weight: normal; text-shadow: 1px 1px #000; }
.result-value.green  { color: var(--mc-green); }
.result-value.yellow { color: var(--mc-yellow); }
.result-value.cyan   { color: var(--mc-cyan); }
.result-value.muted  { color: var(--mc-muted); }
.result-value.purple { color: #c8a8e0; }

/* Divider */
.divider {
  border: none;
  border-top: 2px solid var(--mc-dark);
  margin: 8px 0;
}

/* Fuel tabs */
.fuel-tabs {
  display: flex;
  border-bottom: 2px solid var(--mc-dark);
  margin-bottom: 12px;
}

.fuel-tab {
  padding: 5px 12px;
  cursor: pointer;
  font-size: 0.8rem;
  color: var(--mc-muted);
  border-bottom: 3px solid transparent;
  margin-bottom: -2px;
  user-select: none;
  text-shadow: 1px 1px #000;
}

.fuel-tab:hover { color: var(--mc-text); }
.fuel-tab.active { color: var(--mc-text); border-bottom-color: var(--mc-dark); background: #666; }
.fuel-tab.steam.active  { border-bottom-color: var(--mc-cyan);   color: var(--mc-cyan); }
.fuel-tab.gas.active    { border-bottom-color: var(--mc-yellow);  color: var(--mc-yellow); }
.fuel-tab.plasma.active { border-bottom-color: #c8a8e0;           color: #c8a8e0; }
```

- [ ] **Step 2: Replace table styles**

Replace lines 207–265 with:

```css
/* Table */
.table-wrap { overflow-x: auto; }

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.data-table th {
  background: var(--mc-dark);
  color: var(--mc-text);
  padding: 6px 10px;
  text-align: left;
  cursor: pointer;
  white-space: nowrap;
  user-select: none;
  text-shadow: 1px 1px #000;
  border-right: 1px solid #555;
}

.data-table th.numeric { text-align: center; }
.data-table th .sort-arrow { margin-left: 4px; opacity: 0.4; }
.data-table th.sorted .sort-arrow { opacity: 1; }

.data-table td {
  padding: 5px 10px;
  border-bottom: 1px solid #999;
  color: var(--mc-text-bg);
  background: var(--mc-bg);
}

.data-table td.numeric { text-align: center; }
.data-table tr:hover td { background: #b0b0b0; }

/* Search box above table */
.search-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--mc-panel);
  padding: 8px 12px;
  border-bottom: 2px solid var(--mc-dark);
}

.search-input {
  flex: 1;
  background: var(--mc-dark);
  color: var(--mc-text);
  border-top: 2px solid #222;
  border-left: 2px solid #222;
  border-right: 2px solid #999;
  border-bottom: 2px solid #999;
  padding: 5px 8px;
  font-size: 0.8rem;
  font-family: var(--font);
  outline: none;
  max-width: 300px;
}
```

- [ ] **Step 3: Verify tables render correctly**

Go to Fuels or Rotors section. Table should have dark header, light grey rows, hover effect.

- [ ] **Step 4: Commit**

```bash
git add web/css/components.css
git commit -m "theme: rewrite result rows, tables, fuel tabs"
```

---

### Task 5: Rewrite components — grid helpers, slots, add/remove buttons

**Files:**
- Modify: `web/css/components.css:265-318` (grid through end of file)

- [ ] **Step 1: Replace grid helpers and calc-slot styles**

Replace lines 265–318 with:

```css
/* Grid helpers */
.row { display: flex; gap: 16px; }
.col { flex: 1; }

/* Multi-card calculator slots */
.calc-slots {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-start;
}

.calc-slot {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.slot-remove-btn {
  position: absolute;
  top: -10px;
  right: -10px;
  z-index: 10;
  width: 22px;
  height: 22px;
  border-top: 2px solid var(--mc-light);
  border-left: 2px solid var(--mc-light);
  border-right: 2px solid var(--mc-dark);
  border-bottom: 2px solid var(--mc-dark);
  background: var(--mc-panel);
  color: var(--mc-text);
  font-size: 1rem;
  font-family: var(--font);
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  text-shadow: 1px 1px #000;
}

.slot-remove-btn:hover {
  background: var(--mc-red);
  border-top-color: #ff9999;
  border-left-color: #ff9999;
}

.slot-add-btn {
  margin-top: 8px;
  padding: 7px 14px;
  background: var(--mc-panel);
  color: var(--mc-muted);
  border-top: 3px solid var(--mc-light);
  border-left: 3px solid var(--mc-light);
  border-right: 3px solid var(--mc-dark);
  border-bottom: 3px solid var(--mc-dark);
  font-size: 0.8rem;
  font-family: var(--font);
  cursor: pointer;
  text-shadow: 1px 1px #000;
}

.slot-add-btn:hover { color: var(--mc-text); background: #999; }

.slot-add-btn:active {
  border-top-color: var(--mc-dark);
  border-left-color: var(--mc-dark);
  border-right-color: var(--mc-light);
  border-bottom-color: var(--mc-light);
}
```

- [ ] **Step 2: Verify calculator slots and buttons work visually**

Go to Calculator section, add a second turbine slot. The + button should look raised and flip on click. Remove button should turn red on hover.

- [ ] **Step 3: Commit**

```bash
git add web/css/components.css
git commit -m "theme: rewrite grid helpers and slot buttons"
```

---

### Task 6: Final visual pass and typography tuning

**Files:**
- Modify: `web/css/style.css` (add card-title helper if needed)
- Modify: `web/css/components.css` (add card-title if sections use it)

- [ ] **Step 1: Add card-title helper class**

Append to end of `web/css/components.css`:

```css
/* Card title bar */
.card-title {
  font-size: 0.8rem;
  color: var(--mc-text);
  text-shadow: 1px 1px #000;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 2px solid var(--mc-dark);
}
```

- [ ] **Step 2: Walk through every section and check for visual regressions**

Check each nav item in order: Calculator, EHE Planner, Steam Gen, Fuels, Rotors, Settings.

Look for:
- Any hardcoded `#0d1117` / `#111827` / `#1f2937` colours still visible (use browser DevTools inspector)
- Unreadable text (dark on dark, or light on light)
- Missing borders on any interactive element

Fix any found issues directly in the CSS files.

- [ ] **Step 3: Commit final fixes**

```bash
git add web/css/style.css web/css/components.css
git commit -m "theme: final visual pass and typography tweaks"
```
