"""Parse rotor-capable material properties from GT5-Unofficial Java sources."""
import os
import re
import javalang

_MATERIALS_INIT = os.path.join(
    "main", "java", "gregtech", "loaders", "materials", "MaterialsInit.java"
)
_GGMATERIAL = os.path.join(
    "main", "java", "goodgenerator", "items", "GGMaterial.java"
)
_WERKSTOFF_LOADER = os.path.join(
    "main", "java", "bartworks", "system", "material", "WerkstoffLoader.java"
)


def _float_arg(arg) -> float | None:
    if arg is None:
        return None
    if hasattr(arg, "value"):
        try:
            return float(str(arg.value).replace("_", "").rstrip("fF"))
        except ValueError:
            return None
    if hasattr(arg, "operand") and hasattr(arg.operand, "value"):
        try:
            return -float(str(arg.operand.value).replace("_", "").rstrip("fF"))
        except ValueError:
            return None
    return None


def parse_gt_materials(gt5_src_root: str) -> dict:
    """Parse MaterialsInit.java via javalang AST.

    Returns dict[material_name -> property_dict] for turbine-blade-eligible materials.
    Excludes materials tagged with NO_SMASHING or BOUNCY.
    """
    path = os.path.join(gt5_src_root, _MATERIALS_INIT)
    with open(path, encoding="utf-8") as fh:
        code = fh.read()

    tree = javalang.parse.parse(code)

    result = {}
    for _, method in tree.filter(javalang.tree.MethodDeclaration):
        if not method.name.startswith("load"):
            continue

        mat_name = None
        tool_dur = tool_qual = tool_speed = None
        steam_mult = gas_mult = plasma_mult = 1.0
        subtags = []

        for _, child in method.filter(javalang.tree.MethodInvocation):
            m = child.member
            args = child.arguments or []

            if m == "setName" and args:
                v = getattr(args[0], "value", None)
                if v:
                    mat_name = v.strip('"')

            elif m == "setTool" and len(args) >= 3:
                tool_dur   = _float_arg(args[0])
                tool_qual  = _float_arg(args[1])
                tool_speed = _float_arg(args[2])

            elif m == "setTurbine" and len(args) >= 3:
                steam_mult  = _float_arg(args[0]) or 1.0
                gas_mult    = _float_arg(args[1]) or 1.0
                plasma_mult = _float_arg(args[2]) or 1.0

            elif m == "addSubTag" and args:
                ref = getattr(args[0], "member", None)
                if ref:
                    subtags.append(ref)

        if mat_name is None or tool_dur is None:
            continue
        if "NO_SMASHING" in subtags or "BOUNCY" in subtags:
            continue

        result[mat_name] = {
            "tool_durability": int(tool_dur),
            "tool_quality":    int(tool_qual),
            "tool_speed":      float(tool_speed),
            "steam_mult":      float(steam_mult),
            "gas_mult":        float(gas_mult),
            "plasma_mult":     float(plasma_mult),
        }

    return result


def parse_werkstoff_materials(gt5_src_root: str) -> dict:
    """Parse Werkstoff-based materials with speed/dur/quality overrides.

    Returns same property dict format as parse_gt_materials.
    Steam/gas/plasma multipliers default to 1.0 (no turbine override in Werkstoff).
    """
    result = {}
    for rel_path in (_GGMATERIAL, _WERKSTOFF_LOADER):
        path = os.path.join(gt5_src_root, rel_path)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            code = fh.read()

        for m in re.finditer(r'new Werkstoff\s*\(', code):
            block_start = m.start()
            chunk = code[block_start: block_start + 800]

            name_match = re.search(r'"([\w][^"]{0,60})"', chunk)
            if not name_match:
                continue
            name = name_match.group(1).strip()

            speed_m   = re.search(r'setSpeedOverride\(\s*([\d.]+)F?\s*\)', chunk)
            dur_m     = re.search(r'setDurOverride\(\s*(\d+)\s*\)', chunk)
            quality_m = re.search(r'setQualityOverride\(\s*\(byte\)\s*(\d+)\s*\)', chunk)

            if not (speed_m and dur_m and quality_m):
                continue

            result[name] = {
                "tool_durability": int(dur_m.group(1)),
                "tool_quality":    int(quality_m.group(1)),
                "tool_speed":      float(speed_m.group(1)),
                "steam_mult":      1.0,
                "gas_mult":        1.0,
                "plasma_mult":     1.0,
            }

    return result
