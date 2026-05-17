import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QApplication, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

MAIN_BG   = "#0d1117"
SIDEBAR_BG = "#111827"
ACCENT    = "#e94560"

QSS = f"""
QMainWindow, QWidget#main_bg {{
    background: {MAIN_BG};
}}
QWidget#sidebar {{
    background: {SIDEBAR_BG};
    border: none;
}}
QPushButton#nav_btn {{
    background: transparent;
    color: #9ca3af;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    text-align: left;
    font-size: 12px;
}}
QPushButton#nav_btn:hover {{
    background: #1f2937;
}}
QPushButton#nav_btn[active="true"] {{
    background: {ACCENT};
    color: white;
}}
QScrollArea {{
    background: {MAIN_BG};
    border: none;
}}
QScrollBar:vertical {{
    background: #111827;
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: #374151;
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""

NAV_ITEMS = [
    ("⚡  Calculator",  "calculator"),
    ("🔥  EHE Planner", "ehe"),
    ("💧  Steam Gen",   "steam_gen"),
    ("⛽  Fuels",       "fuels"),
    ("🔩  Rotors",      "rotors"),
]


class TurbineCalcApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GTNH Large Turbine Calculator")
        self.resize(1280, 800)
        self.setMinimumSize(1000, 650)
        self.setStyleSheet(QSS)

        self._tab_classes: dict = {}
        self._frames: dict = {}
        self._nav_buttons: dict[str, QPushButton] = {}
        self._current_tab = ""

        root = QWidget()
        root.setObjectName("main_bg")
        root.setLayout(QHBoxLayout())
        root.layout().setContentsMargins(0, 0, 0, 0)
        root.layout().setSpacing(0)
        self.setCentralWidget(root)

        self._build_sidebar(root)
        self._build_content(root)
        self._switch_tab("calculator")

    def _build_sidebar(self, parent: QWidget):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(160)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(8, 20, 8, 10)
        lay.setSpacing(2)

        title = QLabel("GTNH\nTurbines")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {ACCENT}; font-size: 13px; font-weight: bold;")
        lay.addWidget(title)
        lay.addSpacing(10)

        from gtnh_turbine_calc.ui.calculator import CalculatorTab
        from gtnh_turbine_calc.ui.ehe_planner import EHEPlannerTab
        from gtnh_turbine_calc.ui.steam_gen_tab import SteamGenTab
        from gtnh_turbine_calc.ui.fuels_ref import FuelsRefTab
        from gtnh_turbine_calc.ui.rotors_ref import RotorsRefTab

        self._tab_classes = {
            "calculator": CalculatorTab,
            "ehe":        EHEPlannerTab,
            "steam_gen":  SteamGenTab,
            "fuels":      FuelsRefTab,
            "rotors":     RotorsRefTab,
        }

        for label, key in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName("nav_btn")
            btn.setProperty("active", "false")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, k=key: self._switch_tab(k))
            lay.addWidget(btn)
            self._nav_buttons[key] = btn

        lay.addStretch()

        ver = QLabel("v2.7.0-2.8.4")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet("color: #374151; font-size: 9px;")
        lay.addWidget(ver)

        parent.layout().addWidget(sidebar)

    def _build_content(self, parent: QWidget):
        self._stack = QStackedWidget()
        self._stack.setObjectName("main_bg")
        parent.layout().addWidget(self._stack, stretch=1)

    def _get_or_create(self, key: str) -> QWidget:
        if key not in self._frames:
            widget = self._tab_classes[key]()
            self._stack.addWidget(widget)
            self._frames[key] = widget
        return self._frames[key]

    def _switch_tab(self, key: str):
        for k, btn in self._nav_buttons.items():
            active = "true" if k == key else "false"
            btn.setProperty("active", active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._stack.setCurrentWidget(self._get_or_create(key))
        self._current_tab = key


def run():
    app = QApplication(sys.argv)
    window = TurbineCalcApp()
    window.show()
    sys.exit(app.exec())
