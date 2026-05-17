from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget,
)

from gtnh_turbine_calc.data.fuels import STEAM_FUELS, GAS_FUELS, PLASMA_FUELS
from gtnh_turbine_calc.ui.widgets import SearchableTable

_FUELS_QSS = """
QWidget { background: #0d1117; }
QTabWidget::pane { background: #111827; border: none; }
QTabBar::tab {
    background: #111827;
    color: #9ca3af;
    padding: 6px 16px;
    border: none;
    font-size: 11px;
}
QTabBar::tab:selected { background: #e94560; color: white; }
QTabBar::tab:hover { background: #1f2937; }
"""


class FuelsRefTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_FUELS_QSS)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        title = QLabel("Fuel Reference")
        title.setStyleSheet("color: #e94560; font-size: 14px; font-weight: bold;")
        lay.addWidget(title)

        tabs = QTabWidget()
        lay.addWidget(tabs)

        # Steam tab
        steam_widget = QWidget()
        steam_lay = QVBoxLayout(steam_widget)
        steam_lay.setContentsMargins(0, 0, 0, 0)
        steam_tbl = SearchableTable(columns=[("Type", 200), ("EU/L", 120)])
        steam_tbl.load([[k, f"{v:.1f}"] for k, v in STEAM_FUELS.items()])
        steam_lay.addWidget(steam_tbl)
        tabs.addTab(steam_widget, "Steam")

        # Gas tab
        gas_widget = QWidget()
        gas_lay = QVBoxLayout(gas_widget)
        gas_lay.setContentsMargins(0, 0, 0, 0)
        gas_tbl = SearchableTable(columns=[("Name", 220), ("EU/L", 100), ("XLGT", 60)])
        gas_rows = sorted(
            [[k, f"{v['eu_per_l']:.0f}", "Yes" if v["xlgt"] else "No"]
             for k, v in GAS_FUELS.items()],
            key=lambda r: float(r[1]), reverse=True,
        )
        gas_tbl.load(gas_rows)
        gas_lay.addWidget(gas_tbl)
        tabs.addTab(gas_widget, "Gas")

        # Plasma tab
        plasma_widget = QWidget()
        plasma_lay = QVBoxLayout(plasma_widget)
        plasma_lay.setContentsMargins(0, 0, 0, 0)
        plasma_tbl = SearchableTable(columns=[("Name", 260), ("EU/L", 120)])
        plasma_rows = sorted(
            [[k, f"{v:,.0f}"] for k, v in PLASMA_FUELS.items()],
            key=lambda r: float(r[1].replace(",", "")), reverse=True,
        )
        plasma_tbl.load(plasma_rows)
        plasma_lay.addWidget(plasma_tbl)
        tabs.addTab(plasma_widget, "Plasma")
