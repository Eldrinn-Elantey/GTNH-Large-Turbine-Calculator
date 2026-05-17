import openpyxl
import sys

EXCEL_PATH = "D:/UserData/Eldrinn_Elantey/Downloads/Large Turbine Calculator (2.7.0-2.8.4).xlsx"

def extract_rotors(wb):
    ws = wb["Rotors"]
    sizes = ["Small", "Normal", "Large", "Huge"]
    size_dur_mults = {"Small": 1, "Normal": 2, "Large": 3, "Huge": 4}

    COL_OFFSETS = {
        "steam_tight_eff":       20,
        "steam_loose_eff":       24,
        "steam_opt_flow_tight":  28,
        "steam_opt_flow_loose":  32,
        "steam_power_tight":     36,
        "steam_power_loose":     40,
        "gas_tight_eff":         48,
        "gas_loose_eff":         52,
        "gas_opt_flow_tight":    56,
        "gas_opt_flow_loose":    60,
        "gas_power_tight":       64,
        "gas_power_loose":       68,
        "plasma_tight_eff":      76,
        "plasma_loose_eff":      80,
        "plasma_opt_flow_tight": 84,
        "plasma_opt_flow_loose": 88,
        "plasma_power_tight":    92,
        "plasma_power_loose":    96,
    }

    rotors = {}
    for row in ws.iter_rows(min_row=4, max_row=1000, values_only=True):
        display_name = row[8]  # col I = index 8 (0-based)
        if not display_name or not isinstance(display_name, str):
            continue
        tier = row[9]          # col J
        mining_speed = row[10] # col K
        base_dur = row[11]     # col L (Durability ST)
        overflow_tier = row[12]# col M

        if tier is None:
            continue

        sizes_data = {}
        for i, size in enumerate(sizes, start=1):  # 1=Small, 2=Normal, 3=Large, 4=Huge
            sd = {}
            for key, base_col in COL_OFFSETS.items():
                col_idx = base_col + i  # 1-indexed relative to col I
                abs_col = 9 + col_idx - 1  # absolute column (0-indexed)
                val = row[abs_col] if abs_col < len(row) else None
                sd[key] = round(val, 6) if isinstance(val, float) else val
            sd["dur_mult"] = size_dur_mults[size]
            sizes_data[size] = sd

        rotors[display_name] = {
            "tier": int(tier),
            "mining_speed": mining_speed,
            "base_durability": int(base_dur),
            "overflow_tier": int(overflow_tier),
            "sizes": sizes_data,
        }

    return rotors

def extract_fuels(wb):
    ws = wb["Fuels"]
    steam_fuels = {}
    gas_fuels = {}
    plasma_fuels = {}
    ehe_fuels = {}

    for row in ws.iter_rows(min_row=5, max_row=1000, values_only=True):
        # Steam fuels: col B=name, col C=eu_per_l
        if row[1] and row[2] is not None and isinstance(row[2], (int, float)):
            if row[1] in ("Steam", "SH Steam", "SC Steam"):
                steam_fuels[row[1]] = float(row[2])

        # Gas fuels: col J=name, col K=eu_per_l, col L=xlgt
        if row[9] and row[10] is not None and isinstance(row[10], (int, float)):
            gas_fuels[row[9]] = {"eu_per_l": float(row[10]), "xlgt": bool(row[11])}

        # Plasma fuels: col O=name, col P=eu_per_l
        if row[14] and row[15] is not None and isinstance(row[15], (int, float)):
            plasma_fuels[row[14]] = float(row[15])

        # EHE plasma fuels: col R=name, col S..AC = data
        if row[17] and isinstance(row[17], str) and row[18] is not None:
            ehe_fuels[row[17]] = {
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
            }

    return steam_fuels, gas_fuels, plasma_fuels, ehe_fuels

if __name__ == "__main__":
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

    rotors = extract_rotors(wb)
    steam_fuels, gas_fuels, plasma_fuels, ehe_fuels = extract_fuels(wb)

    if "--rotors" in sys.argv:
        print("ROTOR_DATA =", repr(rotors))
    if "--fuels" in sys.argv:
        print("STEAM_FUELS =", repr(steam_fuels))
        print("GAS_FUELS =", repr(gas_fuels))
        print("PLASMA_FUELS =", repr(plasma_fuels))
        print("EHE_FUELS =", repr(ehe_fuels))
    if len(sys.argv) == 1:
        print(f"Extracted {len(rotors)} rotors, "
              f"{len(steam_fuels)} steam fuels, "
              f"{len(gas_fuels)} gas fuels, "
              f"{len(plasma_fuels)} plasma fuels, "
              f"{len(ehe_fuels)} EHE fuels")
