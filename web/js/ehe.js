/**
 * EHE planner formulas -- ported from gtnh_turbine_calc/calc/ehe.py.
 */
import { findDynamoTier } from "./utils.js";

const TURBINE_TO_ROTOR_SIZE = { Small: "Small", Normal: "Small", Large: "Normal", Huge: "Large", XL: "Normal" };

function steamOptFlowXl(rotor, size, mode) {
  const key = TURBINE_TO_ROTOR_SIZE[size] ?? size;
  const sd = rotor.sizes[key];
  const base = mode === "Tight" ? sd.steam_opt_flow_tight : sd.steam_opt_flow_loose;
  return Math.floor(base * 16 / 1000); // dense L/t display
}

function xlPower(rotor, size, mode, fuelValue, flowLt) {
  const key = TURBINE_TO_ROTOR_SIZE[size] ?? size;
  const sd = rotor.sizes[key];
  const rotorEff = mode === "Tight" ? sd.steam_tight_eff : sd.steam_loose_eff;
  const optFlowCalc = steamOptFlowXl(rotor, size, mode) * 1000; // back to mB/t
  const effFlow = flowLt * 1000;
  const fe = optFlowCalc ? 1.0 - Math.abs((effFlow - optFlowCalc) / optFlowCalc) : 0;
  return Math.floor(effFlow * fe * rotorEff * fuelValue);
}

function denseSCSteamFromPlasma(plasmaType, plasmaLs, eheMaxLs, eheFuels) {
  const fd = eheFuels[plasmaType];
  if (!fd || eheMaxLs <= 0) return 0;
  const maxHotSteam = fd.max_hot_steam_ls ?? 0;
  const TICKS = 20;
  const capped = Math.min(plasmaLs, eheMaxLs);
  const fullSteamMbt = Math.floor(Math.floor(maxHotSteam * capped / eheMaxLs) / 160) * 160 / TICKS;
  const fullCount = Math.floor(plasmaLs / eheMaxLs);
  const fullTotal = Math.floor(fullSteamMbt) * fullCount;
  const partialFlow = plasmaLs % eheMaxLs;
  const partialSteamMbt = Math.floor(Math.floor(maxHotSteam * partialFlow / eheMaxLs) / 160) * 160 / TICKS;
  return fullTotal + Math.floor(partialSteamMbt);
}

export function calcPlasmaEhe(plasmaType, recipeOutputL, recipeTimeS, parallelCount, rotor, size, mode, eheFuels, scSteamEuL) {
  const plasmaOutputLs = recipeOutputL / recipeTimeS * parallelCount;
  const fd = eheFuels[plasmaType] ?? {};
  const eheMaxInputLs = fd.max_convert_ls ?? 0;
  const eheCount = eheMaxInputLs > 0 ? Math.ceil(plasmaOutputLs / eheMaxInputLs) : 0;
  const denseSCSteamLt = denseSCSteamFromPlasma(plasmaType, plasmaOutputLs, eheMaxInputLs, eheFuels);
  const xlOptFlow = steamOptFlowXl(rotor, size, mode);
  const turbineCount = xlOptFlow > 0 && denseSCSteamLt > 0 ? Math.max(1, Math.ceil(denseSCSteamLt / xlOptFlow)) : 0;
  const powerSC = xlPower(rotor, size, mode, scSteamEuL, Math.min(denseSCSteamLt, xlOptFlow));
  return {
    plasmaOutputLs, eheMaxInputLs, eheCount,
    denseSCSteamLt, turbineCount, xlOptFlowLt: xlOptFlow,
    powerPerTurbineSC: powerSC,
    minDynamoTierSC: findDynamoTier(powerSC),
  };
}

const NON_PLASMA_EHE = {
  "Lava":             { max_convert_ls: 160000, threshold_ls: 80000,  max_hot_steam_ls: 12800000, max_normal_steam_ls: 12800000 },
  "IC2 Hot Coolant":  { max_convert_ls: 16000,  threshold_ls: 8000,   max_hot_steam_ls: 3200000,  max_normal_steam_ls: 3200000 },
  "Solar Salt (Hot)": { max_convert_ls: 3200,   threshold_ls: 1600,   max_hot_steam_ls: 3200000,  max_normal_steam_ls: 3200000 },
};

function scSteamFromHotFluid(hotFluid, hotFluidLs) {
  const fd = NON_PLASMA_EHE[hotFluid];
  if (!fd) return [0, 0];
  const { max_convert_ls, threshold_ls, max_hot_steam_ls, max_normal_steam_ls } = fd;
  const capped = Math.min(hotFluidLs, max_convert_ls);
  const fullSteamLs = Math.floor(Math.floor(max_hot_steam_ls * capped / max_convert_ls) / 160) * 160;
  const fullCount = Math.floor(hotFluidLs / max_convert_ls);
  const fullSc = fullSteamLs * fullCount;
  const partialFlow = hotFluidLs % max_convert_ls;
  const partialSteamLs = Math.floor(Math.floor(max_hot_steam_ls * partialFlow / max_convert_ls) / 160) * 160;
  const partialSc = partialFlow >= threshold_ls ? partialSteamLs : 0;
  const scSteamLt = fullSc + partialSc;
  const partialShLs = Math.floor(Math.floor(max_normal_steam_ls * partialFlow / max_convert_ls) / 160) * 160;
  const shSteamLt = partialFlow < threshold_ls ? partialShLs : 0;
  return [scSteamLt, shSteamLt];
}

export function calcNonxlEhe(hotFluid, hotFluidInputLs, rotor, size, mode, scSteamEuL, steamEuL) {
  const [scSteamLt, shSteamLt] = scSteamFromHotFluid(hotFluid, hotFluidInputLs);
  const key = TURBINE_TO_ROTOR_SIZE[size] ?? size;
  const sd = rotor.sizes[key];
  const rotorEff = mode === "Tight" ? sd.steam_tight_eff : sd.steam_loose_eff;
  const optFlow  = mode === "Tight" ? sd.steam_opt_flow_tight : sd.steam_opt_flow_loose;
  const scTurbineCount = scSteamLt && optFlow ? Math.max(1, Math.ceil(scSteamLt / optFlow)) : 0;
  const shTurbineCount = optFlow ? Math.max(1, Math.ceil((scSteamLt + shSteamLt) / optFlow)) : 0;
  const powerSC  = Math.floor(Math.min(scSteamLt, optFlow) * rotorEff * scSteamEuL);
  const powerReg = Math.floor(Math.min(scSteamLt + shSteamLt, optFlow) * rotorEff * steamEuL);
  const maxConvert = NON_PLASMA_EHE[hotFluid]?.max_convert_ls ?? 1;
  const eheCount = Math.ceil(hotFluidInputLs / maxConvert);
  return {
    totalScSteamLt: scSteamLt, totalShSteamLt: shSteamLt,
    rotorEff, optFlowLt: optFlow,
    scTurbineCount, shTurbineCount,
    powerPerScTurbine: powerSC, powerPerRegTurbine: powerReg,
    minDynamoTierSC:  findDynamoTier(powerSC),
    minDynamoTierReg: findDynamoTier(powerReg),
    eheCount,
  };
}
