import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

SIDEBAR_BG = "#111827"
MAIN_BG = "#0d1117"
ACCENT = "#e94560"
SIDEBAR_WIDTH = 160

NAV_ITEMS = [
    ("⚡  Calculator",  "calculator"),
    ("🔥  EHE Planner", "ehe"),
    ("💧  Steam Gen",   "steam_gen"),
    ("⛽  Fuels",       "fuels"),
    ("🔩  Rotors",      "rotors"),
]


class TurbineCalcApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GTNH Large Turbine Calculator")
        self.geometry("1200x750")
        self.minsize(1000, 650)
        self.configure(fg_color=MAIN_BG)

        self._frames: dict[str, ctk.CTkFrame] = {}
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._current_tab = "calculator"

        self._build_sidebar()
        self._build_content_area()
        self._switch_tab("calculator")

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=SIDEBAR_WIDTH, fg_color=SIDEBAR_BG, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        title = ctk.CTkLabel(sidebar, text="GTNH\nTurbines", font=ctk.CTkFont(size=13, weight="bold"),
                              text_color="#e94560")
        title.pack(pady=(20, 16), padx=8)

        for label, key in NAV_ITEMS:
            btn = ctk.CTkButton(
                sidebar, text=label, anchor="w",
                font=ctk.CTkFont(size=12),
                fg_color="transparent", hover_color="#1f2937",
                text_color="#9ca3af", corner_radius=6, height=36,
                command=lambda k=key: self._switch_tab(k),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_buttons[key] = btn

        version = ctk.CTkLabel(sidebar, text="v2.7.0-2.8.4", font=ctk.CTkFont(size=9),
                                text_color="#374151")
        version.pack(side="bottom", pady=10)

    def _build_content_area(self):
        self._content = ctk.CTkFrame(self, fg_color=MAIN_BG, corner_radius=0)
        self._content.pack(side="left", fill="both", expand=True)

        from gtnh_turbine_calc.ui.calculator import CalculatorTab
        from gtnh_turbine_calc.ui.ehe_planner import EHEPlannerTab
        from gtnh_turbine_calc.ui.steam_gen_tab import SteamGenTab
        from gtnh_turbine_calc.ui.fuels_ref import FuelsRefTab
        from gtnh_turbine_calc.ui.rotors_ref import RotorsRefTab

        tab_classes = {
            "calculator": CalculatorTab,
            "ehe":        EHEPlannerTab,
            "steam_gen":  SteamGenTab,
            "fuels":      FuelsRefTab,
            "rotors":     RotorsRefTab,
        }
        for key, cls in tab_classes.items():
            frame = cls(self._content)
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._frames[key] = frame

    def _switch_tab(self, key: str):
        for k, btn in self._nav_buttons.items():
            if k == key:
                btn.configure(fg_color=ACCENT, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="#9ca3af")
        self._frames[key].lift()
        self._current_tab = key
