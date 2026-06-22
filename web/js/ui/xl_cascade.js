import { calcXlTurbine } from "../calc.js";
import { calcPlasmaEhe } from "../ehe.js";
import { formatNumber, formatDynamo, populateSelect, makeCombobox, makeToggle, DYNAMO_TIERS } from "../utils.js";
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

// euLKey maps to regular (non-dense) eu_l; calcXlTurbine handles the ×1000 factor internally when isDense=true
const STAGES = [
  { key: "sc",  label: "💧 SC Steam", fuelType: "Dense SC Steam", euLKey: "SC Steam",  headerColor: "#93c5fd" },
  { key: "hp",  label: "🔵 HP Steam", fuelType: "Dense SH Steam", euLKey: "SH Steam",  headerColor: "#60a5fa" },
  { key: "reg", label: "⚪ Steam",    fuelType: "Dense Steam",    euLKey: "Steam",      headerColor: "#9ca3af" },
];

// rotor passed to calcPlasmaEhe affects only its internal XL turbine pre-calc; cascade uses its own per-stage rotors
function computeEhe(state, data, scSteamEuL) {
  const anyRotor = state.stages.sc.rotor ?? data.rotors[0];
  if (!anyRotor || state.recipeTime <= 0) return null;
  const res = calcPlasmaEhe(
    state.plasmaType, state.recipeOut, state.recipeTime,
    state.parallels, anyRotor, state.size, state.stages.sc.mode,
    data.eheMap, scSteamEuL
  );
  return {
    plasmaOutputLs:     res.plasmaOutputLs,
    eheCount:           res.eheCount,
    denseSCSteamLt:     res.denseSCSteamLt,
    reactorConsumption: state.euPerRecipe * state.parallels,
  };
}

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
  return {
    optFlow, fullCount, remainder,
    fullOutput: full.optOutput, fullLifetime: full.lifetime,
    partial,
    stageTotal: fullCount * full.optOutput + (partial?.effOutput ?? 0),
  };
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

  // EHE source card
  const eheCard = document.createElement("div");
  eheCard.className = "card";
  eheCard.style.flex = "1.1";

  const eheTitleEl = document.createElement("span");
  eheTitleEl.className = "card-title";
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

  // Shared settings card
  const settingsCard = document.createElement("div");
  settingsCard.className = "card";
  settingsCard.style.flex = "1";

  const settingsTitleEl = document.createElement("span");
  settingsTitleEl.className = "card-title";
  settingsTitleEl.textContent = t("cascade_settings");
  settingsCard.appendChild(settingsTitleEl);

  const sizeRow = settingRow(t("label_blade_size"));
  const sizeToggle = makeToggle(["Small", "Normal", "Large", "Huge"], v => { state.size = v; recalc(); });
  sizeToggle.querySelectorAll(".toggle-btn").forEach((b, i) => b.classList.toggle("active", i === 3));
  sizeRow.appendChild(sizeToggle);
  settingsCard.appendChild(sizeRow);

  const dynRow = settingRow(t("label_dynamos"));
  const dynSel = document.createElement("select");
  dynSel.style.width = "90px";
  populateSelect(dynSel, DYNAMO_TIERS.map(([n]) => n), "EV");
  dynSel.addEventListener("change", () => { state.dynamoTier = dynSel.value; recalc(); });
  dynRow.appendChild(dynSel);
  settingsCard.appendChild(dynRow);

  const topRow = document.createElement("div");
  topRow.style.cssText = "display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap;";
  topRow.appendChild(eheCard);
  topRow.appendChild(settingsCard);
  el.appendChild(topRow);

  // Stage cards
  const stageRefs = {};

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
    modeRow.appendChild(modeToggle);
    card.appendChild(modeRow);

    const hr = document.createElement("hr"); hr.className = "divider";
    card.appendChild(hr);

    const optFlowRow   = resultRow(t("result_opt_flow"), "muted");
    const cascadeListEl = document.createElement("div");
    cascadeListEl.style.marginBottom = "6px";
    const stageHr = document.createElement("hr"); stageHr.className = "divider";
    const totalRow  = resultRow(t("result_output"), "green");
    const dynamoRow = resultRow(t("result_dynamo_hatches"), "purple");

    card.appendChild(optFlowRow);
    card.appendChild(cascadeListEl);
    card.appendChild(stageHr);
    card.appendChild(totalRow);
    card.appendChild(dynamoRow);

    stageRefs[key] = { flowBadge, optFlowRow, cascadeListEl, totalRow, dynamoRow };
    stagesRow.appendChild(card);
  });

  el.appendChild(stagesRow);

  // Summary card
  const summaryCard = document.createElement("div");
  summaryCard.style.cssText = "background:#111827;border:1px solid #4b5563;border-radius:8px;padding:14px;";

  const sumTitleEl = document.createElement("span");
  sumTitleEl.className = "card-title";
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

  function recalc() {
    const ehe = computeEhe(state, data, scSteamEuL);
    if (!ehe) return;

    plasmaLsRow.setValue(`${formatNumber(parseFloat(ehe.plasmaOutputLs.toFixed(2)))} L/s`);
    eheCountRow.setValue(String(ehe.eheCount));
    scSteamRow.setValue(`${formatNumber(ehe.denseSCSteamLt)} L/t`);
    reactorRow.setValue(ehe.reactorConsumption > 0 ? `${formatNumber(ehe.reactorConsumption)} EU/t` : "—");

    const steamLt     = ehe.denseSCSteamLt;
    const badgeText   = `${formatNumber(steamLt)} L/t`;
    let grossPower    = 0;
    let totalTurbines = 0;
    let minLifetime   = Infinity;

    STAGES.forEach(({ key, fuelType }) => {
      const s   = state.stages[key];
      const euL = euLMap[fuelType];
      const res = computeStage(steamLt, s.rotor, state.size, s.mode, fuelType, euL);
      const refs = stageRefs[key];

      refs.flowBadge.textContent = badgeText;

      if (!res) {
        refs.optFlowRow.setValue("—");
        refs.cascadeListEl.replaceChildren();
        refs.totalRow.setValue("—");
        refs.dynamoRow.setValue("—");
        return;
      }

      refs.optFlowRow.setValue(`${formatNumber(res.optFlow)} L/t`);

      const children = [];

      if (res.fullCount > 0) {
        const div = document.createElement("div");
        div.style.cssText = "border-left:2px solid #1e3a5f;padding:3px 0 3px 8px;margin-bottom:3px;font-size:0.8rem;display:flex;justify-content:space-between;gap:8px;";
        const left = document.createElement("span");
        left.style.color = "#9ca3af";
        left.textContent = `${res.fullCount}× ${t("cascade_full")} (${formatNumber(res.optFlow)} L/t)`;
        const right = document.createElement("span");
        right.style.color = "#6ee7b7";
        right.textContent = `${formatNumber(res.fullOutput)} EU/t ${t("cascade_each")}`;
        div.appendChild(left);
        div.appendChild(right);
        children.push(div);
        if (res.fullLifetime < minLifetime) minLifetime = res.fullLifetime;
        totalTurbines += res.fullCount;
      }

      if (res.remainder > 0 && res.partial) {
        const div = document.createElement("div");
        div.style.cssText = "border-left:2px solid #78350f;padding:3px 0 3px 8px;margin-bottom:3px;font-size:0.8rem;display:flex;justify-content:space-between;gap:8px;";
        const left = document.createElement("span");
        left.style.color = "#fbbf24";
        left.textContent = `${t("cascade_partial")} (${formatNumber(res.remainder)} L/t)`;
        const right = document.createElement("span");
        right.style.color = "#fbbf24";
        right.textContent = `${formatNumber(res.partial.effOutput)} EU/t`;
        div.appendChild(left);
        div.appendChild(right);
        children.push(div);
        if (res.partial.lifetime < minLifetime) minLifetime = res.partial.lifetime;
        totalTurbines += 1;
      }

      refs.cascadeListEl.replaceChildren(...children);

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
