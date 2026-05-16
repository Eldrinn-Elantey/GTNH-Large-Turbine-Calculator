from PySide6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QLineEdit, QFrame,
)
from PySide6.QtCore import Qt

from gtnh_turbine_calc.data.rotors import ROTOR_DATA, ROTOR_DISPLAY_NAMES
from gtnh_turbine_calc.data.fuels import EHE_FUEL_NAMES
from gtnh_turbine_calc.calc.ehe import calc_plasma_ehe, calc_nonxl_ehe
from gtnh_turbine_calc.ui.widgets import ResultRow, ToggleButton, YELLOW, GREEN, PURPLE, ORANGE

CARD_BG = "#111827"
NON_XL_HOT_FLUIDS = ["Lava", "IC2 Hot Coolant", "Solar Salt (Hot)"]

_EHE_QSS = """
QWidget { background: #0d1117; }
QFrame#card { background: #111827; border-radius: 8px; }
QComboBox {
    background: #1f2937; color: #00d4ff;
    border: 1px solid #374151; border-radius: 4px;
    padding: 3px 6px; font-size: 10px;
}
QComboBox::drop-down { border: none; width: 18px; }
QComboBox QAbstractItemView {
    background: #1f2937; color: #d1d5db;
    border: 1px solid #374151;
    selection-background-color: #1e40af;
}
QLineEdit {
    background: #1f2937; color: #d1d5db;
    border: 1px solid #374151; border-radius: 4px;
    padding: 3px 6px; font-size: 10px;
}
QScrollArea { background: #0d1117; border: none; }
"""


def _lbl(text, color="#9ca3af", size=10, bold=False):
    l = QLabel(text)
    w = "bold" if bold else "normal"
    l.setStyleSheet(f"color:{color};font-size:{size}px;font-weight:{w};background:transparent;")
    return l


def _sep():
    f = QFrame()
    f.setFixedHeight(1)
    f.setStyleSheet("background: #1f2937;")
    return f


class EHEPlannerTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_EHE_QSS)
        self._build()

    def _build(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        lay = QVBoxLayout(content)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(8)

        # Shared rotor row
        shared = QFrame()
        shared.setStyleSheet("background: #111827; border-radius: 8px;")
        sh_lay = QVBoxLayout(shared)
        sh_lay.setContentsMargins(12, 8, 12, 10)
        sh_lay.addWidget(_lbl("Rotor Settings", size=9, color="#6b7280"))
        rotor_row = QHBoxLayout()
        rotor_row.setSpacing(8)
        self._rotor_combo = QComboBox()
        self._rotor_combo.addItems(ROTOR_DISPLAY_NAMES)
        self._rotor_combo.setFixedWidth(220)
        self._rotor_combo.currentTextChanged.connect(self._recalc_all)
        rotor_row.addWidget(self._rotor_combo)
        self._size_toggle = ToggleButton(["Small", "Normal", "Large", "Huge"],
                                          command=lambda _: self._recalc_all())
        rotor_row.addWidget(self._size_toggle)
        rotor_row.addStretch()
        sh_lay.addLayout(rotor_row)
        lay.addWidget(shared)

        # Two-column grid for plasma and non-XL cards
        cards_widget = QWidget()
        cards_grid = QGridLayout(cards_widget)
        cards_grid.setSpacing(8)
        cards_grid.setContentsMargins(0, 0, 0, 0)
        cards_grid.setColumnStretch(0, 1)
        cards_grid.setColumnStretch(1, 1)

        self._build_plasma_ehe(cards_grid, column=0)
        self._build_nonxl_ehe(cards_grid, column=1)
        lay.addWidget(cards_widget)
        lay.addStretch()

        self._recalc_all()

    def _make_input_row(self, parent_lay, label: str, default: str = "") -> QLineEdit:
        row = QHBoxLayout()
        row.setSpacing(4)
        lbl = _lbl(label, size=10)
        lbl.setFixedWidth(160)
        row.addWidget(lbl)
        row.addStretch()
        entry = QLineEdit()
        entry.setFixedWidth(100)
        entry.setFixedHeight(26)
        if default:
            entry.setText(default)
        entry.textChanged.connect(self._recalc_all)
        row.addWidget(entry)
        parent_lay.addLayout(row)
        return entry

    def _make_result(self, parent_lay, label: str, color: str) -> ResultRow:
        row = ResultRow(label, color)
        parent_lay.addWidget(row)
        return row

    def _build_plasma_ehe(self, grid: QGridLayout, column: int):
        card = QFrame()
        card.setObjectName("card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        strip = QFrame()
        strip.setFixedHeight(3)
        strip.setStyleSheet("background: #a855f7;")
        lay.addWidget(strip)

        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(10, 8, 10, 10)
        inner_lay.setSpacing(2)

        inner_lay.addWidget(_lbl("⚛  Plasma EHE Setup Planner", color="#a855f7", size=11, bold=True))

        fuel_row = QHBoxLayout()
        fuel_row.addWidget(_lbl("Plasma Type", size=10))
        fuel_row.addStretch()
        self._plasma_fuel_combo = QComboBox()
        self._plasma_fuel_combo.addItems(EHE_FUEL_NAMES)
        self._plasma_fuel_combo.setFixedWidth(170)
        self._plasma_fuel_combo.currentTextChanged.connect(self._recalc_all)
        fuel_row.addWidget(self._plasma_fuel_combo)
        inner_lay.addLayout(fuel_row)

        self._plasma_output_l  = self._make_input_row(inner_lay, "Recipe Output [L]", "125")
        self._plasma_time_s    = self._make_input_row(inner_lay, "Recipe Time [s]", "0.8")
        self._plasma_eu_t      = self._make_input_row(inner_lay, "EU/t per Recipe", "32720")
        self._plasma_parallels = self._make_input_row(inner_lay, "Parallel Count", "5")

        inner_lay.addWidget(_sep())

        self._plasma_r_output  = self._make_result(inner_lay, "Plasma Output [L/s]", YELLOW)
        self._plasma_r_ehe_max = self._make_result(inner_lay, "EHE Max Input [L/s]", "#9ca3af")
        self._plasma_r_ehe_cnt = self._make_result(inner_lay, "EHE Count", "#9ca3af")
        self._plasma_r_steam   = self._make_result(inner_lay, "Dense SC Steam [L/t]", YELLOW)
        self._plasma_r_fit     = self._make_result(inner_lay, "Rotor Fit", "#9ca3af")
        self._plasma_r_eff     = self._make_result(inner_lay, "Rotor Efficiency", "#9ca3af")
        self._plasma_r_turbs   = self._make_result(inner_lay, "Turbine Count", "#9ca3af")
        self._plasma_r_power   = self._make_result(inner_lay, "Power/Turbine [EU/t]", GREEN)
        self._plasma_r_dynamo  = self._make_result(inner_lay, "Min Dynamo", PURPLE)

        lay.addWidget(inner)
        grid.addWidget(card, 0, column)

    def _build_nonxl_ehe(self, grid: QGridLayout, column: int):
        card = QFrame()
        card.setObjectName("card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        strip = QFrame()
        strip.setFixedHeight(3)
        strip.setStyleSheet("background: #3b82f6;")
        lay.addWidget(strip)

        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(10, 8, 10, 10)
        inner_lay.setSpacing(2)

        inner_lay.addWidget(_lbl("💧  Non-XL EHE Setup Planner", color="#3b82f6", size=11, bold=True))

        fluid_row = QHBoxLayout()
        fluid_row.addWidget(_lbl("Hot Fluid", size=10))
        fluid_row.addStretch()
        self._hot_fluid_combo = QComboBox()
        self._hot_fluid_combo.addItems(NON_XL_HOT_FLUIDS)
        self._hot_fluid_combo.setCurrentText(NON_XL_HOT_FLUIDS[1])
        self._hot_fluid_combo.setFixedWidth(170)
        self._hot_fluid_combo.currentTextChanged.connect(self._recalc_all)
        fluid_row.addWidget(self._hot_fluid_combo)
        inner_lay.addLayout(fluid_row)

        self._hot_input_ls = self._make_input_row(inner_lay, "Hot Fluid Input [L/s]", "32000000")

        inner_lay.addWidget(_sep())

        self._nonxl_r_ehe_max  = self._make_result(inner_lay, "EHE Max Input [L/s]", "#9ca3af")
        self._nonxl_r_sc       = self._make_result(inner_lay, "Total SC Steam [L/t]", YELLOW)
        self._nonxl_r_sh       = self._make_result(inner_lay, "Total SH Steam [L/t]", YELLOW)
        self._nonxl_r_fit      = self._make_result(inner_lay, "Rotor Fit", "#9ca3af")
        self._nonxl_r_eff      = self._make_result(inner_lay, "Rotor Efficiency", "#9ca3af")
        self._nonxl_r_opt_flow = self._make_result(inner_lay, "Opt. Flow/Turbine [L/t]", YELLOW)
        self._nonxl_r_sc_cnt   = self._make_result(inner_lay, "SC Turbine Count", "#9ca3af")
        self._nonxl_r_sh_cnt   = self._make_result(inner_lay, "SH/Reg Turbine Count", "#9ca3af")
        self._nonxl_r_power_sc = self._make_result(inner_lay, "Power/SC Turbine [EU/t]", GREEN)
        self._nonxl_r_power_r  = self._make_result(inner_lay, "Power/Reg Turbine [EU/t]", GREEN)
        self._nonxl_r_dynamo   = self._make_result(inner_lay, "Min Dynamo (Reg)", PURPLE)

        lay.addWidget(inner)
        grid.addWidget(card, 0, column)

    def _get_rotor(self):
        name = self._rotor_combo.currentText()
        size = self._size_toggle.get()
        return ROTOR_DATA.get(name, {}), size

    def _recalc_all(self, *_):
        rotor, size = self._get_rotor()
        if not rotor:
            return

        try:
            ptype = self._plasma_fuel_combo.currentText()
            r_out = float(self._plasma_output_l.text() or 125)
            r_time = float(self._plasma_time_s.text() or 0.8)
            r_par = float(self._plasma_parallels.text() or 5)
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
            hf = self._hot_fluid_combo.currentText()
            hf_ls = float(self._hot_input_ls.text() or 32000000)
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
