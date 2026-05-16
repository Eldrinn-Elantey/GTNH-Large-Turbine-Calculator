import customtkinter as ctk
from gtnh_turbine_calc.data.fuels import STEAM_FUELS, GAS_FUELS, PLASMA_FUELS
from gtnh_turbine_calc.ui.widgets import SearchableTable

CARD_BG = "#111827"


class FuelsRefTab(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Fuel Reference",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#e94560").pack(anchor="w", padx=16, pady=(16, 8))

        tabs = ctk.CTkTabview(self, fg_color="#111827", segmented_button_fg_color="#111827",
                              segmented_button_selected_color="#e94560",
                              segmented_button_selected_hover_color="#c03050")
        tabs.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        steam_tab = tabs.add("Steam")
        steam_tbl = SearchableTable(steam_tab, columns=[("Type", 200), ("EU/L", 120)])
        steam_tbl.pack(fill="both", expand=True)
        steam_tbl.load([[k, f"{v:.1f}"] for k, v in STEAM_FUELS.items()])

        gas_tab = tabs.add("Gas")
        gas_tbl = SearchableTable(gas_tab, columns=[("Name", 220), ("EU/L", 100), ("XLGT", 60)])
        gas_tbl.pack(fill="both", expand=True)
        gas_rows = sorted(
            [[k, f"{v['eu_per_l']:.0f}", "Yes" if v["xlgt"] else "No"]
             for k, v in GAS_FUELS.items()],
            key=lambda r: float(r[1]), reverse=True,
        )
        gas_tbl.load(gas_rows)

        plasma_tab = tabs.add("Plasma")
        plasma_tbl = SearchableTable(plasma_tab, columns=[("Name", 260), ("EU/L", 120)])
        plasma_tbl.pack(fill="both", expand=True)
        plasma_rows = sorted(
            [[k, f"{v:,.0f}"] for k, v in PLASMA_FUELS.items()],
            key=lambda r: float(r[1].replace(",", "")), reverse=True,
        )
        plasma_tbl.load(plasma_rows)
