import math

DYNAMO_TIERS = [
    ("LV",      32),
    ("MV",      128),
    ("HV",      512),
    ("EV",      2048),
    ("IV",      8192),
    ("LuV",     32768),
    ("ZPM",     131072),
    ("UV",      524288),
    ("UHV",     2097152),
    ("UEV",     8388608),
    ("UIV",     33554432),
    ("UMV",     134217728),
    ("UXV",     536870912),
    ("MAX",     2147483648),
    ("MAX+",    8589934592),
    ("MAX++",   34359738368),
    ("MAX+++",  137438953472),
    ("MAX++++", 549755813888),
]


def find_dynamo_tier(eu_per_t: float) -> str:
    """Return the minimum dynamo tier that can output at least eu_per_t EU/t at 1 amp."""
    for name, voltage in DYNAMO_TIERS:
        if voltage > eu_per_t:
            return name
    return "MAX++++"


def dynamo_amps(eu_per_t: float, tier: str) -> float:
    """Return amps needed at the given dynamo tier."""
    voltage = dict(DYNAMO_TIERS).get(tier, 1)
    return round(eu_per_t / voltage, 3)
