import { initCalculator } from "./ui/calculator.js";
import { initEhePlanner } from "./ui/ehe_planner.js";
import { initSteamGen }   from "./ui/steam_gen.js";
import { initFuels }      from "./ui/fuels.js";
import { initRotors }     from "./ui/rotors.js";

// Map section id -> init function (called once on first visit)
const SECTIONS = {
  "calculator": initCalculator,
  "ehe":        initEhePlanner,
  "steam-gen":  initSteamGen,
  "fuels":      initFuels,
  "rotors":     initRotors,
};

const initialised = new Set();

function showSection(sectionId) {
  // Hide all sections
  document.querySelectorAll(".section").forEach(el => el.classList.add("hidden"));
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));

  // Show target section
  const sectionEl = document.getElementById(`section-${sectionId}`);
  if (!sectionEl) return;
  sectionEl.classList.remove("hidden");

  // Mark nav item active
  const navItem = document.querySelector(`.nav-item[data-section="${sectionId}"]`);
  if (navItem) navItem.classList.add("active");

  // Init section on first visit
  if (!initialised.has(sectionId) && SECTIONS[sectionId]) {
    SECTIONS[sectionId](sectionEl);
    initialised.add(sectionId);
  }
}

// Wire up sidebar clicks
document.querySelectorAll(".nav-item").forEach(item => {
  item.addEventListener("click", () => showSection(item.dataset.section));
});

// Init the default section (calculator)
showSection("calculator");
