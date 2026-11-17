"""The glossary of Learn mode: every parameter and concept with its symbol, a definition, the governing relation,
how it is obtained in practice, typical values and the numbers of the sources (``sources.py``).

``FIELDS`` links an input field to its term, so the "?" help of the field in Simple and Expert can point here.
Texts are written for readers with a scientific or engineering degree: precise, not simplified.
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
    text_en: str  # definition and role in the sizing (Markdown)
    text_de: str
    equation: str = ""  # governing relation (LaTeX), "" when none
    practice_en: str = ""  # how it is obtained, typical values
    practice_de: str = ""
    sources: tuple[int, ...] = ()

    @property
    def name(self) -> str:
        return L(self.en, self.de)

    @property
    def text(self) -> str:
        return L(self.text_en, self.text_de)

    @property
    def practice(self) -> str:
        return L(self.practice_en, self.practice_de)


TERMS: tuple[Term, ...] = (
    Term("k_s", "Ground thermal conductivity", "Wärmeleitfähigkeit des Untergrunds", "λ [W/(m·K)]",
         "Effective conductivity of the rock mass over the borehole length, including groundwater in the pores at "
         "rest. It sets the ground thermal resistances of all time scales, R_y, R_m and R_h, which scale with 1/λ. "
         "The borehole resistance does not. For peak-dominated designs the length therefore falls "
         "less than in proportion to λ (elasticity about −0.6). In drift-dominated large fields it can reach −1 "
         "or beyond, because a shorter field also has a larger late-time g-function.",
         "Effektive Leitfähigkeit des Gebirges über die Sondenlänge, einschließlich ruhenden Porenwassers. Sie "
         "bestimmt die Untergrundwiderstände aller Zeitskalen, R_y, R_m und R_h, die mit 1/λ skalieren. Der "
         "Bohrlochwiderstand tut das nicht. Bei spitzendominierter Auslegung sinkt die Länge daher "
         "unterproportional mit λ (Elastizität etwa −0,6). In driftdominierten großen Feldern kann sie −1 oder "
         "mehr erreichen, weil ein kürzeres Feld auch eine größere g-Funktion bei großen Zeiten hat.",
         r"R_{y,m,h} \propto \frac{g(t)}{2\pi\lambda}",
         "Measured in situ with a thermal response test (TRT, line-source evaluation). Without a TRT, use "
         "layer-weighted values from rock tables (VDI 4640-1). Consolidated rock is typically 1.5–3.5 W/(m·K), "
         "dry unconsolidated sediments are lower and quartzite is higher.",
         "In situ mit einem Thermal Response Test gemessen (TRT, Linienquellen-Auswertung). Ohne TRT "
         "schichtgewichtete Tabellenwerte (VDI 4640-1). Festgestein liegt typischerweise bei 1,5–3,5 W/(m·K), "
         "trockene Lockergesteine darunter, Quarzit darüber.", (8, 3)),
    Term("T_g", "Undisturbed ground temperature", "Ungestörte Untergrundtemperatur", "T_g [°C]",
         "Mean temperature of the ground over the borehole length before operation: the surface temperature plus "
         "the geothermal gradient (about 3 K per 100 m) times half the depth. Every temperature in the sizing is "
         "a difference to T_g. A lower T_g moves the whole fluid curve down towards the lower limit, which costs "
         "length at roughly constant m per K.",
         "Mittlere Temperatur des Untergrunds über die Sondenlänge vor Betriebsbeginn: Oberflächentemperatur plus "
         "geothermischer Gradient (etwa 3 K je 100 m) mal halber Tiefe. Alle Temperaturen der Auslegung sind "
         "Differenzen zu T_g. Ein niedrigeres T_g verschiebt die ganze Fluidkurve zur unteren Grenze hin und "
         "kostet Länge mit annähernd konstanten Metern je Kelvin.",
         r"T_g(H) = T_{s} + \frac{\mathrm{d}T}{\mathrm{d}z}\,\frac{H}{2}",
         "Taken from the undisturbed initial phase of a TRT or from a temperature log. In Germany it is typically "
         "9–13 °C at 50–150 m. Urban heat islands add 1–3 K.",
         "Aus der ungestörten Anfangsphase eines TRT oder einem Temperaturlog. In Deutschland typischerweise "
         "9–13 °C in 50–150 m Tiefe. Städtische Wärmeinseln heben sie um 1–3 K an.", (8, 4)),
    Term("volumetric_heat_capacity", "Volumetric heat capacity", "Volumetrische Wärmekapazität", "ρc [MJ/(m³·K)]",
         "Enters through the diffusivity a = λ/(ρc), which sets the time scale of the ground response "
         "(Eskilson's t_s = H²/(9a)). It mainly affects the monthly and peak response. The long-term term "
         "depends on it only weakly, so the length elasticity is usually small (|ε| < 0.2).",
         "Geht über die Temperaturleitfähigkeit a = λ/(ρc) ein, die die Zeitskala der Untergrundantwort bestimmt "
         "(Eskilsons t_s = H²/(9a)). Sie wirkt vor allem auf die Monats- und Spitzenantwort. Der Langzeitterm "
         "hängt nur schwach davon ab, die Elastizität der Länge ist daher meist klein (|ε| < 0,2).",
         r"a = \frac{\lambda}{\rho c}, \qquad t_s = \frac{H^2}{9a}",
         "Taken from tables by rock type and saturation, typically 1.8–2.8 MJ/(m³·K). It is rarely measured.",
         "Aus Tabellen nach Gesteinsart und Sättigung, typischerweise 1,8–2,8 MJ/(m³·K). Selten gemessen.", (8, 3)),
    Term("trt", "Thermal response test (TRT)", "Thermal Response Test (TRT)", "",
         "A field test on a completed borehole. A constant heat rate is injected for 48–72 h while the inlet and "
         "outlet temperatures are logged. At late times the mean fluid temperature rises linearly with ln t. The "
         "slope gives λ, and the intercept gives R_b at the test flow rate.",
         "Ein Feldversuch an einer fertigen Sonde. Für 48–72 h wird eine konstante Wärmeleistung eingetragen, "
         "Vor- und Rücklauf werden aufgezeichnet. Für große Zeiten steigt die mittlere Fluidtemperatur linear mit "
         "ln t. Die Steigung liefert λ, der Achsenabschnitt R_b beim Prüfdurchfluss.",
         r"T_f(t) \approx \frac{q}{4\pi\lambda}\left[\ln\frac{4at}{r_b^2}-\gamma\right] + q R_b + T_g",
         "Recommended by VDI 4640-2 for fields above about 30 kW. The test borehole should be representative "
         "of the field in depth and completion.",
         "Nach VDI 4640-2 ab etwa 30 kW empfohlen. Die Testsonde sollte in Tiefe und Ausbau repräsentativ für "
         "das Feld sein.", (4, 3)),
    Term("gfunction", "g-function", "g-Funktion", "g(t/t_s, B/H, r_b/H) [–]",
         "The dimensionless step response of the whole field: the mean borehole wall temperature after a unit "
         "step of heat rate per metre. It contains the geometry: layout, spacing, depth and borehole radius. At "
         "large times it rises above the single-borehole curve as the boreholes interact. GHEtool superposes it "
         "for the yearly, monthly and peak pulses.",
         "Die dimensionslose Sprungantwort des ganzen Feldes: die mittlere Bohrlochwandtemperatur nach einem "
         "Einheitssprung der Wärmeleistung je Meter. Sie enthält die Geometrie: Anordnung, Abstand, Tiefe und "
         "Bohrlochradius. Für große Zeiten steigt sie über die Kurve der Einzelsonde, weil die Sonden "
         "wechselwirken. GHEtool überlagert sie für den Jahres-, Monats- und Spitzenpuls.",
         r"T_b(t) = T_g - \frac{q'}{2\pi\lambda}\, g\!\left(\frac{t}{t_s}, \frac{B}{H}, \frac{r_b}{H}\right)",
         "pygfunction computes it, for example with the equivalent-borehole method and a uniform borehole wall "
         "temperature as the boundary condition.",
         "Von pygfunction berechnet, z. B. mit der Methode äquivalenter Sonden und gleichförmiger "
         "Bohrlochwandtemperatur als Randbedingung.", (3, 7)),
    Term("spacing", "Borehole spacing", "Sondenabstand", "B [m]",
         "The centre-to-centre distance in the grid. Smaller B/H increases the late-time g-function and so the "
         "long-term drift. A heating-only field reacts strongly. A field with balanced extraction and injection "
         "reacts weakly, because its long-term term nearly cancels. Small fields benefit less than large compact "
         "ones.",
         "Der Achsabstand im Raster. Kleineres B/H erhöht die g-Funktion bei großen Zeiten und damit die "
         "Langzeitdrift. Ein reines Heizfeld reagiert stark. Ein Feld mit ausgeglichenem Entzug und Eintrag "
         "reagiert schwach, weil sich sein Langzeitterm nahezu aufhebt. Kleine Felder profitieren weniger als "
         "große kompakte.",
         r"\frac{\partial g}{\partial (B/H)} < 0 \quad (t \gtrsim t_s/100)",
         "VDI 4640-2 recommends at least 6 m for boreholes up to 100 m in larger fields. The state guidelines "
         "often require 5–6 m and distances to the property boundary.",
         "VDI 4640-2 empfiehlt bei größeren Feldern mindestens 6 m für Sonden bis 100 m. Die Landesleitfäden "
         "fordern oft 5–6 m und Abstände zur Grundstücksgrenze.", (4, 3)),
    Term("borehole_radius", "Borehole radius", "Bohrlochradius", "r_b [mm]",
         "A larger r_b lowers the ground resistance slightly, because the wall is further out, but it adds grout "
         "volume. The net effect on R_b depends on the pipe positions and on λ_g. For good grouts a larger "
         "diameter changes the length only by a few per cent.",
         "Ein größeres r_b senkt den Untergrundwiderstand leicht, weil die Wand weiter außen liegt, vergrößert "
         "aber das Verfüllvolumen. Die Nettowirkung auf R_b hängt von der Rohrlage und λ_g ab. Bei guten "
         "Verfüllungen ändert ein größerer Radius die Länge nur um wenige Prozent.",
         "",
         "Typically r_b = 70–90 mm, a drilled diameter of 140–180 mm, for a double U 32 mm. The minimum annulus for grouting is set by the state "
         "guidelines.",
         "Typischerweise r_b = 70–90 mm, also 140–180 mm Bohrdurchmesser, für Doppel-U 32 mm. Der Mindestringraum für die Verpressung ist in den "
         "Landesleitfäden festgelegt.", (5, 4)),
    Term("Rb", "Effective borehole thermal resistance", "Effektiver thermischer Bohrlochwiderstand", "R_b* [m·K/W]",
         "The resistance between the mean fluid temperature and the borehole wall per metre. It is the sum of "
         "the convective film resistance, the pipe wall resistance and the grout resistance (multipole method), "
         "corrected for thermal short-circuit between the legs. Its share of the temperature difference is "
         "largest at the peak: ΔT = q'·R_b.",
         "Der Widerstand zwischen mittlerer Fluidtemperatur und Bohrlochwand je Meter. Er ist die Summe aus "
         "konvektivem Filmwiderstand, Rohrwandwiderstand und Verfüllwiderstand (Multipolmethode), korrigiert um "
         "den thermischen Kurzschluss zwischen den Schenkeln. Sein Anteil an der Temperaturdifferenz ist in der "
         "Spitze am größten: ΔT = q'·R_b.",
         r"R_b^* = R_{\mathrm{conv}} + R_{\mathrm{pipe}} + R_{\mathrm{grout}}, \quad R_{\mathrm{conv}} = "
         r"\frac{1}{n\,\pi d_i h}",
         "Typically 0.06–0.10 m·K/W for double U with enhanced grout and turbulent flow, and 0.12–0.20 m·K/W "
         "with standard bentonite or laminar flow. It can be measured with a TRT.",
         "Typischerweise 0,06–0,10 m·K/W bei Doppel-U mit thermisch verbesserter Verfüllung und turbulenter "
         "Strömung, 0,12–0,20 m·K/W bei Standard-Bentonit oder laminarer Strömung. Mit TRT messbar.", (7, 4)),
    Term("k_g", "Grout thermal conductivity", "Wärmeleitfähigkeit der Verfüllung", "λ_g [W/(m·K)]",
         "The conductivity of the annulus fill. It usually dominates R_b, since R_grout is roughly proportional "
         "to 1/λ_g. Going from 0.8 to 2.0 W/(m·K) typically halves R_b. The return diminishes once the film "
         "resistance dominates.",
         "Die Leitfähigkeit der Ringraumverfüllung. Sie dominiert meist R_b, da R_grout etwa proportional zu "
         "1/λ_g ist. Der Schritt von 0,8 auf 2,0 W/(m·K) halbiert R_b typischerweise. Der Nutzen nimmt ab, "
         "sobald der Filmwiderstand dominiert.",
         r"R_{\mathrm{grout}} \approx \frac{1}{2\pi\lambda_g}\,\beta(r_b, r_p, s)",
         "Standard bentonite–cement is about 0.8 W/(m·K), and thermally enhanced grouts are 1.6–2.4 W/(m·K). "
         "The LQS EWS (BW) requires certified, frost-resistant grouts.",
         "Standard-Bentonit-Zement etwa 0,8 W/(m·K), thermisch verbesserte Verfüllungen 1,6–2,4 W/(m·K). Die "
         "LQS EWS (BW) verlangt zertifizierte, frostbeständige Baustoffe.", (4, 5)),
    Term("mfr", "Mass flow rate per borehole", "Massenstrom je Sonde", "ṁ [kg/s]",
         "It sets the Reynolds number in the pipes and with it the convective film resistance. Below "
         "Re ≈ 2,300 the flow is laminar: the Nusselt number drops to about 4.4 and R_b jumps. Above the "
         "transition, more flow gains little and costs pumping power, which rises with roughly the cube of the "
         "flow.",
         "Er bestimmt die Reynolds-Zahl in den Rohren und damit den konvektiven Filmwiderstand. Unter "
         "Re ≈ 2.300 ist die Strömung laminar: die Nusselt-Zahl fällt auf etwa 4,4 und R_b springt. Oberhalb des "
         "Übergangs bringt mehr Durchfluss wenig und kostet Pumpenleistung, die etwa mit der dritten Potenz "
         "des Durchflusses steigt.",
         r"Re = \frac{4\,\dot m_{\mathrm{leg}}}{\pi d_i \mu}, \qquad Nu_{\mathrm{lam}} \approx 4.36",
         "Choose the flow so that Re exceeds about 2,300–3,000 at the lowest fluid temperature, where the "
         "viscosity of the antifreeze is highest. A double U splits the flow over two circuits.",
         "Den Durchfluss so wählen, dass Re bei der tiefsten Fluidtemperatur über etwa 2.300–3.000 liegt, wo "
         "die Viskosität des Frostschutzgemischs am höchsten ist. Doppel-U teilt den Durchfluss auf zwei "
         "Kreise.", (7, 4)),
    Term("reynolds", "Reynolds number", "Reynolds-Zahl", "Re [–]",
         "The ratio of inertial to viscous forces in the pipe flow. It decides between laminar flow "
         "(Re < 2,300, Nu ≈ 4.36) and turbulent flow (Gnielinski correlation). The transition region is uncertain; "
         "design for clearly turbulent flow at the lowest fluid temperature.",
         "Verhältnis von Trägheits- zu Zähigkeitskräften in der Rohrströmung. Sie entscheidet zwischen laminarer "
         "Strömung (Re < 2.300, Nu ≈ 4,36) und turbulenter Strömung (Gnielinski-Korrelation). Der "
         "Übergangsbereich ist unsicher; für eindeutig turbulente Strömung bei tiefster Fluidtemperatur "
         "auslegen.",
         r"Re = \frac{\rho\, v\, d_i}{\mu}", "", "", (7,)),
    Term("antifreeze", "Antifreeze concentration", "Frostschutzkonzentration", "w [%]",
         "Glycol lowers the freezing point and permits fluid temperatures below 0 °C. It raises the viscosity, "
         "which lowers Re and raises the pressure drop, and it lowers the specific heat capacity.",
         "Glykol senkt den Gefrierpunkt und erlaubt Fluidtemperaturen unter 0 °C. Es erhöht die Viskosität, "
         "was Re senkt und den Druckverlust erhöht, und es senkt die spezifische Wärmekapazität.",
         "",
         "Monoethylene or monopropylene glycol at 20–33 % by volume. Some states restrict the substances and "
         "concentrations in water protection areas.",
         "Monoethylen- oder Monopropylenglykol mit 20–33 Vol.-%. Einige Länder beschränken Stoffe und "
         "Konzentrationen in Wasserschutzgebieten.", (4, 10)),
    Term("peak_load", "Peak heating load", "Heizlast (Spitze)", "Q̇_H [kW]",
         "The building's design heating load. On the ground side it becomes the peak extraction "
         "Q̇_H(1 − 1/COP), applied for the peak duration in each month. It drives the short-term term q_h·R_h "
         "and the borehole term q_h·R_b, so it often decides small fields.",
         "Die Norm-Heizlast des Gebäudes. Erdseitig wird daraus der Spitzenentzug Q̇_H(1 − 1/COP), der in jedem "
         "Monat für die Spitzendauer angesetzt wird. Sie treibt den Kurzzeitterm q_h·R_h und den Bohrlochterm "
         "q_h·R_b und entscheidet daher oft kleine Felder.",
         r"\dot Q_{\mathrm{ext}} = \dot Q_H\left(1-\frac{1}{\mathrm{COP}}\right)",
         "Calculated to DIN EN 12831. Sizing the heat pump for the full heating load without a backup is usual "
         "in Germany.",
         "Nach DIN EN 12831. Eine monovalente Auslegung der Wärmepumpe ist in Deutschland üblich.", (4,)),
    Term("full_load_hours", "Full-load hours", "Volllaststunden", "t_FL [h/a]",
         "The annual energy divided by the peak power. Together with the peak it fixes the annual extraction and "
         "so the long-term term q_y·R_y. More hours at the same peak shift the design from peak-dominated to "
         "drift-dominated.",
         "Jahresenergie geteilt durch die Spitzenleistung. Zusammen mit der Spitze legt sie den Jahresentzug "
         "und damit den Langzeitterm q_y·R_y fest. Mehr Stunden bei gleicher Spitze verschieben die Auslegung "
         "von spitzen- zu driftdominiert.",
         r"Q_{a} = \dot Q_{\max}\, t_{FL}",
         "For heating only, typically 1,800–2,400 h/a, and more with domestic hot water. VDI 4640-2 tables "
         "give specific extraction rates for 1,800 and 2,400 h.",
         "Für reines Heizen typischerweise 1.800–2.400 h/a, mit Warmwasser mehr. Die Tabellen der VDI 4640-2 "
         "geben spezifische Entzugsleistungen für 1.800 und 2.400 h.", (4,)),
    Term("scop", "Seasonal coefficient of performance", "Jahresarbeitszahl", "SCOP [–]",
         "The ratio of delivered heat to electrical energy over a year. The ground supplies the part not covered "
         "by electricity, Q_H(1 − 1/SCOP), so a higher SCOP means more extraction for the same building load. "
         "The length rises slightly with SCOP, while the operating cost falls.",
         "Verhältnis von abgegebener Wärme zu elektrischer Energie über ein Jahr. Der Untergrund liefert den "
         "nicht durch Strom gedeckten Teil, Q_H(1 − 1/SCOP); eine höhere JAZ bedeutet daher mehr Entzug bei "
         "gleicher Gebäudelast. Die Länge steigt mit der JAZ leicht, die Betriebskosten sinken.",
         r"Q_{\mathrm{ground}} = Q_H\left(1 - \frac{1}{\mathrm{SCOP}}\right)",
         "Brine/water heat pumps reach about 4–5 with floor heating at 35 °C and about 3–3.5 with radiators at "
         "55 °C. It depends on the source temperature, so it also depends on the borefield design.",
         "Sole/Wasser-Wärmepumpen erreichen etwa 4–5 mit Fußbodenheizung (35 °C) und etwa 3–3,5 mit "
         "Heizkörpern (55 °C). Sie hängt von der Quelltemperatur ab und damit auch von der "
         "Sondenfeldauslegung.", (4,)),
    Term("seer", "Seasonal energy efficiency ratio", "Saisonale Kühlleistungszahl", "SEER [–]",
         "The ratio of cooling energy to electrical energy. The ground absorbs Q_C(1 + 1/SEER). Passive (free) "
         "cooling through the borefield has a very high SEER of 15–30, so its injection almost equals the "
         "cooling energy. Active cooling with a chiller adds the compressor work.",
         "Verhältnis von Kälteenergie zu elektrischer Energie. Der Untergrund nimmt Q_C(1 + 1/SEER) auf. "
         "Passive (freie) Kühlung über das Sondenfeld hat eine sehr hohe SEER von 15–30, der Eintrag entspricht "
         "daher fast der Kälteenergie. Aktive Kühlung mit Kältemaschine fügt die Verdichterarbeit hinzu.",
         r"Q_{\mathrm{inj}} = Q_C\left(1 + \frac{1}{\mathrm{SEER}}\right)", "", "", (4,)),
    Term("imbalance", "Annual ground imbalance", "Jährliche Untergrundbilanz", "Q_ext − Q_inj [MWh/a]",
         "The net heat extracted from the ground per year. Its mean heat rate per metre, q_y, drives the "
         "long-term term q_y·R_y with R_y = g(t_end)/(2πλ). That term grows with time and with the interaction "
         "between boreholes, so it is the reason the last simulated year usually limits large fields.",
         "Die netto je Jahr entzogene Wärme. Ihre mittlere Leistung je Meter, q_y, treibt den Langzeitterm "
         "q_y·R_y mit R_y = g(t_end)/(2πλ). Dieser Term wächst mit der Zeit und mit der Wechselwirkung der "
         "Sonden; deshalb begrenzt bei großen Feldern meist das letzte Simulationsjahr.",
         r"q_y = \frac{Q_{\mathrm{ext}}-Q_{\mathrm{inj}}}{8760\,\mathrm{h}\cdot N H}",
         "", "", (1, 3)),
    Term("peak_cooling", "Peak cooling load", "Kühllast (Spitze)", "Q̇_C [kW]",
         "The building's design cooling load. On the ground side it becomes the peak injection "
         "Q̇_C(1 + 1/EER), or Q̇_C alone for passive cooling. Its annual energy offsets the extraction and lowers "
         "q_y; its peak sets the summer maximum through q_h·(R_h + R_b). In a heating-dominated field more "
         "cooling therefore shortens the field until the upper limit T_f,max starts to govern.",
         "Die Auslegungskühllast des Gebäudes. Im Untergrund wird sie zur Spitzeneinspeisung "
         "Q̇_C(1 + 1/EER), bei passiver Kühlung zu Q̇_C selbst. Ihre Jahresenergie gleicht den Entzug aus und "
         "senkt q_y; ihre Spitze bestimmt über q_h·(R_h + R_b) das Sommermaximum. In einem heizdominierten Feld "
         "verkürzt mehr Kühlung das Feld daher, bis die obere Grenze T_f,max maßgebend wird.",
         "", "", "", (3, 4)),
    Term("regeneration", "Thermal regeneration", "Thermische Regeneration", "Q_inj/Q_ext [–]",
         "Heat deliberately returned to the ground, for example from passive cooling, solar collectors or "
         "dry-coolers. It reduces q_y and with it the long-term drift. For a large heating-only field it is often "
         "the most effective way to save length; for a small field the peak still limits.",
         "Gezielt in den Untergrund zurückgeführte Wärme, etwa aus passiver Kühlung, Solarkollektoren oder "
         "Rückkühlern. Sie senkt q_y und damit die Langzeitdrift. Für ein großes reines Heizfeld ist sie oft der "
         "wirksamste Hebel, Länge zu sparen; bei kleinen Feldern begrenzt weiterhin die Spitze.",
         "", "", "", (1, 9)),
    Term("limits", "Fluid temperature limits", "Grenzen der Fluidtemperatur", "T_f,min, T_f,max [°C]",
         "The bounds on the mean fluid temperature that the sizing must respect in every month of the "
         "simulation. The required length is the smallest one for which min T_f ≥ T_f,min and max T_f ≤ T_f,max. "
         "Raising T_f,min shrinks the available temperature difference T_g − T_f,min and costs length nearly in "
         "inverse proportion.",
         "Die Grenzen der mittleren Fluidtemperatur, die die Auslegung in jedem Monat des Simulationszeitraums "
         "einhalten muss. Die erforderliche Länge ist die kleinste, für die min T_f ≥ T_f,min und "
         "max T_f ≤ T_f,max gilt. Ein höheres T_f,min verkleinert die verfügbare Differenz T_g − T_f,min und "
         "kostet Länge annähernd umgekehrt proportional.",
         r"H \propto \frac{q_y R_y + q_m R_m + q_h (R_h + R_b)}{T_g - T_{f,\min}}",
         "VDI 4640-2 bounds the fluid temperature in continuous and peak operation. Several states require a "
         "minimum mean fluid temperature, often 0 °C or −3 °C, to protect the grout from freeze–thaw cycles.",
         "VDI 4640-2 begrenzt die Fluidtemperatur im Dauer- und Spitzenbetrieb. Mehrere Länder fordern eine "
         "Mindest-Fluidtemperatur, oft 0 °C oder −3 °C, zum Schutz der Verfüllung vor Frost-Tau-Wechseln.",
         (4, 5)),
    Term("simulation_period", "Simulation period", "Simulationszeitraum", "t_end [a]",
         "The number of years over which the limits are checked. For a field with a net imbalance the minimum "
         "keeps falling, roughly with ln t once the field acts as a whole. A longer period therefore costs "
         "length; a balanced field is insensitive to it.",
         "Die Zahl der Jahre, über die die Grenzen geprüft werden. Bei einem Feld mit Netto-Bilanz fällt das "
         "Minimum weiter, etwa mit ln t, sobald das Feld als Ganzes wirkt. Ein längerer Zeitraum kostet daher "
         "Länge; ein ausgeglichenes Feld ist unempfindlich dagegen.",
         "",
         "Usually 25–50 years. This app uses 50 years by default.",
         "Üblich sind 25–50 Jahre. Diese Anwendung nimmt standardmäßig 50 Jahre.", (1,)),
    Term("sizing_method", "Sizing methods L2, L3, L4", "Auslegungsverfahren L2, L3, L4", "",
         "GHEtool's methods differ in time resolution. L2 checks the first and the last year with three pulses: "
         "year, month and peak. L3 checks every month of the simulation. L4 works with hourly loads. All of "
         "them solve for the length at which the limiting fluid temperature just touches the limit.",
         "Die Verfahren von GHEtool unterscheiden sich in der zeitlichen Auflösung. L2 prüft erstes und letztes "
         "Jahr mit drei Pulsen: Jahr, Monat und Spitze. L3 prüft jeden Monat des Simulationszeitraums. L4 "
         "arbeitet mit Stundenlasten. Alle lösen nach der Länge, bei der die maßgebende Fluidtemperatur die "
         "Grenze gerade berührt.",
         r"T_f = T_g - q_y R_y - q_m R_m - q_h R_h - q_h R_b",
         "", "", (1, 2)),
    Term("specific_rate", "Specific extraction rate", "Spezifische Entzugsleistung", "q' [W/m]",
         "The peak extraction per metre of borehole. Tabulated values (VDI 4640-2, for small systems up to "
         "30 kW) bundle λ, the full-load hours and a typical R_b into one number. They do not capture "
         "interaction, regeneration or deviating limits, which is why simulation is required for larger fields.",
         "Spitzenentzug je Meter Sonde. Tabellenwerte (VDI 4640-2, für kleine Anlagen bis 30 kW) fassen λ, "
         "Volllaststunden und ein typisches R_b in einer Zahl zusammen. Wechselwirkung, Regeneration und "
         "abweichende Grenzen bilden sie nicht ab, deshalb sind größere Felder zu simulieren.",
         "", "", "", (4,)),
)

BY_KEY = {term.key: term for term in TERMS}

# Input field (property key) -> glossary term, for the "Read more" line in the field's "?" help
FIELDS = {"k_s": "k_s", "T_g": "T_g", "volumetric_heat_capacity": "volumetric_heat_capacity", "B_1": "spacing",
          "B_2": "spacing", "r_b_mm": "borehole_radius", "Rb": "Rb", "k_g": "k_g", "mfr": "mfr", "scop": "scop",
          "seer": "seer", "peak_heating_kw": "peak_load", "peak_cooling_kw": "peak_cooling", "full_load_hours_heating": "full_load_hours",
          "full_load_hours_cooling": "full_load_hours", "T_min": "limits", "T_max": "limits",
          "percentage": "antifreeze", "simulation_period": "simulation_period"}


def for_field(key: str) -> Term | None:
    return BY_KEY.get(FIELDS.get(key, ""))
