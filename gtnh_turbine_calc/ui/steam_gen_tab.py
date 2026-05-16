import customtkinter as ctk
from gtnh_turbine_calc.data.steam_gen import LHE_SOURCES, WWXL_SOURCES, THERMAL_BOILER_SOURCES

CARD_BG = "#111827"


def _steam_row(parent, name: str, data: dict, is_thermal: bool = False):
    row = ctk.CTkFrame(parent, fg_color="#1f2937", corner_radius=4, height=28)
    row.pack(fill="x", pady=1)
    row.pack_propagate(False)
    if is_thermal:
        cols = [
            (name, 160),
            (f"{data['max_ls']:,} L/s", 100),
            (data["steam"], 80),
            (f"x{data['ratio']}", 60),
        ]
    else:
        cols = [
            (name, 160),
            (f"{data['threshold_ls']:,}", 100),
            (f"{data['max_ls']:,}", 100),
            (data["below"], 70),
            (data["above"], 80),
            (f"x{data['ratio_below']}", 60),
            (f"x{data['ratio_above']}", 60),
        ]
    for text, width in cols:
        ctk.CTkLabel(row, text=text, width=width, font=ctk.CTkFont(size=10),
                     text_color="#d1d5db", anchor="w").pack(side="left", padx=4)


def _section(parent, title: str, color: str, headers: list, sources: list, is_thermal: bool = False):
    card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=8)
    card.pack(fill="x", padx=16, pady=6)
    ctk.CTkFrame(card, height=3, fg_color=color, corner_radius=0).pack(fill="x")
    ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=color, anchor="w").pack(anchor="w", padx=10, pady=(8, 4))
    hdr = ctk.CTkFrame(card, fg_color="#374151", corner_radius=4, height=26)
    hdr.pack(fill="x", padx=10, pady=(0, 2))
    hdr.pack_propagate(False)
    for text, width in headers:
        ctk.CTkLabel(hdr, text=text, width=width, font=ctk.CTkFont(size=9, weight="bold"),
                     text_color="#9ca3af", anchor="w").pack(side="left", padx=4)
    for src in sources:
        _steam_row(card, src["name"], src, is_thermal)
    ctk.CTkFrame(card, height=4, fg_color="transparent").pack()


class SteamGenTab(ctk.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="#0d1117", **kwargs)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Steam Generation Reference",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#e94560").pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(self, text="All flows in L/s. Steam output = input x ratio.",
                     font=ctk.CTkFont(size=10), text_color="#6b7280").pack(anchor="w", padx=16, pady=(0, 12))

        lhe_hdrs = [("Source", 160), ("Threshold L/s", 100), ("Max L/s", 100),
                    ("Below thr.", 70), ("Above thr.", 80), ("Ratio below", 60), ("Ratio above", 60)]
        _section(self, "Large Heat Exchanger (LHE)", "#3b82f6", lhe_hdrs, LHE_SOURCES)
        _section(self, "Whakawhiti Wera XL (WWXL)", "#60a5fa", lhe_hdrs, WWXL_SOURCES)

        th_hdrs = [("Source", 160), ("Max L/s", 100), ("Steam Type", 80), ("Ratio", 60)]
        _section(self, "Thermal Boiler", "#f59e0b", th_hdrs, THERMAL_BOILER_SOURCES, is_thermal=True)
