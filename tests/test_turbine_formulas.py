import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.turbine_formulas import compute_rotor_sizes, compute_overflow_tier

def test_eternity_small():
    # Eternity (26): tool_quality=26, tool_speed=1.0
    # Small: speed_mult=1.0, base_damage=0.0
    #   combat = 0.0 + 26 = 26
    #   base_eff = 0.5 + (0.5+26)*0.1 = 0.5 + 2.65 = 3.15
    sizes = compute_rotor_sizes(
        tool_quality=26, tool_speed=1.0,
        steam_mult=1.0, gas_mult=1.0, plasma_mult=1.0
    )
    s = sizes["Small"]
    assert abs(s["steam_tight_eff"] - 3.15) < 1e-4
    assert abs(s["gas_tight_eff"] - 3.15) < 1e-4
    assert abs(s["plasma_tight_eff"] - 3.15) < 1e-4
    assert s["dur_mult"] == 1

def test_eternity_normal():
    # Normal: speed_mult=2.0, base_damage=2.5
    #   combat = 2.5 + 26 = 28.5
    #   base_eff = 0.5 + (0.5+28.5)*0.1 = 0.5 + 2.9 = 3.4
    sizes = compute_rotor_sizes(
        tool_quality=26, tool_speed=1.0,
        steam_mult=1.0, gas_mult=1.0, plasma_mult=1.0
    )
    s = sizes["Normal"]
    assert abs(s["steam_tight_eff"] - 3.4) < 1e-4
    assert s["dur_mult"] == 2

def test_opt_flow_with_multiplier():
    # quality=1, speed=6.0, steam_mult=6.0
    # Small: opt_flow = 1.0 * 6.0 * 50 = 300
    # opt_steam_flow = 300 * 6.0 = 1800
    sizes = compute_rotor_sizes(
        tool_quality=1, tool_speed=6.0,
        steam_mult=6.0, gas_mult=1.0, plasma_mult=1.0
    )
    s = sizes["Small"]
    assert abs(s["steam_opt_flow_tight"] - 1800.0) < 1e-3

def test_overflow_tier():
    # quality=26: 1 + min(2, 26//3) = 1 + min(2, 8) = 3
    assert compute_overflow_tier(26) == 3
    # quality=3: 1 + min(2, 1) = 2
    assert compute_overflow_tier(3) == 2
    # quality=1: 1 + min(2, 0) = 1
    assert compute_overflow_tier(1) == 1

def test_loose_steam_efficiency_small():
    # quality=26, speed=1.0, steam_mult=1.0
    # Small: combat=26, base_eff=3.15
    # loose_eff = -0.2 + floor(3.15*85 + 0.5) * 0.01
    #           = -0.2 + floor(267.75 + 0.5) * 0.01
    #           = -0.2 + 268 * 0.01 = -0.2 + 2.68 = 2.48
    # loose_steam_eff = 2.48 * 0.9 = 2.232
    sizes = compute_rotor_sizes(
        tool_quality=26, tool_speed=1.0,
        steam_mult=1.0, gas_mult=1.0, plasma_mult=1.0
    )
    s = sizes["Small"]
    assert abs(s["steam_loose_eff"] - 2.232) < 1e-4

def test_loose_gas_efficiency_normal():
    # quality=26, Normal: base_damage=2.5, combat=28.5, base_eff=3.4
    # loose_eff = -0.2 + floor(3.4*85 + 0.5)*0.01 = -0.2 + floor(289.5)*0.01
    #           = -0.2 + 289*0.01 = 2.69  (floor of 289.5 = 289)
    # loose_gas_eff = 2.69 * 0.95 = 2.5555
    sizes = compute_rotor_sizes(
        tool_quality=26, tool_speed=1.0,
        steam_mult=1.0, gas_mult=1.0, plasma_mult=1.0
    )
    s = sizes["Normal"]
    assert abs(s["gas_loose_eff"] - 2.5555) < 1e-4
