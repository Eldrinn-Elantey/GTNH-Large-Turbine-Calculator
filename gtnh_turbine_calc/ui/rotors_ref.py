import customtkinter as ctk
from gtnh_turbine_calc.data.rotors import ROTOR_DATA, ROTOR_DISPLAY_NAMES
from gtnh_turbine_calc.ui.widgets import SearchableTable, ToggleButton


class RotorsRefTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Rotor Reference",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#e94560").pack(anchor="w", padx=16, pady=(16, 8))

        size_frame = ctk.CTkFrame(self, fg_color="#111827", corner_radius=6)
        size_frame.pack(anchor="w", padx=16, pady=(0, 8))
        ctk.CTkLabel(size_frame, text="Blade size:", font=ctk.CTkFont(size=10),
                     text_color="#9ca3af").pack(side="left", padx=(10, 6), pady=8)
        self._size_toggle = ToggleButton(size_frame, ["Turbine", "Large", "Huge"],
                                         command=lambda _: self._reload())
        self._size_toggle.pack(side="left", padx=(0, 10), pady=6)

        self._table = SearchableTable(self, columns=[
            ("Display Name", 240),
            ("Tier",         50),
            ("Base Dur",     90),
            ("Overflow",     70),
            ("St.Tight Eff", 90),
            ("St.Loose Eff", 90),
            ("St.Opt Flow",  90),
            ("Gas Tight",    80),
            ("Pla Tight",    80),
        ])
        self._table.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self._reload()

    # Maps UI blade name to internal data column key
    _BLADE_COL = {"Turbine": "Small", "Large": "Normal", "Huge": "Large"}

    def _reload(self):
        col = self._BLADE_COL[self._size_toggle.get()]
        rows = []
        for name in ROTOR_DISPLAY_NAMES:
            rd = ROTOR_DATA[name]
            sd = rd["sizes"][col]
            # Durability uses next col's dur_mult due to data extraction misalignment
            dur_col_map = {"Small": "Normal", "Normal": "Large", "Large": "Huge"}
            dur_sd = rd["sizes"][dur_col_map[col]]
            dur = rd["base_durability"] * dur_sd["dur_mult"]
            rows.append([
                name,
                str(rd["tier"]),
                f"{dur:,}",
                str(rd["overflow_tier"]),
                f"{sd['steam_tight_eff']:.3f}",
                f"{sd['steam_loose_eff']:.3f}",
                f"{sd['steam_opt_flow_tight']:,.0f}",
                f"{sd['gas_tight_eff']:.3f}",
                f"{sd['plasma_tight_eff']:.3f}",
            ])
        self._table.load(rows)
