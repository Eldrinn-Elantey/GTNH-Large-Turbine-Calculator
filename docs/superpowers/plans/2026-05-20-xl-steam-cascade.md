# XL Steam Cascade Planner — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Steam Cascade" inner sub-tab inside "XL Turbo Turbines" that plans the full Dense SC → Dense SH → Dense Steam turbine chain driven by plasma EHEs, including net power after reactor consumption.

**Architecture:** New `xl_cascade.js` component handles all cascade UI and calc; `calculator.js` gains inner sub-tabs (Single Turbine / Steam Cascade) for the XL section; `i18n.js` and `components.css` get small additions. Cascade calls existing `calcPlasmaEhe` for EHE count + steam output, then calls `calcXlTurbine` with `isDense=true` separately for each stage (SC/HP/Reg) using per-stage rotor/mode state.

**Tech Stack:** Vanilla JS ES modules, existing `calcXlTurbine` / `calcPlasmaEhe` / `formatNumber` / `formatDynamo` / `makeCombobox` utilities.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `web/js/ui/xl_cascade.js` | Complete cascade planner component |
| Modify | `web/js/ui/calculator.js` | Add inner sub-tabs to XL section, import xl_cascade |
| Modify | `web/js/i18n.js` | Add 13 new translation keys |
| Modify | `web/css/components.css` | Add `.xl-inner-tabs` / `.xl-inner-tab` CSS (avoids class conflict with outer `.sub-tab`) |

---

### Task 1: Add CSS for inner sub-tabs

**Files:**
- Modify: `web/css/components.css`

- [ ] **Step 1: Append inner-tab styles to components.css**

Open `web/css/components.css` and append at the end:

```css
/* Inner sub-tabs (e.g. Single Turbine / Steam Cascade inside XL section) */
.xl-inner-tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--border);
  margin-bottom: 16px;
}

.xl-inner-tab {
  padding: 5px 16px;
  cursor: pointer;
  color: var(--muted);
  font-size: 0.9rem;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  user-select: none;
  transition: color 0.1s;
}

.xl-inner-tab:hover { color: var(--text); }
.xl-inner-tab.active { color: #93c5fd; border-bottom-color: #3b82f6; }
```

- [ ] **Step 2: Commit**

```bash
git add web/css/components.css
git commit -m "style: add xl-inner-tab styles for XL turbine sub-navigation"
```

---

### Task 2: Add i18n keys

**Files:**
- Modify: `web/js/i18n.js`

- [ ] **Step 1: Add keys to English block**

In `web/js/i18n.js`, inside the `en:` object after the existing `tab_compare_rotors` line, add:

```js
    tab_xl_single:             "Single Turbine",
    tab_xl_cascade:            "Steam Cascade",
    cascade_ehe_source:        "EHE Source",
    cascade_settings:          "Cascade Settings",
    cascade_summary:           "Summary",
    label_eu_per_recipe:       "EU/t per recipe:",
    result_reactor_consumption:"Reactor consumption:",
    result_total_turbines:     "Total turbines:",
    result_gross_power:        "Gross power:",
    result_net_power:          "Net power:",
    cascade_full:              "full",
    cascade_partial:           "partial",
    cascade_each:              "each",
```

- [ ] **Step 2: Add keys to Russian block**

In the `ru:` object after the existing `tab_compare_rotors` line, add:

```js
    tab_xl_single:             "Одиночная турбина",
    tab_xl_cascade:            "Паровой каскад",
    cascade_ehe_source:        "EHE Источник",
    cascade_settings:          "Настройки каскада",
    cascade_summary:           "Итого",
    label_eu_per_recipe:       "EU/t на рецепт:",
    result_reactor_consumption:"Потребление реакторов:",
    result_total_turbines:     "Всего турбин:",
    result_gross_power:        "Валовая мощность:",
    result_net_power:          "Чистый выход:",
    cascade_full:              "полн.",
    cascade_partial:           "частичн.",
    cascade_each:              "каждая",
```

- [ ] **Step 3: Commit**

```bash
git add web/js/i18n.js
git commit -m "i18n: add xl steam cascade translation keys"
```

---

### Task 3: Create xl_cascade.js

**Files:**
- Create: `web/js/ui/xl_cascade.js`

- [ ] **Step 1: Create the file with complete content**

Create `web/js/ui/xl_cascade.js` with this content:

```js
import { calcXlTurbine } from "../calc.js";
import { calcPlasmaEhe } from "../ehe.js";
import { formatNumber, formatDynamo, populateSelect, makeCombobox, DYNAMO_TIERS } from "../utils.js";
import { getVersion } from "../version.js";
import { t } from "../i18n.js";

let _data = null;

export function clearCache() { _data = null; }

async function loadData() {
  if (_data) return _data;
  const v = getVersion();
  const [rotors, fuels] = await Promise.all([
    fetch(`data/${v}/rotors.json`).then(r => r.json()),
    fetch(`data/${v}/fuels.json`).then(r => r.json()),
  ]);
  const eheMap = {};
  for (const e of fuels.ehe) eheMap[e.name] = e;
  const NON_PLASMA = new Set(["Lava", "IC2 Hot Coolant", "Solar Salt (Hot)"]);
  const plasmaTypes = Object.keys(eheMap).filter(n => !NON_PLASMA.has(n));
  _data = { rotors, fuels, eheMap, plasmaTypes };
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

function resultRow(label, colorClass = "green") {
  const row = document.createElement("div");
  row.className = "result-row";
  row.innerHTML = `<span class="result-label">${label}</span><span class="result-value ${colorClass}">—</span>`;
  row.setValue = v => { row.querySelector(".result-value").textContent = v; };
  return row;
}

function settingRow(labelText) {
  const row = document.createElement("div");
  row.className = "setting-row";
  row.innerHTML = `<span class="setting-label">${labelText}</span>`;
  return row;
}

// Dense steam fuel types and their eu_l source keys (regular steam eu_l, not ×1000)
const STAGES = [
  { key: "sc",  label: "💧 SC Steam", fuelType: "Dense SC Steam", euLKey: "SC Steam",  headerColor: "#93c5fd" },
  { key: "hp",  label: "🔵 HP Steam", fuelType: "Dense SH Steam", euLKey: "SH Steam",  headerColor: "#60a5fa" },
  { key: "reg", label: "⚪ Steam",    fuelType: "Dense Steam",    euLKey: "Steam",      headerColor: "#9ca3af" },
];

// Returns EHE-derived values needed for cascade; rotor is used only internally by calcPlasmaEhe
function computeEhe(state, data, scSteamEuL) {
  const anyRotor = state.stages.sc.rotor ?? data.rotors[0];
  if (!anyRotor || state.recipeTime <= 0) return null;
  const res = calcPlasmaEhe(
    state.plasmaType, state.recipeOut, state.recipeTime,
    state.parallels, anyRotor, state.size, "Loose",
    data.eheMap, scSteamEuL
  );
  return {
    plasmaOutputLs:    res.plasmaOutputLs,
    eheCount:          res.eheCount,
    denseSCSteamLt:    res.denseSCSteamLt,
    reactorConsumption: state.euPerRecipe * state.parallels,
  };
}

// Compute one cascade stage; flow is in Dense L/t throughout
function computeStage(denseSCSteamLt, rotor, size, mode, fuelType, euL) {
  if (!rotor || denseSCSteamLt <= 0) return null;
  const full = calcXlTurbine("steam", rotor, size, mode, fuelType, euL, true, null);
  const optFlow = full.optFlow;
  if (optFlow <= 0) return null;
  const fullCount = Math.floor(denseSCSteamLt / optFlow);
  const remainder = denseSCSteamLt - fullCount * optFlow;
  const partial   = remainder > 0
    ? calcXlTurbine("steam", rotor, size, mode, fuelType, euL, true, remainder)
    : null;
  const stageTotal = fullCount * full.optOutput + (partial?.effOutput ?? 0);
  return { optFlow, fullCount, remainder, fullOutput: full.optOutput, fullLifetime: full.lifetime, partial, stageTotal };
}

export async function initXlCascade(el) {
  const data = await loadData();

  const scSteamEuL = data.fuels.steam.find(f => f.name === "SC Steam")?.eu_l ?? 1.0;
  const shSteamEuL = data.fuels.steam.find(f => f.name === "SH Steam")?.eu_l ?? 1.0;
  const steamEuL   = data.fuels.steam.find(f => f.name === "Steam")?.eu_l    ?? 0.5;
  const euLMap = { "Dense SC Steam": scSteamEuL, "Dense SH Steam": shSteamEuL, "Dense Steam": steamEuL };

  const state = {
    plasmaType:   data.plasmaTypes[0] ?? "",
    recipeOut:    1000,
    recipeTime:   20,
    euPerRecipe:  0,
    parallels:    1,
    size:         "Huge",
    dynamoTier:   "EV",
    stages: {
      sc:  { rotor: data.rotors[0] ?? null, mode: "Loose" },
      hp:  { rotor: data.rotors[0] ?? null, mode: "Loose" },
      reg: { rotor: data.rotors[0] ?? null, mode: "Loose" },
    },
  };

  // ---- EHE source card ----
  const eheCard = document.createElement("div");
  eheCard.className = "card";
  eheCard.style.flex = "1.1";

  const eheTitleEl = document.createElement("div");
  eheTitleEl.className = "result-label";
  eheTitleEl.style.cssText = "color:#f87171;font-size:0.78rem;font-weight:bold;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:10px;display:block;";
  eheTitleEl.textContent = t("cascade_ehe_source");
  eheCard.appendChild(eheTitleEl);

  const plasmaRow = settingRow(t("label_plasma_type"));
  const plasmaSel = document.createElement("select");
  plasmaSel.style.maxWidth = "220px";
  populateSelect(plasmaSel, data.plasmaTypes, state.plasmaType);
  plasmaSel.addEventListener("change", () => { state.plasmaType = plasmaSel.value; recalc(); });
  plasmaRow.appendChild(plasmaSel);
  eheCard.appendChild(plasmaRow);

  const recipeOutRow = settingRow(t("label_recipe_out"));
  const recipeOutInput = document.createElement("input");
  recipeOutInput.type = "number"; recipeOutInput.min = "1"; recipeOutInput.value = state.recipeOut;
  recipeOutInput.addEventListener("input", () => { state.recipeOut = parseFloat(recipeOutInput.value) || 0; recalc(); });
  recipeOutRow.appendChild(recipeOutInput);
  eheCard.appendChild(recipeOutRow);

  const recipeTimeRow = settingRow(t("label_recipe_time"));
  const recipeTimeInput = document.createElement("input");
  recipeTimeInput.type = "number"; recipeTimeInput.min = "0.001"; recipeTimeInput.step = "0.1"; recipeTimeInput.value = state.recipeTime;
  recipeTimeInput.addEventListener("input", () => { state.recipeTime = parseFloat(recipeTimeInput.value) || 1; recalc(); });
  recipeTimeRow.appendChild(recipeTimeInput);
  eheCard.appendChild(recipeTimeRow);

  const euRow = settingRow(t("label_eu_per_recipe"));
  const euInput = document.createElement("input");
  euInput.type = "number"; euInput.min = "0"; euInput.value = state.euPerRecipe;
  euInput.addEventListener("input", () => { state.euPerRecipe = parseFloat(euInput.value) || 0; recalc(); });
  euRow.appendChild(euInput);
  eheCard.appendChild(euRow);

  const parallelsRow = settingRow(t("label_parallels"));
  const parallelsInput = document.createElement("input");
  parallelsInput.type = "number"; parallelsInput.min = "1"; parallelsInput.value = state.parallels;
  parallelsInput.addEventListener("input", () => { state.parallels = parseInt(parallelsInput.value) || 1; recalc(); });
  parallelsRow.appendChild(parallelsInput);
  eheCard.appendChild(parallelsRow);

  const eheHr = document.createElement("hr"); eheHr.className = "divider";
  eheCard.appendChild(eheHr);

  const plasmaLsRow  = resultRow(t("result_plasma_ls"), "purple");
  const eheCountRow  = resultRow(t("result_ehe_count"), "muted");
  const scSteamRow   = resultRow(t("result_dense_sc_steam"), "cyan");
  const reactorRow   = resultRow(t("result_reactor_consumption"), "red");
  [plasmaLsRow, eheCountRow, scSteamRow, reactorRow].forEach(r => eheCard.appendChild(r));

  // ---- Shared settings card ----
  const settingsCard = document.createElement("div");
  settingsCard.className = "card";
  settingsCard.style.flex = "1";

  const settingsTitleEl = document.createElement("div");
  settingsTitleEl.style.cssText = "color:#f87171;font-size:0.78rem;font-weight:bold;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:10px;";
  settingsTitleEl.textContent = t("cascade_settings");
  settingsCard.appendChild(settingsTitleEl);

  const sizeRow = settingRow(t("label_blade_size"));
  const sizeToggle = makeToggle(["Small", "Normal", "Large", "Huge"], v => { state.size = v; recalc(); });
  sizeToggle.querySelectorAll(".toggle-btn").forEach((b, i) => b.classList.toggle("active", i === 3));
  state.size = "Huge";
  sizeRow.appendChild(sizeToggle);
  settingsCard.appendChild(sizeRow);

  const dynRow = settingRow(t("label_dynamos"));
  const dynSel = document.createElement("select");
  dynSel.style.width = "90px";
  populateSelect(dynSel, DYNAMO_TIERS.map(([n]) => n), "EV");
  dynSel.addEventListener("change", () => { state.dynamoTier = dynSel.value; recalc(); });
  dynRow.appendChild(dynSel);
  settingsCard.appendChild(dynRow);

  // ---- Top row: EHE + settings ----
  const topRow = document.createElement("div");
  topRow.style.cssText = "display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap;";
  topRow.appendChild(eheCard);
  topRow.appendChild(settingsCard);
  el.appendChild(topRow);

  // ---- Stage cards ----
  const stageRefs = {};  // key -> { flowBadge, optFlowRow, cascadeListEl, totalRow, dynamoRow }

  const stagesRow = document.createElement("div");
  stagesRow.style.cssText = "display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap;";

  STAGES.forEach(({ key, label, headerColor }) => {
    const card = document.createElement("div");
    card.className = "card";
    card.style.flex = "1";
    card.style.minWidth = "200px";

    const titleDiv = document.createElement("div");
    titleDiv.style.cssText = "display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;";
    const titleSpan = document.createElement("span");
    titleSpan.style.cssText = `color:${headerColor};font-size:0.78rem;font-weight:bold;text-transform:uppercase;letter-spacing:0.04em;`;
    titleSpan.textContent = label;
    const flowBadge = document.createElement("span");
    flowBadge.style.cssText = "background:#1e3a5f;color:#93c5fd;border-radius:4px;padding:2px 7px;font-size:0.73rem;";
    flowBadge.textContent = "—";
    titleDiv.appendChild(titleSpan);
    titleDiv.appendChild(flowBadge);
    card.appendChild(titleDiv);

    const rotorRow = settingRow(t("label_rotor"));
    const rotorCombo = makeCombobox(data.rotors.map(r => r.name), v => {
      state.stages[key].rotor = data.rotors.find(r => r.name === v) ?? data.rotors[0] ?? null;
      recalc();
    }, { width: "160px" });
    if (data.rotors[0]) rotorCombo.setValue(data.rotors[0].name);
    rotorRow.appendChild(rotorCombo.el);
    card.appendChild(rotorRow);

    const modeRow = settingRow(t("label_mode"));
    const modeToggle = makeToggle(["Tight", "Loose"], v => { state.stages[key].mode = v; recalc(); });
    modeToggle.querySelectorAll(".toggle-btn").forEach((b, i) => b.classList.toggle("active", i === 1));
    state.stages[key].mode = "Loose";
    modeRow.appendChild(modeToggle);
    card.appendChild(modeRow);

    const hr = document.createElement("hr"); hr.className = "divider";
    card.appendChild(hr);

    const optFlowRow = resultRow(t("result_opt_flow"), "muted");
    card.appendChild(optFlowRow);

    const cascadeListEl = document.createElement("div");
    cascadeListEl.style.marginBottom = "6px";
    card.appendChild(cascadeListEl);

    const stageHr = document.createElement("hr"); stageHr.className = "divider";
    card.appendChild(stageHr);

    const totalRow  = resultRow(t("result_output"), "green");
    const dynamoRow = resultRow(t("result_dynamo_hatches"), "purple");
    card.appendChild(totalRow);
    card.appendChild(dynamoRow);

    stageRefs[key] = { flowBadge, optFlowRow, cascadeListEl, totalRow, dynamoRow };
    stagesRow.appendChild(card);
  });

  el.appendChild(stagesRow);

  // ---- Summary card ----
  const summaryCard = document.createElement("div");
  summaryCard.style.cssText = "background:#111827;border:1px solid #4b5563;border-radius:8px;padding:14px;";

  const sumTitleEl = document.createElement("div");
  sumTitleEl.style.cssText = "color:#f87171;font-size:0.78rem;font-weight:bold;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:10px;";
  sumTitleEl.textContent = t("cascade_summary");
  summaryCard.appendChild(sumTitleEl);

  const sumGrid = document.createElement("div");
  sumGrid.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:6px 32px;";

  const sumTurbinesRow = resultRow(t("result_total_turbines"), "muted");
  const sumGrossRow    = resultRow(t("result_gross_power"), "green");
  const sumLifetimeRow = resultRow(t("result_lifetime"), "yellow");
  const sumReactorRow  = resultRow(t("result_reactor_consumption"), "red");
  const sumDynamoRow   = resultRow(t("result_dynamo_hatches"), "purple");
  [sumTurbinesRow, sumGrossRow, sumLifetimeRow, sumReactorRow, sumDynamoRow].forEach(r => sumGrid.appendChild(r));
  summaryCard.appendChild(sumGrid);

  const netDiv = document.createElement("div");
  netDiv.style.cssText = "background:#0d1f12;border:1px solid #166534;border-radius:5px;padding:7px 12px;margin-top:8px;display:flex;justify-content:space-between;align-items:center;";
  const netLabel = document.createElement("span");
  netLabel.style.cssText = "color:#9ca3af;font-size:0.85rem;";
  netLabel.textContent = `⚡ ${t("result_net_power")}`;
  const netValue = document.createElement("span");
  netValue.style.cssText = "color:#6ee7b7;font-weight:bold;font-size:1.05rem;";
  netValue.textContent = "—";
  netDiv.appendChild(netLabel);
  netDiv.appendChild(netValue);
  summaryCard.appendChild(netDiv);

  el.appendChild(summaryCard);

  // ---- Recalc ----
  function recalc() {
    const ehe = computeEhe(state, data, scSteamEuL);
    if (!ehe) return;

    plasmaLsRow.setValue(`${formatNumber(parseFloat(ehe.plasmaOutputLs.toFixed(2)))} L/s`);
    eheCountRow.setValue(String(ehe.eheCount));
    scSteamRow.setValue(`${formatNumber(ehe.denseSCSteamLt)} L/t`);
    reactorRow.setValue(ehe.reactorConsumption > 0 ? `${formatNumber(ehe.reactorConsumption)} EU/t` : "—");

    const steamLt = ehe.denseSCSteamLt;
    let grossPower    = 0;
    let totalTurbines = 0;
    let minLifetime   = Infinity;

    STAGES.forEach(({ key, fuelType }) => {
      const s   = state.stages[key];
      const euL = euLMap[fuelType];
      const res = computeStage(steamLt, s.rotor, state.size, s.mode, fuelType, euL);
      const refs = stageRefs[key];

      refs.flowBadge.textContent = `${formatNumber(steamLt)} L/t`;

      if (!res) {
        refs.optFlowRow.setValue("—");
        refs.cascadeListEl.innerHTML = "";
        refs.totalRow.setValue("—");
        refs.dynamoRow.setValue("—");
        return;
      }

      refs.optFlowRow.setValue(`${formatNumber(res.optFlow)} L/t`);

      refs.cascadeListEl.innerHTML = "";

      if (res.fullCount > 0) {
        const div = document.createElement("div");
        div.style.cssText = "border-left:2px solid #1e3a5f;padding:3px 0 3px 8px;margin-bottom:3px;font-size:0.8rem;display:flex;justify-content:space-between;gap:8px;";
        div.innerHTML = `<span style="color:#9ca3af;">${res.fullCount}× ${t("cascade_full")} (${formatNumber(res.optFlow)} L/t)</span><span style="color:#6ee7b7;">${formatNumber(res.fullOutput)} EU/t ${t("cascade_each")}</span>`;
        refs.cascadeListEl.appendChild(div);
        if (res.fullLifetime < minLifetime) minLifetime = res.fullLifetime;
        totalTurbines += res.fullCount;
      }

      if (res.remainder > 0 && res.partial) {
        const div = document.createElement("div");
        div.style.cssText = "border-left:2px solid #78350f;padding:3px 0 3px 8px;margin-bottom:3px;font-size:0.8rem;display:flex;justify-content:space-between;gap:8px;";
        div.innerHTML = `<span style="color:#fbbf24;">${t("cascade_partial")} (${formatNumber(res.remainder)} L/t)</span><span style="color:#fbbf24;">${formatNumber(res.partial.effOutput)} EU/t</span>`;
        refs.cascadeListEl.appendChild(div);
        if (res.partial.lifetime < minLifetime) minLifetime = res.partial.lifetime;
        totalTurbines += 1;
      }

      refs.totalRow.setValue(`${formatNumber(res.stageTotal)} EU/t`);
      refs.dynamoRow.setValue(formatDynamo(res.stageTotal, state.dynamoTier));
      grossPower += res.stageTotal;
    });

    const lifetimeDays = minLifetime === Infinity ? 0 : minLifetime / 86400;
    sumTurbinesRow.setValue(String(totalTurbines));
    sumGrossRow.setValue(`${formatNumber(grossPower)} EU/t`);
    sumLifetimeRow.setValue(lifetimeDays > 0 ? `${lifetimeDays.toFixed(2)} days` : "—");
    sumReactorRow.setValue(ehe.reactorConsumption > 0 ? `${formatNumber(ehe.reactorConsumption)} EU/t` : "—");
    sumDynamoRow.setValue(formatDynamo(grossPower, state.dynamoTier));
    netValue.textContent = `${formatNumber(grossPower - ehe.reactorConsumption)} EU/t`;
  }

  recalc();
}
```

- [ ] **Step 2: Verify file was created**

```bash
ls web/js/ui/xl_cascade.js
```
Expected: file exists, no error.

- [ ] **Step 3: Commit**

```bash
git add web/js/ui/xl_cascade.js
git commit -m "feat: add XL steam cascade planner component"
```

---

### Task 4: Wire inner sub-tabs into calculator.js

**Files:**
- Modify: `web/js/ui/calculator.js`

- [ ] **Step 1: Add import for xl_cascade**

At the top of `web/js/ui/calculator.js`, add after the existing imports:

```js
import { initXlCascade, clearCache as clearXlCascade } from "./xl_cascade.js";
```

- [ ] **Step 2: Update clearCache to also clear xl_cascade cache**

Replace the existing `clearCache` export in `calculator.js`:

```js
export function clearCache() { _data = null; }
```

with:

```js
export function clearCache() { _data = null; clearXlCascade(); }
```

- [ ] **Step 3: Replace the XL tab build block**

Find this block in `initCalculator` (around line 528):

```js
      } else if (tab.dataset.tab === "xl") {
        xlEl.classList.remove("hidden");
        if (!xlBuilt) { await buildTurbineTab(xlEl, data, xlCalc); xlBuilt = true; }
```

Replace with:

```js
      } else if (tab.dataset.tab === "xl") {
        xlEl.classList.remove("hidden");
        if (!xlBuilt) {
          // Inner sub-tabs: Single Turbine | Steam Cascade
          const innerTabsBar = document.createElement("div");
          innerTabsBar.className = "xl-inner-tabs";

          const singleTab   = document.createElement("div");
          singleTab.className = "xl-inner-tab active";
          singleTab.textContent = t("tab_xl_single");

          const cascadeTab  = document.createElement("div");
          cascadeTab.className = "xl-inner-tab";
          cascadeTab.textContent = t("tab_xl_cascade");

          innerTabsBar.appendChild(singleTab);
          innerTabsBar.appendChild(cascadeTab);
          xlEl.appendChild(innerTabsBar);

          const xlSingleEl  = document.createElement("div");
          const xlCascadeEl = document.createElement("div");
          xlCascadeEl.classList.add("hidden");
          xlEl.appendChild(xlSingleEl);
          xlEl.appendChild(xlCascadeEl);

          await buildTurbineTab(xlSingleEl, data, xlCalc);

          let cascadeBuilt = false;

          singleTab.addEventListener("click", () => {
            singleTab.classList.add("active");
            cascadeTab.classList.remove("active");
            xlSingleEl.classList.remove("hidden");
            xlCascadeEl.classList.add("hidden");
          });

          cascadeTab.addEventListener("click", async () => {
            cascadeTab.classList.add("active");
            singleTab.classList.remove("active");
            xlCascadeEl.classList.remove("hidden");
            xlSingleEl.classList.add("hidden");
            if (!cascadeBuilt) {
              await initXlCascade(xlCascadeEl);
              cascadeBuilt = true;
            }
          });

          xlBuilt = true;
        }
```

- [ ] **Step 4: Verify the closing brace structure is intact**

After the edit, the full `xl` branch should look like:

```js
      } else if (tab.dataset.tab === "xl") {
        xlEl.classList.remove("hidden");
        if (!xlBuilt) {
          // ... (new block above)
          xlBuilt = true;
        }
      } else {
```

Open the file and confirm `xlBuilt = true;` is the last line before the closing `}` of the `if (!xlBuilt)` block.

- [ ] **Step 5: Commit**

```bash
git add web/js/ui/calculator.js
git commit -m "feat: add Steam Cascade inner sub-tab to XL Turbo Turbines section"
```

---

## Verification

- [ ] Open the web app (or `npx serve web` / open `web/index.html` directly)
- [ ] Navigate to Calculator → XL Turbo Turbines
- [ ] Confirm two inner tabs appear: "Single Turbine" and "Steam Cascade"
- [ ] Confirm "Single Turbine" tab still works (existing behaviour unchanged)
- [ ] Click "Steam Cascade":
  - Plasma type dropdown populated
  - Change plasma type / recipe params → EHE count and Dense SC Steam update
  - Change rotor in SC stage → cascade blocks update
  - With a large enough steam value, confirm full cascade blocks + partial block appear
  - Summary shows gross power, reactor consumption, net power
- [ ] Switch language to Russian → all labels translate correctly
- [ ] Change version in sidebar → cascade resets (clearCache chain works)
