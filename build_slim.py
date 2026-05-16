"""Run PyInstaller with slimmed PySide6 — exclude unused Qt modules."""
import subprocess, sys

excludes = [
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngine",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets",
    "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic", "PySide6.Qt3DAnimation", "PySide6.Qt3DExtras",
    "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.QtQuick", "PySide6.QtQuickWidgets", "PySide6.QtQml",
    "PySide6.QtBluetooth", "PySide6.QtNfc", "PySide6.QtPositioning",
    "PySide6.QtLocation", "PySide6.QtSensors", "PySide6.QtSerialPort",
    "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtXml",
    "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets",
    "PySide6.QtPdf", "PySide6.QtPdfWidgets",
    "PySide6.QtSvg", "PySide6.QtSvgWidgets",
    "matplotlib", "numpy", "tkinter", "customtkinter",
]

args = [
    sys.executable, "-m", "PyInstaller",
    "--onefile", "--windowed",
    "--name", "GTNH-Turbine-Calc",
    "--clean",
]
for mod in excludes:
    args += ["--exclude-module", mod]
args.append("gtnh_turbine_calc/main.py")

subprocess.run(args, check=True)
