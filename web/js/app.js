import { initCalculator } from "./ui/calculator.js";
import { initEhePlanner } from "./ui/ehe_planner.js";
import { initSteamGen, clearCache as clearSteamGen } from "./ui/steam_gen.js";
import { initFuels, clearCache as clearFuels }       from "./ui/fuels.js";
import { initRotors, clearCache as clearRotors }     from "./ui/rotors.js";
import { loadVersions, resolveVersion, setVersion }  from "./version.js";

const SECTIONS = {
  "calculator": initCalculator,
  "ehe":        initEhePlanner,
  "steam-gen":  initSteamGen,
  "fuels":      initFuels,
  "rotors":     initRotors,
};

const initialised = new Set();
let activeSection = "calculator";

function showSection(sectionId) {
  document.querySelectorAll(".section").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));

  const sectionEl = document.getElementById(`section-${sectionId}`);
  if (!sectionEl) return;
  sectionEl.classList.remove("hidden");

  const navItem = document.querySelector(`.nav-item[data-section="${sectionId}"]`);
  if (navItem) navItem.classList.add("active");

  activeSection = sectionId;

  if (!initialised.has(sectionId) && SECTIONS[sectionId]) {
    SECTIONS[sectionId](sectionEl);
    initialised.add(sectionId);
  }
}

function reloadActiveSection() {
  const sectionEl = document.getElementById(`section-${activeSection}`);
  if (!sectionEl || !SECTIONS[activeSection]) return;
  initialised.delete(activeSection);
  sectionEl.innerHTML = "";
  SECTIONS[activeSection](sectionEl);
  initialised.add(activeSection);
}

async function initVersionSelect() {
  const versions = await loadVersions();
  const current = await resolveVersion();

  const select = document.getElementById("version-select");
  versions.forEach(v => {
    const opt = document.createElement("option");
    opt.value = v.id;
    opt.textContent = v.label;
    if (v.id === current) opt.selected = true;
    select.appendChild(opt);
  });

  select.addEventListener("change", () => {
    setVersion(select.value);
    clearRotors();
    clearFuels();
    clearSteamGen();
    reloadActiveSection();
  });
}

// Wire up sidebar clicks
document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", () => showSection(item.dataset.section));
});

await initVersionSelect();
showSection("calculator");
