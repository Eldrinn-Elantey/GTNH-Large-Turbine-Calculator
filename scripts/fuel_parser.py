"""Parse gas and plasma fuel values from GT5-Unofficial Java source files."""
import os
import re
import javalang

_MATERIALS_INIT = os.path.join(
    "main", "java", "gregtech", "loaders", "materials", "MaterialsInit.java"
)
_PLASMA_FUEL_FILE = os.path.join(
    "main", "java", "gregtech", "loaders", "oreprocessing", "ProcessingCell.java"
)

# Extra gas fuels not in MaterialsInit (FuelLoader, GoodGenerator, BartWorks, etc.)
_EXTRA_GAS_FUEL_FILES = [
    os.path.join("main", "java", "gregtech", "loaders", "load", "FuelLoader.java"),
    os.path.join("main", "java", "goodgenerator", "loader", "RecipeLoader.java"),
    os.path.join("main", "java", "goodgenerator", "loader", "RecipeLoader2.java"),
    os.path.join("main", "java", "gtPlusPlus", "core", "item", "chemistry",
                 "RecipeLoaderCoalTar.java"),
    os.path.join("main", "java", "gtPlusPlus", "core", "item", "chemistry",
                 "RecipeLoaderGenericChem.java"),
    os.path.join("main", "java", "bartworks", "system", "material",
                 "processingLoaders", "AdditionalRecipes.java"),
]

_GAS_FUEL_TYPE_RE = re.compile(
    r'metadata\s*\(\s*FUEL_TYPE\s*,\s*(?:1\b|GTRecipeConstants\.FuelType\.GasTurbine\.ordinal\(\))'
)
_FUEL_VALUE_RE = re.compile(r'metadata\s*\(\s*FUEL_VALUE\s*,\s*([\d_]+)\s*\)')
_GGMATERIAL_RE  = re.compile(r'GGMaterial\s*\.\s*(\w+)\s*\.')
_MATERIALS_RE   = re.compile(r'Materials\s*\.\s*(\w+)\s*\.\s*(?:getCells|get\s*\(\s*OrePrefixes\.cell)')
_OREDICT_RE     = re.compile(r'getItemStackOfAmountFromOreDict\s*\(\s*"cell(\w+)"\s*,')
_MODITEM_RE     = re.compile(r'getModItem\s*\([^,]+,\s*"(?:bucket|cell)([^"]+)"')

# Arrow-switch pattern in ProcessingCell.java for plasma fuels (Java 14+)
_PLASMA_CASE_RE = re.compile(
    r'case\s+"(\w[\w ]*?)"\s+->\s+recipeBuilder\s*\.\s*metadata\s*\(\s*FUEL_VALUE\s*,\s*([\d_]+)\s*\)'
    r'(?:(?!case).){0,300}?metadata\s*\(\s*FUEL_TYPE\s*,\s*4\s*\)',
    re.DOTALL,
)

_CAMEL_OVERRIDES = {
    "naquadahGas":     "Naquadah Gas",
    "nitrobenzene":    "Nitrobenzene",
    "tertButylbenzene": "Tert-Butylbenzene",
    "benzene":         "Benzene",
    "ether":           "Ether",
    "ethanolGasoline": "Ethanol Gasoline",
    "cyclopentadiene": "Cyclopentadiene",
}

# Material setName() value -> display name for gas fuels
_GAS_NAME_ALIASES: dict[str, str] = {
    "Gas":         "Refinery Gas",   # mToolSpeed named just "Gas" in Java
    "NatruralGas": "Natural Gas",    # typo in Java source
    "nefariousgas": "Nefarious Gas",
    "Rocket fuel":  "Rocket Fuel",
}

# ProcessingCell case label -> display name for plasma fuels (before " Plasma" suffix)
_PLASMA_NAME_ALIASES: dict[str, str] = {
    "Helium_3":    "Helium-3",
    "Plutonium":   "Plutonium 239",
    "Plutonium241": "Plutonium 241",
    "Uranium":     "Uranium 238",
    "Uranium235":  "Uranium 235",
    "Silicon":     "Raw Silicon",
}


def _parse_int(s: str) -> int:
    return int(s.replace("_", ""))


def _camel_to_display(name: str) -> str:
    if name in _CAMEL_OVERRIDES:
        return _CAMEL_OVERRIDES[name]
    spaced = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name)
    return spaced[0].upper() + spaced[1:]


def _extract_fuel_name_from_block(block: str) -> str | None:
    """Extract display name from a stdBuilder recipe block."""
    m = _GGMATERIAL_RE.search(block)
    if m:
        return _camel_to_display(m.group(1))
    m = _MATERIALS_RE.search(block)
    if m:
        return _camel_to_display(m.group(1))
    m = _OREDICT_RE.search(block)
    if m:
        return _camel_to_display(m.group(1))
    m = _MODITEM_RE.search(block)
    if m:
        raw = m.group(1).replace("_", " ").replace("-", " ")
        return raw[0].upper() + raw[1:]
    return None


def _parse_gas_from_materials_init(gt5_src_root: str) -> dict:
    """Parse setFuel(FuelType.Gas, value) entries from MaterialsInit.java via AST."""
    path = os.path.join(gt5_src_root, _MATERIALS_INIT)
    with open(path, encoding="utf-8") as fh:
        code = fh.read()

    tree = javalang.parse.parse(code)
    result = {}

    for _, method in tree.filter(javalang.tree.MethodDeclaration):
        if not method.name.startswith("load"):
            continue

        mat_name = None
        gas_power = None

        for _, child in method.filter(javalang.tree.MethodInvocation):
            m = child.member
            args = child.arguments or []

            if m == "setName" and args:
                v = getattr(args[0], "value", None)
                if v:
                    mat_name = v.strip('"')

            elif m == "setFuel" and len(args) >= 2:
                # First arg is FuelType.Gas (MemberReference with member "Gas")
                type_arg = args[0]
                type_name = getattr(type_arg, "member", None)
                if type_name == "Gas":
                    power_v = getattr(args[1], "value", None)
                    if power_v:
                        try:
                            gas_power = float(str(power_v).replace("_", ""))
                        except ValueError:
                            pass

        if mat_name and gas_power is not None:
            display = _GAS_NAME_ALIASES.get(mat_name) or _camel_to_display(mat_name)
            display = _GAS_NAME_ALIASES.get(display, display)
            result[display] = {"eu_per_l": gas_power}

    return result


def _parse_gas_from_extra_files(gt5_src_root: str) -> dict:
    """Parse gas fuels from extra recipe loader files (stdBuilder pattern)."""
    result = {}
    for rel_path in _EXTRA_GAS_FUEL_FILES:
        path = os.path.join(gt5_src_root, rel_path)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            code = fh.read()

        blocks = re.split(r'GTValues\.RA\.stdBuilder\s*\(\s*\)', code)
        for block in blocks:
            if not _GAS_FUEL_TYPE_RE.search(block):
                continue
            fuel_m = _FUEL_VALUE_RE.search(block)
            if not fuel_m:
                continue
            display = _extract_fuel_name_from_block(block)
            if not display:
                continue
            eu_per_l = float(_parse_int(fuel_m.group(1)))
            result[display] = {"eu_per_l": eu_per_l}

    return result


def parse_gas_fuels(gt5_src_root: str) -> dict:
    """Return dict[display_name -> {"eu_per_l": float}] for gas turbine fuels."""
    result = _parse_gas_from_materials_init(gt5_src_root)
    # Extra files can override or add entries
    result.update(_parse_gas_from_extra_files(gt5_src_root))
    return result


def parse_plasma_fuels(gt5_src_root: str) -> dict:
    """Return dict[display_name -> {"eu_per_l": float}] for plasma fuels.

    Names are formatted as "<Material> Plasma" to match web data conventions.
    """
    path = os.path.join(gt5_src_root, _PLASMA_FUEL_FILE)
    with open(path, encoding="utf-8") as fh:
        code = fh.read()

    result = {}
    for m in _PLASMA_CASE_RE.finditer(code):
        raw_name = m.group(1)
        eu_per_l  = float(_parse_int(m.group(2)))
        canonical = _PLASMA_NAME_ALIASES.get(raw_name, raw_name)
        display = canonical if canonical.endswith(" Plasma") else f"{canonical} Plasma"
        result[display] = {"eu_per_l": eu_per_l}

    return result
