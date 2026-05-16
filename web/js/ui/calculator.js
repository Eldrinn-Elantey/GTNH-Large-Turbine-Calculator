import { calcRegularTurbine, calcXlTurbine } from "../calc.js";
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
    modeRow.innerHTML = `<span class="setting-label">Mode:</span>`;
    const modeToggle = makeToggle(["Tight", "Loose"], val => {
      tabState[key].mode = val;
      recalc(key);
    });
    modeRow.appendChild(modeToggle);
    panel.appendChild(modeRow);

    // Fuel
    const fuelRow = document.createElement("div");
    fuelRow.className = "setting-row";
    fuelRow.innerHTML = `<span class="setting-label">Fuel:</span>`;
    const fuelSel = document.createElement("select");
    populateSelect(fuelSel, fuelMap[key].map(f => f.name), fuelMap[key][0]?.name);
    fuelSel.addEventListener("change", () => { tabState[key].fuel = fuelSel.value; recalc(key); });
    fuelRow.appendChild(fuelSel);
    panel.appendChild(fuelRow);

    // Flow
    const flowRow = document.createElement("div");
    flowRow.className = "setting-row";
    flowRow.innerHTML = `<span class="setting-label">Flow:</span>`;
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
      optFlow:   makeResultRow("Optimal flow:", "cyan"),
      optOutput: makeResultRow("Output EU/t:", "green"),
      dynamo:    makeResultRow("Dynamo tier:", "muted"),
      effFlow:   makeResultRow("Eff. flow:", "cyan"),
      effOutput: makeResultRow("Eff. output:", "green"),
      rotorEff:  makeResultRow("Rotor eff.:", "muted"),
      lifetime:  makeResultRow("Lifetime:", "yellow"),
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
    rows.optFlow.setValue(`${formatNumber(r.optFlow)} ${flowUnit}`);
    rows.optOutput.setValue(`${formatNumber(r.optOutput)} EU/t`);
    rows.dynamo.setValue(r.minDynamoTierOpt);
    rows.effFlow.setValue(isManual ? `${formatNumber(r.effFlow)} ${flowUnit}` : "—");
    rows.effOutput.setValue(isManual ? `${formatNumber(r.effOutput)} EU/t` : "—");
    rows.rotorEff.setValue(`${(r.rotorEff * 100).toFixed(1)}%`);
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

/** Shared settings: tier filter + rotor select + blade size. */
function buildSharedSettings(rotors, onChange) {
  const state = { rotor: null, size: "Normal" };

  // Unique tiers sorted
  const tiers = ["All", ...new Set(rotors.map(r => r.tier).sort((a, b) => a - b))];
  let filteredRotors = rotors;

  const div = document.createElement("div");
  div.className = "card card-narrow";
  div.style.cssText = "margin-bottom:16px;display:flex;flex-wrap:wrap;gap:16px;align-items:center;";

  // Tier filter
  const tierRow = document.createElement("div");
  tierRow.className = "setting-row";
  tierRow.innerHTML = `<span class="setting-label">Rotor Tier:</span>`;
  const tierSel = document.createElement("select");
  populateSelect(tierSel, tiers.map(String), "All");
  tierRow.appendChild(tierSel);
  div.appendChild(tierRow);

  // Rotor select
  const rotorRow = document.createElement("div");
  rotorRow.className = "setting-row";
  rotorRow.innerHTML = `<span class="setting-label">Rotor:</span>`;
  const rotorSel = document.createElement("select");
  rotorSel.style.maxWidth = "220px";
  rotorRow.appendChild(rotorSel);
  div.appendChild(rotorRow);

  function refreshRotors(notify = true) {
    const tier = tierSel.value;
    filteredRotors = tier === "All" ? rotors : rotors.filter(r => String(r.tier) === tier);
    populateSelect(rotorSel, filteredRotors.map(r => r.name), filteredRotors[0]?.name);
    state.rotor = filteredRotors[0] ?? null;
    if (notify) onChange(state);
  }

  tierSel.addEventListener("change", refreshRotors);
  rotorSel.addEventListener("change", () => {
    state.rotor = filteredRotors.find(r => r.name === rotorSel.value) ?? null;
    onChange(state);
  });

  // Size toggle — default Normal
  const sizeRow = document.createElement("div");
  sizeRow.className = "setting-row";
  sizeRow.innerHTML = `<span class="setting-label">Blade Size:</span>`;
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

  // Initial populate — skip onChange, buildTurbineTab calls recalc explicitly after card is created
  refreshRotors(false);

  return { el: div, state };
}

async function buildTurbineTab(el, data, calcFn) {
  const fuelMap = {
    steam:  data.fuels.steam,
    gas:    data.fuels.gas,
    plasma: data.fuels.plasma,
  };

  const { el: settingsEl, state } = buildSharedSettings(data.rotors, () => turbineCard.recalc());

  const turbineCard = buildTurbineCard(fuelMap, calcFn, state);

  el.appendChild(settingsEl);
  el.appendChild(turbineCard);
  turbineCard.recalc();
}

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

  const regularCalc = (type, rotor, size, mode, fuelType, fuelValue, manualFlow) =>
    calcRegularTurbine(type, rotor, size, mode, fuelType, fuelValue, manualFlow);

  const xlCalc = (type, rotor, size, mode, fuelType, fuelValue, manualFlow) =>
    calcXlTurbine(type, rotor, size, mode, fuelType, fuelValue, false, manualFlow);

  await buildTurbineTab(largeEl, data, regularCalc);

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
        if (!xlBuilt) { await buildTurbineTab(xlEl, data, xlCalc); xlBuilt = true; }
      }
    });
  });
}
