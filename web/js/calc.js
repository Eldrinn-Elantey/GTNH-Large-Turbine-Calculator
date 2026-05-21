/**
 * Turbine calculation formulas — ported from gtnh_turbine_calc/calc/turbine.py.
 * Do NOT change these without verifying against the Python source.
 */
import { findDynamoTier } from "./utils.js";

export const TURBINE_TO_ROTOR_SIZE = {
  Small:  "Small",
  Normal: "Normal",
  Large:  "Large",
  Huge:   "Huge",
  XL:     "Large",
};

export const TURBINE_TO_DUR_SIZE = {
  Small:  "Small",
  Normal: "Normal",
  Large:  "Large",
  Huge:   "Huge",
  XL:     "Large",
};

function rotorSizeData(rotor, size) {
  const key = TURBINE_TO_ROTOR_SIZE[size] ?? size;
  return rotor.sizes[key];
}

function rotorDurability(rotor, size) {
  const key = TURBINE_TO_DUR_SIZE[size] ?? size;
  return rotor.base_durability * rotor.sizes[key].dur_mult;
}

function lifetimeRegular(durability, output, turbineType, steamFuelType, mode) {
  if (output <= 0) return 0;
  const damage = Math.min(output / 5, Math.pow(output, 0.6));
  const base = Math.ceil(durability / damage * 50);
  // Plasma: base (no ×2). Gas: 2*base. Steam: 2*base*mult.
  // Multipliers verified against Google Sheets formula (H25 cell).
  if (turbineType === "plasma") return base;
  if (turbineType === "gas")    return 2 * base;
  let mult;
  if (steamFuelType === "SC Steam") {
    mult = mode === "Tight" ? 0.5 : 2.0;
  } else { // Steam or SH Steam
    mult = mode === "Tight" ? 1.0 : 4 / 3;
  }
  return 2 * base * mult;
}

function lifetimeXl(durability, output, turbineType, mode) {
  if (output <= 0) return 0;
  const damage = Math.min(output / 5 / 5, Math.pow(output / 5, 0.6));
  if (turbineType === "steam") {
    const mult = mode === "Tight" ? 1.0 : 4 / 3;
    return Math.ceil(mult * durability / damage * 50);
  } else if (turbineType === "gas") {
    return Math.ceil(4 / 3 * durability / damage * 50);
  } else {
    return Math.ceil(1.25 * durability / damage * 50);
  }
}

function flowEffSteam(effFlow, optFlow, overflowTier, fuelType) {
  if (optFlow <= 0) return 0;
  if (effFlow > optFlow) {
    let mult;
    if (fuelType === "SC Steam") mult = 1.25;
    else if (fuelType === "SH Steam") mult = overflowTier + 2;
    else mult = overflowTier + 1;
    return 1.0 - Math.abs((effFlow - optFlow) / (optFlow * mult));
  }
  return 1.0 - Math.abs((effFlow - optFlow) / optFlow);
}

function flowEffGas(effFlow, optFlow, overflowTier) {
  if (optFlow <= 0) return 0;
  if (effFlow > optFlow) {
    return 1.0 - Math.abs((effFlow - optFlow) / (optFlow * (overflowTier * 3 - 1)));
  }
  return 1.0 - Math.abs((effFlow - optFlow) / optFlow);
}

function flowEffPlasma(effFlow, optFlow, overflowTier) {
  if (optFlow <= 0) return 0;
  if (effFlow > optFlow) {
    return 1.0 - Math.abs((effFlow - optFlow) / (optFlow * (overflowTier * 3 + 1)));
  }
  return 1.0 - Math.abs((effFlow - optFlow) / optFlow);
}

/**
 * Calculate outputs for one regular turbine configuration.
 */
export function calcRegularTurbine(turbineType, rotor, size, mode, fuelType, fuelValue, manualFlow = null) {
  const sd = rotorSizeData(rotor, size);
  const overflowTier = rotor.overflow_tier;
  const durability = rotorDurability(rotor, size);

  let optFlow, optOutput, maxFlow, effFlow, effOutput, rotor_eff, lifetime;

  if (turbineType === "steam") {
    rotor_eff = mode === "Tight" ? sd.steam_tight_eff : sd.steam_loose_eff;
    optFlow   = mode === "Tight" ? sd.steam_opt_flow_tight : sd.steam_opt_flow_loose;
    optOutput = Math.floor(optFlow * rotor_eff * fuelValue);

    let maxFlowMult;
    if (fuelType === "SC Steam") maxFlowMult = 1.25;
    else if (fuelType === "SH Steam") maxFlowMult = 0.5 * overflowTier + 1.5;
    else maxFlowMult = 0.5 * overflowTier + 1;
    maxFlow = Math.floor(optFlow * maxFlowMult);

    effFlow = manualFlow !== null ? Math.min(maxFlow, manualFlow) : optFlow;
    const fe = flowEffSteam(effFlow, optFlow, overflowTier, fuelType);
    effOutput = Math.max(1, Math.floor(effFlow * fe * rotor_eff * fuelValue));
    lifetime  = lifetimeRegular(durability, effOutput, "steam", fuelType, mode);

  } else if (turbineType === "gas") {
    rotor_eff    = mode === "Tight" ? sd.gas_tight_eff : sd.gas_loose_eff;
    const optFlowEuT = mode === "Tight" ? sd.gas_opt_flow_tight : sd.gas_opt_flow_loose;
    optFlow  = Math.max(1, Math.floor(optFlowEuT / fuelValue));
    optOutput = Math.floor(optFlow * rotor_eff * fuelValue);

    maxFlow  = Math.floor(overflowTier * 1.5 * optFlow);
    effFlow  = manualFlow !== null ? Math.min(maxFlow, manualFlow) : optFlow;
    const fe  = flowEffGas(effFlow, optFlow, overflowTier);
    effOutput = Math.floor(effFlow * fe * rotor_eff * fuelValue);
    lifetime  = lifetimeRegular(durability, effOutput, "gas", null, mode);

  } else { // plasma
    rotor_eff    = mode === "Tight" ? sd.plasma_tight_eff : sd.plasma_loose_eff;
    const optFlowEuT = mode === "Tight" ? sd.plasma_opt_flow_tight : sd.plasma_opt_flow_loose;
    optFlow  = Math.max(1, Math.ceil(optFlowEuT * 20 / fuelValue));
    optOutput = Math.floor(optFlow * rotor_eff * fuelValue / 20);

    maxFlow  = Math.floor((1.5 * overflowTier + 1) * optFlow);
    effFlow  = manualFlow !== null ? Math.min(maxFlow, manualFlow) : optFlow;
    const fe  = flowEffPlasma(effFlow, optFlow, overflowTier);
    effOutput = Math.max(1, Math.floor(effFlow * fe * rotor_eff * fuelValue / 20));
    lifetime  = lifetimeRegular(durability, effOutput, "plasma", null, mode);
  }

  return {
    turbineType, mode, fuelType, fuelValue,
    optFlow, optOutput, effFlow, effOutput,
    rotorEff: rotor_eff, maxFlow, overflowTier, lifetime, durability,
    minDynamoTierOpt: findDynamoTier(optOutput),
    minDynamoTierEff: findDynamoTier(effOutput),
  };
}

/**
 * Calculate outputs for one XL turbine (16x flow multiplier).
 */
export function calcXlTurbine(turbineType, rotor, size, mode, fuelType, fuelValue, isDense = false, manualFlow = null) {
  const sd = rotorSizeData(rotor, size);
  const overflowTier = rotor.overflow_tier;
  const durability = rotorDurability(rotor, size);
  const XL = 16;

  let optFlow, optOutput, maxFlow, effFlow, effOutput, rotor_eff, lifetime;

  if (turbineType === "steam") {
    rotor_eff = mode === "Tight" ? sd.steam_tight_eff : sd.steam_loose_eff;
    const baseOptFlow = mode === "Tight" ? sd.steam_opt_flow_tight : sd.steam_opt_flow_loose;
    const optFlowRaw  = baseOptFlow * XL;
    const displayFlow = isDense ? Math.floor(optFlowRaw / 1000) : optFlowRaw;
    const optFlowCalc = isDense ? displayFlow * 1000 : optFlowRaw;
    optOutput = Math.floor(optFlowCalc * rotor_eff * fuelValue);

    const maxFlowRaw = Math.floor(optFlowRaw * 1.25);
    const effFlowRaw = manualFlow !== null
      ? Math.min(maxFlowRaw, manualFlow * (isDense ? 1000 : 1))
      : optFlowCalc;
    const fe = optFlowCalc ? 1.0 - Math.abs((effFlowRaw - optFlowCalc) / optFlowCalc) : 0;
    effOutput = Math.max(1, Math.floor(effFlowRaw * fe * rotor_eff * fuelValue));
    lifetime  = lifetimeXl(durability, effOutput, "steam", mode);
    optFlow   = displayFlow;
    effFlow   = isDense ? Math.floor(effFlowRaw / 1000) : effFlowRaw;
    maxFlow   = isDense ? Math.floor(maxFlowRaw / 1000) : maxFlowRaw;

  } else if (turbineType === "gas") {
    rotor_eff    = mode === "Tight" ? sd.gas_tight_eff : sd.gas_loose_eff;
    const optFlowEuT = mode === "Tight" ? sd.gas_opt_flow_tight : sd.gas_opt_flow_loose;
    optFlow  = Math.max(1, Math.floor(XL * optFlowEuT / fuelValue));
    optOutput = Math.floor(optFlow * rotor_eff * fuelValue);
    maxFlow  = Math.floor(optFlow * 1.25);
    effFlow  = manualFlow !== null ? Math.min(maxFlow, manualFlow) : optFlow;
    const fe  = optFlow ? 1.0 - Math.abs((effFlow - optFlow) / optFlow) : 0;
    effOutput = Math.floor(effFlow * fe * rotor_eff * fuelValue);
    lifetime  = lifetimeXl(durability, effOutput, "gas", mode);

  } else { // plasma
    rotor_eff    = mode === "Tight" ? sd.plasma_tight_eff : sd.plasma_loose_eff;
    const optFlowEuT = mode === "Tight" ? sd.plasma_opt_flow_tight : sd.plasma_opt_flow_loose;
    optFlow  = Math.max(1, Math.floor(XL * optFlowEuT * 20 / fuelValue));
    const plasmaPowerTight = sd.plasma_power_tight;
    const nerfMult = plasmaPowerTight
      ? Math.min(1.0, Math.pow(fuelValue * 0.005, 2) / plasmaPowerTight)
      : 1.0;
    optOutput = Math.floor(optFlow * rotor_eff * fuelValue / 20 * nerfMult);
    maxFlow  = Math.floor(optFlow * 1.25);
    effFlow  = manualFlow !== null ? Math.min(maxFlow, manualFlow) : optFlow;
    const fe  = optFlow ? 1.0 - Math.abs((effFlow - optFlow) / optFlow) : 0;
    effOutput = Math.floor(optOutput * Math.min(1 + overflowTier * 1.5, effFlow / optFlow) * fe);
    lifetime  = lifetimeXl(durability, effOutput, "plasma", mode);
  }

  return {
    turbineType, mode, fuelType, fuelValue,
    optFlow, optOutput, effFlow, effOutput,
    rotorEff: rotor_eff, maxFlow, overflowTier, lifetime, durability,
    minDynamoTierOpt: findDynamoTier(optOutput),
    minDynamoTierEff: findDynamoTier(effOutput),
  };
}
