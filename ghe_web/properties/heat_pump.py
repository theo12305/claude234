"""Heat pump efficiency: fixed SCOP/SEER (entered with the load) or a COP/EER that follows the fluid temperature."""
import numpy as np
from GHEtool.VariableClasses.Efficiency import COP, EER

from ..catalog import COOLING_CURVES, HEATING_CURVES
from ..i18n import t
from .base import PresetGroup, Property, Section, Variant
from .registry import register

# Average fluid temperatures [°C] at which the curve is given. GHEtool interpolates linearly between them
# and keeps the end values outside the range.
COP_TEMPS = (-5, 0, 5, 10, 15)
EER_TEMPS = (10, 15, 20, 25, 30)


def _cop_prop(t, default):
    return Property(f"cop_{t}".replace("-", "m"), f"COP at {t} °C fluid", default, min=1.0, max=15.0, step=0.1,
                    help="Heating COP when the average fluid temperature in the borefield is "
                         f"{t} °C (heat pump source side). Take it from the data sheet at the supply temperature "
                         "of your heating system.")


def _eer_prop(t, default):
    return Property(f"eer_{t}", f"EER at {t} °C fluid", default, min=1.0, max=100.0, step=0.1,
                    help=f"Cooling EER when the average fluid temperature is {t} °C. Passive cooling (only pumps): "
                         "use a high value such as 20.")


COP_KEYS = tuple(f"cop_{t}".replace("-", "m") for t in COP_TEMPS)
EER_KEYS = tuple(f"eer_{t}" for t in EER_TEMPS)


def curves(values: dict) -> tuple[np.ndarray, np.ndarray]:
    return (np.array([values[k] for k in COP_KEYS], dtype=float), np.array([values[k] for k in EER_KEYS], dtype=float))


def _build(values: dict) -> dict:
    cop, eer = curves(values)
    return {"cop": COP(cop, np.array(COP_TEMPS, dtype=float)), "eer": EER(eer, np.array(EER_TEMPS, dtype=float))}


def _cop_rises(values: dict) -> str | None:
    cop, _ = curves(values)
    if np.any(np.diff(cop) < 0):
        return t("The COP usually rises with the fluid temperature. Check the values from left to right.")
    return None


register(Section(
    key="heat_pump",
    group="Loads",
    label="Heat pump efficiency",
    order=65,
    help="Only used with building demand (yearly or hourly), where the heat pump turns building demand "
         "into ground load.",
    variants=(
        Variant(
            key="fixed",
            label="Fixed SCOP / SEER",
            help="Uses the SCOP and SEER entered with the building demand above.",
            properties=(),
            build=lambda v: None,
        ),
        Variant(
            key="curve",
            label="Depends on the fluid temperature",
            help="The COP falls as the borefield gets colder, so more electricity and less ground heat are needed "
                 "in a cold year. Replaces the SCOP and SEER above and gives the real seasonal performance factor. "
                 "Sizing takes longer, with hourly sizing one to two minutes.",
            properties=tuple(_cop_prop(t, d) for t, d in zip(COP_TEMPS, HEATING_CURVES["Floor heating (35 °C)"]))
            + tuple(_eer_prop(t, d) for t, d in zip(EER_TEMPS, COOLING_CURVES["Passive cooling (pumps only)"])),
            build=_build,
            presets=(
                PresetGroup("Heating system", {name: dict(zip(COP_KEYS, vals)) for name, vals in HEATING_CURVES.items()},
                            help="Typical brine/water heat pump COPs at three supply temperatures (EN 14511 data "
                                 "sheets). Replace them with your heat pump's values if you have them."),
                PresetGroup("Cooling", {name: dict(zip(EER_KEYS, vals)) for name, vals in COOLING_CURVES.items()},
                            help="Passive cooling uses only the circulation pumps; active cooling runs the heat pump "
                                 "as a chiller."),
            ),
            warnings=(_cop_rises,),
        ),
    ),
))
