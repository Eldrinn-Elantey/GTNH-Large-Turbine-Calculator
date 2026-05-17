import math
from dataclasses import dataclass
from typing import Literal

from gtnh_turbine_calc.calc.common import find_dynamo_tier, dynamo_amps

TurbineType = Literal["steam", "gas", "plasma"]

# Maps the UI blade size name to the data column key used for EFFICIENCY stats.
# Our data columns "Small"/"Normal"/"Large" correspond to game blades:
#   "Turbine" (2x speed) / "Large Turbine" (3x) / "Huge Turbine" (4x).
# The game's "Small Turbine" (1x) blade is not in our data.
TURBINE_TO_ROTOR_SIZE: dict[str, str] = {
    "Small":  "Small",   # efficiency from "Small" data col
    "Normal": "Small",   # efficiency from "Small" data col
    "Large":  "Normal",  # efficiency from "Normal" data col ← confirmed vs Excel
    "Huge":   "Large",   # efficiency from "Large" data col
    "XL":     "Normal",  # XL uses same efficiency col as Large
}

# Due to an extraction misalignment, the correct durability multiplier for each
# blade size is stored in the NEXT data column.
# Confirmed: Normal size → 6,144,000 for Orichalcum (= base × 3 = "Large" col dur_mult).
_TURBINE_TO_DUR_SIZE: dict[str, str] = {
    "Small":  "Normal",  # durMult from "Normal" col
    "Normal": "Large",   # durMult from "Large" col
    "Large":  "Large",   # durMult from "Large" col → 6,144,000 for Orichalcum ✓ confirmed
    "Huge":   "Huge",    # durMult from "Huge" col
    "XL":     "Large",   # XL same dur as Large
}


@dataclass
class TurbineResult:
    turbine_type: str
    mode: str
    fuel_type: str
    fuel_value: float
    opt_flow: float          # L/t for steam/gas, L/s for plasma
    opt_output_eu_t: int     # EU/t at optimal flow, tight efficiency
    eff_flow: float          # same units as opt_flow (capped to max)
    eff_output_eu_t: int     # EU/t at effective flow
    rotor_eff: float
    max_flow: float
    min_dynamo_tier_opt: str
    min_dynamo_tier_eff: str
    lifetime_s: float        # seconds at effective flow
    overflow_tier: int


def _rotor_size(rotor: dict, size: str) -> dict:
    rotor_key = TURBINE_TO_ROTOR_SIZE.get(size, size)
    return rotor["sizes"][rotor_key]


def _durability(rotor: dict, size: str) -> int:
    rotor_key = _TURBINE_TO_DUR_SIZE.get(size, size)
    return rotor["base_durability"] * rotor["sizes"][rotor_key]["dur_mult"]


def _lifetime_regular(durability: int, output: int, steam_mode: str | None, mode: str) -> float:
    """Regular turbine lifetime in seconds. Formula: 2*ceil(dur/min(out/5, out^0.6)*50)*mult."""
    if output <= 0:
        return 0.0
    damage = min(output / 5, output ** 0.6)
    base = 2 * math.ceil(durability / damage * 50)
    if steam_mode == "SC Steam":
        mult = 1.0 if mode == "Tight" else 4.0
    elif steam_mode in ("Steam", "SH Steam"):
        mult = 2.0 if mode == "Tight" else 8 / 3
    else:  # gas, plasma
        mult = 1.0
    return base * mult


def _lifetime_xl(durability: int, output: int, turbine_type: str, mode: str) -> float:
    """XL turbine lifetime in seconds."""
    if output <= 0:
        return 0.0
    damage = min(output / 5 / 5, (output / 5) ** 0.6)
    if turbine_type == "steam":
        mult = 1.0 if mode == "Tight" else 4 / 3
        return math.ceil(mult * durability / damage * 50)
    elif turbine_type == "gas":
        return math.ceil(4 / 3 * durability / damage * 50)
    else:  # plasma
        return math.ceil(1.25 * durability / damage * 50)


def _flow_efficiency_steam(eff_flow: float, opt_flow: float, overflow_tier: int, fuel_type: str) -> float:
    """Steam turbine flow efficiency (0..1). <optimal underflows, >optimal overflows."""
    if opt_flow <= 0:
        return 0.0
    if eff_flow > opt_flow:
        if fuel_type == "SC Steam":
            mult = 1.25
        elif fuel_type == "SH Steam":
            mult = overflow_tier + 2
        else:
            mult = overflow_tier + 1
        return 1.0 - abs((eff_flow - opt_flow) / (opt_flow * mult))
    else:
        return 1.0 - abs((eff_flow - opt_flow) / opt_flow)


def _flow_efficiency_gas(eff_flow: float, opt_flow: float, overflow_tier: int) -> float:
    if opt_flow <= 0:
        return 0.0
    if eff_flow > opt_flow:
        return 1.0 - abs((eff_flow - opt_flow) / (opt_flow * (overflow_tier * 3 - 1)))
    return 1.0 - abs((eff_flow - opt_flow) / opt_flow)


def _flow_efficiency_plasma(eff_flow: float, opt_flow: float, overflow_tier: int) -> float:
    if opt_flow <= 0:
        return 0.0
    if eff_flow > opt_flow:
        return 1.0 - abs((eff_flow - opt_flow) / (opt_flow * (overflow_tier * 3 + 1)))
    return 1.0 - abs((eff_flow - opt_flow) / opt_flow)


def calc_regular_turbine(
    turbine_type: TurbineType,
    rotor: dict,
    size: str,
    mode: str,
    fuel_type: str,
    fuel_value: float,
    manual_flow: float | None = None,
) -> TurbineResult:
    """Calculate all outputs for one regular turbine configuration."""
    sd = _rotor_size(rotor, size)
    overflow_tier = rotor["overflow_tier"]
    durability = _durability(rotor, size)

    if turbine_type == "steam":
        rotor_eff = sd["steam_tight_eff"] if mode == "Tight" else sd["steam_loose_eff"]
        opt_flow = sd["steam_opt_flow_tight"] if mode == "Tight" else sd["steam_opt_flow_loose"]
        opt_output = int(math.floor(opt_flow * rotor_eff * fuel_value))

        if fuel_type == "SC Steam":
            max_flow_mult = 1.25
        elif fuel_type == "SH Steam":
            max_flow_mult = 0.5 * overflow_tier + 1.5
        else:
            max_flow_mult = 0.5 * overflow_tier + 1
        max_flow = int(math.floor(opt_flow * max_flow_mult))

        eff_flow = min(max_flow, manual_flow) if manual_flow is not None else opt_flow
        flow_eff = _flow_efficiency_steam(eff_flow, opt_flow, overflow_tier, fuel_type)
        eff_output = max(1, int(math.floor(eff_flow * flow_eff * rotor_eff * fuel_value)))
        lifetime = _lifetime_regular(durability, eff_output, fuel_type, mode)

    elif turbine_type == "gas":
        rotor_eff = sd["gas_tight_eff"] if mode == "Tight" else sd["gas_loose_eff"]
        opt_flow_eu_t = sd["gas_opt_flow_tight"] if mode == "Tight" else sd["gas_opt_flow_loose"]
        opt_flow = max(1, int(math.floor(opt_flow_eu_t / fuel_value)))
        opt_output = int(math.floor(opt_flow * rotor_eff * fuel_value))

        max_flow_mult = overflow_tier * 1.5
        max_flow = int(math.floor(max_flow_mult * opt_flow))

        eff_flow = min(max_flow, manual_flow) if manual_flow is not None else opt_flow
        flow_eff = _flow_efficiency_gas(eff_flow, opt_flow, overflow_tier)
        eff_output = int(math.floor(eff_flow * flow_eff * rotor_eff * fuel_value))
        lifetime = _lifetime_regular(durability, eff_output, None, mode)

    else:  # plasma
        rotor_eff = sd["plasma_tight_eff"] if mode == "Tight" else sd["plasma_loose_eff"]
        opt_flow_eu_t = sd["plasma_opt_flow_tight"] if mode == "Tight" else sd["plasma_opt_flow_loose"]
        opt_flow = max(1, int(math.ceil(opt_flow_eu_t * 20 / fuel_value)))
        opt_output = int(math.floor(opt_flow * rotor_eff * fuel_value / 20))

        max_flow_mult = 1.5 * overflow_tier + 1
        max_flow = int(math.floor(max_flow_mult * opt_flow))

        eff_flow = min(max_flow, manual_flow) if manual_flow is not None else opt_flow
        flow_eff = _flow_efficiency_plasma(eff_flow, opt_flow, overflow_tier)
        eff_output = max(1, int(math.floor(eff_flow * flow_eff * rotor_eff * fuel_value / 20)))
        lifetime = _lifetime_regular(durability, eff_output, None, mode)

    return TurbineResult(
        turbine_type=turbine_type,
        mode=mode,
        fuel_type=fuel_type,
        fuel_value=fuel_value,
        opt_flow=opt_flow,
        opt_output_eu_t=opt_output,
        eff_flow=eff_flow,
        eff_output_eu_t=eff_output,
        rotor_eff=rotor_eff,
        max_flow=max_flow,
        min_dynamo_tier_opt=find_dynamo_tier(opt_output),
        min_dynamo_tier_eff=find_dynamo_tier(eff_output),
        lifetime_s=lifetime,
        overflow_tier=overflow_tier,
    )


def calc_xl_turbine(
    turbine_type: TurbineType,
    rotor: dict,
    size: str,
    mode: str,
    fuel_type: str,
    fuel_value: float,
    is_dense: bool = False,
    manual_flow: float | None = None,
) -> TurbineResult:
    """Calculate all outputs for one XL turbine (16x flow multiplier)."""
    sd = _rotor_size(rotor, size)
    overflow_tier = rotor["overflow_tier"]
    durability = _durability(rotor, size)
    XL = 16  # XL multiplier

    if turbine_type == "steam":
        rotor_eff = sd["steam_tight_eff"] if mode == "Tight" else sd["steam_loose_eff"]
        base_opt_flow = sd["steam_opt_flow_tight"] if mode == "Tight" else sd["steam_opt_flow_loose"]
        opt_flow_raw = base_opt_flow * XL   # L/t (or mB/t when dense)
        display_flow = int(math.floor(opt_flow_raw / 1000)) if is_dense else int(opt_flow_raw)
        opt_flow_calc = display_flow * 1000 if is_dense else opt_flow_raw
        opt_output = int(math.floor(opt_flow_calc * rotor_eff * fuel_value))

        max_flow_raw = int(math.floor(opt_flow_raw * 1.25))
        max_flow_calc = max_flow_raw

        eff_flow_raw = min(max_flow_raw, manual_flow * (1000 if is_dense else 1)) if manual_flow is not None else opt_flow_calc
        flow_eff = 1.0 - abs((eff_flow_raw - opt_flow_calc) / opt_flow_calc) if opt_flow_calc else 0.0
        eff_output = max(1, int(math.floor(eff_flow_raw * flow_eff * rotor_eff * fuel_value)))
        lifetime = _lifetime_xl(durability, eff_output, "steam", mode)
        opt_flow = display_flow
        eff_flow = int(math.floor(eff_flow_raw / 1000)) if is_dense else eff_flow_raw
        max_flow = int(math.floor(max_flow_raw / 1000)) if is_dense else max_flow_raw

    elif turbine_type == "gas":
        rotor_eff = sd["gas_tight_eff"] if mode == "Tight" else sd["gas_loose_eff"]
        opt_flow_eu_t = sd["gas_opt_flow_tight"] if mode == "Tight" else sd["gas_opt_flow_loose"]
        opt_flow = max(1, int(math.floor(XL * opt_flow_eu_t / fuel_value)))
        opt_output = int(math.floor(opt_flow * rotor_eff * fuel_value))

        max_flow = int(math.floor(opt_flow * 1.25))
        eff_flow = min(max_flow, manual_flow) if manual_flow is not None else opt_flow
        flow_eff = 1.0 - abs((eff_flow - opt_flow) / opt_flow) if opt_flow else 0.0
        eff_output = int(math.floor(eff_flow * flow_eff * rotor_eff * fuel_value))
        lifetime = _lifetime_xl(durability, eff_output, "gas", mode)

    else:  # plasma
        rotor_eff = sd["plasma_tight_eff"] if mode == "Tight" else sd["plasma_loose_eff"]
        opt_flow_eu_t = sd["plasma_opt_flow_tight"] if mode == "Tight" else sd["plasma_opt_flow_loose"]
        opt_flow = max(1, int(math.floor(XL * opt_flow_eu_t * 20 / fuel_value)))
        plasma_power_tight = sd["plasma_power_tight"]
        nerf_mult = min(1.0, (fuel_value * 0.005) ** 2 / plasma_power_tight) if plasma_power_tight else 1.0
        opt_output = int(math.floor(opt_flow * rotor_eff * fuel_value / 20 * nerf_mult))

        max_flow = int(math.floor(opt_flow * 1.25))
        eff_flow = min(max_flow, manual_flow) if manual_flow is not None else opt_flow
        flow_eff = 1.0 - abs((eff_flow - opt_flow) / opt_flow) if opt_flow else 0.0
        eff_output = int(math.floor(opt_output * min(1 + overflow_tier * 1.5, eff_flow / opt_flow) * flow_eff))
        lifetime = _lifetime_xl(durability, eff_output, "plasma", mode)

    return TurbineResult(
        turbine_type=turbine_type,
        mode=mode,
        fuel_type=fuel_type,
        fuel_value=fuel_value,
        opt_flow=opt_flow,
        opt_output_eu_t=opt_output,
        eff_flow=eff_flow,
        eff_output_eu_t=eff_output,
        rotor_eff=rotor_eff,
        max_flow=max_flow,
        min_dynamo_tier_opt=find_dynamo_tier(opt_output),
        min_dynamo_tier_eff=find_dynamo_tier(eff_output),
        lifetime_s=lifetime,
        overflow_tier=overflow_tier,
    )
