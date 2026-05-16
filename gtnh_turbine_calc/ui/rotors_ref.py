from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
)

from gtnh_turbine_calc.data.rotors import ROTOR_DATA, ROTOR_DISPLAY_NAMES
from gtnh_turbine_calc.ui.widgets import SearchableTable, ToggleButton

_ROTORS_QSS = """
QWidget { background: #0d1117; }
QFrame#size_bar { background: #111827; border-radius: 6px; }
"""

# Durability column offset mapping (verified against GT5-Unofficial source)
_DUR_COL = {"Small": "Normal", "Normal": "Large", "Large": "Huge", "Huge": "Huge"}


class RotorsRefTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_ROTORS_QSS)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        title = QLabel("Rotor Reference")
        title.setStyleSheet("color: #e94560; font-size: 14px; font-weight: bold;")
        lay.addWidget(title)

        size_bar = QFrame()
        size_bar.setObjectName("size_bar")
        sb_lay = QHBoxLayout(size_bar)
        sb_lay.setContentsMargins(10, 6, 10, 6)
        sb_lay.setSpacing(6)
        lbl = QLabel("Blade size:")
        lbl.setStyleSheet("color: #9ca3af; font-size: 10px; background: transparent;")
        sb_lay.addWidget(lbl)
        self._size_toggle = ToggleButton(["Small", "Normal", "Large", "Huge"],
                                          command=lambda _: self._reload())
        sb_lay.addWidget(self._size_toggle)
        sb_lay.addStretch()
        lay.addWidget(size_bar)

        self._table = SearchableTable(columns=[
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
        lay.addWidget(self._table)
        self._reload()

    def _reload(self):
        size = self._size_toggle.get()
        rows = []
        for name in ROTOR_DISPLAY_NAMES:
            rd = ROTOR_DATA[name]
            sd = rd["sizes"][size]
            dur = rd["base_durability"] * rd["sizes"][_DUR_COL[size]]["dur_mult"]
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
