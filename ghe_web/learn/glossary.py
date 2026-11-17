"""The glossary of Learn mode: the technical terms used in the labels, with a definition, the unit, a typical range
and the numbers of the sources (see ``sources.py``). ``FIELDS`` links an input field to its term, so the "?" help of
the field can say where to read more.

Typical ranges are the ones the app already shows next to the inputs (``guidance.TYPICAL``) where there is one.
"""
from __future__ import annotations

from dataclasses import dataclass

from .text import L


@dataclass(frozen=True)
class Term:
    key: str
    en: str
    de: str
    symbol: str  # symbol and unit, e.g. "λ [W/(m·K)]"; "" when none
    text_en: str
    text_de: str
    sources: tuple[int, ...]
    module: int  # the introduction module that explains it

    @property
    def name(self) -> str:
        return L(self.en, self.de)

    @property
    def text(self) -> str:
        return L(self.text_en, self.text_de)


TERMS: tuple[Term, ...] = (
    Term("k_s", "Ground thermal conductivity", "Wärmeleitfähigkeit des Untergrunds", "λ [W/(m·K)]",
         "How well the ground conducts heat to the boreholes. The most important ground property for the length: "
         "a higher value means shorter boreholes. Usually 1.5 to 3.5 W/(m·K) in Germany; best measured with a "
         "thermal response test.",
         "Wie gut der Untergrund Wärme zu den Sonden leitet. Die wichtigste Untergrundeigenschaft für die Länge: "
         "ein höherer Wert bedeutet kürzere Sonden. In Deutschland meist 1,5 bis 3,5 W/(m·K); am besten mit einem "
         "Thermal Response Test gemessen.", (8, 3), 1),
    Term("T_g", "Undisturbed ground temperature", "Ungestörte Untergrundtemperatur", "T_g [°C]",
         "Temperature of the ground at the depth of the boreholes before the system runs. In Germany usually 8 to "
         "14 °C; it rises with depth (geothermal gradient). Every kelvin less costs length, because the fluid limit "
         "stays the same.",
         "Temperatur des Untergrunds in Sondentiefe, bevor die Anlage läuft. In Deutschland meist 8 bis 14 °C; sie "
         "steigt mit der Tiefe (geothermischer Gradient). Jedes Kelvin weniger kostet Länge, weil die Grenze für das "
         "Fluid gleich bleibt.", (8,), 1),
    Term("volumetric_heat_capacity", "Volumetric heat capacity", "Volumetrische Wärmekapazität", "ρc [MJ/(m³·K)]",
         "How much heat one cubic metre of ground stores per kelvin. Matters for short periods (months, peaks); "
         "much less than the conductivity for the long term. Usually 1.8 to 2.8 MJ/(m³·K).",
         "Wie viel Wärme ein Kubikmeter Untergrund je Kelvin speichert. Wichtig für kurze Zeiträume (Monate, "
         "Spitzen), langfristig viel weniger als die Wärmeleitfähigkeit. Meist 1,8 bis 2,8 MJ/(m³·K).", (8,), 1),
    Term("trt", "Thermal response test (TRT)", "Thermal Response Test (TRT)", "",
         "A field test on a finished borehole: heated fluid circulates for a few days while inlet and outlet "
         "temperatures are logged. The result is the effective ground thermal conductivity and the borehole "
         "resistance at the site. Recommended for larger fields.",
         "Ein Feldversuch an einer fertigen Sonde: Erwärmtes Fluid zirkuliert einige Tage, Vor- und "
         "Rücklauftemperatur werden aufgezeichnet. Ergebnis sind die effektive Wärmeleitfähigkeit und der "
         "Bohrlochwiderstand am Standort. Für größere Felder empfohlen.", (4,), 1),
    Term("gfunction", "g-function", "g-Funktion", "g [–]",
         "The dimensionless temperature response of the whole field to a constant heat flow, as a function of "
         "time. Introduced by Eskilson. It contains the field's geometry: spacing, number and length of the "
         "boreholes. Its rise at long times shows how strongly the boreholes influence each other.",
         "Die dimensionslose Temperaturantwort des ganzen Feldes auf einen konstanten Wärmestrom, abhängig von der "
         "Zeit. Von Eskilson eingeführt. Sie enthält die Geometrie des Feldes: Abstand, Anzahl und Länge der "
         "Sonden. Ihr Anstieg bei langen Zeiten zeigt, wie stark sich die Sonden gegenseitig beeinflussen.", (3, 7), 2),
    Term("spacing", "Borehole spacing", "Sondenabstand", "B [m]",
         "Distance between neighbouring boreholes. Closer boreholes share the same ground and cool each other "
         "down over the years, so the field needs more length. Usually 5 to 10 m.",
         "Abstand benachbarter Sonden. Nahe Sonden teilen sich denselben Untergrund und kühlen sich über die "
         "Jahre gegenseitig ab, das Feld braucht dann mehr Länge. Meist 5 bis 10 m.", (4, 3), 2),
    Term("Rb", "Borehole thermal resistance", "Thermischer Bohrlochwiderstand", "R_b [m·K/W]",
         "How much the borehole itself resists the heat flow between the borehole wall and the fluid: fluid film, "
         "pipe wall and grout in series. Multiply by the heat flow per metre to get the temperature difference "
         "inside the borehole. Lower is better; usually about 0.06 to 0.15 m·K/W.",
         "Wie stark das Bohrloch selbst den Wärmestrom zwischen Bohrlochwand und Fluid behindert: Fluidgrenzschicht, "
         "Rohrwand und Verfüllung hintereinander. Mal Wärmestrom je Meter ergibt den Temperaturunterschied im "
         "Bohrloch. Kleiner ist besser; meist etwa 0,06 bis 0,15 m·K/W.", (4, 7), 2),
    Term("k_g", "Grout thermal conductivity", "Wärmeleitfähigkeit der Verfüllung", "λ_g [W/(m·K)]",
         "Conductivity of the material that fills the borehole around the pipes. Usually the largest part of the "
         "borehole resistance. Standard bentonite is about 0.8, thermally enhanced grouts 1.6 to 2.4 W/(m·K).",
         "Wärmeleitfähigkeit des Materials, das das Bohrloch um die Rohre füllt. Meist der größte Teil des "
         "Bohrlochwiderstands. Standard-Bentonit etwa 0,8, thermisch verbesserte Verfüllbaustoffe 1,6 bis "
         "2,4 W/(m·K).", (4, 5), 2),
    Term("reynolds", "Reynolds number", "Reynolds-Zahl", "Re [–]",
         "Tells whether the flow in the pipes is laminar (below about 2300) or turbulent. Laminar flow transfers "
         "heat poorly, so the borehole resistance rises. A higher flow rate or a lower glycol share helps, at the "
         "cost of pump power.",
         "Zeigt, ob die Strömung in den Rohren laminar (unter etwa 2300) oder turbulent ist. Laminare Strömung "
         "überträgt Wärme schlecht, der Bohrlochwiderstand steigt. Mehr Durchfluss oder weniger Glykol hilft, "
         "kostet aber Pumpenleistung.", (7,), 2),
    Term("mfr", "Mass flow rate per borehole", "Massenstrom je Sonde", "ṁ [kg/s]",
         "How much heat transfer fluid flows through one borehole. Sets the Reynolds number and the pressure drop.",
         "Wie viel Wärmeträgerfluid durch eine Sonde fließt. Bestimmt die Reynolds-Zahl und den Druckverlust.",
         (7,), 2),
    Term("scop", "SCOP", "SCOP (Jahresarbeitszahl)", "SCOP [–]",
         "Seasonal coefficient of performance of the heat pump: heat delivered per unit of electricity over a "
         "year. The ground supplies the rest: ground extraction = heating × (1 − 1/SCOP). Brine/water heat pumps "
         "reach about 3.5 to 5.5.",
         "Jahresarbeitszahl der Wärmepumpe: abgegebene Wärme je Einheit Strom über ein Jahr. Den Rest liefert der "
         "Untergrund: Entzug = Heizwärme × (1 − 1/SCOP). Sole/Wasser-Wärmepumpen erreichen etwa 3,5 bis 5,5.",
         (4,), 3),
    Term("full_load_hours", "Full-load hours", "Volllaststunden", "h/yr",
         "Yearly energy divided by the peak power. Few full-load hours mean short peaks; many mean the field "
         "works hard all year and needs more length. Heating in German homes often runs about 1,800 to 2,400 h.",
         "Jahresenergie geteilt durch die Spitzenleistung. Wenige Volllaststunden bedeuten kurze Spitzen; viele "
         "bedeuten, dass das Feld das ganze Jahr arbeitet und mehr Länge braucht. Heizung in Wohngebäuden läuft "
         "oft etwa 1.800 bis 2.400 h.", (4,), 3),
    Term("imbalance", "Ground imbalance", "Unausgeglichene Jahresbilanz", "MWh/yr",
         "Difference between the heat taken from the ground and the heat put back per year. A net extraction "
         "cools the ground a little more every year; that slow drift is why GHEtool checks the last year.",
         "Unterschied zwischen dem Wärmeentzug und dem Wärmeeintrag pro Jahr. Ein Nettoentzug kühlt den "
         "Untergrund jedes Jahr etwas mehr ab; wegen dieser langsamen Drift prüft GHEtool das letzte Jahr.", (1,), 3),
    Term("regeneration", "Regeneration", "Regeneration", "",
         "Putting heat back into the ground, e.g. by cooling the building in summer or with solar heat. It "
         "reduces the imbalance and therefore the length.",
         "Wärme zurück in den Untergrund bringen, z. B. durch Kühlen des Gebäudes im Sommer oder mit Solarwärme. "
         "Sie verringert die Jahresbilanz und damit die Länge.", (1, 6), 3),
    Term("limits", "Fluid temperature limits", "Grenzen der Fluidtemperatur", "T_f [°C]",
         "The lowest and highest mean fluid temperature the design may reach. The sizing makes the boreholes "
         "just long enough to stay within them. The lower limit protects the grout and the ground from freezing; "
         "check the rules of the state and VDI 4640-2.",
         "Die niedrigste und höchste mittlere Fluidtemperatur, die die Anlage erreichen darf. Die Auslegung macht "
         "die Sonden gerade lang genug, um sie einzuhalten. Die untere Grenze schützt Verfüllung und Untergrund vor "
         "Frost; Regeln des Bundeslands und VDI 4640-2 prüfen.", (4,), 4),
    Term("antifreeze", "Antifreeze (water-glycol)", "Frostschutz (Wasser-Glykol)", "%",
         "Glycol in the heat transfer fluid lowers its freezing point, so the fluid may go below 0 °C. More glycol "
         "makes the fluid more viscous: more pressure drop and earlier laminar flow. Usually 20 to 33 %.",
         "Glykol im Wärmeträgerfluid senkt den Gefrierpunkt, so darf das Fluid unter 0 °C fallen. Mehr Glykol "
         "macht das Fluid zäher: mehr Druckverlust und früher laminare Strömung. Meist 20 bis 33 %.", (4,), 4),
    Term("sizing_method", "Monthly and hourly sizing (L2, L3, L4)", "Monatliche und stündliche Auslegung (L2, L3, L4)",
         "",
         "GHEtool sizes with monthly loads plus a peak per month (L2: first or last year, L3: every year) or with "
         "hourly loads (L4, slower and more exact for short peaks).",
         "GHEtool legt mit Monatslasten plus einer Spitze je Monat aus (L2: erstes oder letztes Jahr, L3: jedes "
         "Jahr) oder mit Stundenlasten (L4, langsamer und genauer bei kurzen Spitzen).", (1, 12), 5),
    Term("specific_rate", "Specific extraction rate", "Spezifische Entzugsleistung", "W/m",
         "Heat extracted per metre of borehole. A rule-of-thumb value from tables only holds for small systems with "
         "typical running hours; a simulation also counts the yearly energy, the neighbours and the years.",
         "Entzogene Wärme je Meter Sonde. Ein Faustwert aus Tabellen gilt nur für kleine Anlagen mit üblichen "
         "Laufzeiten; eine Simulation berücksichtigt auch die Jahresenergie, die Nachbarn und die Jahre.", (4,), 5),
    Term("simulation_period", "Simulation period", "Simulationszeitraum", "years",
         "How many years the design is checked for. Longer periods show more of the slow drift; this app uses 50 "
         "years by default.",
         "Für wie viele Jahre die Auslegung geprüft wird. Längere Zeiträume zeigen mehr von der langsamen Drift; "
         "diese Anwendung nimmt standardmäßig 50 Jahre.", (1,), 5),
)

BY_KEY = {term.key: term for term in TERMS}

# Input field (property key) -> glossary term, for the "Read more" line in the field's "?" help
FIELDS = {"k_s": "k_s", "T_g": "T_g", "volumetric_heat_capacity": "volumetric_heat_capacity", "B_1": "spacing",
          "B_2": "spacing", "Rb": "Rb", "k_g": "k_g", "mfr": "mfr", "scop": "scop",
          "full_load_hours_heating": "full_load_hours", "full_load_hours_cooling": "full_load_hours",
          "T_min": "limits", "T_max": "limits", "percentage": "antifreeze", "simulation_period": "simulation_period"}


def for_field(key: str) -> Term | None:
    return BY_KEY.get(FIELDS.get(key, ""))
