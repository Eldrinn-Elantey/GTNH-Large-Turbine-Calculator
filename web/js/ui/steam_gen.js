import { formatNumber } from "../utils.js";
import { getVersion } from "../version.js";
import { t } from "../i18n.js";

let _data = null;

export function clearCache() { _data = null; }

async function loadData() {
  if (_data) return _data;
  const res = await fetch(`data/${getVersion()}/steam_gen.json`);
  _data = await res.json();
  return _data;
}

function renderTable(title, rows) {
  if (!rows || rows.length === 0) return document.createElement("div");
  const keys = Object.keys(rows[0]);
  const div = document.createElement("div");
  div.style.marginBottom = "24px";
  div.innerHTML = `<h3 style="color:#9ca3af;font-size:13px;margin-bottom:10px;">${title}</h3>`;
  const wrap = document.createElement("div");
  wrap.className = "table-wrap";
  const table = document.createElement("table");
  table.className = "data-table";

  // Build header from keys
  const thead = document.createElement("thead");
  const hrow = document.createElement("tr");
  for (const key of keys) {
    const th = document.createElement("th");
    th.textContent = key.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
    if (typeof rows[0][key] === "number") th.classList.add("numeric");
    hrow.appendChild(th);
  }
  thead.appendChild(hrow);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const key of keys) {
      const td = document.createElement("td");
      const val = row[key];
      if (typeof val === "number") {
        td.classList.add("numeric");
        td.textContent = formatNumber(val);
      } else {
        td.textContent = val ?? "—";
      }
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  table.appendChild(tbody);
  wrap.appendChild(table);
  div.appendChild(wrap);
  return div;
}

export async function initSteamGen(el) {
  const data = await loadData();
  el.innerHTML = `<h2 class="section-title">${t("title_steam_gen")}</h2>`;
  el.appendChild(renderTable("Large Heat Exchanger", data.lhe));
  el.appendChild(renderTable("Thermal Boiler", data.thermal_boiler));
  el.appendChild(renderTable("Whakawhiti Wera XL", data.wwxl));
}
