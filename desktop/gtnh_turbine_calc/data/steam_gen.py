LHE_SOURCES = [
    {"name": "Lava",              "threshold_ls": 1000,  "max_ls": 2000,  "below": "Steam",    "above": "SH Steam", "ratio_below": 160, "ratio_above": 80},
    {"name": "Hot Coolant",       "threshold_ls": 800,   "max_ls": 1600,  "below": "Steam",    "above": "SH Steam", "ratio_below": 400, "ratio_above": 200},
    {"name": "Solar Salt (Hot)",  "threshold_ls": 160,   "max_ls": 320,   "below": "Steam",    "above": "SH Steam", "ratio_below": 1000,"ratio_above": 500},
]

WWXL_SOURCES = [
    {"name": "Lava",              "threshold_ls": 32000, "max_ls": 64000, "below": "Steam",    "above": "SH Steam", "ratio_below": 160, "ratio_above": 80},
    {"name": "Hot Coolant",       "threshold_ls": 25600, "max_ls": 51200, "below": "Steam",    "above": "SH Steam", "ratio_below": 400, "ratio_above": 200},
]

THERMAL_BOILER_SOURCES = [
    {"name": "Lava",              "max_ls": 1000,  "steam": "Steam",    "ratio": 16},
    {"name": "Pahoehoe Lava",     "max_ls": 1000,  "steam": "Steam",    "ratio": 16},
    {"name": "Solar Salt (Hot)",  "max_ls": 100,   "steam": "SH Steam", "ratio": 1000},
    {"name": "Hot Coolant",       "max_ls": 500,   "steam": "SH Steam", "ratio": 200},
]
