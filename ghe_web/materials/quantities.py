"""The material list (bill of quantities, no prices) of a sized borefield: drilling, borehole heat exchangers,
grouting, horizontal piping, heat transfer fluid and tests. Plain Python, no Streamlit.

Every quantity comes with its basis (how it was found), so it can be checked and changed in the exported table.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .. import catalog
from ..i18n import fmt, t
from . import network

# PE100 SDR 11 pipes for the connection and header lines: outer diameter and wall thickness in mm
PE_SDR11 = {25: 2.3, 32: 2.9, 40: 3.7, 50: 4.6, 63: 5.8, 75: 6.8, 90: 8.2, 110: 10.0, 125: 11.4, 140: 12.7,
            160: 14.6, 180: 16.4, 200: 18.2, 225: 20.5, 250: 22.7}
# Density of the pure antifreeze in kg/m³ (only for the common glycols and alcohols)
ANTIFREEZE_DENSITY = {"MPG": 1036.0, "MEG": 1113.0, "MEA": 789.0, "MMA": 792.0}

MANIFOLD_MODES = {"auto": "Manifold shaft beside the field (automatic)", "point": "Manifold shaft where you click",
                  "building": "Manifold in the building (one circuit per BHE to the plant room)"}

DEFAULTS = {
    "entrance": None,  # [x, y] in m, None = assumed
    "manifold_mode": "auto",
    "manifold": None,  # [x, y] for manifold_mode "point"
    "trenches": [],  # drawn trench lines, each a list of [x, y]
    "trench_depth": 1.2,
    "trench_width": 0.5,
    "bedding": 0.3,  # sand bedding and cover, total height
    "reserve": 2.0,  # extra pipe per circuit (up to the surface at the BHE head and at the manifold)
    "length_step": 5.0,  # BHE delivery lengths
    "grout_loss": 15.0,  # % more grout than the annulus (fissures, karst, loss into the formation)
    "connection_pipe": "auto",  # outer diameter in mm or "auto"
    "header_pipe": "auto",
    "v_max": 1.2,  # m/s, largest flow velocity for the automatic pipe size
}


def settings(saved: dict | None) -> dict:
    """The saved settings with defaults for everything missing."""
    out = {k: (list(v) if isinstance(v, list) else v) for k, v in DEFAULTS.items()}
    out.update({k: v for k, v in (saved or {}).items() if k in DEFAULTS})
    return out


@dataclass
class Item:
    group: str
    description: str
    quantity: float
    unit: str
    basis: str
    decimals: int = 0


@dataclass
class Layout:
    bhes: list[network.Point]
    entrance: network.Point
    entrance_assumed: bool
    manifold: network.Point
    manifold_in_building: bool
    routing: network.Routing


def pipe_name(d: float) -> str:
    return fmt("PE100 {d:g} × {s:g} (SDR 11)", d=d, s=PE_SDR11[int(d)])


def inner_area(d: float) -> float:
    """Inner cross section in m² of a PE100 SDR 11 pipe with outer diameter d mm."""
    return math.pi * ((d - 2 * PE_SDR11[int(d)]) / 2000) ** 2


def pick_pipe(flow_m3s: float, v_max: float, choice) -> tuple[int, float]:
    """The pipe (outer diameter mm) and its flow velocity: the chosen one, or the smallest within v_max."""
    if choice != "auto" and int(choice) in PE_SDR11:
        d = int(choice)
    else:
        d = next((d for d in PE_SDR11 if flow_m3s / inner_area(d) <= v_max), max(PE_SDR11))
    return d, flow_m3s / inner_area(d)


def positions(result) -> list[network.Point]:
    return [(float(b.x), float(b.y)) for b in result.borefield.borefield]


def layout(result, s: dict) -> Layout:
    bhes = positions(result)
    entrance = tuple(s["entrance"]) if s["entrance"] else network.assumed_entrance(bhes)
    in_building = s["manifold_mode"] == "building"
    if in_building:
        manifold = entrance
    elif s["manifold_mode"] == "point" and s["manifold"]:
        manifold = tuple(s["manifold"])
    else:
        manifold = network.auto_manifold(bhes, entrance)
    lines = [[tuple(p) for p in line] for line in s["trenches"] if len(line) > 1]
    if lines:
        routing = network.drawn_routing(bhes, manifold, entrance, lines, in_building)
    else:
        routing = network.auto_routing(bhes, manifold, None if in_building else entrance)
    return Layout(bhes, entrance, not s["entrance"], manifold, in_building, routing)


def _pipe(inputs) -> dict:
    """The BHE pipe: legs, outer and inner radius in m and its name."""
    p = inputs["pipe"]
    v = p.values
    if p.variant == "coaxial":
        return {"kind": "coaxial", "legs": 1, "r_out": v["r_out_out_mm"] / 1000, "volume_area":
                math.pi * (v["r_in_in_mm"] / 1000) ** 2 + math.pi * ((v["r_out_in_mm"] / 1000) ** 2
                                                                     - (v["r_in_out_mm"] / 1000) ** 2),
                "name": fmt("Coaxial BHE Ø {d:g} mm", d=v["r_out_out_mm"] * 2)}
    if p.variant == "constant_rb":  # pipe unknown: a double U-tube 32 × 2.9 is assumed for the quantities
        v = {"r_out_mm": 16.0, "r_in_mm": 13.1}
        legs, kind = 4, "assumed"
    else:
        legs, kind = (4, "double_u") if p.variant == "double_u" else (2, "single_u")
    d, s = v["r_out_mm"] * 2, v["r_out_mm"] - v["r_in_mm"]
    name = next((n for n, x in catalog.PIPES.items() if abs(x["r_out_mm"] - v["r_out_mm"]) < 0.05
                 and abs(x["r_in_mm"] - v["r_in_mm"]) < 0.05), fmt("PE {d:g} × {s:.1f}", d=d, s=s))
    return {"kind": kind, "legs": legs, "r_out": v["r_out_mm"] / 1000, "d": d, "s": s, "name": name,
            "volume_area": legs * math.pi * (v["r_in_mm"] / 1000) ** 2}


def _grout_name(k_g: float) -> str:
    return next((t(n) for n, x in catalog.GROUT.items() if abs(x["k_g"] - k_g) < 0.01),
                fmt("λ = {k:g} W/(m·K)", k=k_g))


def flow_per_bhe(result) -> float:
    """Volume flow per BHE in m³/s (at 10 °C, as a design value)."""
    bf = result.borefield
    try:
        return float(bf.borehole.flow_data.vfr_borehole(fluid_data=bf.borehole.fluid_data, temperature=10.0)) / 1000
    except Exception:
        return 0.6 / 1030


def material_list(result, inputs, s: dict, lay: Layout | None = None) -> list[Item]:
    """Quantities for the sized field. ``inputs`` are the inputs the result was calculated with."""
    lay = lay or layout(result, s)
    n = result.number_of_boreholes
    H = result.borehole_length
    D = float(inputs["borefield"].values["D"])
    r_b = float(inputs["borefield"].values["r_b_mm"]) / 1000
    pipe = _pipe(inputs)
    items: list[Item] = []

    def add(group, description, quantity, unit, basis, decimals=0):
        items.append(Item(t(group), description, quantity, t(unit), basis, decimals))

    # drilling
    drilled = n * (H + D)
    add("Drilling", t("Boreholes Ø {d:g} mm", d=r_b * 2000), n, "pcs", t("from the sizing"))
    add("Drilling", t("Drilled length"), drilled, "m",
        t("{n} × ({H:.1f} m + {D:.1f} m buried depth)", n=n, H=H, D=D), 1)
    add("Drilling", t("Borehole volume (cuttings, solid)"), math.pi * r_b ** 2 * drilled, "m³",
        t("π × r² × drilled length"), 1)
    if H + D > 100:
        add("Drilling", t("Notification under mining law (BBergG, boreholes deeper than 100 m)"), 1, "LS",
            t("{x:.0f} m deep", x=H + D))

    # borehole heat exchangers
    step = max(float(s["length_step"]), 0.5)
    probe = math.ceil((H + D) / step - 1e-9) * step
    kind = {"double_u": t("Double U-tube BHE"), "single_u": t("Single U-tube BHE"), "coaxial": "",
            "assumed": t("Double U-tube BHE")}[pipe["kind"]]
    label = pipe["name"] if pipe["kind"] == "coaxial" else f"{kind} {pipe['name']}"
    add("Borehole heat exchangers", t("{name}, length {L:g} m, with BHE foot", name=label, L=probe), n, "pcs",
        t("{x:.1f} m rounded up to the next {step:g} m", x=H + D, step=step) +
        (" · " + t("pipe assumed (measured Rb)") if pipe["kind"] == "assumed" else ""))
    if pipe["kind"] != "coaxial":
        add("Borehole heat exchangers", t("PE pipe in the BHEs ({name})", name=pipe["name"]), n * pipe["legs"] * probe,
            "m", t("{n} × {legs} legs × {L:g} m", n=n, legs=pipe["legs"], L=probe))
        add("Borehole heat exchangers", t("Spacers"), n * math.ceil(probe / 2.0), "pcs", t("one every 2 m"))
    if pipe["kind"] in ("double_u", "assumed"):
        add("Borehole heat exchangers", t("Y-pieces at the BHE head (2 legs to 1 pipe)"), 2 * n, "pcs",
            t("supply and return per BHE"))
    add("Borehole heat exchangers", t("Grouting pipe (tremie), lost or recovered"), n * probe, "m",
        t("one per BHE, full length"))

    # grouting
    annulus = math.pi * (r_b ** 2 - pipe["legs"] * pipe["r_out"] ** 2) * (H + D)
    grout = annulus * n * (1 + float(s["grout_loss"]) / 100)
    add("Grouting", t("Grout suspension, {name}", name=_grout_name(float(inputs["pipe"].values.get("k_g", 0)))),
        grout, "m³", t("{a:.2f} m³ annulus per BHE × {n} × (1 + {loss:g} % loss)", a=annulus, n=n,
                       loss=float(s["grout_loss"])), 1)

    # horizontal piping
    r = lay.routing
    q_bhe = flow_per_bhe(result)
    d_con, v_con = pick_pipe(q_bhe, float(s["v_max"]), s["connection_pipe"])
    circuit = [2 * (p + float(s["reserve"])) for p in r.paths]
    trench = r.trench_length
    add("Horizontal piping", t("Trench, depth {d:g} m, width {w:g} m", d=float(s["trench_depth"]),
                               w=float(s["trench_width"])), trench, "m",
        t("drawn on the plan") if s["trenches"] else t("shortest trench network (automatic)"), 1)
    add("Horizontal piping", t("Excavation"), trench * float(s["trench_width"]) * float(s["trench_depth"]), "m³",
        t("length × width × depth"), 1)
    add("Horizontal piping", t("Sand bedding and cover"), trench * float(s["trench_width"]) * float(s["bedding"]),
        "m³", t("length × width × {h:g} m", h=float(s["bedding"])), 1)
    add("Horizontal piping", t("Warning tape"), trench, "m", t("trench length"), 1)
    add("Horizontal piping", t("Connection pipe {name}", name=pipe_name(d_con)), sum(circuit), "m",
        t("supply + return per BHE, path to the manifold + {r:g} m each; longest circuit {x:.0f} m; v = {v:.2f} m/s",
          r=float(s["reserve"]), x=max(circuit) / 2, v=v_con), 1)
    add("Horizontal piping", t("Electrofusion couplers / transition fittings"), 4 * n, "pcs",
        t("2 at the BHE head and 2 at the manifold per circuit"))
    q_all = q_bhe * n
    if lay.manifold_in_building:
        add("Horizontal piping", t("Manifold with {n} circuits (flow meters, balancing and isolation valves)", n=n), 1,
            "pcs", t("in the plant room"))
        add("Horizontal piping", t("Wall penetrations, gas- and watertight"), 2 * n, "pcs",
            t("supply and return of every circuit"))
    else:
        d_head, v_head = pick_pipe(q_all, float(s["v_max"]), s["header_pipe"])
        add("Horizontal piping", t("Header pipe {name}", name=pipe_name(d_head)), 2 * r.header_length, "m",
            t("supply + return, manifold to the building entrance {x:.1f} m; v = {v:.2f} m/s", x=r.header_length,
              v=v_head), 1)
        add("Horizontal piping", t("Manifold with {n} circuits (flow meters, balancing and isolation valves)", n=n), 1,
            "pcs", t("in the manifold shaft"))
        add("Horizontal piping", t("Manifold shaft (PE or concrete)"), 1, "pcs", t(MANIFOLD_MODES[s["manifold_mode"]]))
        add("Horizontal piping", t("Wall penetrations, gas- and watertight"), 2, "pcs", t("header supply and return"))

    # heat transfer fluid
    vol_bhe = n * pipe["volume_area"] * probe
    vol_con = sum(circuit) * inner_area(d_con)
    vol_head = 0.0 if lay.manifold_in_building else 2 * r.header_length * inner_area(d_head)
    volume = vol_bhe + vol_con + vol_head
    fluid = inputs["fluid"].values
    add("Heat transfer fluid", t("System volume (without manifold and heat pump)"), volume, "m³",
        t("BHEs {a:.2f} + connection pipes {b:.2f} + header {c:.2f} m³", a=vol_bhe, b=vol_con, c=vol_head), 2)
    share = 0.0 if fluid["name"] == "Water" else float(fluid["percentage"]) / 100
    if share > 0:
        mass = volume * 1030.0 * share  # mixture density about 1030 kg/m³
        rho = ANTIFREEZE_DENSITY.get(fluid["name"])
        if rho:
            add("Heat transfer fluid", t("Antifreeze {name}, concentrate", name=t(fluid["name"])), mass / rho * 1000,
                "l", t("{x:g} % by mass of the system volume, {kg:,.0f} kg", x=share * 100, kg=mass))
        else:
            add("Heat transfer fluid", t("Antifreeze {name}, concentrate", name=t(fluid["name"])), mass, "kg",
                t("{x:g} % by mass of the system volume", x=share * 100))

    # tests
    add("Tests and documentation", t("Pressure and flow test of each BHE (VDI 4640-2)"), n, "pcs", t("one per BHE"))
    add("Tests and documentation", t("Pressure test of the horizontal piping"), 1, "LS", "")
    add("Tests and documentation", t("Layer documentation (Schichtenverzeichnis) to the state geological survey"),
        1, "LS", t("Geologiedatengesetz (GeolDG)"))
    return items

