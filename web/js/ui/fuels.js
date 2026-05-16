import { SortableTable } from "../table.js";

let _data = null;

async function loadData() {
  if (_data) return _data;
  const res = await fetch("data/fuels.json");
  _data = await res.json();
  return _data;
}

export async function initFuels(el) {
  el.innerHTML = `
    <h2 class="section-title">⛽ Fuels</h2>
    <div class="sub-tabs">
      <div class="sub-tab active" data-tab="steam">💧 Steam</div>
      <div class="sub-tab" data-tab="gas">🔥 Gas</div>
      <div class="sub-tab" data-tab="plasma">⚡ Plasma</div>
    </div>
    <div id="fuels-content"></div>
  `;

  const data = await loadData();
  const contentEl = el.querySelector("#fuels-content");

  // Prepare row data
  const steamRows = data.steam.map(f => ({ name: f.name, eu_l: f.eu_l }));

  const gasRows = data.gas.map(f => ({
    name: f.name,
    eu_l: f.eu_l,
    xlgt: f.xlgt ? "Yes" : "No",
  }));

  const plasmaRows = [...data.plasma]
    .sort((a, b) => b.eu_l - a.eu_l)
    .map(f => ({ name: f.name, eu_l: f.eu_l }));

  const containers = {
    steam:  document.createElement("div"),
    gas:    document.createElement("div"),
    plasma: document.createElement("div"),
  };

  const tables = {
    steam: new SortableTable(containers.steam, [
      { key: "name",  label: "Name",   numeric: false },
      { key: "eu_l",  label: "EU/L",   numeric: true  },
    ], steamRows),
    gas: new SortableTable(containers.gas, [
      { key: "name",  label: "Name",   numeric: false },
      { key: "eu_l",  label: "EU/L",   numeric: true  },
      { key: "xlgt",  label: "XLGT",   numeric: false },
    ], gasRows),
    plasma: new SortableTable(containers.plasma, [
      { key: "name",  label: "Name",   numeric: false },
      { key: "eu_l",  label: "EU/L",   numeric: true  },
    ], plasmaRows),
  };

  function showTab(tab) {
    el.querySelectorAll(".sub-tab").forEach(t =>
      t.classList.toggle("active", t.dataset.tab === tab)
    );
    tables[tab].render();
    contentEl.innerHTML = "";
    contentEl.appendChild(containers[tab]);
  }

  el.querySelectorAll(".sub-tab").forEach(t =>
    t.addEventListener("click", () => showTab(t.dataset.tab))
  );

  showTab("steam");
}
