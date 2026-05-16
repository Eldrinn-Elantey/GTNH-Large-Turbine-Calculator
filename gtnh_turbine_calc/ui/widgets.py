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
    font-size: 12px;
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
    font-size: 12px;
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
    font-size: 12px;
}
QTableView {
    background: #0d1117;
    color: #d1d5db;
    border: none;
    gridline-color: #1f2937;
    font-size: 12px;
    selection-background-color: #1e40af;
    selection-color: #93c5fd;
}
QHeaderView::section {
    background: #1f2937;
    color: #9ca3af;
    border: none;
    padding: 4px 6px;
    font-size: 12px;
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
        lbl.setStyleSheet(f"color: {RESULT_LABEL_COLOR}; font-size: 12px;")
        lay.addWidget(lbl)
        lay.addStretch()

        self._value = QLabel("—")
        self._value.setStyleSheet(f"color: {value_color}; font-size: 12px; font-weight: bold;")
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
