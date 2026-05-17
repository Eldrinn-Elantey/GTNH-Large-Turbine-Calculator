"""Download GT5-Unofficial source by tag, extract data, update web/data/<gtnh_version>/.

Usage:
    python scripts/update_web_data.py --tag 5.09.44.08 --gtnh 2.9
    python scripts/update_web_data.py --source excel --file data.xlsx --gtnh 2.7
"""
import argparse
import io
import json
import os
import sys
import tempfile
import urllib.request
import zipfile

import openpyxl

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.extract_from_java import build_rotor_data, build_fuel_data
from scripts.excel_parser import extract_rotors, extract_fuels, extract_steam_gen

_GT5_ZIP_URL = "https://github.com/GTNewHorizons/GT5-Unofficial/archive/refs/tags/{tag}.zip"
_WEB_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "data")


def _download_zip(tag: str) -> bytes:
    url = _GT5_ZIP_URL.format(tag=tag)
    print(f"Downloading {url} ...")
    with urllib.request.urlopen(url) as resp:
        data = resp.read()
    print(f"Downloaded {len(data) // 1024} KB")
    return data


def _extract_src(zip_bytes: bytes, tmp_dir: str) -> str:
    """Extract ZIP and return path to the src/ directory inside."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        zf.extractall(tmp_dir)
    # Top-level dir is GT5-Unofficial-<tag>/
    top = next(
        os.path.join(tmp_dir, e)
        for e in os.listdir(tmp_dir)
        if os.path.isdir(os.path.join(tmp_dir, e))
    )
    src = os.path.join(top, "src")
    if not os.path.isdir(src):
        raise FileNotFoundError(f"src/ not found inside extracted archive at {top}")
    return src


def _build_rotors_json(rotor_data: dict) -> list:
    rows = []
    for name, props in sorted(rotor_data.items(), key=lambda kv: -kv[1]["tier"]):
        rows.append({
            "name": name,
            "tier": props["tier"],
            "mining_speed": props["mining_speed"],
            "base_durability": props["base_durability"],
            "overflow_tier": props["overflow_tier"],
            "sizes": props["sizes"],
        })
    return rows


def _build_fuels_json(gas_fuels: dict, plasma_fuels: dict, existing: dict | None) -> dict:
    gas_rows = sorted(
        [{"name": n, "eu_l": v["eu_per_l"]} for n, v in gas_fuels.items()],
        key=lambda x: -x["eu_l"],
    )
    plasma_rows = sorted(
        [{"name": n, "eu_l": v["eu_per_l"] if isinstance(v, dict) else v}
         for n, v in plasma_fuels.items()],
        key=lambda x: -x["eu_l"],
    )

    # Preserve steam and ehe sections from existing file (not parsed from Java)
    steam = existing["steam"] if existing else []
    ehe   = existing["ehe"]   if existing else []

    return {"steam": steam, "gas": gas_rows, "plasma": plasma_rows, "ehe": ehe}


def _diff_rotors(new_rows: list, old_rows: list | None) -> None:
    if old_rows is None:
        print(f"  New file — {len(new_rows)} rotors")
        return

    old_map = {r["name"]: r for r in old_rows}
    new_map = {r["name"]: r for r in new_rows}

    added   = sorted(set(new_map) - set(old_map))
    removed = sorted(set(old_map) - set(new_map))
    changed = []
    for name in sorted(set(new_map) & set(old_map)):
        n, o = new_map[name], old_map[name]
        small_new = n["sizes"]["Small"]["steam_tight_eff"]
        small_old = o["sizes"]["Small"]["steam_tight_eff"]
        if abs(small_new - small_old) > 1e-6:
            changed.append(f"  ~ {name}: eff Small {small_old:.4f} -> {small_new:.4f}")

    if added:
        print(f"  + {len(added)} new:  {', '.join(added[:5])}{'...' if len(added) > 5 else ''}")
    if removed:
        print(f"  - {len(removed)} removed:  {', '.join(removed[:5])}{'...' if len(removed) > 5 else ''}")
    if changed:
        print(f"  {len(changed)} stat changes:")
        for line in changed[:10]:
            print(f"    {line}")
        if len(changed) > 10:
            print(f"    ... and {len(changed) - 10} more")
    if not added and not removed and not changed:
        print("  No changes.")


def _diff_fuels(new_fuels: dict, old_fuels: dict | None) -> None:
    if old_fuels is None:
        print(f"  New file")
        return

    for section in ("gas", "plasma"):
        old_map = {r["name"]: r["eu_l"] for r in (old_fuels.get(section) or [])}
        new_map = {r["name"]: r["eu_l"] for r in (new_fuels.get(section) or [])}
        added   = sorted(set(new_map) - set(old_map))
        removed = sorted(set(old_map) - set(new_map))
        changed = [
            f"{n}: {old_map[n]} -> {new_map[n]}"
            for n in sorted(set(new_map) & set(old_map))
            if new_map[n] != old_map[n]
        ]
        if added or removed or changed:
            print(f"  [{section}]")
            if added:   print(f"    + {', '.join(added[:5])}{'...' if len(added) > 5 else ''}")
            if removed: print(f"    - {', '.join(removed[:5])}{'...' if len(removed) > 5 else ''}")
            for line in changed[:5]: print(f"    ~ {line}")
        else:
            print(f"  [{section}] no changes")


def _diff_steam_gen(new_sg: dict, old_sg: dict | None) -> None:
    if old_sg is None:
        print("  New file")
        return

    for section in ("lhe", "wwxl", "thermal_boiler"):
        old_map = {e["name"]: e for e in (old_sg.get(section) or [])}
        new_map = {e["name"]: e for e in (new_sg.get(section) or [])}
        added   = sorted(set(new_map) - set(old_map))
        removed = sorted(set(old_map) - set(new_map))
        changed = []
        for name in sorted(set(new_map) & set(old_map)):
            diffs = [
                f"{k}: {old_map[name][k]} -> {new_map[name][k]}"
                for k in new_map[name]
                if k != "name" and k in old_map[name]
                and str(old_map[name][k]) != str(new_map[name][k])
            ]
            if diffs:
                changed.append(f"  ~ {name}: {', '.join(diffs)}")
        if added or removed or changed:
            print(f"  [{section}]")
            if added:   print(f"    + {', '.join(added)}")
            if removed: print(f"    - {', '.join(removed)}")
            for line in changed: print(f"   {line}")
        else:
            print(f"  [{section}] no changes")


def _run_java(args) -> None:
    out_dir = os.path.join(_WEB_DATA_DIR, args.gtnh)
    rotors_path = os.path.join(out_dir, "rotors.json")
    fuels_path  = os.path.join(out_dir, "fuels.json")

    existing_rotors = json.load(open(rotors_path)) if os.path.exists(rotors_path) else None
    existing_fuels  = json.load(open(fuels_path))  if os.path.exists(fuels_path)  else None

    zip_bytes = _download_zip(args.tag)

    with tempfile.TemporaryDirectory() as tmp:
        src = _extract_src(zip_bytes, tmp)
        print(f"Parsing from {src} ...")
        rotor_data = build_rotor_data(src)
        gas_fuels, plasma_fuels = build_fuel_data(src)

    new_rotors = _build_rotors_json(rotor_data)
    new_fuels  = _build_fuels_json(gas_fuels, plasma_fuels, existing_fuels)

    print(f"\n=== Rotors: {len(new_rotors)} total ===")
    _diff_rotors(new_rotors, existing_rotors)

    print(f"\n=== Fuels ===")
    _diff_fuels(new_fuels, existing_fuels)

    print()
    answer = input(f"Write to web/data/{args.gtnh}/? [y/N] ").strip().lower()
    if answer != "y":
        print("Aborted.")
        return

    os.makedirs(out_dir, exist_ok=True)
    with open(rotors_path, "w", encoding="utf-8") as fh:
        json.dump(new_rotors, fh, ensure_ascii=False, indent=2)
    with open(fuels_path, "w", encoding="utf-8") as fh:
        json.dump(new_fuels, fh, ensure_ascii=False, indent=2)
    print(f"Written {rotors_path}")
    print(f"Written {fuels_path}")


def _run_excel(args) -> None:
    out_dir        = os.path.join(_WEB_DATA_DIR, args.gtnh)
    rotors_path    = os.path.join(out_dir, "rotors.json")
    fuels_path     = os.path.join(out_dir, "fuels.json")
    steam_gen_path = os.path.join(out_dir, "steam_gen.json")

    existing_rotors    = json.load(open(rotors_path))     if os.path.exists(rotors_path)     else None
    existing_fuels     = json.load(open(fuels_path))      if os.path.exists(fuels_path)      else None
    existing_steam_gen = json.load(open(steam_gen_path))  if os.path.exists(steam_gen_path)  else None

    print(f"Loading {args.file} ...")
    wb = openpyxl.load_workbook(args.file, data_only=True)

    new_rotors    = extract_rotors(wb)
    new_fuels     = extract_fuels(wb)
    new_steam_gen = extract_steam_gen(wb)

    print(f"\n=== Rotors: {len(new_rotors)} total ===")
    _diff_rotors(new_rotors, existing_rotors)

    print(f"\n=== Fuels ===")
    _diff_fuels(new_fuels, existing_fuels)

    print(f"\n=== Steam Gen ===")
    _diff_steam_gen(new_steam_gen, existing_steam_gen)

    print()
    answer = input(f"Write to web/data/{args.gtnh}/? [y/N] ").strip().lower()
    if answer != "y":
        print("Aborted.")
        return

    os.makedirs(out_dir, exist_ok=True)
    with open(rotors_path, "w", encoding="utf-8") as fh:
        json.dump(new_rotors, fh, ensure_ascii=False, indent=2)
    with open(fuels_path, "w", encoding="utf-8") as fh:
        json.dump(new_fuels, fh, ensure_ascii=False, indent=2)
    with open(steam_gen_path, "w", encoding="utf-8") as fh:
        json.dump(new_steam_gen, fh, ensure_ascii=False, indent=2)

    versions_path = os.path.join(_WEB_DATA_DIR, "versions.json")
    versions = json.load(open(versions_path)) if os.path.exists(versions_path) else []
    if not any(v["id"] == args.gtnh for v in versions):
        versions.append({"id": args.gtnh, "label": args.gtnh})
        with open(versions_path, "w", encoding="utf-8") as fh:
            json.dump(versions, fh, ensure_ascii=False, indent=2)
        print(f"Added {args.gtnh} to versions.json")

    print(f"Written {rotors_path}")
    print(f"Written {fuels_path}")
    print(f"Written {steam_gen_path}")


def main():
    parser = argparse.ArgumentParser(description="Update web/data from GT5-Unofficial source or Excel file")
    parser.add_argument("--source", choices=["java", "excel"], default="java",
                        help="Data source: 'java' (default) downloads GT5 source, 'excel' reads .xlsx file")
    parser.add_argument("--tag",  help="GT5-Unofficial git tag (required for --source java), e.g. 5.09.44.08")
    parser.add_argument("--file", help="Path to Excel .xlsx file (required for --source excel)")
    parser.add_argument("--gtnh", required=True, help="GTNH version string, e.g. 2.9")
    args = parser.parse_args()

    if args.source == "java":
        if not args.tag:
            parser.error("--tag is required when --source java")
        if args.file:
            parser.error("--file is not used with --source java")
        _run_java(args)
    else:
        if not args.file:
            parser.error("--file is required when --source excel")
        if args.tag:
            parser.error("--tag is not used with --source excel")
        _run_excel(args)


if __name__ == "__main__":
    main()
