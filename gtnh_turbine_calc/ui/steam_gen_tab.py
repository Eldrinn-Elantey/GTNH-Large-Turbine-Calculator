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
