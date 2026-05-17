import { calcPlasmaEhe, calcNonxlEhe } from "../ehe.js";
import { formatNumber, populateSelect } from "../utils.js";
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
  // Convert ehe array to object keyed by name
  const eheMap = {};
  for (const entry of fuels.ehe) {
    eheMap[entry.name] = entry;
  }
  _data = { rotors, fuels, eheMap };
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
  el.innerHTML = `<h2 class="section-title">${t("title_ehe")}</h2>
    <div class="row">
      <div class="col" id="plasma-ehe-col"></div>
      <div class="col" id="nonxl-ehe-col"></div>
    </div>`;

  const data = await loadData();
  const scSteamEuL = data.fuels.steam.find(f => f.name === "SC Steam")?.eu_l ?? 1.0;
  const steamEuL   = data.fuels.steam.find(f => f.name === "Steam")?.eu_l ?? 0.5;

  // Plasma types: all ehe entries except the 3 non-plasma hot fluids
  const NON_PLASMA = new Set(["Lava", "IC2 Hot Coolant", "Solar Salt (Hot)"]);
  const plasmaTypes = Object.keys(data.eheMap).filter(n => !NON_PLASMA.has(n));

  // --- Plasma EHE ---
  const plasmaCol = el.querySelector("#plasma-ehe-col");
  plasmaCol.innerHTML = `
    <div class="card">
      <h3 style="color:#c084fc;font-size:14px;margin-bottom:14px;">Plasma EHE</h3>
      <div class="setting-row"><span class="setting-label">${t("label_plasma_type")}</span>
        <select id="p-plasma-type" style="max-width:200px;"></select></div>
      <div class="setting-row"><span class="setting-label">${t("label_recipe_out")}</span>
        <input type="number" id="p-recipe-out" value="1000" min="1"></div>
      <div class="setting-row"><span class="setting-label">${t("label_recipe_time")}</span>
        <input type="number" id="p-recipe-time" value="20" min="1"></div>
      <div class="setting-row"><span class="setting-label">${t("label_parallels")}</span>
        <input type="number" id="p-parallels" value="1" min="1"></div>
      <div class="setting-row"><span class="setting-label">${t("label_rotor")}</span>
        <select id="p-rotor" style="max-width:200px;"></select></div>
      <div class="setting-row"><span class="setting-label">${t("label_blade_size")}</span>
        <div id="p-size-toggle"></div></div>
      <div class="setting-row"><span class="setting-label">${t("label_mode")}</span>
        <div id="p-mode-toggle"></div></div>
      <hr class="divider">
      ${row(t("result_plasma_ls"), "p-plasma-ls", "purple")}
      ${row(t("result_ehe_count"), "p-ehe-count", "muted")}
      ${row(t("result_dense_sc_steam"), "p-sc-steam", "cyan")}
      ${row(t("result_xl_turb"), "p-turb-count", "muted")}
      ${row(t("result_power_turb"), "p-power", "green")}
      ${row(t("result_dynamo_tier"), "p-dynamo", "muted")}
    </div>`;

  populateSelect(plasmaCol.querySelector("#p-plasma-type"), plasmaTypes, plasmaTypes[0]);
  populateSelect(plasmaCol.querySelector("#p-rotor"), data.rotors.map(r => r.name), data.rotors[0]?.name);

  const pSizeToggle = makeToggle(["Small", "Normal", "Large", "Huge"], () => plasmaRecalc());
  const pModeToggle = makeToggle(["Tight", "Loose"], () => plasmaRecalc());
  plasmaCol.querySelector("#p-size-toggle").appendChild(pSizeToggle);
  plasmaCol.querySelector("#p-mode-toggle").appendChild(pModeToggle);

  plasmaCol.querySelectorAll("select, input[type=number]").forEach(i => i.addEventListener("change", plasmaRecalc));
  plasmaCol.querySelectorAll("input[type=number]").forEach(i => i.addEventListener("input", plasmaRecalc));

  function plasmaRecalc() {
    const plasmaType = plasmaCol.querySelector("#p-plasma-type").value;
    const recipeOut  = parseFloat(plasmaCol.querySelector("#p-recipe-out").value) || 0;
    const recipeTime = parseFloat(plasmaCol.querySelector("#p-recipe-time").value) || 1;
    const parallels  = parseFloat(plasmaCol.querySelector("#p-parallels").value) || 1;
    const rotorName  = plasmaCol.querySelector("#p-rotor").value;
    const rotor      = data.rotors.find(r => r.name === rotorName);
    const size       = pSizeToggle.getValue();
    const mode       = pModeToggle.getValue();
    if (!rotor) return;
    const res = calcPlasmaEhe(plasmaType, recipeOut, recipeTime, parallels, rotor, size, mode, data.eheMap, scSteamEuL);
    plasmaCol.querySelector("#p-plasma-ls").textContent  = formatNumber(parseFloat(res.plasmaOutputLs.toFixed(2)));
    plasmaCol.querySelector("#p-ehe-count").textContent  = res.eheCount;
    plasmaCol.querySelector("#p-sc-steam").textContent   = formatNumber(res.denseSCSteamLt);
    plasmaCol.querySelector("#p-turb-count").textContent = res.turbineCount;
    plasmaCol.querySelector("#p-power").textContent      = `${formatNumber(res.powerPerTurbineSC)} EU/t`;
    plasmaCol.querySelector("#p-dynamo").textContent     = res.minDynamoTierSC;
  }

  plasmaRecalc();

  // --- Non-XL EHE ---
  const nonxlCol = el.querySelector("#nonxl-ehe-col");
  const hotFluids = ["Lava", "IC2 Hot Coolant", "Solar Salt (Hot)"];
  nonxlCol.innerHTML = `
    <div class="card">
      <h3 style="color:#60a5fa;font-size:14px;margin-bottom:14px;">Non-XL EHE</h3>
      <div class="setting-row"><span class="setting-label">${t("label_hot_fluid")}</span>
        <select id="n-fluid"></select></div>
      <div class="setting-row"><span class="setting-label">${t("label_flow")}</span>
        <input type="number" id="n-flow" value="10000" min="1"></div>
      <div class="setting-row"><span class="setting-label">${t("label_rotor")}</span>
        <select id="n-rotor" style="max-width:200px;"></select></div>
      <div class="setting-row"><span class="setting-label">${t("label_blade_size")}</span>
        <div id="n-size-toggle"></div></div>
      <div class="setting-row"><span class="setting-label">${t("label_mode")}</span>
        <div id="n-mode-toggle"></div></div>
      <hr class="divider">
      ${row(t("result_ehe_count"), "n-ehe-count", "muted")}
      ${row(t("result_sc_steam"), "n-sc-steam", "cyan")}
      ${row(t("result_sh_steam"), "n-sh-steam", "cyan")}
      ${row(t("result_sc_turb"), "n-sc-turb", "muted")}
      ${row(t("result_sh_turb"), "n-sh-turb", "muted")}
      ${row(t("result_power_sc"), "n-power-sc", "green")}
      ${row(t("result_power_reg"), "n-power-reg", "green")}
      ${row(t("result_dynamo_sc"), "n-dynamo-sc", "muted")}
      ${row(t("result_dynamo_reg"), "n-dynamo-reg", "muted")}
    </div>`;

  populateSelect(nonxlCol.querySelector("#n-fluid"), hotFluids, hotFluids[0]);
  populateSelect(nonxlCol.querySelector("#n-rotor"), data.rotors.map(r => r.name), data.rotors[0]?.name);

  const nSizeToggle = makeToggle(["Small", "Normal", "Large", "Huge"], () => nonxlRecalc());
  const nModeToggle = makeToggle(["Tight", "Loose"], () => nonxlRecalc());
  nonxlCol.querySelector("#n-size-toggle").appendChild(nSizeToggle);
  nonxlCol.querySelector("#n-mode-toggle").appendChild(nModeToggle);

  nonxlCol.querySelectorAll("select, input[type=number]").forEach(i => i.addEventListener("change", nonxlRecalc));
  nonxlCol.querySelectorAll("input[type=number]").forEach(i => i.addEventListener("input", nonxlRecalc));

  function nonxlRecalc() {
    const hotFluid  = nonxlCol.querySelector("#n-fluid").value;
    const flow      = parseFloat(nonxlCol.querySelector("#n-flow").value) || 0;
    const rotorName = nonxlCol.querySelector("#n-rotor").value;
    const rotor     = data.rotors.find(r => r.name === rotorName);
    const size      = nSizeToggle.getValue();
    const mode      = nModeToggle.getValue();
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
