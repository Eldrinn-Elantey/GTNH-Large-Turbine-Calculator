import { calcRegularTurbine, calcXlTurbine } from "../calc.js";
import { formatNumber, formatDynamo, populateSelect, makeCombobox, makeToggle, DYNAMO_TIERS } from "../utils.js";
import { SortableTable } from "../table.js";
import { getVersion } from "../version.js";
import { t } from "../i18n.js";
import { initXlCascade, clearCache as clearXlCascade } from "./xl_cascade.js";

let _data = null;

export function clearCache() { _data = null; clearXlCascade(); }

async function loadData() {
  if (_data) return _data;
  const v = getVersion();
  const [rotors, fuels] = await Promise.all([
    fetch(`data/${v}/rotors.json`).then(r => r.json()),
    fetch(`data/${v}/fuels.json`).then(r => r.json()),
  ]);
  _data = { rotors, fuels };
  return _data;
}

function makeResultRow(label, colorClass = "green") {
  const row = document.createElement("div");
  row.className = "result-row";
  row.innerHTML = `<span class="result-label">${label}</span><span class="result-value ${colorClass}">—</span>`;
  row.setValue = v => { row.querySelector(".result-value").textContent = v; };
  return row;
}

/**
 * One card with Steam / Gas / Plasma tabs inside.
 * Each tab remembers its own mode/fuel/flow state.
 */
const LIFETIME_UNITS = [
  { label: "s",    factor: 1 },
  { label: "min",  factor: 1 / 60 },
  { label: "h",    factor: 1 / 3600 },
  { label: "days", factor: 1 / 86400 },
];

function formatLifetime(seconds, unit) {
  const val = seconds * unit.factor;
  // Show more decimals for small values
  const formatted = val >= 100 ? formatNumber(Math.round(val)) : val.toFixed(2);
  return `${formatted} ${unit.label}`;
}

function buildTurbineCard(fuelMap, calcFn, sharedState) {
  const card = document.createElement("div");
  card.className = "card card-narrow";

  // --- Tab bar ---
  const tabBar = document.createElement("div");
  tabBar.className = "fuel-tabs";
  const TYPES = [
    { key: "steam",  label: "💧 Steam"  },
    { key: "gas",    label: "🔥 Gas"    },
    { key: "plasma", label: "⚡ Plasma" },
  ];

  // Per-tab state (mode, fuel, flow)
  const tabState = {};
  TYPES.forEach(({ key }, i) => {
    tabState[key] = { mode: "Tight", fuel: fuelMap[key][0]?.name ?? "", flow: "Optimal", manualFlow: 1000 };
  });

  // Build content panels (one per type, show/hide on tab switch)
  const panels = {};
  TYPES.forEach(({ key }) => {
    const panel = document.createElement("div");
    panel.dataset.panel = key;
    if (key !== "steam") panel.classList.add("hidden");

    // Mode
    const modeRow = document.createElement("div");
    modeRow.className = "setting-row";
    modeRow.innerHTML = `<span class="setting-label">${t("label_mode")}</span>`;
    const modeToggle = makeToggle(["Tight", "Loose"], val => {
      tabState[key].mode = val;
      recalc(key);
    });
    modeRow.appendChild(modeToggle);
    panel.appendChild(modeRow);

    // Fuel
    const fuelRow = document.createElement("div");
    fuelRow.className = "setting-row";
    fuelRow.innerHTML = `<span class="setting-label">${t("label_fuel")}</span>`;
    const fuelSel = document.createElement("select");
    populateSelect(fuelSel, fuelMap[key].map(f => f.name), fuelMap[key][0]?.name);
    fuelSel.addEventListener("change", () => { tabState[key].fuel = fuelSel.value; recalc(key); });
    fuelRow.appendChild(fuelSel);
    panel.appendChild(fuelRow);

    // Flow
    const flowRow = document.createElement("div");
    flowRow.className = "setting-row";
    flowRow.innerHTML = `<span class="setting-label">${t("label_flow")}</span>`;
    const flowToggle = makeToggle(["Optimal", "Manual"], val => {
      tabState[key].flow = val;
      manualInput.style.display = val === "Manual" ? "inline" : "none";
      recalc(key);
    });
    const manualInput = document.createElement("input");
    manualInput.type = "number";
    manualInput.min = 1;
    manualInput.value = tabState[key].manualFlow;
    manualInput.style.display = "none";
    manualInput.style.marginLeft = "8px";
    manualInput.addEventListener("input", () => { tabState[key].manualFlow = parseFloat(manualInput.value) || 1000; recalc(key); });
    flowRow.appendChild(flowToggle);
    flowRow.appendChild(manualInput);
    panel.appendChild(flowRow);

    const hr = document.createElement("hr");
    hr.className = "divider";
    panel.appendChild(hr);

    // Results
    const rows = {
      optFlow:    makeResultRow(t("result_opt_flow"), "cyan"),
      optOutput:  makeResultRow(t("result_output"), "green"),
      effFlow:    makeResultRow(t("result_eff_flow"), "cyan"),
      effOutput:  makeResultRow(t("result_eff_output"), "green"),
      dynamo:     makeResultRow(t("result_dynamo_hatches"), "purple"),
      rotorEff:   makeResultRow(t("result_rotor_eff"), "muted"),
      durability: makeResultRow(t("result_durability"), "muted"),
      lifetime:   makeResultRow(t("result_lifetime"), "yellow"),
    };

    // Lifetime unit toggle — default days
    let lifetimeUnit = LIFETIME_UNITS[3]; // days
    const lifetimeRow = rows.lifetime;
    const unitToggle = document.createElement("div");
    unitToggle.className = "toggle-group";
    unitToggle.style.cssText = "margin-left:8px;transform:scale(0.85);transform-origin:right center;";
    LIFETIME_UNITS.forEach(u => {
      const btn = document.createElement("button");
      btn.className = "toggle-btn" + (u === lifetimeUnit ? " active" : "");
      btn.textContent = u.label;
      btn.addEventListener("click", () => {
        lifetimeUnit = u;
        unitToggle.querySelectorAll(".toggle-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        recalc(key);
      });
      unitToggle.appendChild(btn);
    });
    // Insert unit toggle into the lifetime row label area
    lifetimeRow.querySelector(".result-label").appendChild(unitToggle);

    Object.values(rows).forEach(r => panel.appendChild(r));

    panels[key] = { el: panel, fuelSel, rows, getLifetimeUnit: () => lifetimeUnit };
    card.appendChild(panel);
  });

  // --- Tab click handlers ---
  TYPES.forEach(({ key, label }) => {
    const tab = document.createElement("div");
    tab.className = `fuel-tab ${key}` + (key === "steam" ? " active" : "");
    tab.textContent = label;
    tab.addEventListener("click", () => {
      tabBar.querySelectorAll(".fuel-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      Object.entries(panels).forEach(([k, p]) => p.el.classList.toggle("hidden", k !== key));
      recalc(key);
    });
    tabBar.appendChild(tab);
  });

  card.insertBefore(tabBar, card.firstChild);

  function recalc(type) {
    if (!sharedState.rotor) return;
    const st = tabState[type];
    const fuelList = fuelMap[type];
    const f = fuelList.find(x => x.name === st.fuel) ?? fuelList[0];
    if (!f) return;
    const isManual = st.flow === "Manual";
    const manualFlow = isManual ? st.manualFlow : null;

    const r = calcFn(type, sharedState.rotor, sharedState.size, st.mode, f.name, f.eu_l, manualFlow);
    const { rows, getLifetimeUnit } = panels[type];
    const flowUnit = type === "plasma" ? "L/s" : "L/t";
    rows.optFlow.style.display  = isManual ? "none" : "";
    rows.optOutput.style.display = isManual ? "none" : "";
    rows.effFlow.style.display  = isManual ? "" : "none";
    rows.effOutput.style.display = isManual ? "" : "none";

    rows.optFlow.setValue(`${formatNumber(r.optFlow)} ${flowUnit}`);
    rows.optOutput.setValue(`${formatNumber(r.optOutput)} EU/t`);
    rows.dynamo.setValue(formatDynamo(isManual ? r.effOutput : r.optOutput, sharedState.dynamoTier));
    rows.effFlow.setValue(`${formatNumber(r.effFlow)} ${flowUnit}`);
    rows.effOutput.setValue(`${formatNumber(r.effOutput)} EU/t`);
    rows.rotorEff.setValue(`${(r.rotorEff * 100).toFixed(1)}%`);
    rows.durability.setValue(formatNumber(r.durability));
    rows.lifetime.setValue(formatLifetime(r.lifetime, getLifetimeUnit()));
  }

  // Recalc currently visible tab
  card.recalc = () => {
    const activeTab = tabBar.querySelector(".fuel-tab.active");
    const activeType = activeTab ? [...tabBar.querySelectorAll(".fuel-tab")].find(t => t.classList.contains("active"))?.classList[1] : "steam";
    recalc(activeType ?? "steam");
  };

  return card;
}

/** Shared settings: tier filter + rotor select + blade size + dynamo tier. */
function buildSharedSettings(rotors, onChange) {
  const state = { rotor: null, size: "Normal", dynamoTier: "EV" };

  // Unique tiers sorted
  const tiers = ["All", ...new Set(rotors.map(r => r.tier).sort((a, b) => a - b))];
  let filteredRotors = rotors;

  const div = document.createElement("div");
  div.className = "card card-narrow";
  div.style.cssText = "margin-bottom:16px;";

  // Tier filter
  const tierRow = document.createElement("div");
  tierRow.className = "setting-row";
  tierRow.innerHTML = `<span class="setting-label">${t("label_rotor_tier")}</span>`;
  const tierSel = document.createElement("select");
  tierSel.style.width = "60px";
  populateSelect(tierSel, tiers.map(String), "All");
  tierRow.appendChild(tierSel);
  div.appendChild(tierRow);

  // Rotor select (searchable combobox)
  const rotorRow = document.createElement("div");
  rotorRow.className = "setting-row";
  rotorRow.innerHTML = `<span class="setting-label">${t("label_rotor")}</span>`;
  const rotorCombo = makeCombobox(rotors.map(r => r.name), value => {
    state.rotor = filteredRotors.find(r => r.name === value) ?? rotors.find(r => r.name === value) ?? null;
    onChange(state);
  });
  rotorRow.appendChild(rotorCombo.el);
  div.appendChild(rotorRow);

  function refreshRotors(notify = true) {
    const tier = tierSel.value;
    filteredRotors = tier === "All" ? rotors : rotors.filter(r => String(r.tier) === tier);
    rotorCombo.setItems(filteredRotors.map(r => r.name));
    state.rotor = filteredRotors[0] ?? null;
    if (notify) onChange(state);
  }

  tierSel.addEventListener("change", refreshRotors);

  // Size toggle — default Normal
  const sizeRow = document.createElement("div");
  sizeRow.className = "setting-row";
  sizeRow.innerHTML = `<span class="setting-label">${t("label_blade_size")}</span>`;
  const sizeToggle = makeToggle(["Small", "Normal", "Large", "Huge"], val => {
    state.size = val;
    onChange(state);
  });
  const sizeBtns = sizeToggle.querySelectorAll(".toggle-btn");
  sizeBtns[0].classList.remove("active");
  sizeBtns[1].classList.add("active");
  state.size = "Normal";
  sizeRow.appendChild(sizeToggle);
  div.appendChild(sizeRow);

  // Dynamo tier
  const dynamoRow = document.createElement("div");
  dynamoRow.className = "setting-row";
  dynamoRow.innerHTML = `<span class="setting-label">${t("label_dynamos")}</span>`;
  const dynamoSel = document.createElement("select");
  dynamoSel.style.width = "90px";
  populateSelect(dynamoSel, DYNAMO_TIERS.map(([name]) => name), "EV");
  dynamoSel.addEventListener("change", () => { state.dynamoTier = dynamoSel.value; onChange(state); });
  dynamoRow.appendChild(dynamoSel);
  div.appendChild(dynamoRow);

  // Initial populate — skip onChange, buildTurbineTab calls recalc explicitly after card is created
  refreshRotors(false);

  return { el: div, state };
}

function buildSlot(slotsEl, data, calcFn, removable) {
  const fuelMap = { steam: data.fuels.steam, gas: data.fuels.gas, plasma: data.fuels.plasma };

  const slot = document.createElement("div");
  slot.className = "calc-slot";

  // Remove button
  if (removable) {
    const removeBtn = document.createElement("button");
    removeBtn.className = "slot-remove-btn";
    removeBtn.textContent = "×";
    removeBtn.title = "Remove";
    removeBtn.addEventListener("click", () => slot.remove());
    slot.appendChild(removeBtn);
  }

  const { el: settingsEl, state } = buildSharedSettings(data.rotors, () => turbineCard.recalc());
  const turbineCard = buildTurbineCard(fuelMap, calcFn, state);

  slot.appendChild(settingsEl);
  slot.appendChild(turbineCard);
  slotsEl.appendChild(slot);
  turbineCard.recalc();
}

async function buildTurbineTab(el, data, calcFn) {
  const slotsEl = document.createElement("div");
  slotsEl.className = "calc-slots";
  el.appendChild(slotsEl);

  buildSlot(slotsEl, data, calcFn, false);

  const addBtn = document.createElement("button");
  addBtn.className = "slot-add-btn";
  addBtn.textContent = "+ Add card";
  addBtn.addEventListener("click", () => buildSlot(slotsEl, data, calcFn, true));
  el.appendChild(addBtn);
}

function buildCompareTab(el, data) {
  const FUEL_TYPES = ["steam", "gas", "plasma"];
  const fuelMap = { steam: data.fuels.steam, gas: data.fuels.gas, plasma: data.fuels.plasma };

  const state = {
    turbine: "large",
    fuelType: "gas",
    fuel: fuelMap.gas[0],
    mode: "Tight",
    size: "Normal",
    dynamoTier: "EV",
    tierFilter: "All",
  };

  // Settings card
  const settings = document.createElement("div");
  settings.className = "card";
  settings.style.cssText = "margin-bottom:16px;max-width:700px;";

  function row(labelText) {
    const r = document.createElement("div");
    r.className = "setting-row";
    r.innerHTML = `<span class="setting-label">${labelText}</span>`;
    return r;
  }

  // Turbine type
  const turbineRow = row(t("label_turbine"));
  const turbineToggle = makeToggle(["Large", "XL"], val => { state.turbine = val.toLowerCase(); rebuild(); });
  turbineRow.appendChild(turbineToggle);
  settings.appendChild(turbineRow);

  // Fuel type tabs → simple toggle
  const ftRow = row(t("label_fuel_type"));
  const ftToggle = makeToggle(["Steam", "Gas", "Plasma"], val => {
    state.fuelType = val.toLowerCase();
    state.fuel = fuelMap[state.fuelType][0];
    populateSelect(fuelSel, fuelMap[state.fuelType].map(f => f.name), state.fuel.name);
    rebuild();
  });
  // default Gas active
  ftToggle.querySelectorAll(".toggle-btn")[0].classList.remove("active");
  ftToggle.querySelectorAll(".toggle-btn")[1].classList.add("active");
  ftRow.appendChild(ftToggle);
  settings.appendChild(ftRow);

  // Fuel select
  const fuelRow = row(t("label_fuel"));
  const fuelSel = document.createElement("select");
  fuelSel.style.width = "200px";
  populateSelect(fuelSel, fuelMap.gas.map(f => f.name), fuelMap.gas[0].name);
  fuelSel.addEventListener("change", () => {
    state.fuel = fuelMap[state.fuelType].find(f => f.name === fuelSel.value) ?? fuelMap[state.fuelType][0];
    rebuild();
  });
  fuelRow.appendChild(fuelSel);
  settings.appendChild(fuelRow);

  // Mode
  const modeRow = row(t("label_mode"));
  const modeToggle = makeToggle(["Tight", "Loose"], val => { state.mode = val; rebuild(); });
  modeRow.appendChild(modeToggle);
  settings.appendChild(modeRow);

  // Blade size
  const sizeRow = row(t("label_blade_size"));
  const sizeToggle = makeToggle(["Small", "Normal", "Large", "Huge"], val => { state.size = val; rebuild(); });
  // default Normal
  sizeToggle.querySelectorAll(".toggle-btn")[0].classList.remove("active");
  sizeToggle.querySelectorAll(".toggle-btn")[1].classList.add("active");
  sizeRow.appendChild(sizeToggle);
  settings.appendChild(sizeRow);

  // Dynamo tier
  const dynRow = row(t("label_dynamo_tier"));
  const dynSel = document.createElement("select");
  dynSel.style.width = "90px";
  populateSelect(dynSel, DYNAMO_TIERS.map(([n]) => n), "EV");
  dynSel.addEventListener("change", () => { state.dynamoTier = dynSel.value; rebuild(); });
  dynRow.appendChild(dynSel);
  settings.appendChild(dynRow);

  // Rotor tier filter
  const tiers = ["All", ...new Set(data.rotors.map(r => r.tier).sort((a, b) => a - b))];
  const tierRow = row(t("label_rotor_tier"));
  const tierSel = document.createElement("select");
  tierSel.style.width = "60px";
  populateSelect(tierSel, tiers.map(String), "All");
  tierSel.addEventListener("change", () => { state.tierFilter = tierSel.value; rebuild(); });
  tierRow.appendChild(tierSel);
  settings.appendChild(tierRow);

  el.appendChild(settings);

  // Table container
  const tableWrap = document.createElement("div");
  el.appendChild(tableWrap);

  const columns = [
    { key: "name",     label: t("col_rotor"),              numeric: false, width: 200 },
    { key: "tier",     label: t("col_tier"),               numeric: true,  width: 50  },
    { key: "flow",     label: t("col_opt_flow"),           numeric: true,  width: 100 },
    { key: "output",   label: t("col_output"),             numeric: true,  width: 120 },
    { key: "dynamo",   label: t("result_dynamo_hatches"),  numeric: false, width: 160 },
    { key: "eff",      label: t("result_rotor_eff"),       numeric: true,  width: 90  },
    { key: "lifetime", label: t("col_lifetime_days"),      numeric: true,  width: 110 },
  ];

  let table = null;

  function rebuild() {
    const calcFn = state.turbine === "xl"
      ? (type, rotor, size, mode, fuelName, euL) => calcXlTurbine(type, rotor, size, mode, fuelName, euL, false, null)
      : (type, rotor, size, mode, fuelName, euL) => calcRegularTurbine(type, rotor, size, mode, fuelName, euL, null);

    const rotors = state.tierFilter === "All"
      ? data.rotors
      : data.rotors.filter(r => String(r.tier) === state.tierFilter);

    const flowUnit = state.fuelType === "plasma" ? "L/s" : "L/t";

    const rows = rotors.map(rotor => {
      const r = calcFn(state.fuelType, rotor, state.size, state.mode, state.fuel.name, state.fuel.eu_l);
      return {
        name:     rotor.name,
        tier:     String(rotor.tier),
        flow:     `${formatNumber(r.optFlow)} ${flowUnit}`,
        output:   `${formatNumber(r.optOutput)} EU/t`,
        dynamo:   formatDynamo(r.optOutput, state.dynamoTier),
        eff:      `${(r.rotorEff * 100).toFixed(1)}%`,
        lifetime: (r.lifetime / 86400).toFixed(2),
      };
    });

    if (!table) {
      table = new SortableTable(tableWrap, columns, rows);
      table.render();
    } else {
      table.update(rows);
    }
  }

  rebuild();
}

export async function initCalculator(el) {
  el.innerHTML = `
    <h2 class="section-title">${t("title_calculator")}</h2>
    <div class="sub-tabs">
      <div class="sub-tab active" data-tab="large">${t("tab_large_turbines")}</div>
      <div class="sub-tab" data-tab="xl">${t("tab_xl_turbines")}</div>
      <div class="sub-tab" data-tab="compare">${t("tab_compare_rotors")}</div>
    </div>
    <div id="calc-large"></div>
    <div id="calc-xl" class="hidden"></div>
    <div id="calc-compare" class="hidden"></div>
  `;

  const data = await loadData();
  const largeEl   = el.querySelector("#calc-large");
  const xlEl      = el.querySelector("#calc-xl");
  const compareEl = el.querySelector("#calc-compare");

  const regularCalc = (type, rotor, size, mode, fuelType, fuelValue, manualFlow) =>
    calcRegularTurbine(type, rotor, size, mode, fuelType, fuelValue, manualFlow);

  const xlCalc = (type, rotor, size, mode, fuelType, fuelValue, manualFlow) =>
    calcXlTurbine(type, rotor, size, mode, fuelType, fuelValue, false, manualFlow);

  await buildTurbineTab(largeEl, data, regularCalc);

  let xlBuilt = false;
  let compareBuilt = false;

  el.querySelectorAll(".sub-tab").forEach(tab => {
    tab.addEventListener("click", async () => {
      el.querySelectorAll(".sub-tab").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      largeEl.classList.add("hidden");
      xlEl.classList.add("hidden");
      compareEl.classList.add("hidden");

      if (tab.dataset.tab === "large") {
        largeEl.classList.remove("hidden");
      } else if (tab.dataset.tab === "xl") {
        xlEl.classList.remove("hidden");
        if (!xlBuilt) {
          // Inner sub-tabs: Single Turbine | Steam Cascade
          const innerTabsBar = document.createElement("div");
          innerTabsBar.className = "xl-inner-tabs";

          const singleTab  = document.createElement("div");
          singleTab.className = "xl-inner-tab active";
          singleTab.textContent = t("tab_xl_single");

          const cascadeTab = document.createElement("div");
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
      } else {
        compareEl.classList.remove("hidden");
        if (!compareBuilt) { buildCompareTab(compareEl, data); compareBuilt = true; }
      }
    });
  });
}
