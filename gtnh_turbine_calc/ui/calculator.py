import math
from PySide6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QFrame, QCheckBox,
    QSizePolicy,
)
from PySide6.QtCore import Qt

from gtnh_turbine_calc.data.rotors import ROTOR_DATA, ROTOR_DISPLAY_NAMES
from gtnh_turbine_calc.data.fuels import (
    STEAM_FUELS, GAS_FUELS, GAS_FUEL_NAMES, PLASMA_FUELS, PLASMA_FUEL_NAMES,
)
from gtnh_turbine_calc.calc.turbine import calc_regular_turbine, calc_xl_turbine, TURBINE_TO_ROTOR_SIZE
from gtnh_turbine_calc.calc.common import DYNAMO_TIERS
from gtnh_turbine_calc.ui.widgets import ResultRow, ToggleButton, YELLOW, GREEN, PURPLE, ORANGE

CARD_BG = "#111827"
DYNAMO_TIER_NAMES = [name for name, _ in DYNAMO_TIERS]
DYNAMO_VOLTAGE = dict(DYNAMO_TIERS)
_ALL_TIERS = sorted({v["tier"] for v in ROTOR_DATA.values()})
TIER_OPTIONS = ["All"] + [str(t) for t in _ALL_TIERS]

_CALC_QSS = """
QWidget { background: #0d1117; }
QFrame#card {
    background: #111827;
    border-radius: 8px;
}
QFrame#card_strip { border-radius: 0; }
QFrame#shared {
    background: #111827;
    border-radius: 8px;
}
QPushButton#collapse_btn {
    background: #111827;
    color: #9ca3af;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    text-align: left;
    font-size: 11px;
}
QPushButton#collapse_btn:hover { background: #1f2937; }
QComboBox {
    background: #1f2937;
    color: #00d4ff;
    border: 1px solid #374151;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
}
QComboBox::drop-down { border: none; width: 18px; }
QComboBox QAbstractItemView {
    background: #1f2937;
    color: #d1d5db;
    border: 1px solid #374151;
    selection-background-color: #1e40af;
}
QLineEdit {
    background: #1f2937;
    color: #d1d5db;
    border: 1px solid #374151;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 10px;
}
QCheckBox { color: #9ca3af; font-size: 9px; background: transparent; }
QScrollArea { background: #0d1117; border: none; }
"""


def _fmt_lifetime(seconds: float) -> str:
    days = seconds / 3600 / 24
    if days >= 1:
        return f"{days:.2f} days"
    return f"{seconds / 3600:.1f} h"


def _fmt_dynamo(eu_t: float, chosen_tier: str) -> str:
    voltage = DYNAMO_VOLTAGE.get(chosen_tier, 1)
    count = math.ceil(eu_t / voltage) if eu_t > 0 else 0
    amps = round(eu_t / voltage, 3)
    return f"{count}x {chosen_tier}  ({amps} A)"


def _rotor_names_for_tier(tier_str: str) -> list[str]:
    if tier_str == "All":
        return ROTOR_DISPLAY_NAMES
    tier = int(tier_str)
    return [n for n in ROTOR_DISPLAY_NAMES if ROTOR_DATA[n]["tier"] == tier]


def _sep(parent=None) -> QFrame:
    line = QFrame(parent)
    line.setFixedHeight(1)
    line.setStyleSheet("background: #1f2937;")
    return line


def _label(text: str, color: str = "#6b7280", size: int = 9, bold: bool = False, parent=None) -> QLabel:
    lbl = QLabel(text, parent)
    weight = "bold" if bold else "normal"
    lbl.setStyleSheet(f"color: {color}; font-size: {size}px; font-weight: {weight}; background: transparent;")
    return lbl


class RegularTurbineCard(QFrame):
    def __init__(self, turbine_type: str, accent: str, parent=None):
        super().__init__(parent)
        self._type = turbine_type
        self._accent = accent
        self._rotor: dict = {}
        self._size = "Normal"
        self._dynamo_tier = "EV"
        self._build()

    def _build(self):
        self.setObjectName("card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        strip = QFrame()
        strip.setFixedHeight(3)
        strip.setStyleSheet(f"background: {self._accent};")
        lay.addWidget(strip)

        icons = {"steam": "💨", "gas": "🔥", "plasma": "⚛"}
        titles = {"steam": "Large Steam Turbine", "gas": "Large Gas Turbine", "plasma": "Large Plasma Gen"}
        title_lbl = _label(f"{icons[self._type]}  {titles[self._type]}",
                           color=self._accent, size=11, bold=True)
        title_lbl.setContentsMargins(10, 8, 10, 4)
        lay.addWidget(title_lbl)

        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(10, 0, 10, 0)
        inner_lay.setSpacing(2)

        # Mode toggle
        mode_row = QHBoxLayout()
        mode_row.addWidget(_label("Mode", size=9))
        self._mode_toggle = ToggleButton(["Tight", "Loose"], command=self._recalc)
        mode_row.addWidget(self._mode_toggle)
        mode_row.addStretch()
        inner_lay.addLayout(mode_row)

        # Fuel combo
        fuel_row = QHBoxLayout()
        fuel_row.addWidget(_label("Fuel", size=9))
        fuel_names = {"steam": list(STEAM_FUELS), "gas": GAS_FUEL_NAMES, "plasma": PLASMA_FUEL_NAMES}
        self._fuel_combo = QComboBox()
        self._fuel_combo.addItems(fuel_names[self._type])
        self._fuel_combo.setFixedWidth(170)
        self._fuel_combo.currentTextChanged.connect(self._recalc)
        fuel_row.addWidget(self._fuel_combo)
        fuel_row.addStretch()
        inner_lay.addLayout(fuel_row)

        # Flow toggle
        flow_row = QHBoxLayout()
        flow_row.addWidget(_label("Flow", size=9))
        self._flow_toggle = ToggleButton(["Optimal", "Manual"], command=self._on_flow_mode)
        flow_row.addWidget(self._flow_toggle)
        flow_row.addStretch()
        inner_lay.addLayout(flow_row)

        # Manual entry (hidden initially)
        self._manual_entry = QLineEdit()
        self._manual_entry.setPlaceholderText("L/t or L/s")
        self._manual_entry.setFixedWidth(100)
        self._manual_entry.setFixedHeight(24)
        self._manual_entry.textChanged.connect(self._recalc)
        self._manual_entry.hide()
        inner_lay.addWidget(self._manual_entry)

        inner_lay.addWidget(_sep())

        unit = "L/s" if self._type == "plasma" else "L/t"
        self._row_opt_flow = ResultRow(f"Opt. Flow [{unit}]", YELLOW)
        self._row_output   = ResultRow("Output [EU/t]", GREEN)
        self._row_dynamo   = ResultRow("Dynamo hatches (opt)", PURPLE)
        self._row_eff_flow = ResultRow(f"Eff. Flow [{unit}]", YELLOW)
        self._row_eff_out  = ResultRow("Eff. Output [EU/t]", GREEN)
        self._row_eff_dyn  = ResultRow("Dynamo hatches (eff)", PURPLE)
        self._row_lifetime = ResultRow("Rotor Lifetime", ORANGE)

        for row in [self._row_opt_flow, self._row_output, self._row_dynamo,
                    self._row_eff_flow, self._row_eff_out, self._row_eff_dyn, self._row_lifetime]:
            inner_lay.addWidget(row)

        inner_lay.addSpacing(6)
        lay.addWidget(inner)

    def _on_flow_mode(self, mode: str):
        if mode == "Manual":
            self._manual_entry.show()
        else:
            self._manual_entry.hide()
        self._recalc()

    def set_rotor(self, rotor: dict, size: str):
        self._rotor = rotor
        self._size = size
        self._recalc()

    def set_dynamo_tier(self, tier: str):
        self._dynamo_tier = tier
        self._recalc()

    def _recalc(self, *_):
        if not self._rotor:
            return
        mode = self._mode_toggle.get()
        fuel_type = self._fuel_combo.currentText()

        if self._type == "steam":
            fuel_val = STEAM_FUELS.get(fuel_type, 0.5)
        elif self._type == "gas":
            fuel_val = GAS_FUELS.get(fuel_type, {}).get("eu_per_l", 1)
        else:
            fuel_val = PLASMA_FUELS.get(fuel_type, 81920)

        manual_flow = None
        if self._flow_toggle.get() == "Manual":
            try:
                manual_flow = float(self._manual_entry.text())
            except ValueError:
                pass

        try:
            r = calc_regular_turbine(self._type, self._rotor, self._size, mode, fuel_type, fuel_val, manual_flow)
        except Exception:
            return

        unit = "L/s" if self._type == "plasma" else "L/t"
        self._row_opt_flow.set(f"{r.opt_flow:,.0f} {unit}")
        self._row_output.set(f"{r.opt_output_eu_t:,} EU/t")
        self._row_dynamo.set(_fmt_dynamo(r.opt_output_eu_t, self._dynamo_tier))
        self._row_eff_flow.set(f"{r.eff_flow:,.0f} {unit}")
        self._row_eff_out.set(f"{r.eff_output_eu_t:,} EU/t")
        self._row_eff_dyn.set(_fmt_dynamo(r.eff_output_eu_t, self._dynamo_tier))
        self._row_lifetime.set(_fmt_lifetime(r.lifetime_s))


class XLTurbineCard(QFrame):
    def __init__(self, turbine_type: str, accent: str, parent=None):
        super().__init__(parent)
        self._type = turbine_type
        self._accent = accent
        self._rotor: dict = {}
        self._size = "Normal"
        self._dynamo_tier = "EV"
        self._build()

    def _build(self):
        self.setObjectName("card")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        strip = QFrame()
        strip.setFixedHeight(3)
        strip.setStyleSheet(f"background: {self._accent};")
        lay.addWidget(strip)

        titles = {
            "steam": "XL Turbo SC Steam Turbine",
            "gas":   "XL Turbo Gas Turbine",
            "plasma": "XL Turbo Plasma Turbine",
        }
        title_lbl = _label(titles[self._type], color=self._accent, size=10, bold=True)
        title_lbl.setContentsMargins(10, 8, 10, 4)
        lay.addWidget(title_lbl)

        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(10, 0, 10, 0)
        inner_lay.setSpacing(2)

        mode_row = QHBoxLayout()
        mode_row.addWidget(_label("Mode", size=9))
        self._mode_toggle = ToggleButton(["Tight", "Loose"], command=self._recalc)
        mode_row.addWidget(self._mode_toggle)
        mode_row.addStretch()
        inner_lay.addLayout(mode_row)

        fuel_row = QHBoxLayout()
        fuel_row.addWidget(_label("Fuel", size=9))
        if self._type == "steam":
            fuel_names = ["SC Steam"]
            self._dense_check = QCheckBox("Dense")
            self._dense_check.setChecked(True)
            self._dense_check.stateChanged.connect(self._recalc)
            fuel_row.addWidget(self._dense_check)
        elif self._type == "gas":
            fuel_names = [k for k, v in GAS_FUELS.items() if v["xlgt"]]
        else:
            fuel_names = PLASMA_FUEL_NAMES

        self._fuel_combo = QComboBox()
        self._fuel_combo.addItems(fuel_names)
        self._fuel_combo.setFixedWidth(140)
        self._fuel_combo.currentTextChanged.connect(self._recalc)
        fuel_row.insertWidget(1, self._fuel_combo)
        fuel_row.addStretch()
        inner_lay.addLayout(fuel_row)

        inner_lay.addWidget(_sep())

        unit = "L/s" if self._type == "plasma" else "L/t"
        self._row_flow   = ResultRow(f"Opt. Flow [{unit}]", YELLOW)
        self._row_output = ResultRow("Output [EU/t]", GREEN)
        self._row_dynamo = ResultRow("Dynamo hatches", PURPLE)
        self._row_life   = ResultRow("Rotor Lifetime", ORANGE)

        for row in [self._row_flow, self._row_output, self._row_dynamo, self._row_life]:
            inner_lay.addWidget(row)

        inner_lay.addSpacing(6)
        lay.addWidget(inner)

    def set_rotor(self, rotor: dict, size: str):
        self._rotor = rotor
        self._size = size
        self._recalc()

    def set_dynamo_tier(self, tier: str):
        self._dynamo_tier = tier
        self._recalc()

    def _recalc(self, *_):
        if not self._rotor:
            return
        mode = self._mode_toggle.get()
        fuel_type = self._fuel_combo.currentText()
        is_dense = getattr(self, "_dense_check", None)
        is_dense = is_dense.isChecked() if is_dense else False

        if self._type == "steam":
            fuel_val = STEAM_FUELS.get(fuel_type, 1.0)
        elif self._type == "gas":
            fuel_val = GAS_FUELS.get(fuel_type, {}).get("eu_per_l", 1)
        else:
            fuel_val = PLASMA_FUELS.get(fuel_type, 81920)

        try:
            r = calc_xl_turbine(self._type, self._rotor, self._size, mode, fuel_type, fuel_val, is_dense)
        except Exception:
            return

        unit = "L/s" if self._type == "plasma" else "L/t"
        self._row_flow.set(f"{r.opt_flow:,.0f} {unit}")
        self._row_output.set(f"{r.opt_output_eu_t:,} EU/t")
        self._row_dynamo.set(_fmt_dynamo(r.opt_output_eu_t, self._dynamo_tier))
        self._row_life.set(_fmt_lifetime(r.lifetime_s))


class CalculatorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_CALC_QSS)
        self._large_visible = True
        self._xl_visible = False
        self._build()

    def _build(self):
        # Wrap in scroll area
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
        lay.setSpacing(4)

        # Shared settings card
        shared = QFrame()
        shared.setObjectName("shared")
        shared_lay = QVBoxLayout(shared)
        shared_lay.setContentsMargins(12, 10, 12, 10)
        shared_lay.setSpacing(6)
        shared_lay.addWidget(_label("SHARED SETTINGS", size=9))

        rotor_row = QHBoxLayout()
        rotor_row.setSpacing(8)

        rotor_row.addWidget(_label("Tier", size=9))
        self._tier_combo = QComboBox()
        self._tier_combo.addItems(TIER_OPTIONS)
        self._tier_combo.setFixedWidth(70)
        self._tier_combo.currentTextChanged.connect(self._on_tier_change)
        rotor_row.addWidget(self._tier_combo)

        rotor_row.addWidget(_label("Material", size=9))
        self._rotor_combo = QComboBox()
        self._rotor_combo.addItems(ROTOR_DISPLAY_NAMES)
        self._rotor_combo.setFixedWidth(240)
        self._rotor_combo.currentTextChanged.connect(lambda _: self._on_rotor_change())
        rotor_row.addWidget(self._rotor_combo)

        self._size_toggle = ToggleButton(["Small", "Normal", "Large", "Huge"],
                                          command=lambda _: self._on_rotor_change())
        self._size_toggle.set("Normal")
        rotor_row.addWidget(self._size_toggle)

        self._lbl_eff = _label("Eff: —", color="#4ade80", size=10)
        self._lbl_dur = _label("Dur: —", color=YELLOW, size=10)
        rotor_row.addWidget(self._lbl_eff)
        rotor_row.addWidget(self._lbl_dur)
        rotor_row.addStretch()
        shared_lay.addLayout(rotor_row)

        dynamo_row = QHBoxLayout()
        dynamo_row.setSpacing(8)
        dynamo_row.addWidget(_label("Dynamo Hatch Tier", size=9))
        self._dynamo_combo = QComboBox()
        self._dynamo_combo.addItems(DYNAMO_TIER_NAMES)
        self._dynamo_combo.setCurrentText("EV")
        self._dynamo_combo.setFixedWidth(100)
        self._dynamo_combo.currentTextChanged.connect(self._on_dynamo_tier_change)
        dynamo_row.addWidget(self._dynamo_combo)
        dynamo_row.addWidget(_label("— choose tier to see how many dynamo hatches needed",
                                    color="#4b5563", size=9))
        dynamo_row.addStretch()
        shared_lay.addLayout(dynamo_row)

        lay.addWidget(shared)

        # Large turbines collapsible
        self._large_btn = QPushButton("▼  Large Turbines")
        self._large_btn.setObjectName("collapse_btn")
        self._large_btn.clicked.connect(self._toggle_large)
        lay.addWidget(self._large_btn)

        self._large_widget = QWidget()
        grid = QGridLayout(self._large_widget)
        grid.setSpacing(8)
        self._steam_card  = RegularTurbineCard("steam",  "#3b82f6")
        self._gas_card    = RegularTurbineCard("gas",    "#f59e0b")
        self._plasma_card = RegularTurbineCard("plasma", "#a855f7")
        grid.addWidget(self._steam_card,  0, 0)
        grid.addWidget(self._gas_card,    0, 1)
        grid.addWidget(self._plasma_card, 0, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        lay.addWidget(self._large_widget)

        # XL turbines collapsible
        self._xl_btn = QPushButton("▶  XL Turbo Turbines  (click to expand)")
        self._xl_btn.setObjectName("collapse_btn")
        self._xl_btn.clicked.connect(self._toggle_xl)
        lay.addWidget(self._xl_btn)

        self._xl_widget = QWidget()
        xl_grid = QGridLayout(self._xl_widget)
        xl_grid.setSpacing(8)
        self._xl_steam  = XLTurbineCard("steam",  "#93c5fd")
        self._xl_gas    = XLTurbineCard("gas",    "#fcd34d")
        self._xl_plasma = XLTurbineCard("plasma", "#c084fc")
        xl_grid.addWidget(self._xl_steam,  0, 0)
        xl_grid.addWidget(self._xl_gas,    0, 1)
        xl_grid.addWidget(self._xl_plasma, 0, 2)
        xl_grid.setColumnStretch(0, 1)
        xl_grid.setColumnStretch(1, 1)
        xl_grid.setColumnStretch(2, 1)
        self._xl_widget.hide()
        lay.addWidget(self._xl_widget)

        lay.addStretch()
        self._on_rotor_change()

    def _toggle_large(self):
        if self._large_visible:
            self._large_widget.hide()
            self._large_btn.setText("▶  Large Turbines  (click to expand)")
            self._large_visible = False
        else:
            self._large_widget.show()
            self._large_btn.setText("▼  Large Turbines")
            self._large_visible = True

    def _toggle_xl(self):
        if self._xl_visible:
            self._xl_widget.hide()
            self._xl_btn.setText("▶  XL Turbo Turbines  (click to expand)")
            self._xl_visible = False
        else:
            self._xl_widget.show()
            self._xl_btn.setText("▼  XL Turbo Turbines")
            self._xl_visible = True

    def _on_tier_change(self, tier_str: str):
        names = _rotor_names_for_tier(tier_str)
        self._rotor_combo.blockSignals(True)
        self._rotor_combo.clear()
        self._rotor_combo.addItems(names)
        self._rotor_combo.blockSignals(False)
        self._on_rotor_change()

    def _on_dynamo_tier_change(self, tier: str):
        for card in [self._steam_card, self._gas_card, self._plasma_card,
                     self._xl_steam, self._xl_gas, self._xl_plasma]:
            card.set_dynamo_tier(tier)

    def _on_rotor_change(self, *_):
        name = self._rotor_combo.currentText()
        size = self._size_toggle.get()
        rotor = ROTOR_DATA.get(name, {})
        if not rotor:
            return
        blade_size = TURBINE_TO_ROTOR_SIZE.get(size, size)
        sd = rotor["sizes"][blade_size]
        dur = rotor["base_durability"] * sd["dur_mult"]
        self._lbl_eff.setText(f"Eff(tight): {sd['steam_tight_eff']*100:.1f}%")
        self._lbl_dur.setText(f"Dur: {dur:,}")
        dynamo_tier = self._dynamo_combo.currentText()
        for card in [self._steam_card, self._gas_card, self._plasma_card,
                     self._xl_steam, self._xl_gas, self._xl_plasma]:
            card.set_dynamo_tier(dynamo_tier)
            card.set_rotor(rotor, size)
