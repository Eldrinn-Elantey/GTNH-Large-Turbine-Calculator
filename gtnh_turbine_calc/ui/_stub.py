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
