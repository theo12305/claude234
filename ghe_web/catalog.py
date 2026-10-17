"""Material databases, like the ones EED ships with.

Values are typical design values (based on VDI 4640 part 1 and common manufacturer data).
They are a starting point: use measured values (thermal response test, data sheets) when you have them.
"""

# Ground: thermal conductivity [W/(m·K)] and volumetric heat capacity [MJ/(m³·K)]
GROUND = {
    "Clay / silt, dry": {"k_s": 0.5, "volumetric_heat_capacity": 1.75},
    "Clay / silt, water saturated": {"k_s": 1.7, "volumetric_heat_capacity": 2.4},
    "Sand, dry": {"k_s": 0.4, "volumetric_heat_capacity": 1.4},
    "Sand, moist": {"k_s": 1.0, "volumetric_heat_capacity": 1.7},
    "Sand, water saturated": {"k_s": 2.4, "volumetric_heat_capacity": 2.5},
    "Gravel, water saturated": {"k_s": 1.8, "volumetric_heat_capacity": 2.4},
    "Till / loam": {"k_s": 2.4, "volumetric_heat_capacity": 2.3},
    "Claystone / mudstone": {"k_s": 2.2, "volumetric_heat_capacity": 2.3},
    "Marl": {"k_s": 2.1, "volumetric_heat_capacity": 2.25},
    "Sandstone": {"k_s": 2.3, "volumetric_heat_capacity": 2.2},
    "Limestone": {"k_s": 2.8, "volumetric_heat_capacity": 2.2},
    "Dolomite": {"k_s": 3.2, "volumetric_heat_capacity": 2.5},
    "Quartzite": {"k_s": 6.0, "volumetric_heat_capacity": 2.1},
    "Granite": {"k_s": 3.4, "volumetric_heat_capacity": 2.4},
    "Gneiss": {"k_s": 2.9, "volumetric_heat_capacity": 2.2},
    "Mica schist": {"k_s": 2.0, "volumetric_heat_capacity": 2.2},
    "Basalt": {"k_s": 1.7, "volumetric_heat_capacity": 2.6},
    "Rock salt": {"k_s": 5.4, "volumetric_heat_capacity": 2.0},
}

# Grout / backfill: thermal conductivity [W/(m·K)]
GROUT = {
    "Bentonite, standard": {"k_g": 0.8},
    "Bentonite-cement": {"k_g": 1.0},
    "Thermally enhanced grout": {"k_g": 1.6},
    "High-performance grout": {"k_g": 2.0},
    "Quartz sand, water saturated": {"k_g": 2.4},
}

# Pipes: radii in mm, PE conductivity 0.42 W/(m·K), PE-RT and PE-Xa similar
PIPES = {
    "PE100 25 × 2.3 (SDR 11)": {"r_out_mm": 12.5, "r_in_mm": 10.2, "k_p": 0.42},
    "PE100 32 × 2.9 (SDR 11)": {"r_out_mm": 16.0, "r_in_mm": 13.1, "k_p": 0.42},
    "PE100 32 × 2.0 (SDR 17)": {"r_out_mm": 16.0, "r_in_mm": 14.0, "k_p": 0.42},
    "PE100 40 × 3.7 (SDR 11)": {"r_out_mm": 20.0, "r_in_mm": 16.3, "k_p": 0.42},
    "PE100 40 × 2.4 (SDR 17)": {"r_out_mm": 20.0, "r_in_mm": 17.6, "k_p": 0.42},
    "PE100 50 × 4.6 (SDR 11)": {"r_out_mm": 25.0, "r_in_mm": 20.4, "k_p": 0.42},
}

# Borehole diameters commonly drilled, radius in mm
BOREHOLES = {
    "Ø 115 mm": {"r_b_mm": 57.5},
    "Ø 140 mm": {"r_b_mm": 70.0},
    "Ø 152 mm": {"r_b_mm": 76.0},
    "Ø 165 mm": {"r_b_mm": 82.5},
    "Ø 180 mm": {"r_b_mm": 90.0},
}

# Fluids GHEtool knows, with the concentration range [%] it has data for
FLUIDS = {
    "Water": (0, 0),
    "MPG": (0, 60),
    "MEG": (0, 60),
    "MEA": (0, 60),
    "MMA": (0, 60),
    "Thermox DTX": (25, 55),
    "Coolflow NTP": (30, 60),
    "Kilfrost GEO": (30, 60),
    "Kilfrost GEO Plus": (35, 65),
    "GeoPro": (35, 40),
}

# Share of the yearly energy per month, Jan..Dec. The first two are the profiles of the GHEtool example.
MONTHLY_PROFILES = {
    "Heating (office, GHEtool example)": (0.155, 0.148, 0.125, 0.099, 0.064, 0.0, 0.0, 0.0, 0.061, 0.087, 0.117, 0.144),
    "Cooling (office, GHEtool example)": (0.025, 0.05, 0.05, 0.05, 0.075, 0.1, 0.2, 0.2, 0.1, 0.075, 0.05, 0.025),
    "Constant": (1 / 12,) * 12,
}

# Heat pump COP at average fluid temperatures of -5, 0, 5, 10 and 15 °C (brine/water units, typical
# EN 14511 data sheet values at the given supply temperature).
HEATING_CURVES = {
    "Floor heating (35 °C)": (3.9, 4.5, 5.0, 5.6, 6.2),
    "Low-temperature radiators (45 °C)": (3.1, 3.5, 3.9, 4.3, 4.7),
    "Radiators (55 °C)": (2.5, 2.8, 3.1, 3.4, 3.7),
}

# EER at average fluid temperatures of 10, 15, 20, 25 and 30 °C.
COOLING_CURVES = {
    "Passive cooling (pumps only)": (20.0, 20.0, 20.0, 20.0, 20.0),
    "Active cooling (heat pump as chiller)": (7.5, 6.5, 5.5, 4.6, 3.8),
}
