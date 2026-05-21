/**
 * CLI runner for calcRegularTurbine — used by automated Sheets comparison tests.
 * Usage: node calc_runner.mjs <turbineType> <rotorName> <size> <mode> <fuelType> <dataVersion>
 * Outputs JSON result to stdout.
 */
import { readFileSync } from "fs";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { calcRegularTurbine } from "./calc.js";

const __dir = dirname(fileURLToPath(import.meta.url));

const [turbineType, rotorName, size, mode, fuelType, dataVersion = "2.7"] = process.argv.slice(2);

if (!turbineType || !rotorName || !size || !mode || !fuelType) {
  console.error("Usage: node calc_runner.mjs <turbineType> <rotorName> <size> <mode> <fuelType> [dataVersion]");
  process.exit(1);
}

const dataDir = join(__dir, "../../web/data", dataVersion);
const rotors  = JSON.parse(readFileSync(join(dataDir, "rotors.json"), "utf8"));
const fuels   = JSON.parse(readFileSync(join(dataDir, "fuels.json"), "utf8"));

const rotor = rotors.find(r => r.name === rotorName);
if (!rotor) {
  console.error(`Rotor not found: ${rotorName}`);
  process.exit(1);
}

let fuelValue;
if (turbineType === "steam") {
  const entry = fuels.steam.find(f => f.name === fuelType);
  if (!entry) { console.error(`Steam fuel not found: ${fuelType}`); process.exit(1); }
  fuelValue = entry.eu_l;
} else if (turbineType === "gas") {
  const entry = fuels.gas.find(f => f.name === fuelType);
  if (!entry) { console.error(`Gas fuel not found: ${fuelType}`); process.exit(1); }
  fuelValue = entry.eu_l;
} else {
  const entry = fuels.plasma.find(f => f.name === fuelType);
  if (!entry) { console.error(`Plasma fuel not found: ${fuelType}`); process.exit(1); }
  fuelValue = entry.eu_l;
}

const result = calcRegularTurbine(turbineType, rotor, size, mode, fuelType, fuelValue);
console.log(JSON.stringify(result));
