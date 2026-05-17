import { initCalculator, clearCache as clearCalculator } from "./ui/calculator.js";
import { initEhePlanner, clearCache as clearEhe }        from "./ui/ehe_planner.js";
import { initSteamGen, clearCache as clearSteamGen }     from "./ui/steam_gen.js";
import { initFuels, clearCache as clearFuels }           from "./ui/fuels.js";
import { initRotors, clearCache as clearRotors }         from "./ui/rotors.js";
import { initSettings }                                  from "./ui/settings_section.js";
import { loadVersions, resolveVersion, setVersion }      from "./version.js";
import { t }                                             from "./i18n.js";
import { applyFontSize }                                 from "./settings.js";

const SECTIONS = {
  "calculator": initCalculator,
  "ehe":        initEhePlanner,
  "steam-gen":  initSteamGen,
  "fuels":      initFuels,
  "rotors":     initRotors,
  "settings":   initSettings,
};

const initialised = new Set();
let activeSection = "calculator";

function applyNavTranslations() {
  document.querySelectorAll(".nav-item[data-i18n]").forEach(el => {
    el.textContent = t(el.dataset.i18n);
  });
}

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

function reloadAllSections() {
  for (const id of [...initialised]) {
    const sectionEl = document.getElementById(`section-${id}`);
    if (!sectionEl || !SECTIONS[id]) continue;
    initialised.delete(id);
    sectionEl.innerHTML = "";
    if (id === activeSection) {
      SECTIONS[id](sectionEl);
      initialised.add(id);
    }
  }
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
    clearCalculator();
    clearEhe();
    clearSteamGen();
    clearFuels();
    clearRotors();
    reloadActiveSection();
  });
}

const sidebar = document.getElementById("sidebar");
const overlay = document.getElementById("sidebar-overlay");
const hamburger = document.getElementById("hamburger");

function openSidebar() {
  sidebar.classList.add("open");
  overlay.classList.add("active");
  hamburger.style.display = "none";
}

function closeSidebar() {
  sidebar.classList.remove("open");
  overlay.classList.remove("active");
  hamburger.style.display = "";
}

hamburger.addEventListener("click", openSidebar);
overlay.addEventListener("click", closeSidebar);
document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", () => showSection(item.dataset.section));
});

document.addEventListener("gtnh:lang-change", () => {
  applyNavTranslations();
  reloadAllSections();
  // Rerender Settings immediately (it's always initialised when this fires)
  const settingsEl = document.getElementById("section-settings");
  if (settingsEl && activeSection !== "settings") {
    initialised.delete("settings");
    settingsEl.innerHTML = "";
    initSettings(settingsEl);
    initialised.add("settings");
  }
});

applyFontSize();
applyNavTranslations();
await initVersionSelect();
showSection("calculator");
