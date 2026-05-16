import customtkinter as ctk
from gtnh_turbine_calc.data.rotors import ROTOR_DATA, ROTOR_DISPLAY_NAMES
from gtnh_turbine_calc.data.fuels import EHE_FUEL_NAMES
from gtnh_turbine_calc.calc.ehe import calc_plasma_ehe, calc_nonxl_ehe
from gtnh_turbine_calc.ui.widgets import ResultRow, ToggleButton, YELLOW, GREEN, PURPLE, ORANGE

CARD_BG = "#111827"
NON_XL_HOT_FLUIDS = ["Lava", "IC2 Hot Coolant", "Solar Salt (Hot)"]


class EHEPlannerTab(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        self._build()

    def _build(self):
        shared = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8)
        shared.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(shared, text="Rotor Settings",
                     font=ctk.CTkFont(size=9), text_color="#6b7280").pack(anchor="w", padx=12, pady=(8, 2))
        rotor_row = ctk.CTkFrame(shared, fg_color="transparent")
        rotor_row.pack(fill="x", padx=12, pady=(0, 10))
        self._rotor_combo = ctk.CTkComboBox(
            rotor_row, values=ROTOR_DISPLAY_NAMES, width=220, height=30,
            font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937", text_color="#00d4ff",
            command=lambda _: self._recalc_all(),
        )
        self._rotor_combo.pack(side="left", padx=(0, 12))
        self._rotor_combo.set(ROTOR_DISPLAY_NAMES[0])

        self._size_toggle = ToggleButton(rotor_row, ["Small", "Normal", "Large", "Huge"],
                                          command=lambda _: self._recalc_all())
        self._size_toggle.pack(side="left")

        two_cols = ctk.CTkFrame(self, fg_color="transparent")
        two_cols.pack(fill="x", padx=16, pady=4)
        two_cols.columnconfigure((0, 1), weight=1, uniform="ehe")

        self._build_plasma_ehe(two_cols, column=0)
        self._build_nonxl_ehe(two_cols, column=1)
        self._recalc_all()

    def _make_input_row(self, parent, label: str, default: str = "") -> ctk.CTkEntry:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(row, text=label, width=160, font=ctk.CTkFont(size=10),
                     text_color="#9ca3af", anchor="w").pack(side="left")
        entry = ctk.CTkEntry(row, width=100, height=26,
                             font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151")
        entry.pack(side="right")
        if default:
            entry.insert(0, default)
        entry.bind("<KeyRelease>", lambda _: self._recalc_all())
        return entry

    def _build_plasma_ehe(self, parent, column: int):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=8)
        card.grid(row=0, column=column, sticky="nsew", padx=4, pady=4)
        ctk.CTkFrame(card, height=3, fg_color="#a855f7", corner_radius=0).pack(fill="x")
        ctk.CTkLabel(card, text="⚛  Plasma EHE Setup Planner",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#a855f7", anchor="w").pack(anchor="w", padx=10, pady=(8, 6))

        fuel_row = ctk.CTkFrame(card, fg_color="transparent")
        fuel_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(fuel_row, text="Plasma Type", width=120, font=ctk.CTkFont(size=10),
                     text_color="#9ca3af", anchor="w").pack(side="left")
        self._plasma_fuel_combo = ctk.CTkComboBox(
            fuel_row, values=EHE_FUEL_NAMES, width=170, height=26,
            font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937", text_color="#00d4ff",
            command=lambda _: self._recalc_all(),
        )
        self._plasma_fuel_combo.pack(side="right")
        if EHE_FUEL_NAMES:
            self._plasma_fuel_combo.set(EHE_FUEL_NAMES[0])

        self._plasma_output_l  = self._make_input_row(card, "Recipe Output [L]", "125")
        self._plasma_time_s    = self._make_input_row(card, "Recipe Time [s]", "0.8")
        self._plasma_eu_t      = self._make_input_row(card, "EU/t per Recipe", "32720")
        self._plasma_parallels = self._make_input_row(card, "Parallel Count", "5")

        ctk.CTkFrame(card, height=1, fg_color="#1f2937").pack(fill="x", padx=10, pady=6)

        self._plasma_r_output   = self._make_result(card, "Plasma Output [L/s]", YELLOW)
        self._plasma_r_ehe_max  = self._make_result(card, "EHE Max Input [L/s]", "#9ca3af")
        self._plasma_r_ehe_cnt  = self._make_result(card, "EHE Count", "#9ca3af")
        self._plasma_r_steam    = self._make_result(card, "Dense SC Steam [L/t]", YELLOW)
        self._plasma_r_fit      = self._make_result(card, "Rotor Fit", "#9ca3af")
        self._plasma_r_eff      = self._make_result(card, "Rotor Efficiency", "#9ca3af")
        self._plasma_r_turbs    = self._make_result(card, "Turbine Count", "#9ca3af")
        self._plasma_r_power    = self._make_result(card, "Power/Turbine [EU/t]", GREEN)
        self._plasma_r_dynamo   = self._make_result(card, "Min Dynamo", PURPLE)

    def _build_nonxl_ehe(self, parent, column: int):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=8)
        card.grid(row=0, column=column, sticky="nsew", padx=4, pady=4)
        ctk.CTkFrame(card, height=3, fg_color="#3b82f6", corner_radius=0).pack(fill="x")
        ctk.CTkLabel(card, text="💧  Non-XL EHE Setup Planner",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#3b82f6", anchor="w").pack(anchor="w", padx=10, pady=(8, 6))

        fluid_row = ctk.CTkFrame(card, fg_color="transparent")
        fluid_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(fluid_row, text="Hot Fluid", width=120, font=ctk.CTkFont(size=10),
                     text_color="#9ca3af", anchor="w").pack(side="left")
        self._hot_fluid_combo = ctk.CTkComboBox(
            fluid_row, values=NON_XL_HOT_FLUIDS, width=170, height=26,
            font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937", text_color="#00d4ff",
            command=lambda _: self._recalc_all(),
        )
        self._hot_fluid_combo.pack(side="right")
        self._hot_fluid_combo.set(NON_XL_HOT_FLUIDS[1])

        self._hot_input_ls = self._make_input_row(card, "Hot Fluid Input [L/s]", "32000000")

        ctk.CTkFrame(card, height=1, fg_color="#1f2937").pack(fill="x", padx=10, pady=6)

        self._nonxl_r_ehe_max  = self._make_result(card, "EHE Max Input [L/s]", "#9ca3af")
        self._nonxl_r_sc       = self._make_result(card, "Total SC Steam [L/t]", YELLOW)
        self._nonxl_r_sh       = self._make_result(card, "Total SH Steam [L/t]", YELLOW)
        self._nonxl_r_fit      = self._make_result(card, "Rotor Fit", "#9ca3af")
        self._nonxl_r_eff      = self._make_result(card, "Rotor Efficiency", "#9ca3af")
        self._nonxl_r_opt_flow = self._make_result(card, "Opt. Flow/Turbine [L/t]", YELLOW)
        self._nonxl_r_sc_cnt   = self._make_result(card, "SC Turbine Count", "#9ca3af")
        self._nonxl_r_sh_cnt   = self._make_result(card, "SH/Reg Turbine Count", "#9ca3af")
        self._nonxl_r_power_sc = self._make_result(card, "Power/SC Turbine [EU/t]", GREEN)
        self._nonxl_r_power_r  = self._make_result(card, "Power/Reg Turbine [EU/t]", GREEN)
        self._nonxl_r_dynamo   = self._make_result(card, "Min Dynamo (Reg)", PURPLE)

    def _make_result(self, parent, label: str, color: str) -> ResultRow:
        row = ResultRow(parent, label=label, value_color=color)
        row.pack(fill="x", padx=10, pady=1)
        return row

    def _get_rotor(self):
        name = self._rotor_combo.get()
        size = self._size_toggle.get()
        rotor = ROTOR_DATA.get(name, {})
        return rotor, size

    def _recalc_all(self, *_):
        rotor, size = self._get_rotor()
        if not rotor:
            return

        try:
            ptype = self._plasma_fuel_combo.get()
            r_out = float(self._plasma_output_l.get() or 125)
            r_time = float(self._plasma_time_s.get() or 0.8)
            r_par = float(self._plasma_parallels.get() or 5)
            pr = calc_plasma_ehe(ptype, r_out, r_time, r_par, rotor, size)
            self._plasma_r_output.set(f"{pr['plasma_output_ls']:.2f} L/s")
            self._plasma_r_ehe_max.set(f"{pr['ehe_max_input_ls']:,} L/s")
            self._plasma_r_ehe_cnt.set(str(pr['ehe_count']))
            self._plasma_r_steam.set(f"{pr['dense_sc_steam_lt']:,} L/t")
            self._plasma_r_fit.set(pr['rotor_fit'])
            self._plasma_r_eff.set(f"{pr['rotor_eff']:.3f}")
            self._plasma_r_turbs.set(str(pr['turbine_count']))
            self._plasma_r_power.set(f"{pr['power_per_turbine_sc']:,} EU/t")
            self._plasma_r_dynamo.set(pr['min_dynamo_tier_sc'])
        except Exception:
            pass

        try:
            hf = self._hot_fluid_combo.get()
            hf_ls = float(self._hot_input_ls.get() or 32000000)
            nr = calc_nonxl_ehe(hf, hf_ls, rotor, size)
            self._nonxl_r_ehe_max.set(f"{nr.get('ehe_count', '—')} EHEs")
            self._nonxl_r_sc.set(f"{nr['total_sc_steam_lt']:,} L/t")
            self._nonxl_r_sh.set(f"{nr['total_sh_steam_lt']:,} L/t")
            self._nonxl_r_fit.set(nr['rotor_fit'])
            self._nonxl_r_eff.set(f"{nr['rotor_eff']:.3f}")
            self._nonxl_r_opt_flow.set(f"{nr['opt_flow_lt']:,} L/t")
            self._nonxl_r_sc_cnt.set(str(nr['sc_turbine_count']))
            self._nonxl_r_sh_cnt.set(str(nr['sh_turbine_count']))
            self._nonxl_r_power_sc.set(f"{nr['power_per_sc_turbine']:,} EU/t")
            self._nonxl_r_power_r.set(f"{nr['power_per_reg_turbine']:,} EU/t")
            self._nonxl_r_dynamo.set(nr['min_dynamo_tier_reg'])
        except Exception:
            pass
