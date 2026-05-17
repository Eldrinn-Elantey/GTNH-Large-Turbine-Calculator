import { SortableTable } from "../table.js";
import { formatNumber } from "../utils.js";
import { getVersion } from "../version.js";
import { t } from "../i18n.js";

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

function buildRows(rotors, uiSize) {
  const effKey = TURBINE_TO_ROTOR_SIZE[uiSize];
  const durKey = TURBINE_TO_DUR_SIZE[uiSize];
  return rotors.map(r => {
    const sd = r.sizes[effKey];
    const durMult = r.sizes[durKey]?.dur_mult ?? 1;
    return {
      name:              r.name,
      tier:              r.tier,
      base_dur:          r.base_durability * durMult,
      overflow:          r.overflow_tier,
      steam_tight_eff:   sd ? (sd.steam_tight_eff * 100).toFixed(1) + "%" : "—",
      steam_loose_eff:   sd ? (sd.steam_loose_eff * 100).toFixed(1) + "%" : "—",
      opt_flow_tight:    sd ? sd.steam_opt_flow_tight : null,
      opt_flow_loose:    sd ? sd.steam_opt_flow_loose : null,
    };
  });
}

export async function initRotors(el) {
  const COLUMNS = [
    { key: "name",            label: t("col_name"),       numeric: false },
    { key: "tier",            label: t("col_tier"),       numeric: true,  width: "50px" },
    { key: "base_dur",        label: t("col_base_dur"),   numeric: true  },
    { key: "overflow",        label: t("col_overflow"),   numeric: true,  width: "70px" },
    { key: "steam_tight_eff", label: t("col_eff_tight"),  numeric: false, width: "80px" },
    { key: "steam_loose_eff", label: t("col_eff_loose"),  numeric: false, width: "80px" },
    { key: "opt_flow_tight",  label: t("col_flow_tight"), numeric: true  },
    { key: "opt_flow_loose",  label: t("col_flow_loose"), numeric: true  },
  ];

  el.innerHTML = `
    <h2 class="section-title">${t("title_rotors")}</h2>
    <div class="setting-row" style="margin-bottom:16px;">
      <span class="setting-label">${t("label_blade_size")}</span>
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
