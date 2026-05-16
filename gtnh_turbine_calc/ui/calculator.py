import math
from PySide6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QFrame, QCheckBox,
    QTabWidget, QSizePolicy,
)
from PySide6.QtCore import Qt

from gtnh_turbine_calc.data.rotors import ROTOR_DATA, ROTOR_DISPLAY_NAMES
from gtnh_turbine_calc.data.fuels import (
    STEAM_FUELS, GAS_FUELS, GAS_FUEL_NAMES, PLASMA_FUELS, PLASMA_FUEL_NAMES,
)
from gtnh_turbine_calc.calc.turbine import (
    calc_regular_turbine, calc_xl_turbine, TURBINE_TO_ROTOR_SIZE, _TURBINE_TO_DUR_SIZE,
)
from gtnh_turbine_calc.calc.common import DYNAMO_TIERS
from gtnh_turbine_calc.ui.widgets import ResultRow, ToggleButton, YELLOW, GREEN, PURPLE, ORANGE

CARD_BG = "#111827"
DYNAMO_TIER_NAMES = [name for name, _ in DYNAMO_TIERS]
DYNAMO_VOLTAGE = dict(DYNAMO_TIERS)
_ALL_TIERS = sorted({v["tier"] for v in ROTOR_DATA.values()})
TIER_OPTIONS = ["All"] + [str(t) for t in _ALL_TIERS]

_CALC_QSS = """
QWidget { background: #0d1117; }
QFrame#card { background: #111827; border-radius: 8px; }
QFrame#shared { background: #111827; border-radius: 8px; }
QTabWidget::pane { background: #0d1117; border: none; }
QTabBar::tab {
    background: #111827;
    color: #9ca3af;
    padding: 8px 20px;
    border: none;
    font-size: 13px;
}
QTabBar::tab:selected { background: #1e40af; color: #93c5fd; }
QTabBar::tab:hover { background: #1f2937; }
QComboBox {
    background: #1f2937;
    color: #00d4ff;
    border: 1px solid #374151;
    border-radius: 4px;
    padding: 3px 6px;
    font-size: 12px;
}
QComboBox::drop-down { border: none; width: 18px; }
QComboBox QAbstractItemView {
    background: #1f2937;
    color: #d1d5db;
    border: 1px solid #374151;
    selection-background-color: #1e40af;
    font-size: 12px;
}
QLineEdit {
    background: #1f2937;
    color: #d1d5db;
    border: 1px solid #374151;
    border-radius: 4px;
    padding: 3px 6px;
    font-size: 12px;
}
QCheckBox { color: #9ca3af; font-size: 12px; background: transparent; }
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


def _label(text: str, color: str = "#6b7280", size: int = 11, bold: bool = False, parent=None) -> QLabel:
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
                           color=self._accent, size=13, bold=True)
        title_lbl.setContentsMargins(10, 8, 10, 4)
        lay.addWidget(title_lbl)

        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(10, 2, 10, 0)
        inner_lay.setSpacing(4)

        # Mode toggle
        mode_row = QHBoxLayout()
        mode_row.addWidget(_label("Mode"))
        self._mode_toggle = ToggleButton(["Tight", "Loose"], command=self._recalc)
        mode_row.addWidget(self._mode_toggle)
        mode_row.addStretch()
        inner_lay.addLayout(mode_row)

        # Fuel combo
        fuel_row = QHBoxLayout()
        fuel_row.addWidget(_label("Fuel"))
        fuel_names = {"steam": list(STEAM_FUELS), "gas": GAS_FUEL_NAMES, "plasma": PLASMA_FUEL_NAMES}
        self._fuel_combo = QComboBox()
        self._fuel_combo.addItems(fuel_names[self._type])
        self._fuel_combo.setFixedWidth(180)
        self._fuel_combo.currentTextChanged.connect(self._recalc)
        fuel_row.addWidget(self._fuel_combo)
        fuel_row.addStretch()
        inner_lay.addLayout(fuel_row)

        # Flow toggle
        flow_row = QHBoxLayout()
        flow_row.addWidget(_label("Flow"))
        self._flow_toggle = ToggleButton(["Optimal", "Manual"], command=self._on_flow_mode)
        flow_row.addWidget(self._flow_toggle)
        flow_row.addStretch()
        inner_lay.addLayout(flow_row)

        # Manual entry (hidden initially)
        self._manual_entry = QLineEdit()
        self._manual_entry.setPlaceholderText("L/t or L/s")
        self._manual_entry.setFixedWidth(110)
        self._manual_entry.setFixedHeight(28)
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

        inner_lay.addSpacing(8)
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
        # XL always uses "Normal" rotor size internally (TURBINE_TO_ROTOR_SIZE["XL"] = "Normal")
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
        title_lbl = _label(titles[self._type], color=self._accent, size=12, bold=True)
        title_lbl.setContentsMargins(10, 8, 10, 4)
        lay.addWidget(title_lbl)

        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(10, 2, 10, 0)
        inner_lay.setSpacing(4)

        mode_row = QHBoxLayout()
        mode_row.addWidget(_label("Mode"))
        self._mode_toggle = ToggleButton(["Tight", "Loose"], command=self._recalc)
        mode_row.addWidget(self._mode_toggle)
        mode_row.addStretch()
        inner_lay.addLayout(mode_row)

        fuel_row = QHBoxLayout()
        fuel_row.addWidget(_label("Fuel"))
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
        self._fuel_combo.setFixedWidth(160)
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

        inner_lay.addSpacing(8)
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


def _make_scroll_page() -> tuple[QScrollArea, QVBoxLayout]:
    """Returns (scroll_area, content_layout) — wrap content_layout with widgets."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    content = QWidget()
    scroll.setWidget(content)
    lay = QVBoxLayout(content)
    lay.setContentsMargins(16, 16, 16, 16)
    lay.setSpacing(8)
    return scroll, lay


def _shared_settings_frame(
    tier_combo_out: list,
    rotor_combo_out: list,
    dynamo_combo_out: list,
    lbl_eff_out: list,
    lbl_dur_out: list,
    show_size: bool = True,
    size_toggle_out: list = None,
) -> QFrame:
    """Build the shared settings card. Outputs widget refs via single-element lists."""
    shared = QFrame()
    shared.setObjectName("shared")
    shared_lay = QVBoxLayout(shared)
    shared_lay.setContentsMargins(12, 10, 12, 10)
    shared_lay.setSpacing(8)
    shared_lay.addWidget(_label("SHARED SETTINGS", size=10))

    rotor_row = QHBoxLayout()
    rotor_row.setSpacing(10)

    rotor_row.addWidget(_label("Tier"))
    tier_combo = QComboBox()
    tier_combo.addItems(TIER_OPTIONS)
    tier_combo.setFixedWidth(80)
    rotor_row.addWidget(tier_combo)
    tier_combo_out.append(tier_combo)

    rotor_row.addWidget(_label("Material"))
    rotor_combo = QComboBox()
    rotor_combo.addItems(ROTOR_DISPLAY_NAMES)
    rotor_combo.setFixedWidth(260)
    rotor_row.addWidget(rotor_combo)
    rotor_combo_out.append(rotor_combo)

    if show_size and size_toggle_out is not None:
        size_toggle = ToggleButton(["Small", "Normal", "Large", "Huge"])
        size_toggle.set("Normal")
        rotor_row.addWidget(size_toggle)
        size_toggle_out.append(size_toggle)

    lbl_eff = _label("Eff: —", color="#4ade80", size=12)
    lbl_dur = _label("Dur: —", color=YELLOW, size=12)
    rotor_row.addWidget(lbl_eff)
    rotor_row.addWidget(lbl_dur)
    rotor_row.addStretch()
    shared_lay.addLayout(rotor_row)
    lbl_eff_out.append(lbl_eff)
    lbl_dur_out.append(lbl_dur)

    dynamo_row = QHBoxLayout()
    dynamo_row.setSpacing(10)
    dynamo_row.addWidget(_label("Dynamo Hatch Tier"))
    dynamo_combo = QComboBox()
    dynamo_combo.addItems(DYNAMO_TIER_NAMES)
    dynamo_combo.setCurrentText("EV")
    dynamo_combo.setFixedWidth(110)
    dynamo_row.addWidget(dynamo_combo)
    dynamo_row.addWidget(_label("— how many dynamo hatches needed", color="#4b5563", size=11))
    dynamo_row.addStretch()
    shared_lay.addLayout(dynamo_row)
    dynamo_combo_out.append(dynamo_combo)

    return shared


class LargeTurbinesTab(QWidget):
    """Tab for Large (non-XL) turbines: Steam, Gas, Plasma."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        scroll, lay = _make_scroll_page()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # Shared settings
        _tier_combo, _rotor_combo, _dynamo_combo = [], [], []
        _lbl_eff, _lbl_dur, _size_toggle = [], [], []
        shared = _shared_settings_frame(
            _tier_combo, _rotor_combo, _dynamo_combo,
            _lbl_eff, _lbl_dur,
            show_size=True, size_toggle_out=_size_toggle,
        )
        self._tier_combo   = _tier_combo[0]
        self._rotor_combo  = _rotor_combo[0]
        self._dynamo_combo = _dynamo_combo[0]
        self._lbl_eff      = _lbl_eff[0]
        self._lbl_dur      = _lbl_dur[0]
        self._size_toggle  = _size_toggle[0]
        lay.addWidget(shared)

        # 3 turbine cards
        grid = QGridLayout()
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
        lay.addLayout(grid)
        lay.addStretch()

        # Wire signals
        self._tier_combo.currentTextChanged.connect(self._on_tier_change)
        self._rotor_combo.currentTextChanged.connect(lambda _: self._on_rotor_change())
        self._size_toggle._command = lambda _: self._on_rotor_change()
        self._dynamo_combo.currentTextChanged.connect(self._on_dynamo_change)

        self._on_rotor_change()

    def _on_tier_change(self, tier_str: str):
        names = _rotor_names_for_tier(tier_str)
        self._rotor_combo.blockSignals(True)
        self._rotor_combo.clear()
        self._rotor_combo.addItems(names)
        self._rotor_combo.blockSignals(False)
        self._on_rotor_change()

    def _on_dynamo_change(self, tier: str):
        for card in [self._steam_card, self._gas_card, self._plasma_card]:
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
        for card in [self._steam_card, self._gas_card, self._plasma_card]:
            card.set_dynamo_tier(dynamo_tier)
            card.set_rotor(rotor, size)


class XLTurbinesTab(QWidget):
    """Tab for XL Turbo turbines — all 4 rotor sizes supported."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        scroll, lay = _make_scroll_page()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # Shared settings — with size toggle
        _tier_combo, _rotor_combo, _dynamo_combo = [], [], []
        _lbl_eff, _lbl_dur, _size_toggle = [], [], []
        shared = _shared_settings_frame(
            _tier_combo, _rotor_combo, _dynamo_combo,
            _lbl_eff, _lbl_dur,
            show_size=True, size_toggle_out=_size_toggle,
        )
        self._tier_combo   = _tier_combo[0]
        self._rotor_combo  = _rotor_combo[0]
        self._dynamo_combo = _dynamo_combo[0]
        self._lbl_eff      = _lbl_eff[0]
        self._lbl_dur      = _lbl_dur[0]
        self._size_toggle  = _size_toggle[0]
        lay.addWidget(shared)

        # 3 XL cards
        grid = QGridLayout()
        grid.setSpacing(8)
        self._xl_steam  = XLTurbineCard("steam",  "#93c5fd")
        self._xl_gas    = XLTurbineCard("gas",    "#fcd34d")
        self._xl_plasma = XLTurbineCard("plasma", "#c084fc")
        grid.addWidget(self._xl_steam,  0, 0)
        grid.addWidget(self._xl_gas,    0, 1)
        grid.addWidget(self._xl_plasma, 0, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        lay.addLayout(grid)
        lay.addStretch()

        # Wire signals
        self._tier_combo.currentTextChanged.connect(self._on_tier_change)
        self._rotor_combo.currentTextChanged.connect(lambda _: self._on_rotor_change())
        self._size_toggle._command = lambda _: self._on_rotor_change()
        self._dynamo_combo.currentTextChanged.connect(self._on_dynamo_change)

        self._on_rotor_change()

    def _on_tier_change(self, tier_str: str):
        names = _rotor_names_for_tier(tier_str)
        self._rotor_combo.blockSignals(True)
        self._rotor_combo.clear()
        self._rotor_combo.addItems(names)
        self._rotor_combo.blockSignals(False)
        self._on_rotor_change()

    def _on_dynamo_change(self, tier: str):
        for card in [self._xl_steam, self._xl_gas, self._xl_plasma]:
            card.set_dynamo_tier(tier)

    def _on_rotor_change(self, *_):
        name = self._rotor_combo.currentText()
        size = self._size_toggle.get()
        rotor = ROTOR_DATA.get(name, {})
        if not rotor:
            return
        blade_size = TURBINE_TO_ROTOR_SIZE.get(size, size)
        sd = rotor["sizes"][blade_size]
        dur = rotor["base_durability"] * rotor["sizes"][_TURBINE_TO_DUR_SIZE.get(size, size)]["dur_mult"]
        self._lbl_eff.setText(f"Eff(tight): {sd['steam_tight_eff']*100:.1f}%")
        self._lbl_dur.setText(f"Dur: {dur:,}")
        dynamo_tier = self._dynamo_combo.currentText()
        for card in [self._xl_steam, self._xl_gas, self._xl_plasma]:
            card.set_dynamo_tier(dynamo_tier)
            card.set_rotor(rotor, size)


class CalculatorTab(QWidget):
    """Top-level Calculator tab — sub-tabs for Large and XL turbines."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_CALC_QSS)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        tabs = QTabWidget()
        tabs.addTab(LargeTurbinesTab(), "⚡  Large Turbines")
        tabs.addTab(XLTurbinesTab(),   "⚡  XL Turbo Turbines")
        lay.addWidget(tabs)
