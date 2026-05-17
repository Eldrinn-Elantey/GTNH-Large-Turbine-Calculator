"""Parse gas and plasma fuel values from GT5-Unofficial Java source loader files."""
import os
import re

_GAS_FUEL_FILES = [
    os.path.join("main", "java", "gregtech", "loaders", "load", "FuelLoader.java"),
    os.path.join("main", "java", "goodgenerator", "loader", "RecipeLoader.java"),
    os.path.join("main", "java", "gtPlusPlus", "core", "item", "chemistry",
                 "RecipeLoaderCoalTar.java"),
    os.path.join("main", "java", "gtPlusPlus", "core", "item", "chemistry",
                 "RecipeLoaderGenericChem.java"),
    os.path.join("main", "java", "bartworks", "system", "material",
                 "processingLoaders", "AdditionalRecipes.java"),
]

_PLASMA_FUEL_FILE = os.path.join(
    "main", "java", "gregtech", "loaders", "oreprocessing", "ProcessingCell.java"
)

_FUEL_VALUE_RE = re.compile(
    r'metadata\s*\(\s*FUEL_VALUE\s*,\s*([\d_]+)\s*\)'
)

_GAS_FUEL_TYPE_RE = re.compile(
    r'metadata\s*\(\s*FUEL_TYPE\s*,\s*(?:1\b|GTRecipeConstants\.FuelType\.GasTurbine\.ordinal\(\))'
)

# Patterns for extracting fuel name from itemInputs

# GGMaterial.fieldName.get(OrePrefixes.cell) or similar
_GGMATERIAL_RE = re.compile(
    r'GGMaterial\s*\.\s*(\w+)\s*\.'
)

# Materials.fieldName.getCells(...) or Materials.fieldName.get(OrePrefixes.cell)
_MATERIALS_RE = re.compile(
    r'Materials\s*\.\s*(\w+)\s*\.\s*(?:getCells|get\s*\(\s*OrePrefixes\.cell)'
)

# getItemStackOfAmountFromOreDict("cellXxx", N) -> strip "cell" prefix
_OREDICT_RE = re.compile(
    r'getItemStackOfAmountFromOreDict\s*\(\s*"cell(\w+)"\s*,'
)

# GTModHandler.getModItem(ModID, "bucketXxx" or "cellXxx", ...) -> strip prefix
_MODITEM_RE = re.compile(
    r'getModItem\s*\([^,]+,\s*"(?:bucket|cell)([^"]+)"'
)

# Arrow-switch pattern in ProcessingCell.java for plasma fuels
_PLASMA_CASE_RE = re.compile(
    r'case\s+"(\w[\w ]*?)"\s+->\s+recipeBuilder\s*\.\s*metadata\s*\(\s*FUEL_VALUE\s*,\s*([\d_]+)\s*\)'
    r'(?:(?!case).){0,300}?metadata\s*\(\s*FUEL_TYPE\s*,\s*4\s*\)',
    re.DOTALL,
)


def _parse_int(s: str) -> int:
    return int(s.replace("_", ""))


def _field_to_display(field_name: str) -> str:
    """Convert camelCase Java field name to display name.

    e.g. "naquadahGas" -> "Naquadah Gas", "Benzene" -> "Benzene"
    """
    _NAME_OVERRIDES = {
        "naquadahGas": "Naquadah Gas",
        "nitrobenzene": "Nitrobenzene",
        "tertButylbenzene": "Tert-Butylbenzene",
        "benzene": "Benzene",
        "ether": "Ether",
        "ethanolGasoline": "Ethanol Gasoline",
        "cyclopentadiene": "Cyclopentadiene",
    }
    if field_name in _NAME_OVERRIDES:
        return _NAME_OVERRIDES[field_name]
    # Insert space before uppercase letters following lowercase
    spaced = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', field_name)
    return spaced[0].upper() + spaced[1:]


def _extract_fuel_name(block: str) -> str | None:
    """Extract a display name from a recipe block's itemInputs."""
    m = _GGMATERIAL_RE.search(block)
    if m:
        return _field_to_display(m.group(1))

    m = _MATERIALS_RE.search(block)
    if m:
        return _field_to_display(m.group(1))

    m = _OREDICT_RE.search(block)
    if m:
        return _field_to_display(m.group(1))

    m = _MODITEM_RE.search(block)
    if m:
        raw = m.group(1).replace("_", " ").replace("-", " ")
        return raw[0].upper() + raw[1:]

    return None


def parse_gas_fuels(gt5_src_root: str) -> dict:
    """Return dict[display_name -> {"eu_per_l": float}] for gas turbine fuels."""
    result = {}
    for rel_path in _GAS_FUEL_FILES:
        path = os.path.join(gt5_src_root, rel_path)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            code = fh.read()

        # Split on stdBuilder() to isolate individual recipe blocks
        blocks = re.split(r'GTValues\.RA\.stdBuilder\s*\(\s*\)', code)
        for block in blocks:
            if not _GAS_FUEL_TYPE_RE.search(block):
                continue
            fuel_m = _FUEL_VALUE_RE.search(block)
            if not fuel_m:
                continue

            display = _extract_fuel_name(block)
            if not display:
                continue

            eu_per_l = float(_parse_int(fuel_m.group(1)))
            result[display] = {"eu_per_l": eu_per_l}

    return result


def parse_plasma_fuels(gt5_src_root: str) -> dict:
    """Return dict[material_name -> {"eu_per_l": float}] for plasma fuels."""
    path = os.path.join(gt5_src_root, _PLASMA_FUEL_FILE)
    with open(path, encoding="utf-8") as fh:
        code = fh.read()

    result = {}
    for m in _PLASMA_CASE_RE.finditer(code):
        name     = m.group(1)
        eu_per_l = float(_parse_int(m.group(2)))
        result[name] = {"eu_per_l": eu_per_l}

    return result
