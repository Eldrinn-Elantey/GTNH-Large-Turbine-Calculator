import math
from gtnh_turbine_calc.calc.common import find_dynamo_tier
from gtnh_turbine_calc.data.fuels import EHE_FUELS, STEAM_FUELS

# Maps UI blade size name to data column key (same as turbine.py)
TURBINE_TO_ROTOR_SIZE = {
    "Small":  "Small",
    "Normal": "Normal",
    "Large":  "Large",
    "Huge":   "Huge",
    "XL":     "Normal",
}


def _steam_opt_flow_xl(rotor: dict, size: str, mode: str) -> float:
    """XL turbine optimal steam flow in L/t (dense SC mode, divides by 1000)."""
    blade_size = TURBINE_TO_ROTOR_SIZE.get(size, size)
    sd = rotor["sizes"][blade_size]
    base = sd["steam_opt_flow_tight"] if mode == "Tight" else sd["steam_opt_flow_loose"]
    return math.floor(base * 16 / 1000)  # display L/t (dense)


def _steam_opt_flow_regular(rotor: dict, size: str, mode: str) -> float:
    blade_size = TURBINE_TO_ROTOR_SIZE.get(size, size)
    sd = rotor["sizes"][blade_size]
    return sd["steam_opt_flow_tight"] if mode == "Tight" else sd["steam_opt_flow_loose"]


def _xl_power(rotor: dict, size: str, mode: str, fuel_value: float, flow_lt: float) -> int:
    """XL turbine output EU/t given a steam flow [L/t] (dense units, so multiply by 1000)."""
    blade_size = TURBINE_TO_ROTOR_SIZE.get(size, size)
    sd = rotor["sizes"][blade_size]
    rotor_eff = sd["steam_tight_eff"] if mode == "Tight" else sd["steam_loose_eff"]
    opt_flow_calc = _steam_opt_flow_xl(rotor, size, mode) * 1000  # back to mB/t
    eff_flow = flow_lt * 1000
    flow_eff = 1.0 - abs((eff_flow - opt_flow_calc) / opt_flow_calc) if opt_flow_calc else 0.0
    return int(math.floor(eff_flow * flow_eff * rotor_eff * fuel_value))


def _dense_sc_steam_from_plasma(plasma_type: str, plasma_ls: float, ehe_max_ls: float) -> int:
    """Dense SC Steam [L/t] from plasma EHE."""
    if plasma_type not in EHE_FUELS:
        return 0
    fd = EHE_FUELS[plasma_type]
    max_hot_steam = fd.get("max_hot_steam_ls") or 0
    if ehe_max_ls <= 0:
        return 0

    # max_hot_steam is in mB/s (milli-buckets per second); convert to mB/t (divide by 20 ticks/s)
    TICKS_PER_SECOND = 20
    capped = min(plasma_ls, ehe_max_ls)
    full_steam_mbt = math.floor(math.floor(max_hot_steam * capped / ehe_max_ls) / 160) * 160 / TICKS_PER_SECOND
    full_count = math.floor(plasma_ls / ehe_max_ls)
    full_total = math.floor(full_steam_mbt) * full_count

    partial_flow = plasma_ls % ehe_max_ls
    partial_steam_mbt = math.floor(math.floor(max_hot_steam * partial_flow / ehe_max_ls) / 160) * 160 / TICKS_PER_SECOND
    partial_total = math.floor(partial_steam_mbt)

    return int(full_total + partial_total)


def calc_plasma_ehe(
    plasma_type: str,
    recipe_output_l: float,
    recipe_time_s: float,
    parallel_count: float,
    rotor: dict,
    size: str,
    mode: str = "Loose",
) -> dict:
    """Plasma EHE Setup Planner calculation."""
    plasma_output_ls = recipe_output_l / recipe_time_s * parallel_count

    fd = EHE_FUELS.get(plasma_type, {})
    ehe_max_input_ls = fd.get("max_convert_ls") or 0
    ehe_count = math.ceil(plasma_output_ls / ehe_max_input_ls) if ehe_max_input_ls > 0 else 0
    dense_sc_steam_lt = _dense_sc_steam_from_plasma(plasma_type, plasma_output_ls, ehe_max_input_ls)

    blade_size = TURBINE_TO_ROTOR_SIZE.get(size, size)
    sd = rotor["sizes"][blade_size]
    rotor_eff = sd["steam_tight_eff"] if mode == "Tight" else sd["steam_loose_eff"]

    xl_opt_flow = _steam_opt_flow_xl(rotor, size, mode)  # L/t display (dense)
    turbine_count = max(1, math.ceil(dense_sc_steam_lt / xl_opt_flow)) if xl_opt_flow > 0 else 0

    power_sc = _xl_power(rotor, size, mode, STEAM_FUELS["SC Steam"], min(dense_sc_steam_lt, xl_opt_flow))

    return {
        "plasma_output_ls": plasma_output_ls,
        "ehe_max_input_ls": ehe_max_input_ls,
        "ehe_count": ehe_count,
        "dense_sc_steam_lt": dense_sc_steam_lt,
        "rotor_fit": mode,
        "rotor_eff": rotor_eff,
        "turbine_count": turbine_count,
        "xl_opt_flow_lt": xl_opt_flow,
        "power_per_turbine_sc": power_sc,
        "min_dynamo_tier_sc": find_dynamo_tier(power_sc),
    }


def _sc_steam_from_hot_fluid(hot_fluid: str, hot_fluid_ls: float) -> tuple[int, int]:
    """Non-XL EHE: SC Steam [L/t] and SH Steam [L/t] from hot fluid."""
    NON_PLASMA_EHE = {
        "Lava":             {"max_convert_ls": 160000, "threshold_ls": 80000,  "max_hot_steam_ls": 12800000, "max_normal_steam_ls": 12800000},
        "IC2 Hot Coolant":  {"max_convert_ls": 16000,  "threshold_ls": 8000,   "max_hot_steam_ls": 3200000,  "max_normal_steam_ls": 3200000},
        "Solar Salt (Hot)": {"max_convert_ls": 3200,   "threshold_ls": 1600,   "max_hot_steam_ls": 3200000,  "max_normal_steam_ls": 3200000},
    }
    fd = NON_PLASMA_EHE.get(hot_fluid)
    if not fd:
        return 0, 0

    max_convert = fd["max_convert_ls"]
    threshold = fd["threshold_ls"]
    max_hot = fd["max_hot_steam_ls"]
    max_normal = fd["max_normal_steam_ls"]

    capped = min(hot_fluid_ls, max_convert)
    full_steam_ls = math.floor(math.floor(max_hot * capped / max_convert) / 160) * 160
    full_count = math.floor(hot_fluid_ls / max_convert)
    full_sc = full_steam_ls * full_count

    partial_flow = hot_fluid_ls % max_convert
    partial_steam_ls = math.floor(math.floor(max_hot * partial_flow / max_convert) / 160) * 160
    partial_sc = partial_steam_ls if partial_flow >= threshold else 0

    sc_steam_lt = int(full_sc + partial_sc)

    partial_sh_ls = math.floor(math.floor(max_normal * partial_flow / max_convert) / 160) * 160
    sh_steam_lt = int(partial_sh_ls if partial_flow < threshold else 0)

    return sc_steam_lt, sh_steam_lt


def calc_nonxl_ehe(
    hot_fluid: str,
    hot_fluid_input_ls: float,
    rotor: dict,
    size: str,
    mode: str = "Loose",
) -> dict:
    """Non-XL EHE Setup Planner calculation."""
    sc_steam_lt, sh_steam_lt = _sc_steam_from_hot_fluid(hot_fluid, hot_fluid_input_ls)

    blade_size = TURBINE_TO_ROTOR_SIZE.get(size, size)
    sd = rotor["sizes"][blade_size]
    rotor_eff = sd["steam_tight_eff"] if mode == "Tight" else sd["steam_loose_eff"]
    opt_flow = sd["steam_opt_flow_tight"] if mode == "Tight" else sd["steam_opt_flow_loose"]

    sc_turbine_count = max(1, math.ceil(sc_steam_lt / opt_flow)) if sc_steam_lt and opt_flow else 0
    sh_turbine_count = max(1, math.ceil((sc_steam_lt + sh_steam_lt) / opt_flow)) if opt_flow else 0

    power_sc = int(math.floor(min(sc_steam_lt, opt_flow) * rotor_eff * STEAM_FUELS["SC Steam"]))
    power_reg = int(math.floor(min(sc_steam_lt + sh_steam_lt, opt_flow) * rotor_eff * STEAM_FUELS["Steam"]))

    ehe_count = math.ceil(hot_fluid_input_ls / {
        "Lava": 160000, "IC2 Hot Coolant": 16000, "Solar Salt (Hot)": 3200
    }.get(hot_fluid, 1))

    return {
        "total_sc_steam_lt": sc_steam_lt,
        "total_sh_steam_lt": sh_steam_lt,
        "rotor_fit": mode,
        "rotor_eff": rotor_eff,
        "opt_flow_lt": opt_flow,
        "sc_turbine_count": sc_turbine_count,
        "sh_turbine_count": sh_turbine_count,
        "power_per_sc_turbine": power_sc,
        "power_per_reg_turbine": power_reg,
        "min_dynamo_tier_sc": find_dynamo_tier(power_sc),
        "min_dynamo_tier_reg": find_dynamo_tier(power_reg),
        "ehe_count": ehe_count,
    }
