# PySide6 Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate the GTNH Large Turbine Calculator UI from CustomTkinter to PySide6, preserving all functionality and keeping `calc/` and `data/` untouched.

**Architecture:** `QMainWindow` with a fixed 160px left sidebar (`QWidget`) and a `QStackedWidget` for tab content. Each tab is a `QWidget` subclass created lazily on first navigation. `QSS` dark theme loaded from a string constant in `app.py`. Tables use `QAbstractTableModel` + `QSortFilterProxyModel` + `QTableView`.

**Tech Stack:** PySide6 (Qt 6), Python 3.10+, existing `calc/` and `data/` modules untouched.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `gtnh_turbine_calc/main.py` | Modify | Create `QApplication`, call `app.run()` |
| `gtnh_turbine_calc/app.py` | Rewrite | `QMainWindow` + sidebar + `QStackedWidget` + QSS theme |
| `gtnh_turbine_calc/ui/widgets.py` | Rewrite | `ToggleButton`, `ResultRow`, `SearchableTableModel`, `SearchableTable` |
| `gtnh_turbine_calc/ui/calculator.py` | Rewrite | `CalculatorTab` (shared settings + 6 turbine cards) |
| `gtnh_turbine_calc/ui/ehe_planner.py` | Rewrite | `EHEPlannerTab` |
| `gtnh_turbine_calc/ui/fuels_ref.py` | Rewrite | `FuelsRefTab` with inner tab widget |
| `gtnh_turbine_calc/ui/rotors_ref.py` | Rewrite | `RotorsRefTab` with size toggle |
| `gtnh_turbine_calc/ui/steam_gen_tab.py` | Rewrite | `SteamGenTab` (scrollable static reference) |

`calc/`, `data/`, `tests/` — **DO NOT TOUCH**.

---

### Task 1: Rewrite `app.py` and `main.py`

**Files:**
- Modify: `gtnh_turbine_calc/main.py`
- Rewrite: `gtnh_turbine_calc/app.py`

- [ ] **Step 1: Verify tests still pass (baseline)**

```bash
cd C:\Users\Eldrinn_Elantey\GitHub\GTNH-Large-Turbine-Calculator
python -m pytest tests/ -q
```
Expected: all tests PASS.

- [ ] **Step 2: Rewrite `app.py`**

Replace entire file with:

```python
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
            # Force QSS re-evaluation after property change
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._stack.setCurrentWidget(self._get_or_create(key))
        self._current_tab = key


def run():
    app = QApplication(sys.argv)
    window = TurbineCalcApp()
    window.show()
    sys.exit(app.exec())
```

- [ ] **Step 3: Rewrite `main.py`**

```python
from gtnh_turbine_calc.app import run

if __name__ == "__main__":
    run()
```

- [ ] **Step 4: Temporarily stub all tabs so the window opens**

Create `gtnh_turbine_calc/ui/_stub.py`:
```python
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

def make_stub(name: str):
    class StubTab(QWidget):
        def __init__(self):
            super().__init__()
            lay = QVBoxLayout(self)
            lbl = QLabel(f"{name} — coming soon")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #9ca3af; font-size: 14px;")
            lay.addWidget(lbl)
    return StubTab
```

Then temporarily update each tab file to export a stub. For now, add these one-liners at the top of each broken tab file to make imports work (we'll replace them in later tasks). In `calculator.py`, `ehe_planner.py`, `steam_gen_tab.py`, `fuels_ref.py`, `rotors_ref.py` — replace entire contents temporarily with:

```python
# Temporary stub — will be replaced in later tasks
from gtnh_turbine_calc.ui._stub import make_stub
CalculatorTab  = make_stub("Calculator")   # use the correct class name per file
```

Class name mapping:
- `calculator.py` → `CalculatorTab`
- `ehe_planner.py` → `EHEPlannerTab`
- `steam_gen_tab.py` → `SteamGenTab`
- `fuels_ref.py` → `FuelsRefTab`
- `rotors_ref.py` → `RotorsRefTab`

- [ ] **Step 5: Verify the window opens**

```bash
python -m gtnh_turbine_calc.main
```
Expected: window appears with dark sidebar, 5 nav buttons, "coming soon" placeholders. Close it manually.

- [ ] **Step 6: Run tests**

```bash
python -m pytest tests/ -q
```
Expected: all PASS.

---

### Task 2: Rewrite `ui/widgets.py`

**Files:**
- Rewrite: `gtnh_turbine_calc/ui/widgets.py`

This file provides shared widgets used by all tabs. No tests needed — they are visual components. We verify by running the app after each tab is wired up.

- [ ] **Step 1: Rewrite `widgets.py`**

```python
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel,
    QLineEdit, QFrame, QTableView, QHeaderView, QAbstractItemView,
    QSizePolicy,
)
from PySide6.QtCore import (
    Qt, QSortFilterProxyModel, QAbstractTableModel, QModelIndex,
)
from PySide6.QtGui import QColor

CARD_BG           = "#111827"
RESULT_LABEL_COLOR = "#6b7280"
GREEN  = "#4ade80"
YELLOW = "#facc15"
PURPLE = "#c084fc"
ORANGE = "#fb923c"
CYAN   = "#00d4ff"

_WIDGET_QSS = """
QPushButton#toggle_btn {
    background: transparent;
    color: #6b7280;
    border: none;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 10px;
}
QPushButton#toggle_btn:hover { background: #374151; }
QPushButton#toggle_btn[selected="true"] {
    background: #1e40af;
    color: #93c5fd;
}
QComboBox {
    background: #1f2937;
    color: #00d4ff;
    border: 1px solid #374151;
    border-radius: 4px;
    padding: 3px 6px;
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
    padding: 3px 6px;
    font-size: 10px;
}
QTableView {
    background: #0d1117;
    color: #d1d5db;
    border: none;
    gridline-color: #1f2937;
    font-size: 10px;
    selection-background-color: #1e40af;
    selection-color: #93c5fd;
}
QHeaderView::section {
    background: #1f2937;
    color: #9ca3af;
    border: none;
    padding: 4px 6px;
    font-size: 10px;
    font-weight: bold;
}
QScrollBar:vertical {
    background: #111827;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #374151;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


class ToggleButton(QWidget):
    """Segmented button group: two or more mutually exclusive options."""

    def __init__(self, options: list[str], command=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_WIDGET_QSS)
        self._options = options
        self._command = command
        self._selected = options[0]
        self._buttons: dict[str, QPushButton] = {}

        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(2)

        container = QFrame()
        container.setStyleSheet("background: #1f2937; border-radius: 6px;")
        inner = QHBoxLayout(container)
        inner.setContentsMargins(2, 2, 2, 2)
        inner.setSpacing(2)

        for opt in options:
            btn = QPushButton(opt)
            btn.setObjectName("toggle_btn")
            btn.setProperty("selected", "false")
            btn.setFixedHeight(26)
            btn.setMinimumWidth(64)
            btn.clicked.connect(lambda checked=False, o=opt: self._select(o))
            inner.addWidget(btn)
            self._buttons[opt] = btn

        lay.addWidget(container)
        self._select(options[0], notify=False)

    def _select(self, opt: str, notify: bool = True):
        self._selected = opt
        for o, btn in self._buttons.items():
            val = "true" if o == opt else "false"
            btn.setProperty("selected", val)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        if notify and self._command:
            self._command(opt)

    def get(self) -> str:
        return self._selected

    def set(self, opt: str):
        self._select(opt, notify=False)


class ResultRow(QWidget):
    """One label=value row inside a turbine card."""

    def __init__(self, label: str, value_color: str = GREEN, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {RESULT_LABEL_COLOR}; font-size: 11px;")
        lay.addWidget(lbl)
        lay.addStretch()

        self._value = QLabel("—")
        self._value.setStyleSheet(f"color: {value_color}; font-size: 11px; font-weight: bold;")
        self._value.setAlignment(Qt.AlignmentFlag.AlignRight)
        lay.addWidget(self._value)

    def set(self, text: str):
        self._value.setText(text)


class _TableModel(QAbstractTableModel):
    def __init__(self, columns: list[str], parent=None):
        super().__init__(parent)
        self._columns = columns
        self._rows: list[list[str]] = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._columns)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            return self._rows[index.row()][index.column()]
        if role == Qt.ItemDataRole.ForegroundRole:
            return QColor("#d1d5db")
        if role == Qt.ItemDataRole.BackgroundRole:
            return QColor("#0d1117")
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._columns[section]
        return None

    def load(self, rows: list[list[str]]):
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()


class SearchableTable(QWidget):
    """Search bar + sortable table backed by QTableView."""

    def __init__(self, columns: list[tuple[str, int]], parent=None):
        super().__init__(parent)
        self.setStyleSheet(_WIDGET_QSS)
        col_names = [c[0] for c in columns]
        col_widths = [c[1] for c in columns]
        self._all_rows: list[list[str]] = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Search bar
        search_bar = QWidget()
        search_bar.setStyleSheet("background: #111827;")
        sb_lay = QHBoxLayout(search_bar)
        sb_lay.setContentsMargins(10, 6, 10, 6)
        sb_lay.setSpacing(6)
        icon = QLabel("🔍")
        icon.setStyleSheet("font-size: 12px; background: transparent;")
        sb_lay.addWidget(icon)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search...")
        self._search.setFixedHeight(32)
        self._search.textChanged.connect(self._on_search)
        sb_lay.addWidget(self._search)
        lay.addWidget(search_bar)

        # Model + proxy
        self._model = _TableModel(col_names)
        self._proxy = QSortFilterProxyModel()
        self._proxy.setSourceModel(self._model)
        self._proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy.setFilterKeyColumn(-1)  # search all columns

        # Table view
        self._view = QTableView()
        self._view.setModel(self._proxy)
        self._view.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._view.horizontalHeader().setStretchLastSection(True)
        self._view.verticalHeader().setVisible(False)
        self._view.setSortingEnabled(True)
        self._view.setShowGrid(False)
        self._view.setAlternatingRowColors(False)
        for i, w in enumerate(col_widths):
            self._view.setColumnWidth(i, w)
        lay.addWidget(self._view)

    def load(self, rows: list[list[str]]):
        self._all_rows = rows
        self._model.load(rows)

    def _on_search(self, text: str):
        self._proxy.setFilterFixedString(text)
```

- [ ] **Step 2: Run tests**

```bash
python -m pytest tests/ -q
```
Expected: all PASS (widgets.py has no test coverage needed — pure UI).

---

### Task 3: Rewrite `ui/calculator.py`

**Files:**
- Rewrite: `gtnh_turbine_calc/ui/calculator.py`

- [ ] **Step 1: Rewrite `calculator.py`**

```python
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
```

- [ ] **Step 2: Verify window opens with functional Calculator tab**

```bash
python -m gtnh_turbine_calc.main
```
Expected: Calculator tab shows shared settings + 3 Large cards with results updating on changes.

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/ -q
```
Expected: all PASS.

---

### Task 4: Rewrite `ui/ehe_planner.py`

**Files:**
- Rewrite: `gtnh_turbine_calc/ui/ehe_planner.py`

- [ ] **Step 1: Rewrite `ehe_planner.py`**

```python
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
```

- [ ] **Step 2: Verify EHE tab works**

```bash
python -m gtnh_turbine_calc.main
```
Expected: EHE Planner tab shows two cards with results.

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/ -q
```

---

### Task 5: Rewrite `ui/fuels_ref.py`

**Files:**
- Rewrite: `gtnh_turbine_calc/ui/fuels_ref.py`

- [ ] **Step 1: Rewrite `fuels_ref.py`**

```python
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
```

- [ ] **Step 2: Verify Fuels tab works**

```bash
python -m gtnh_turbine_calc.main
```
Expected: Fuels tab shows Steam/Gas/Plasma sub-tabs with searchable tables.

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/ -q
```

---

### Task 6: Rewrite `ui/rotors_ref.py`

**Files:**
- Rewrite: `gtnh_turbine_calc/ui/rotors_ref.py`

- [ ] **Step 1: Rewrite `rotors_ref.py`**

```python
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
        sb_lay.addWidget(QLabel("Blade size:"))
        size_bar.findChildren(QLabel)[0].setStyleSheet("color: #9ca3af; font-size: 10px; background: transparent;")
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
```

- [ ] **Step 2: Verify Rotors tab works**

```bash
python -m gtnh_turbine_calc.main
```
Expected: Rotors tab shows size toggle + 9-column searchable/sortable table, durability updates when size changes.

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/ -q
```

---

### Task 7: Rewrite `ui/steam_gen_tab.py`

**Files:**
- Rewrite: `gtnh_turbine_calc/ui/steam_gen_tab.py`

- [ ] **Step 1: Rewrite `steam_gen_tab.py`**

```python
from PySide6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame,
)
from PySide6.QtCore import Qt

from gtnh_turbine_calc.data.steam_gen import LHE_SOURCES, WWXL_SOURCES, THERMAL_BOILER_SOURCES

_STEAM_QSS = """
QWidget { background: #0d1117; }
QFrame#card { background: #111827; border-radius: 8px; }
QFrame#row_frame { background: #1f2937; border-radius: 4px; }
QFrame#hdr_frame { background: #374151; border-radius: 4px; }
QScrollArea { background: #0d1117; border: none; }
"""


def _data_label(text: str, width: int) -> QLabel:
    lbl = QLabel(text)
    lbl.setFixedWidth(width)
    lbl.setStyleSheet("color: #d1d5db; font-size: 10px; background: transparent;")
    return lbl


def _hdr_label(text: str, width: int) -> QLabel:
    lbl = QLabel(text)
    lbl.setFixedWidth(width)
    lbl.setStyleSheet("color: #9ca3af; font-size: 9px; font-weight: bold; background: transparent;")
    return lbl


def _steam_row(parent_lay, name: str, data: dict, is_thermal: bool = False):
    row = QFrame()
    row.setObjectName("row_frame")
    row.setFixedHeight(28)
    rlay = QHBoxLayout(row)
    rlay.setContentsMargins(4, 0, 4, 0)
    rlay.setSpacing(0)
    if is_thermal:
        cols = [
            (name,                    160),
            (f"{data['max_ls']:,} L/s", 100),
            (data["steam"],             80),
            (f"x{data['ratio']}",       60),
        ]
    else:
        cols = [
            (name,                          160),
            (f"{data['threshold_ls']:,}",    100),
            (f"{data['max_ls']:,}",          100),
            (data["below"],                   70),
            (data["above"],                   80),
            (f"x{data['ratio_below']}",       60),
            (f"x{data['ratio_above']}",       60),
        ]
    for text, width in cols:
        rlay.addWidget(_data_label(text, width))
    parent_lay.addWidget(row)


def _section(parent_lay, title: str, color: str, headers: list, sources: list, is_thermal: bool = False):
    card = QFrame()
    card.setObjectName("card")
    lay = QVBoxLayout(card)
    lay.setContentsMargins(0, 0, 0, 6)
    lay.setSpacing(0)

    strip = QFrame()
    strip.setFixedHeight(3)
    strip.setStyleSheet(f"background: {color};")
    lay.addWidget(strip)

    title_lbl = QLabel(title)
    title_lbl.setContentsMargins(10, 8, 10, 4)
    title_lbl.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: bold; background: transparent;")
    lay.addWidget(title_lbl)

    inner = QWidget()
    inner_lay = QVBoxLayout(inner)
    inner_lay.setContentsMargins(10, 0, 10, 0)
    inner_lay.setSpacing(2)

    hdr = QFrame()
    hdr.setObjectName("hdr_frame")
    hdr.setFixedHeight(26)
    hdr_lay = QHBoxLayout(hdr)
    hdr_lay.setContentsMargins(4, 0, 4, 0)
    hdr_lay.setSpacing(0)
    for text, width in headers:
        hdr_lay.addWidget(_hdr_label(text, width))
    inner_lay.addWidget(hdr)

    for src in sources:
        _steam_row(inner_lay, src["name"], src, is_thermal)

    lay.addWidget(inner)
    parent_lay.addWidget(card)


class SteamGenTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_STEAM_QSS)
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
        lay.setSpacing(6)

        title = QLabel("Steam Generation Reference")
        title.setStyleSheet("color: #e94560; font-size: 14px; font-weight: bold; background: transparent;")
        lay.addWidget(title)

        sub = QLabel("All flows in L/s. Steam output = input x ratio.")
        sub.setStyleSheet("color: #6b7280; font-size: 10px; background: transparent;")
        lay.addWidget(sub)

        lhe_hdrs = [
            ("Source", 160), ("Threshold L/s", 100), ("Max L/s", 100),
            ("Below thr.", 70), ("Above thr.", 80), ("Ratio below", 60), ("Ratio above", 60),
        ]
        _section(lay, "Large Heat Exchanger (LHE)", "#3b82f6", lhe_hdrs, LHE_SOURCES)
        _section(lay, "Whakawhiti Wera XL (WWXL)", "#60a5fa", lhe_hdrs, WWXL_SOURCES)

        th_hdrs = [("Source", 160), ("Max L/s", 100), ("Steam Type", 80), ("Ratio", 60)]
        _section(lay, "Thermal Boiler", "#f59e0b", th_hdrs, THERMAL_BOILER_SOURCES, is_thermal=True)

        lay.addStretch()
```

- [ ] **Step 2: Verify Steam Gen tab works**

```bash
python -m gtnh_turbine_calc.main
```
Expected: Steam Gen tab shows 3 reference sections with correct data rows.

- [ ] **Step 3: Run tests**

```bash
python -m pytest tests/ -q
```

---

### Task 8: Cleanup — remove stub files and CTk dependencies

**Files:**
- Delete: `gtnh_turbine_calc/ui/_stub.py`
- Verify: no `customtkinter` imports remain

- [ ] **Step 1: Delete stub file**

```bash
del "C:\Users\Eldrinn_Elantey\GitHub\GTNH-Large-Turbine-Calculator\gtnh_turbine_calc\ui\_stub.py"
```

- [ ] **Step 2: Confirm no CTk imports remain**

```bash
grep -r "customtkinter" gtnh_turbine_calc/
```
Expected: no output.

- [ ] **Step 3: Full smoke test**

```bash
python -m gtnh_turbine_calc.main
```
Navigate all 5 tabs. Expected: all tabs render correctly, no errors in terminal.

- [ ] **Step 4: Final test run**

```bash
python -m pytest tests/ -q
```
Expected: all PASS.
