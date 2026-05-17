"""Extract rotor and fuel data from GT5-Unofficial Java sources.

Usage:
    python scripts/extract_from_java.py --gt5 <path>              # print counts
    python scripts/extract_from_java.py --gt5 <path> --rotors     # print rotor dict
    python scripts/extract_from_java.py --gt5 <path> --fuels      # print fuel dicts
    python scripts/extract_from_java.py --gt5 <path> --compare    # diff vs current data
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.rotor_parser import parse_gt_materials, parse_werkstoff_materials
from scripts.fuel_parser import parse_gas_fuels, parse_plasma_fuels
from scripts.turbine_formulas import compute_rotor_sizes, compute_overflow_tier


def build_rotor_data(gt5_src: str) -> dict:
    gt_mats = parse_gt_materials(gt5_src)
    wk_mats = parse_werkstoff_materials(gt5_src)
    all_mats = {**gt_mats, **wk_mats}

    rotor_data = {}
    for name, props in all_mats.items():
        qual  = props["tool_quality"]
        speed = props["tool_speed"]
        dur   = props["tool_durability"]
        rotor_name = f"{name} ({qual})"

        rotor_data[rotor_name] = {
            "tier":            qual,
            "mining_speed":    speed,
            "base_durability": dur * 100,
            "overflow_tier":   compute_overflow_tier(qual),
            "sizes":           compute_rotor_sizes(
                tool_quality=qual,
                tool_speed=speed,
                steam_mult=props["steam_mult"],
                gas_mult=props["gas_mult"],
                plasma_mult=props["plasma_mult"],
            ),
        }
    return rotor_data


def build_fuel_data(gt5_src: str) -> tuple:
    gas    = parse_gas_fuels(gt5_src)
    plasma = parse_plasma_fuels(gt5_src)
    return gas, plasma


def compare_rotors(java_data: dict, current_data: dict) -> None:
    java_keys    = set(java_data)
    current_keys = set(current_data)
    new_in_java      = java_keys - current_keys
    missing_in_java  = current_keys - java_keys
    common           = java_keys & current_keys

    print(f"\n=== ROTOR COMPARISON ===")
    print(f"Java: {len(java_keys)}  Current: {len(current_keys)}  Common: {len(common)}")

    if new_in_java:
        print(f"\nNew in Java ({len(new_in_java)}):")
        for n in sorted(new_in_java): print(f"  + {n}")

    if missing_in_java:
        print(f"\nMissing from Java ({len(missing_in_java)}):")
        for n in sorted(missing_in_java): print(f"  - {n}")

    print(f"\nStat diffs (steam_tight_eff Small, >5% delta):")
    diffs = []
    for name in sorted(common):
        j_eff = java_data[name]["sizes"]["Small"]["steam_tight_eff"]
        c_eff = current_data[name]["sizes"]["Small"]["steam_tight_eff"]
        if c_eff and abs(j_eff - c_eff) / max(abs(c_eff), 1e-9) > 0.05:
            diffs.append((name, c_eff, j_eff))
    if diffs:
        for name, c, j in diffs:
            print(f"  {name}: current={c:.4f}  java={j:.4f}")
    else:
        print("  (none)")


def compare_fuels(java_gas: dict, java_plasma: dict,
                  current_gas: dict, current_plasma: dict) -> None:
    print(f"\n=== GAS FUEL COMPARISON ===")
    print(f"Java: {len(java_gas)}  Current: {len(current_gas)}")
    all_gas = sorted(set(current_gas) | set(java_gas))
    for name in all_gas:
        j = java_gas.get(name, {}).get("eu_per_l")
        c = current_gas.get(name, {}).get("eu_per_l")
        if j != c:
            print(f"  {name}: current={c}  java={j}")

    print(f"\n=== PLASMA FUEL COMPARISON ===")
    print(f"Java: {len(java_plasma)}  Current: {len(current_plasma)}")
    all_plasma = sorted(set(current_plasma) | set(java_plasma))
    for name in all_plasma:
        j_val = java_plasma.get(name)
        j = j_val.get("eu_per_l") if isinstance(j_val, dict) else j_val
        c = current_plasma.get(name)
        if j != c:
            print(f"  {name}: current={c}  java={j}")


def main():
    parser = argparse.ArgumentParser(description="Extract data from GT5 Java sources")
    parser.add_argument("--gt5", required=True, help="Path to GT5-Unofficial src directory")
    parser.add_argument("--rotors",  action="store_true")
    parser.add_argument("--fuels",   action="store_true")
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()

    rotor_data = build_rotor_data(args.gt5)
    gas_fuels, plasma_fuels = build_fuel_data(args.gt5)

    if args.rotors:
        print("ROTOR_DATA =", repr(rotor_data))

    if args.fuels:
        print("GAS_FUELS =",    repr(gas_fuels))
        print("PLASMA_FUELS =", repr(plasma_fuels))

    if args.compare:
        sys.path.insert(0, ".")
        from gtnh_turbine_calc.data.rotors_raw import ROTOR_DATA as current_rotors
        from gtnh_turbine_calc.data.fuels_raw  import GAS_FUELS, PLASMA_FUELS
        compare_rotors(rotor_data, current_rotors)
        compare_fuels(gas_fuels, plasma_fuels, GAS_FUELS, PLASMA_FUELS)

    if not (args.rotors or args.fuels or args.compare):
        print(f"Extracted {len(rotor_data)} rotors, "
              f"{len(gas_fuels)} gas fuels, "
              f"{len(plasma_fuels)} plasma fuels")


if __name__ == "__main__":
    main()
