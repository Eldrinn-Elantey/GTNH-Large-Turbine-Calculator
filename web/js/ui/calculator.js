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

function makeDivider() {
  const hr = document.createElement("hr");
  hr.className = "divider";
  return hr;
}

// Build a single turbine card (steam / gas / plasma)
function buildTurbineCard(type, fuelList, calcFn, sharedState) {
  const wrap = document.createElement("div");

  // Fuel type tabs (Steam / Gas / Plasma)
  const tabBar = document.createElement("div");
  tabBar.className = "fuel-tabs";
  [["steam","💧 Steam"],["gas","🔥 Gas"],["plasma","⚡ Plasma"]].forEach(([t, label]) => {
    const tab = document.createElement("div");
    tab.className = `fuel-tab ${t}` + (t === type ? " active" : "");
    tab.textContent = label;
    tab.dataset.type = t;
    // Clicking another tab fires an event handled by the parent
    tab.addEventListener("click", () => {
      wrap.dispatchEvent(new CustomEvent("switchtype", { detail: t, bubbles: true }));
    });
    tabBar.appendChild(tab);
  });
  wrap.appendChild(tabBar);

  // Mode toggle
  const modeRow = document.createElement("div");
  modeRow.className = "setting-row";
  modeRow.innerHTML = `<span class="setting-label">Mode:</span>`;
  const modeToggle = makeToggle(["Tight", "Loose"], () => recalc());
  modeRow.appendChild(modeToggle);
  wrap.appendChild(modeRow);

  // Fuel select
  const fuelRow = document.createElement("div");
  fuelRow.className = "setting-row";
  fuelRow.innerHTML = `<span class="setting-label">Fuel:</span>`;
  const fuelSel = document.createElement("select");
  populateSelect(fuelSel, fuelList.map(f => f.name), fuelList[0]?.name);
  fuelSel.addEventListener("change", () => recalc());
  fuelRow.appendChild(fuelSel);
  wrap.appendChild(fuelRow);

  // Flow toggle + manual input
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
  wrap.appendChild(flowRow);

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
    const f = fuelList.find(x => x.name === fuelSel.value);
    return f ? f.eu_l : 1;
  }

  function recalc() {
    if (!sharedState.rotor) return;
    const mode       = modeToggle.getValue();
    const fuelType   = fuelSel.value;
    const fuelValue  = getFuelValue();
    const isManual   = flowToggle.getValue() === "Manual";
    const manualFlow = isManual ? (parseFloat(manualInput.value) || null) : null;

    const r = calcFn(type, sharedState.rotor, sharedState.size, mode, fuelType, fuelValue, manualFlow);

    const unit = type === "plasma" ? "L/s" : "L/t";
    rows.optFlow.setValue(`${formatNumber(r.optFlow)} ${unit}`);
    rows.optOutput.setValue(`${formatNumber(r.optOutput)} EU/t`);
    rows.dynamo.setValue(r.minDynamoTierOpt);
    rows.effFlow.setValue(isManual ? `${formatNumber(r.effFlow)} ${unit}` : "—");
    rows.effOutput.setValue(isManual ? `${formatNumber(r.effOutput)} EU/t` : "—");
    rows.rotorEff.setValue(`${(r.rotorEff * 100).toFixed(1)}%`);
    rows.lifetime.setValue(`${formatNumber(Math.round(r.lifetime))} s`);
  }

  wrap.recalc = recalc;
  return wrap;
}

// Shared settings: rotor selector + size toggle
function buildSharedSettings(rotors, onChange) {
  const state = { rotor: rotors[0] ?? null, size: "Normal" };
  const div = document.createElement("div");
  div.className = "card";
  div.style.cssText = "margin-bottom:16px;display:flex;flex-wrap:wrap;gap:16px;align-items:center;";

  // Rotor select
  const rotorRow = document.createElement("div");
  rotorRow.className = "setting-row";
  rotorRow.innerHTML = `<span class="setting-label">Rotor:</span>`;
  const rotorSel = document.createElement("select");
  rotorSel.style.maxWidth = "220px";
  populateSelect(rotorSel, rotors.map(r => r.name), rotors[0]?.name);
  rotorSel.addEventListener("change", () => {
    state.rotor = rotors.find(r => r.name === rotorSel.value) ?? null;
    onChange(state);
  });
  rotorRow.appendChild(rotorSel);
  div.appendChild(rotorRow);

  // Size toggle — default Normal (index 1)
  const sizeRow = document.createElement("div");
  sizeRow.className = "setting-row";
  sizeRow.innerHTML = `<span class="setting-label">Blade Size:</span>`;
  const sizeToggle = makeToggle(["Small","Normal","Large","Huge"], val => {
    state.size = val;
    onChange(state);
  });
  // Activate "Normal" by default (index 1), makeToggle activates index 0 by default
  const sizeBtns = sizeToggle.querySelectorAll(".toggle-btn");
  sizeBtns[0].classList.remove("active");
  sizeBtns[1].classList.add("active");
  state.size = "Normal";
  sizeRow.appendChild(sizeToggle);
  div.appendChild(sizeRow);

  return { el: div, state };
}

async function buildTurbineTab(el, data, calcFn) {
  const fuelMap = {
    steam:  data.fuels.steam,
    gas:    data.fuels.gas,
    plasma: data.fuels.plasma,
  };

  const { el: settingsEl, state } = buildSharedSettings(data.rotors, () => {
    cards.forEach(c => c.recalc());
  });

  const cardsWrap = document.createElement("div");
  cardsWrap.style.cssText = "display:flex;gap:12px;flex-wrap:wrap;";

  const cards = ["steam", "gas", "plasma"].map(type => {
    const box = document.createElement("div");
    box.className = "card";
    box.style.cssText = "flex:1;min-width:240px;";

    const card = buildTurbineCard(type, fuelMap[type], calcFn, state);

    // Handle fuel-tab switching between sibling cards
    card.addEventListener("switchtype", e => {
      const newType = e.detail;
      cardsWrap.querySelectorAll(".fuel-tab").forEach(tab => {
        tab.classList.toggle("active", tab.dataset.type === newType);
      });
    });

    box.appendChild(card);
    box.recalc = card.recalc;
    return box;
  });

  cards.forEach(c => cardsWrap.appendChild(c));
  el.appendChild(settingsEl);
  el.appendChild(cardsWrap);
  cards.forEach(c => c.recalc());
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

  // Regular turbine calc wrapper
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
        if (!xlBuilt) {
          await buildTurbineTab(xlEl, data, xlCalc);
          xlBuilt = true;
        }
      }
    });
  });
}
