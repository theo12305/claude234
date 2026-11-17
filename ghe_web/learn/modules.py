"""The introduction for new colleagues: eight short modules along the app's own steps.

A module is a short text in both languages, the exercises it shows (keys of ``exercises.EXERCISES``), a self-check
question and the numbers of its sources (``sources.py``). Texts are Markdown. To correct a text, edit it here; no
other code changes.
"""
from __future__ import annotations

from dataclasses import dataclass

from .text import L


@dataclass(frozen=True)
class Question:
    en: str
    de: str
    options: tuple[tuple[str, str], ...]  # (en, de)
    answer: int  # index of the right option
    why_en: str
    why_de: str

    @property
    def text(self) -> str:
        return L(self.en, self.de)

    @property
    def choices(self) -> list[str]:
        return [L(en, de) for en, de in self.options]

    @property
    def why(self) -> str:
        return L(self.why_en, self.why_de)


@dataclass(frozen=True)
class Module:
    number: int
    title_en: str
    title_de: str
    minutes: int
    body_en: str
    body_de: str
    exercises: tuple[str, ...]
    question: Question | None
    sources: tuple[int, ...]
    terms: tuple[str, ...]  # glossary keys

    @property
    def title(self) -> str:
        return L(self.title_en, self.title_de)

    @property
    def body(self) -> str:
        return L(self.body_en, self.body_de)


MODULES: tuple[Module, ...] = (
    Module(0, "Tour of the app", "Rundgang durch die Anwendung", 10,
           """**What the app does.** It sizes borehole heat exchangers (closed loop) with the open-source package
GHEtool, and groundwater wells (open loop) with its own model. For boreholes the question is always: *how many metres
of borehole keep the fluid temperature within its limits for the whole simulation period?*

**The steps** follow the order of a real design:

1. **⓪ Site plan** (optional): parcel, buildings, distances, how many boreholes fit.
2. **① Ground & borefield**: ground properties and the layout of the field.
3. **② Loads**: what the building needs, or what the ground has to deliver. Below it, with typical values: the
   borehole (probe type, grout), the heat transfer fluid and the allowed fluid temperatures.
4. **③ Design check**, then **Results** and **Further analysis**.

In *Expert* the borehole and fluid and the limits get steps of their own (② to ④), so the numbers shift by one.

**Three modes.** *Simple* shows the main fields and puts the others under "More options". *Expert* shows all fields.
*Learn* is Simple plus explanations, this introduction, the glossary and the literature list. The calculation is the
same in all three.""",
           """**Was die Anwendung macht.** Sie legt Erdwärmesonden (geschlossenes System) mit dem Open-Source-Paket
GHEtool aus und Grundwasserbrunnen (offenes System) mit einem eigenen Modell. Bei Sonden lautet die Frage immer:
*Wie viele Meter Sonde halten die Fluidtemperatur über den ganzen Simulationszeitraum innerhalb der Grenzen?*

**Die Schritte** folgen der Reihenfolge einer echten Planung:

1. **⓪ Lageplan** (optional): Flurstück, Gebäude, Abstände, wie viele Sonden passen.
2. **① Untergrund & Sondenfeld**: Untergrundeigenschaften und Anordnung des Feldes.
3. **② Lasten**: was das Gebäude braucht oder was der Untergrund liefern muss. Darunter, mit typischen Werten: die
   Sonde (Sondentyp, Verfüllung), das Wärmeträgerfluid und die zulässigen Fluidtemperaturen.
4. **③ Planungsprüfung**, dann **Ergebnisse** und **Weitere Auswertungen**.

Im Modus *Experte* bekommen Sonde und Fluid sowie die Grenzen eigene Schritte (② bis ④), die Nummern verschieben
sich darum um eins.

**Drei Modi.** *Einfach* zeigt die wichtigsten Felder und legt die anderen unter „Weitere Optionen“. *Experte* zeigt
alle Felder. *Lernen* ist Einfach plus Erklärungen, diese Einführung, das Glossar und die Literaturliste. Die
Berechnung ist in allen dreien gleich.""",
           (), Question(
               "Which question does the sizing answer?", "Welche Frage beantwortet die Auslegung?",
               (("How much the system costs", "Was die Anlage kostet"),
                ("How long the boreholes must be so the fluid stays within its limits",
                 "Wie lang die Sonden sein müssen, damit das Fluid in seinen Grenzen bleibt"),
                ("Which heat pump to buy", "Welche Wärmepumpe man kauft")), 1,
               "The sizing finds the shortest total length that keeps the mean fluid temperature within the limits "
               "for every month of the simulation period.",
               "Die Auslegung sucht die kürzeste Gesamtlänge, die die mittlere Fluidtemperatur in jedem Monat des "
               "Simulationszeitraums innerhalb der Grenzen hält."), (2, 12), ()),
    Module(1, "Ground", "Untergrund", 20,
           """The ground is the heat source. Three properties matter:

- **Thermal conductivity λ**: how fast heat flows through the rock to the borehole. It changes the length most.
- **Undisturbed ground temperature**: the starting point. The colder it is, the less room to the lower fluid limit.
- **Volumetric heat capacity**: how much heat the rock stores. It matters for months and peaks, less for decades.

Values come from the geological map and the rock type (VDI 4640-1 has a table), from the state geological survey's
borehole logs, or best from a **thermal response test** on site. Under ① you can choose a rock type, enter layers,
or let the app predict layers from the state data.

**Rule of thumb:** a better conductivity shortens the boreholes, but less than in proportion, because part of the
temperature drop happens inside the borehole. The exercise shows by how much.""",
           """Der Untergrund ist die Wärmequelle. Drei Eigenschaften zählen:

- **Wärmeleitfähigkeit λ**: wie schnell Wärme durch das Gestein zur Sonde fließt. Sie ändert die Länge am stärksten.
- **Ungestörte Untergrundtemperatur**: der Ausgangspunkt. Je kälter, desto weniger Abstand zur unteren Fluidgrenze.
- **Volumetrische Wärmekapazität**: wie viel Wärme das Gestein speichert. Wichtig für Monate und Spitzen, weniger
  für Jahrzehnte.

Werte kommen aus der geologischen Karte und der Gesteinsart (VDI 4640-1 hat eine Tabelle), aus Bohrprofilen des
Geologischen Dienstes oder am besten aus einem **Thermal Response Test** vor Ort. Unter ① können Sie eine Gesteinsart
wählen, Schichten eingeben oder Schichten aus den Landesdaten vorhersagen lassen.

**Faustregel:** Eine bessere Wärmeleitfähigkeit verkürzt die Sonden, aber weniger als proportional, weil ein Teil
des Temperaturabfalls im Bohrloch selbst passiert. Die Übung zeigt, um wie viel.""",
           ("predict_ks",), None, (8, 3, 5), ("k_s", "T_g", "volumetric_heat_capacity", "trt")),
    Module(2, "Borefield and borehole", "Sondenfeld und Bohrloch", 30,
           """**The field.** Boreholes close to each other share the same ground and cool it together. This
interaction grows over the years and is captured by the **g-function** of the field. More spacing or a more open
shape (a line or an L instead of a compact block) means less interaction and less length, but needs more area.

**The borehole.** Between the borehole wall and the fluid the heat passes the grout, the pipe wall and the fluid
film. Together they form the **borehole thermal resistance R_b**. The temperature difference across it is
R_b × heat flow per metre: at 30 W/m and 0.10 m·K/W that is 3 K, a big share of the available range.

What lowers R_b: a better grout, a double U instead of a single U, and enough flow to keep it turbulent. Laminar flow
(Reynolds number below about 2300) raises R_b noticeably.""",
           """**Das Feld.** Nahe beieinander liegende Sonden teilen sich denselben Untergrund und kühlen ihn gemeinsam
ab. Diese Wechselwirkung wächst über die Jahre und steckt in der **g-Funktion** des Feldes. Mehr Abstand oder eine
offenere Form (eine Reihe oder ein L statt eines kompakten Blocks) heißt weniger Wechselwirkung und weniger Länge,
braucht aber mehr Fläche.

**Das Bohrloch.** Zwischen Bohrlochwand und Fluid geht die Wärme durch Verfüllung, Rohrwand und Fluidgrenzschicht.
Zusammen bilden sie den **thermischen Bohrlochwiderstand R_b**. Der Temperaturunterschied darüber ist R_b × Wärmestrom
je Meter: bei 30 W/m und 0,10 m·K/W sind das 3 K, ein großer Teil des verfügbaren Bereichs.

Was R_b senkt: eine bessere Verfüllung, eine Doppel-U- statt einer Einfach-U-Sonde und genug Durchfluss, damit die
Strömung turbulent bleibt. Laminare Strömung (Reynolds-Zahl unter etwa 2300) erhöht R_b deutlich.""",
           ("predict_spacing", "inside_borehole"), None, (3, 7, 4), ("gfunction", "spacing", "Rb", "k_g", "reynolds")),
    Module(3, "Loads", "Lasten", 25,
           """**From building to ground.** A heat pump with a seasonal performance **SCOP** takes ground heat =
heating × (1 − 1/SCOP); the rest is electricity. Cooling puts heat back: passive cooling almost 1:1, with a chiller
plus its electricity.

**Energy and peak.** The yearly energy (peak power × **full-load hours**) decides the long-term cooling of the
ground. The peak decides the short-term drop in the coldest month. Both are checked.

**Imbalance.** If more heat is taken than put back, the ground gets a little colder every year. That is why the design
looks at the last year of the simulation, and why summer cooling or solar **regeneration** can save a lot of length.
The exercise shows the same field with and without summer cooling over 50 years.""",
           """**Vom Gebäude zum Untergrund.** Eine Wärmepumpe mit der Jahresarbeitszahl **SCOP** entzieht dem
Untergrund Heizwärme × (1 − 1/SCOP); der Rest ist Strom. Kühlung bringt Wärme zurück: passive Kühlung fast 1:1, mit
Kältemaschine zuzüglich deren Strom.

**Energie und Spitze.** Die Jahresenergie (Spitzenleistung × **Volllaststunden**) bestimmt die langfristige
Abkühlung des Untergrunds. Die Spitze bestimmt den kurzfristigen Abfall im kältesten Monat. Beides wird geprüft.

**Bilanz.** Wird mehr Wärme entzogen als zurückgegeben, wird der Untergrund jedes Jahr etwas kälter. Deshalb schaut
die Auslegung auf das letzte Jahr der Simulation, und deshalb können Sommerkühlung oder solare **Regeneration** viel
Länge sparen. Die Übung zeigt dasselbe Feld mit und ohne Sommerkühlung über 50 Jahre.""",
           ("ground_years",), None, (1, 4, 6), ("scop", "full_load_hours", "imbalance", "regeneration")),
    Module(4, "Limits and design check", "Grenzen und Planungsprüfung", 20,
           """**Temperature limits.** The sizing makes the boreholes just long enough that the *mean* fluid
temperature stays between the lower and upper limit. The lower limit protects the grout and the ground from freezing
and keeps the heat pump efficient; the upper one matters for cooling. With **antifreeze** the fluid may go below
0 °C, but check what the state guideline and VDI 4640-2 allow for the project.

**Design check.** Before calculating, the ③ Design check step lists every input check: spacing, flow, antifreeze,
temperatures, balance. A warning is not an error, but each one should have a reason you can explain to a client or
an authority.""",
           """**Temperaturgrenzen.** Die Auslegung macht die Sonden gerade so lang, dass die *mittlere*
Fluidtemperatur zwischen unterer und oberer Grenze bleibt. Die untere Grenze schützt Verfüllung und Untergrund vor
Frost und hält die Wärmepumpe effizient; die obere zählt beim Kühlen. Mit **Frostschutz** darf das Fluid unter 0 °C
fallen, aber prüfen Sie, was der Landesleitfaden und VDI 4640-2 für das Projekt erlauben.

**Planungsprüfung.** Vor der Berechnung listet der Schritt ③ Planungsprüfung alle Eingabeprüfungen: Abstand,
Durchfluss, Frostschutz, Temperaturen, Bilanz. Eine Warnung ist kein Fehler, aber für jede sollte es einen Grund
geben, den Sie einem Kunden oder einer Behörde erklären können.""",
           (), Question(
               "The lower fluid limit is raised from 0 °C to +2 °C. What happens to the length?",
               "Die untere Fluidgrenze wird von 0 °C auf +2 °C angehoben. Was passiert mit der Länge?",
               (("It gets shorter", "Sie wird kürzer"), ("It stays the same", "Sie bleibt gleich"),
                ("It gets longer", "Sie wird länger")), 2,
               "Less room between the ground temperature and the limit means each metre may take less heat, so more "
               "metres are needed.",
               "Weniger Abstand zwischen Untergrundtemperatur und Grenze heißt, jeder Meter darf weniger Wärme "
               "liefern, also braucht es mehr Meter."), (4, 1), ("limits", "antifreeze")),
    Module(5, "Reading the results", "Ergebnisse lesen", 25,
           """**The answer card** gives the number and length of the boreholes and which side (heating or cooling)
sets the length.

**The temperature chart** shows the mean fluid temperature over the whole period: the base load and the peaks.
Check where the curves touch the limits, and whether the yearly low still falls at the end (the ground is not yet
in balance).

**The energy balance** shows extraction and injection per month and the yearly net.

**Specific values** like W/m are results here, not inputs. Compare them with rule-of-thumb tables only for small,
typical systems; for anything larger the simulation is the reference. GHEtool's method is published and validated,
see the sources.

In Learn mode the results also say *why* the length came out like this, and how the 10 °C of the ground turn into the
limiting fluid temperature.""",
           """**Die Ergebniskarte** nennt Anzahl und Länge der Sonden und welche Seite (Heizen oder Kühlen) die Länge
bestimmt.

**Das Temperaturdiagramm** zeigt die mittlere Fluidtemperatur über den ganzen Zeitraum: Grundlast und Spitzen.
Prüfen Sie, wo die Kurven die Grenzen berühren und ob das Jahrestief am Ende noch fällt (der Untergrund ist dann noch
nicht im Gleichgewicht).

**Die Energiebilanz** zeigt Entzug und Eintrag je Monat und die Jahresbilanz.

**Spezifische Werte** wie W/m sind hier Ergebnisse, keine Eingaben. Vergleichen Sie sie mit Faustwert-Tabellen nur
bei kleinen, üblichen Anlagen; bei allem Größeren ist die Simulation maßgebend. Die Methode von GHEtool ist
veröffentlicht und validiert, siehe Quellen.

Im Lernmodus sagen die Ergebnisse außerdem, *warum* die Länge so herauskommt und wie aus den 10 °C des Untergrunds
die maßgebende Fluidtemperatur wird.""",
           (), Question(
               "The yearly lowest fluid temperature still falls in the last years. What does it mean?",
               "Das Jahrestief der Fluidtemperatur fällt in den letzten Jahren noch. Was bedeutet das?",
               (("The ground is not in balance yet: more heat is taken than returned",
                 "Der Untergrund ist noch nicht im Gleichgewicht: es wird mehr Wärme entzogen als zurückgegeben"),
                ("The heat pump is too small", "Die Wärmepumpe ist zu klein"),
                ("The flow rate is too high", "Der Durchfluss ist zu hoch")), 0,
               "A falling yearly low is the long-term drift from the imbalance; a longer period would show more of it.",
               "Ein fallendes Jahrestief ist die Langzeitdrift aus der Bilanz; ein längerer Zeitraum zeigt mehr davon."),
           (1, 12, 4), ("sizing_method", "specific_rate", "simulation_period")),
    Module(6, "Site plan and permits", "Lageplan und Genehmigung", 20,
           """**Space and distances.** Boreholes need distance to the parcel border, to buildings, to pipes and to
each other. The ⓪ Site plan step loads the parcel and buildings from the state's free cadastre services and places as
many boreholes as fit.

**Ground data.** The state geological surveys publish borehole logs and maps; the app links or loads them where they
are free.

**Permits.** Borehole heat exchangers need at least a notification to the lower water authority, often a permit
under water law; boreholes deeper than 100 m must also be reported to the mining authority. Water protection areas
can forbid drilling. Each state has its own guideline: read the one for your project's state (several are in the
list).""",
           """**Platz und Abstände.** Sonden brauchen Abstand zur Grundstücksgrenze, zu Gebäuden, zu Leitungen und
zueinander. Der Schritt ⓪ Lageplan lädt Flurstück und Gebäude aus den freien Katasterdiensten der Länder und setzt so
viele Sonden, wie passen.

**Untergrunddaten.** Die Geologischen Dienste der Länder veröffentlichen Bohrprofile und Karten; die Anwendung
verlinkt oder lädt sie, wo sie frei sind.

**Genehmigung.** Erdwärmesonden brauchen mindestens eine Anzeige bei der Unteren Wasserbehörde, oft eine
wasserrechtliche Erlaubnis; Bohrungen tiefer als 100 m müssen außerdem der Bergbehörde angezeigt werden.
Wasserschutzgebiete können Bohrungen verbieten. Jedes Land hat einen eigenen Leitfaden: Lesen Sie den des
Bundeslands Ihres Projekts (mehrere stehen in der Liste).""",
           (), Question(
               "A borehole is planned 120 m deep. Besides the water authority, who must be informed?",
               "Eine Sonde soll 120 m tief werden. Wer muss außer der Wasserbehörde informiert werden?",
               (("Nobody", "Niemand"), ("The mining authority", "Die Bergbehörde"),
                ("The energy supplier", "Der Energieversorger")), 1,
               "Drilling deeper than 100 m must be reported to the mining authority (§ 127 BBergG).",
               "Bohrungen tiefer als 100 m sind der Bergbehörde anzuzeigen (§ 127 BBergG)."),
           (5, 6, 9, 10, 11, 8), ()),
    Module(7, "Groundwater wells", "Grundwasserbrunnen", 30,
           """**Open loop.** A production well takes groundwater, the heat pump cools it, an injection well returns it
downstream. It needs a productive aquifer at a shallow depth and suitable water chemistry.

**What the app sizes:** the flow from the load and the temperature spread, the drawdown and rise at the wells
(Thiem, Dupuit-Jacob), the well spacing, and the cold plume downstream. The injection well must not feed cold water
back to the production well (thermal short circuit).

**Permits** are stricter than for boreholes: the water authority decides on the extraction, the injection
temperature and the plume. The NRW worksheet in the list gives an idea of the requirements.""",
           """**Offenes System.** Ein Förderbrunnen entnimmt Grundwasser, die Wärmepumpe kühlt es ab, ein
Schluckbrunnen gibt es abstromig zurück. Es braucht einen ergiebigen Grundwasserleiter in geringer Tiefe und eine
passende Wasserchemie.

**Was die Anwendung auslegt:** den Volumenstrom aus Last und Spreizung, Absenkung und Aufhöhung an den Brunnen
(Thiem, Dupuit-Jacob), den Brunnenabstand und die Kältefahne abstromig. Der Schluckbrunnen darf kein kaltes Wasser
zum Förderbrunnen zurückschicken (thermischer Kurzschluss).

**Die Genehmigung** ist strenger als bei Sonden: Die Wasserbehörde entscheidet über Entnahme,
Einleittemperatur und Kältefahne. Das NRW-Arbeitsblatt in der Liste gibt einen Eindruck von den Anforderungen.""",
           (), Question(
               "Where does the injection well go?", "Wo liegt der Schluckbrunnen?",
               (("Upstream of the production well", "Oberstromig des Förderbrunnens"),
                ("Downstream of the production well", "Abstromig des Förderbrunnens"),
                ("Right next to it", "Direkt daneben")), 1,
               "Downstream, so the cooled water flows away from the production well instead of back to it.",
               "Abstromig, damit das abgekühlte Wasser vom Förderbrunnen wegfließt statt zu ihm zurück."),
           (11,), ()),
)

BY_NUMBER = {m.number: m for m in MODULES}
TOTAL_MINUTES = sum(m.minutes for m in MODULES)
