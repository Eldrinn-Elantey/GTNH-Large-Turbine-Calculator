_SIZES = ["Small", "Normal", "Large", "Huge"]
_SIZE_DUR_MULTS = {"Small": 1, "Normal": 2, "Large": 3, "Huge": 4}

_COL_SMALL = {
    "steam_tight_eff":       28,
    "steam_loose_eff":       32,
    "steam_opt_flow_tight":  36,
    "steam_opt_flow_loose":  40,
    "steam_power_tight":     44,
    "steam_power_loose":     48,
    "gas_tight_eff":         56,
    "gas_loose_eff":         60,
    "gas_opt_flow_tight":    64,
    "gas_opt_flow_loose":    68,
    "gas_power_tight":       72,
    "gas_power_loose":       76,
    "plasma_tight_eff":      84,
    "plasma_loose_eff":      88,
    "plasma_opt_flow_tight": 92,
    "plasma_opt_flow_loose": 96,
    "plasma_power_tight":    100,
    "plasma_power_loose":    104,
}


def extract_rotors(wb) -> list:
    ws = wb["Rotors"]
    rotors = []
    for row in ws.iter_rows(min_row=4, max_row=1000, values_only=True):
        display_name = row[8]
        if not display_name or not isinstance(display_name, str):
            continue
        tier = row[9]
        if tier is None:
            continue

        sizes_data = {}
        for i, size in enumerate(_SIZES):
            sd = {}
            for key, small_col in _COL_SMALL.items():
                col = small_col + i
                val = row[col] if col < len(row) else None
                sd[key] = round(val, 6) if isinstance(val, float) else val
            sd["dur_mult"] = _SIZE_DUR_MULTS[size]
            sizes_data[size] = sd

        try:
            tier_int = int(tier)
            base_dur = int(row[11]) if row[11] is not None else None
            overflow = int(row[12]) if row[12] is not None else None
        except (ValueError, TypeError) as e:
            raise ValueError(f"Bad numeric value in Rotors row for '{display_name}': {e}") from e

        rotors.append({
            "name": display_name,
            "tier": tier_int,
            "mining_speed": round(row[10], 6) if isinstance(row[10], float) else row[10],
            "base_durability": base_dur,
            "overflow_tier": overflow,
            "sizes": sizes_data,
        })

    rotors.sort(key=lambda r: -r["tier"])
    return rotors
