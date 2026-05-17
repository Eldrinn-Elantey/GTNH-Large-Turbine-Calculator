import math

_SIZE_SPEED_MULT  = {"Small": 1.0, "Normal": 2.0, "Large": 3.0, "Huge": 4.0}
_SIZE_BASE_DAMAGE = {"Small": 0.0, "Normal": 2.5, "Large": 5.0, "Huge": 7.5}
_SIZE_DUR_MULT    = {"Small": 1,   "Normal": 2,   "Large": 3,   "Huge": 4}


def compute_overflow_tier(tool_quality: int) -> int:
    return 1 + min(2, tool_quality // 3)


def _round6(x: float) -> float:
    return round(x, 6)


def compute_rotor_sizes(
    tool_quality: int,
    tool_speed: float,
    steam_mult: float,
    gas_mult: float,
    plasma_mult: float,
) -> dict:
    sizes = {}
    for size in ("Small", "Normal", "Large", "Huge"):
        speed_mult  = _SIZE_SPEED_MULT[size]
        base_damage = _SIZE_BASE_DAMAGE[size]
        dur_mult    = _SIZE_DUR_MULT[size]

        combat    = base_damage + tool_quality
        base_eff  = 0.5 + (0.5 + combat) * 0.1

        loose_eff        = -0.2 + round(base_eff * 85.0) * 0.01
        loose_steam_eff  = loose_eff * 0.9
        loose_gas_eff    = loose_eff * 0.95
        loose_plasma_eff = loose_eff

        opt_flow         = speed_mult * tool_speed * 50.0
        opt_steam        = opt_flow * steam_mult
        opt_gas          = opt_flow * gas_mult
        opt_plasma       = opt_flow * plasma_mult * 42.0

        decay = (base_eff - 0.8) * 20.0
        loose_steam  = 3.0 * opt_steam  * math.pow(1.1,  decay)
        loose_gas    = 2.0 * opt_gas    * math.pow(1.05, decay)
        loose_plasma = 2.0 * opt_plasma * math.pow(1.03, decay)

        sizes[size] = {
            "steam_tight_eff":       _round6(base_eff),
            "steam_loose_eff":       _round6(loose_steam_eff),
            "steam_opt_flow_tight":  _round6(opt_steam),
            "steam_opt_flow_loose":  _round6(loose_steam),
            "steam_power_tight":     _round6(opt_steam  * base_eff        * 0.5),
            "steam_power_loose":     _round6(loose_steam * loose_steam_eff * 0.5),
            "gas_tight_eff":         _round6(base_eff),
            "gas_loose_eff":         _round6(loose_gas_eff),
            "gas_opt_flow_tight":    _round6(opt_gas),
            "gas_opt_flow_loose":    _round6(loose_gas),
            "gas_power_tight":       _round6(opt_gas   * base_eff      * 1.0),
            "gas_power_loose":       _round6(loose_gas * loose_gas_eff * 1.0),
            "plasma_tight_eff":      _round6(base_eff),
            "plasma_loose_eff":      _round6(loose_plasma_eff),
            "plasma_opt_flow_tight": _round6(opt_plasma),
            "plasma_opt_flow_loose": _round6(loose_plasma),
            "plasma_power_tight":    _round6(opt_plasma   * base_eff          * 1.0),
            "plasma_power_loose":    _round6(loose_plasma * loose_plasma_eff  * 1.0),
            "dur_mult":              dur_mult,
        }
    return sizes
