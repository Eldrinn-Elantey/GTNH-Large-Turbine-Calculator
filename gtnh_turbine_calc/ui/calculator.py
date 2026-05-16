import math
import customtkinter as ctk

from gtnh_turbine_calc.data.rotors import ROTOR_DATA, ROTOR_DISPLAY_NAMES
from gtnh_turbine_calc.data.fuels import (
    STEAM_FUELS, GAS_FUELS, GAS_FUEL_NAMES, PLASMA_FUELS, PLASMA_FUEL_NAMES
)
from gtnh_turbine_calc.calc.turbine import calc_regular_turbine, calc_xl_turbine, TURBINE_TO_ROTOR_SIZE
from gtnh_turbine_calc.calc.common import DYNAMO_TIERS
from gtnh_turbine_calc.ui.widgets import ResultRow, ToggleButton, YELLOW, GREEN, PURPLE, ORANGE

CARD_BG = "#111827"
DYNAMO_TIER_NAMES = [name for name, _ in DYNAMO_TIERS]
DYNAMO_VOLTAGE = dict(DYNAMO_TIERS)

# Unique rotor tiers sorted ascending, for the filter
_ALL_TIERS = sorted({v["tier"] for v in ROTOR_DATA.values()})
TIER_OPTIONS = ["All"] + [str(t) for t in _ALL_TIERS]


def _fmt_lifetime(seconds: float) -> str:
    days = seconds / 3600 / 24
    if days >= 1:
        return f"{days:.2f} days"
    hours = seconds / 3600
    return f"{hours:.1f} h"


def _fmt_dynamo(eu_t: float, chosen_tier: str) -> str:
    """Show dynamo count × tier and amps."""
    voltage = DYNAMO_VOLTAGE.get(chosen_tier, 1)
    count = math.ceil(eu_t / voltage) if eu_t > 0 else 0
    amps = round(eu_t / voltage, 3)
    return f"{count}× {chosen_tier}  ({amps} A)"


def _rotor_names_for_tier(tier_str: str) -> list[str]:
    if tier_str == "All":
        return ROTOR_DISPLAY_NAMES
    tier = int(tier_str)
    return [n for n in ROTOR_DISPLAY_NAMES if ROTOR_DATA[n]["tier"] == tier]


class RegularTurbineCard(ctk.CTkFrame):
    def __init__(self, master, turbine_type: str, accent: str, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=8, **kwargs)
        self._type = turbine_type
        self._accent = accent
        self._rotor_ref: list[dict] = [{}]
        self._size_ref: list[str] = ["Normal"]
        self._dynamo_tier_ref: list[str] = ["EV"]
        self._build()

    def _build(self):
        ctk.CTkFrame(self, height=3, fg_color=self._accent, corner_radius=0).pack(fill="x")
        icons = {"steam": "💨", "gas": "🔥", "plasma": "⚛"}
        titles = {"steam": "Large Steam Turbine", "gas": "Large Gas Turbine", "plasma": "Large Plasma Gen"}
        ctk.CTkLabel(self, text=f"{icons[self._type]}  {titles[self._type]}",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self._accent, anchor="w").pack(anchor="w", padx=10, pady=(8, 6))

        mode_row = ctk.CTkFrame(self, fg_color="transparent")
        mode_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(mode_row, text="Mode", font=ctk.CTkFont(size=9),
                     text_color="#6b7280", width=60, anchor="w").pack(side="left")
        self._mode_toggle = ToggleButton(mode_row, ["Tight", "Loose"], command=self._recalc)
        self._mode_toggle.pack(side="left")

        fuel_row = ctk.CTkFrame(self, fg_color="transparent")
        fuel_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(fuel_row, text="Fuel", font=ctk.CTkFont(size=9),
                     text_color="#6b7280", width=60, anchor="w").pack(side="left")
        fuel_names = {"steam": list(STEAM_FUELS), "gas": GAS_FUEL_NAMES, "plasma": PLASMA_FUEL_NAMES}
        self._fuel_combo = ctk.CTkComboBox(
            fuel_row, values=fuel_names[self._type], width=170, height=26,
            font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937", text_color="#00d4ff",
            command=lambda _: self._recalc(),
        )
        self._fuel_combo.pack(side="left")
        self._fuel_combo.set(fuel_names[self._type][0])

        eff_row = ctk.CTkFrame(self, fg_color="transparent")
        eff_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(eff_row, text="Flow", font=ctk.CTkFont(size=9),
                     text_color="#6b7280", width=60, anchor="w").pack(side="left")
        self._flow_toggle = ToggleButton(eff_row, ["Optimal", "Manual"], command=self._on_flow_mode)
        self._flow_toggle.pack(side="left")

        self._manual_entry = ctk.CTkEntry(self, width=100, height=24,
                                          placeholder_text="L/t or L/s",
                                          font=ctk.CTkFont(size=10),
                                          fg_color="#1f2937", border_color="#374151")
        self._manual_visible = False

        ctk.CTkFrame(self, height=1, fg_color="#1f2937").pack(fill="x", padx=10, pady=6)

        unit = "L/s" if self._type == "plasma" else "L/t"
        self._row_opt_flow = self._make_result(f"Opt. Flow [{unit}]", YELLOW)
        self._row_output   = self._make_result("Output [EU/t]", GREEN)
        self._row_dynamo   = self._make_result("Dynamo hatches (opt)", PURPLE)
        self._row_eff_flow = self._make_result(f"Eff. Flow [{unit}]", YELLOW)
        self._row_eff_out  = self._make_result("Eff. Output [EU/t]", GREEN)
        self._row_eff_dyn  = self._make_result("Dynamo hatches (eff)", PURPLE)
        self._row_lifetime = self._make_result("Rotor Lifetime", ORANGE)

    def _make_result(self, label: str, color: str) -> ResultRow:
        row = ResultRow(self, label=label, value_color=color)
        row.pack(fill="x", padx=10, pady=1)
        return row

    def _on_flow_mode(self, mode: str):
        if mode == "Manual" and not self._manual_visible:
            self._manual_entry.pack(padx=10, pady=(0, 4))
            self._manual_entry.bind("<KeyRelease>", lambda _: self._recalc())
            self._manual_visible = True
        elif mode == "Optimal" and self._manual_visible:
            self._manual_entry.pack_forget()
            self._manual_visible = False
        self._recalc()

    def set_rotor(self, rotor: dict, size: str):
        self._rotor_ref[0] = rotor
        self._size_ref[0] = size
        self._recalc()

    def set_dynamo_tier(self, tier: str):
        self._dynamo_tier_ref[0] = tier
        self._recalc()

    def _recalc(self, *_):
        rotor = self._rotor_ref[0]
        if not rotor:
            return
        size = self._size_ref[0]
        mode = self._mode_toggle.get()
        fuel_type = self._fuel_combo.get()
        dynamo_tier = self._dynamo_tier_ref[0]

        if self._type == "steam":
            fuel_val = STEAM_FUELS.get(fuel_type, 0.5)
        elif self._type == "gas":
            fuel_val = GAS_FUELS.get(fuel_type, {}).get("eu_per_l", 1)
        else:
            fuel_val = PLASMA_FUELS.get(fuel_type, 81920)

        manual_flow = None
        if self._flow_toggle.get() == "Manual":
            try:
                manual_flow = float(self._manual_entry.get())
            except ValueError:
                pass

        try:
            r = calc_regular_turbine(self._type, rotor, size, mode, fuel_type, fuel_val, manual_flow)
        except Exception:
            return

        unit = "L/s" if self._type == "plasma" else "L/t"
        self._row_opt_flow.set(f"{r.opt_flow:,.0f} {unit}")
        self._row_output.set(f"{r.opt_output_eu_t:,} EU/t")
        self._row_dynamo.set(_fmt_dynamo(r.opt_output_eu_t, dynamo_tier))
        self._row_eff_flow.set(f"{r.eff_flow:,.0f} {unit}")
        self._row_eff_out.set(f"{r.eff_output_eu_t:,} EU/t")
        self._row_eff_dyn.set(_fmt_dynamo(r.eff_output_eu_t, dynamo_tier))
        self._row_lifetime.set(_fmt_lifetime(r.lifetime_s))


class XLTurbineCard(ctk.CTkFrame):
    def __init__(self, master, turbine_type: str, accent: str, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=8, **kwargs)
        self._type = turbine_type
        self._accent = accent
        self._rotor_ref: list[dict] = [{}]
        self._size_ref: list[str] = ["Normal"]
        self._dynamo_tier_ref: list[str] = ["EV"]
        self._build()

    def _build(self):
        ctk.CTkFrame(self, height=3, fg_color=self._accent, corner_radius=0).pack(fill="x")
        titles = {
            "steam": "XL Turbo SC Steam Turbine",
            "gas":   "XL Turbo Gas Turbine",
            "plasma": "XL Turbo Plasma Turbine",
        }
        ctk.CTkLabel(self, text=titles[self._type],
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=self._accent, anchor="w").pack(anchor="w", padx=10, pady=(8, 6))

        mode_row = ctk.CTkFrame(self, fg_color="transparent")
        mode_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(mode_row, text="Mode", font=ctk.CTkFont(size=9),
                     text_color="#6b7280", width=60, anchor="w").pack(side="left")
        self._mode_toggle = ToggleButton(mode_row, ["Tight", "Loose"], command=self._recalc)
        self._mode_toggle.pack(side="left")

        fuel_row = ctk.CTkFrame(self, fg_color="transparent")
        fuel_row.pack(fill="x", padx=10, pady=2)
        ctk.CTkLabel(fuel_row, text="Fuel", font=ctk.CTkFont(size=9),
                     text_color="#6b7280", width=60, anchor="w").pack(side="left")

        if self._type == "steam":
            fuel_names = ["SC Steam"]
            self._dense_var = ctk.BooleanVar(value=True)
            ctk.CTkCheckBox(fuel_row, text="Dense", variable=self._dense_var,
                            font=ctk.CTkFont(size=9), command=self._recalc).pack(side="right")
        elif self._type == "gas":
            fuel_names = [k for k, v in GAS_FUELS.items() if v["xlgt"]]
        else:
            fuel_names = PLASMA_FUEL_NAMES

        self._fuel_combo = ctk.CTkComboBox(
            fuel_row, values=fuel_names, width=140, height=26,
            font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937", text_color="#00d4ff",
            command=lambda _: self._recalc(),
        )
        self._fuel_combo.pack(side="left")
        if fuel_names:
            self._fuel_combo.set(fuel_names[0])

        ctk.CTkFrame(self, height=1, fg_color="#1f2937").pack(fill="x", padx=10, pady=6)

        unit = "L/s" if self._type == "plasma" else "L/t"
        self._row_flow   = self._make_result(f"Opt. Flow [{unit}]", YELLOW)
        self._row_output = self._make_result("Output [EU/t]", GREEN)
        self._row_dynamo = self._make_result("Dynamo hatches", PURPLE)
        self._row_life   = self._make_result("Rotor Lifetime", ORANGE)

    def _make_result(self, label: str, color: str) -> ResultRow:
        row = ResultRow(self, label=label, value_color=color)
        row.pack(fill="x", padx=10, pady=1)
        return row

    def set_rotor(self, rotor: dict, size: str):
        self._rotor_ref[0] = rotor
        self._size_ref[0] = size
        self._recalc()

    def set_dynamo_tier(self, tier: str):
        self._dynamo_tier_ref[0] = tier
        self._recalc()

    def _recalc(self, *_):
        rotor = self._rotor_ref[0]
        if not rotor:
            return
        size = self._size_ref[0]
        mode = self._mode_toggle.get()
        fuel_type = self._fuel_combo.get()
        dynamo_tier = self._dynamo_tier_ref[0]
        is_dense = getattr(self, "_dense_var", None)
        is_dense = is_dense.get() if is_dense else False

        if self._type == "steam":
            fuel_val = STEAM_FUELS.get(fuel_type, 1.0)
        elif self._type == "gas":
            fuel_val = GAS_FUELS.get(fuel_type, {}).get("eu_per_l", 1)
        else:
            fuel_val = PLASMA_FUELS.get(fuel_type, 81920)

        try:
            r = calc_xl_turbine(self._type, rotor, size, mode, fuel_type, fuel_val, is_dense)
        except Exception:
            return

        unit = "L/s" if self._type == "plasma" else "L/t"
        self._row_flow.set(f"{r.opt_flow:,.0f} {unit}")
        self._row_output.set(f"{r.opt_output_eu_t:,} EU/t")
        self._row_dynamo.set(_fmt_dynamo(r.opt_output_eu_t, dynamo_tier))
        self._row_life.set(_fmt_lifetime(r.lifetime_s))


class CalculatorTab(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        self._large_visible = True
        self._xl_visible = False
        self._build()

    def _build(self):
        # --- Shared settings ---
        shared = ctk.CTkFrame(self, fg_color="#111827", corner_radius=8)
        shared.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(shared, text="SHARED SETTINGS",
                     font=ctk.CTkFont(size=9), text_color="#6b7280").pack(anchor="w", padx=12, pady=(10, 4))

        rotor_row = ctk.CTkFrame(shared, fg_color="transparent")
        rotor_row.pack(fill="x", padx=12, pady=(0, 6))

        # Tier filter
        ctk.CTkLabel(rotor_row, text="Tier", font=ctk.CTkFont(size=9),
                     text_color="#6b7280", anchor="w").pack(side="left", padx=(0, 4))
        self._tier_combo = ctk.CTkComboBox(
            rotor_row, values=TIER_OPTIONS, width=70, height=28,
            font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937", text_color="#00d4ff",
            command=self._on_tier_change,
        )
        self._tier_combo.set("All")
        self._tier_combo.pack(side="left", padx=(0, 12))

        # Rotor material
        ctk.CTkLabel(rotor_row, text="Material", font=ctk.CTkFont(size=9),
                     text_color="#6b7280", anchor="w").pack(side="left", padx=(0, 4))
        self._rotor_combo = ctk.CTkComboBox(
            rotor_row, values=ROTOR_DISPLAY_NAMES, width=240, height=28,
            font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937", text_color="#00d4ff",
            command=lambda _: self._on_rotor_change(),
        )
        self._rotor_combo.set(ROTOR_DISPLAY_NAMES[0])
        self._rotor_combo.pack(side="left", padx=(0, 12))

        # Size toggle
        self._size_toggle = ToggleButton(rotor_row, ["Turbine", "Large", "Huge"],
                                          command=lambda _: self._on_rotor_change())
        self._size_toggle.pack(side="left", padx=(0, 12))
        self._size_toggle.set("Large")

        self._lbl_eff = ctk.CTkLabel(rotor_row, text="Eff: —", font=ctk.CTkFont(size=10),
                                      text_color=GREEN)
        self._lbl_eff.pack(side="left", padx=(0, 8))
        self._lbl_dur = ctk.CTkLabel(rotor_row, text="Dur: —", font=ctk.CTkFont(size=10),
                                      text_color=YELLOW)
        self._lbl_dur.pack(side="left")

        # Dynamo hatch tier selector
        dynamo_row = ctk.CTkFrame(shared, fg_color="transparent")
        dynamo_row.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(dynamo_row, text="Dynamo Hatch Tier", font=ctk.CTkFont(size=9),
                     text_color="#6b7280", anchor="w").pack(side="left", padx=(0, 8))
        self._dynamo_combo = ctk.CTkComboBox(
            dynamo_row, values=DYNAMO_TIER_NAMES, width=100, height=28,
            font=ctk.CTkFont(size=10), fg_color="#1f2937", border_color="#374151",
            button_color="#374151", dropdown_fg_color="#1f2937", text_color=PURPLE,
            command=self._on_dynamo_tier_change,
        )
        self._dynamo_combo.set("EV")
        self._dynamo_combo.pack(side="left")
        ctk.CTkLabel(dynamo_row, text="— choose tier to see how many dynamo hatches needed",
                     font=ctk.CTkFont(size=9), text_color="#4b5563").pack(side="left", padx=8)

        # --- Large Turbines collapsible ---
        large_header = ctk.CTkButton(
            self, text="▼  Large Turbines",
            font=ctk.CTkFont(size=11), fg_color="#111827", hover_color="#1f2937",
            text_color="#9ca3af", corner_radius=6, height=36, anchor="w",
            command=self._toggle_large,
        )
        large_header.pack(fill="x", padx=16, pady=(4, 0))
        self._large_header_btn = large_header

        self._large_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._large_frame.pack(fill="x", padx=16, pady=(0, 4))
        self._large_frame.columnconfigure((0, 1, 2), weight=1, uniform="card")

        self._steam_card  = RegularTurbineCard(self._large_frame, "steam",  "#3b82f6")
        self._gas_card    = RegularTurbineCard(self._large_frame, "gas",    "#f59e0b")
        self._plasma_card = RegularTurbineCard(self._large_frame, "plasma", "#a855f7")
        self._steam_card.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self._gas_card.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        self._plasma_card.grid(row=0, column=2, sticky="nsew", padx=4, pady=4)

        # --- XL Turbines collapsible ---
        xl_header = ctk.CTkButton(
            self, text="▶  XL Turbo Turbines  (click to expand)",
            font=ctk.CTkFont(size=11), fg_color="#111827", hover_color="#1f2937",
            text_color="#9ca3af", corner_radius=6, height=36, anchor="w",
            command=self._toggle_xl,
        )
        xl_header.pack(fill="x", padx=16, pady=(4, 0))
        self._xl_header_btn = xl_header

        self._xl_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._xl_frame.columnconfigure((0, 1, 2), weight=1, uniform="xl")
        self._xl_steam  = XLTurbineCard(self._xl_frame, "steam",  "#93c5fd")
        self._xl_gas    = XLTurbineCard(self._xl_frame, "gas",    "#fcd34d")
        self._xl_plasma = XLTurbineCard(self._xl_frame, "plasma", "#c084fc")
        self._xl_steam.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self._xl_gas.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        self._xl_plasma.grid(row=0, column=2, sticky="nsew", padx=4, pady=4)

        self._on_rotor_change()

    def _toggle_large(self):
        if self._large_visible:
            self._large_frame.pack_forget()
            self._large_header_btn.configure(text="▶  Large Turbines  (click to expand)")
            self._large_visible = False
        else:
            self._large_frame.pack(fill="x", padx=16, pady=(0, 4),
                                   before=self._xl_header_btn)
            self._large_header_btn.configure(text="▼  Large Turbines")
            self._large_visible = True

    def _toggle_xl(self):
        if self._xl_visible:
            self._xl_frame.pack_forget()
            self._xl_header_btn.configure(text="▶  XL Turbo Turbines  (click to expand)")
            self._xl_visible = False
        else:
            self._xl_frame.pack(fill="x", padx=16, pady=(0, 16))
            self._xl_header_btn.configure(text="▼  XL Turbo Turbines")
            self._xl_visible = True

    def _on_tier_change(self, tier_str: str):
        names = _rotor_names_for_tier(tier_str)
        self._rotor_combo.configure(values=names)
        if names:
            self._rotor_combo.set(names[0])
        self._on_rotor_change()

    def _on_dynamo_tier_change(self, tier: str):
        all_cards = [self._steam_card, self._gas_card, self._plasma_card,
                     self._xl_steam, self._xl_gas, self._xl_plasma]
        for card in all_cards:
            card.set_dynamo_tier(tier)

    def _on_rotor_change(self, *_):
        name = self._rotor_combo.get()
        size = self._size_toggle.get()
        rotor = ROTOR_DATA.get(name, {})
        if not rotor:
            return

        blade_size = TURBINE_TO_ROTOR_SIZE.get(size, size)
        sd = rotor["sizes"][blade_size]
        dur = rotor["base_durability"] * sd["dur_mult"]
        self._lbl_eff.configure(text=f"Eff(tight): {sd['steam_tight_eff']:.3f}")
        self._lbl_dur.configure(text=f"Dur: {dur:,}")

        dynamo_tier = self._dynamo_combo.get()
        all_cards = [self._steam_card, self._gas_card, self._plasma_card,
                     self._xl_steam, self._xl_gas, self._xl_plasma]
        for card in all_cards:
            card.set_dynamo_tier(dynamo_tier)
            card.set_rotor(rotor, size)
