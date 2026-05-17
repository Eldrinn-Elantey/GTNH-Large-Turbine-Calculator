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


def extract_fuels(wb, existing: dict | None = None) -> dict:
    ws = wb["Fuels"]
    steam, gas, plasma, ehe = [], [], [], []

    for row in ws.iter_rows(min_row=5, max_row=1000, values_only=True):
        # Steam: col B (1) = name, col C (2) = eu_l
        if row[1] and isinstance(row[2], (int, float)):
            steam.append({"name": row[1], "eu_l": float(row[2])})

        # Gas: col J (9) = name, col K (10) = eu_l, col L (11) = xlgt
        if row[9] and isinstance(row[10], (int, float)):
            gas.append({
                "name": row[9],
                "eu_l": float(row[10]),
                "xlgt": bool(row[11]) if row[11] is not None else False,
            })

        # Plasma: col O (14) = name, col P (15) = eu_l
        if row[14] and isinstance(row[15], (int, float)):
            plasma.append({"name": row[14], "eu_l": float(row[15])})

        # EHE: col R (17) = name, cols S-AC (18-28) = data
        if row[17] and isinstance(row[17], str) and row[18] is not None:
            ehe.append({
                "name": row[17],
                "max_convert_ls": row[18],
                "threshold_ls": row[19],
                "eu_t": row[20],
                "coolant": row[21],
                "max_coolant_ls": row[22],
                "normal_steam": row[23],
                "max_normal_steam_ls": row[24],
                "hot_steam": row[25],
                "max_hot_steam_ls": row[26],
                "cooled_fluid": row[27],
                "max_cooled_fluid_ls": row[28],
            })

    return {"steam": steam, "gas": gas, "plasma": plasma, "ehe": ehe}
