"""
Compare Google Sheets calculator (ground truth) vs JS calcRegularTurbine (web/js/calc.js).

Each test case:
  1. Writes inputs to the Calculator sheet
  2. Waits for Sheets to recalculate
  3. Reads outputs (opt flow, EU/t, rotor lifetime)
  4. Runs calc_runner.mjs via Node.js with the same inputs
  5. Asserts values match within tolerance; prints diff on failure
"""
import re
import json
import subprocess
import sys
import os
import time
import pytest
import gspread
from google.oauth2.service_account import Credentials

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tests.sheets_config import SPREADSHEET_ID, CREDENTIALS_FILE

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
RECALC_DELAY = 3  # seconds to wait after writing before reading

RUNNER = os.path.join(os.path.dirname(__file__), "..", "web", "js", "calc_runner.mjs")
DATA_VERSION = "2.7"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_flow(raw: str) -> int:
    """Parse sheet flow cell like '1,200 (EV)' or '13 (LV)' → int."""
    m = re.match(r"[\d,]+", str(raw).replace(" ", ""))
    if not m:
        raise ValueError(f"Cannot parse flow: {raw!r}")
    return int(m.group().replace(",", ""))


def _parse_float(raw) -> float:
    return float(str(raw).replace(",", ""))


def _run_js(turbine_type: str, rotor_name: str, size: str, mode: str, fuel_type: str) -> dict:
    result = subprocess.run(
        ["node", RUNNER, turbine_type, rotor_name, size, mode, fuel_type, DATA_VERSION],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"JS runner failed: {result.stderr}")
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ws():
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    return sh.worksheet("Calculator")


def _set_inputs(ws, rotor_name: str, size: str, mode: str, fuel_type: str, turbine: str):
    ws.update(values=[[rotor_name]], range_name="C4")
    ws.update(values=[[size]],       range_name="C5")
    if turbine == "steam":
        ws.update(values=[[mode]],      range_name="H4")
        ws.update(values=[[fuel_type]], range_name="H5")
        ws.update(values=[["Optimal"]], range_name="H9")  # ensure effective = optimal
    elif turbine == "gas":
        ws.update(values=[[mode]],      range_name="L4")
        ws.update(values=[[fuel_type]], range_name="L5")
        ws.update(values=[["Optimal"]], range_name="L9")
    else:
        ws.update(values=[[mode]],      range_name="P4")
        ws.update(values=[[fuel_type]], range_name="P5")
        ws.update(values=[["Optimal"]], range_name="P9")
    time.sleep(RECALC_DELAY)


def _read_sheet(ws, turbine: str) -> dict:
    if turbine == "steam":
        flow_raw = ws.acell("H6").value
        eut_raw  = ws.acell("H7").value
        days_raw = ws.acell("H13").value
    elif turbine == "gas":
        flow_raw = ws.acell("L6").value
        eut_raw  = ws.acell("L7").value
        days_raw = ws.acell("L13").value
    else:
        flow_raw = ws.acell("P6").value
        eut_raw  = ws.acell("P7").value
        days_raw = ws.acell("P13").value
    return {
        "opt_flow":      _parse_flow(flow_raw),
        "opt_eut":       int(_parse_float(eut_raw)),
        "lifetime_days": _parse_float(days_raw),
    }


def _compare(label: str, sheet: dict, js: dict):
    sheet_lifetime_s = sheet["lifetime_days"] * 86400
    # Sheet displays lifetime rounded to 0.01 days = 864s — use that as tolerance.
    LIFETIME_TOL = 864
    diffs = []
    if sheet["opt_flow"] != int(js["optFlow"]):
        diffs.append(f"  opt_flow:  sheets={sheet['opt_flow']}  js={js['optFlow']}")
    if sheet["opt_eut"] != js["optOutput"]:
        diffs.append(f"  opt_eut:   sheets={sheet['opt_eut']}  js={js['optOutput']}")
    if abs(sheet_lifetime_s - js["lifetime"]) > LIFETIME_TOL:
        diffs.append(f"  lifetime:  sheets={sheet_lifetime_s:.0f}s  js={js['lifetime']:.0f}s"
                     f"  (sheets={sheet['lifetime_days']:.4f}d)")
    assert not diffs, f"[{label}]\n" + "\n".join(diffs)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

STEAM_CASES = [
    ("Energetic Alloy (3)", "Normal", "Tight", "Steam"),
    ("Energetic Alloy (3)", "Normal", "Loose", "Steam"),
    ("Energetic Alloy (3)", "Normal", "Tight", "SH Steam"),
    ("Energetic Alloy (3)", "Normal", "Tight", "SC Steam"),
    ("Energetic Alloy (3)", "Small",  "Tight", "Steam"),
    ("Energetic Alloy (3)", "Large",  "Tight", "Steam"),
    ("Energetic Alloy (3)", "Huge",   "Tight", "Steam"),
]

GAS_CASES = [
    ("Energetic Alloy (3)", "Normal", "Tight", "Benzene"),
    ("Energetic Alloy (3)", "Normal", "Loose", "Benzene"),
    ("Energetic Alloy (3)", "Normal", "Tight", "Nitrobenzene"),
]

PLASMA_CASES = [
    ("Energetic Alloy (3)", "Normal", "Tight", "Helium Plasma"),
    ("Energetic Alloy (3)", "Normal", "Loose", "Helium Plasma"),
]


@pytest.mark.parametrize("rotor_name,size,mode,fuel_type", STEAM_CASES)
def test_steam(ws, rotor_name, size, mode, fuel_type):
    _set_inputs(ws, rotor_name, size, mode, fuel_type, "steam")
    sheet = _read_sheet(ws, "steam")
    js    = _run_js("steam", rotor_name, size, mode, fuel_type)
    _compare(f"{rotor_name} | {size} | {mode} | {fuel_type}", sheet, js)


@pytest.mark.parametrize("rotor_name,size,mode,fuel_type", GAS_CASES)
def test_gas(ws, rotor_name, size, mode, fuel_type):
    _set_inputs(ws, rotor_name, size, mode, fuel_type, "gas")
    sheet = _read_sheet(ws, "gas")
    js    = _run_js("gas", rotor_name, size, mode, fuel_type)
    _compare(f"{rotor_name} | {size} | {mode} | {fuel_type}", sheet, js)


@pytest.mark.parametrize("rotor_name,size,mode,fuel_type", PLASMA_CASES)
def test_plasma(ws, rotor_name, size, mode, fuel_type):
    _set_inputs(ws, rotor_name, size, mode, fuel_type, "plasma")
    sheet = _read_sheet(ws, "plasma")
    js    = _run_js("plasma", rotor_name, size, mode, fuel_type)
    _compare(f"{rotor_name} | {size} | {mode} | {fuel_type}", sheet, js)
