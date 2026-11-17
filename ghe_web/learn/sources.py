"""The literature list of Learn mode: one numbered list for the whole app.

A number here is the number shown everywhere ([4] in a result card, in the glossary and in a module). Keep the
numbers stable: add new entries at the end. Each entry was opened on 2026-11-17 to confirm title, year and access;
``tools/check_sources.py`` can check the links again.
"""
from __future__ import annotations

from dataclasses import dataclass

from .text import L

CHECKED = "2026-11-17"


@dataclass(frozen=True)
class Source:
    number: int
    authors: str
    title: str
    venue: str
    year: int
    language: str  # language of the document: "EN" or "DE"
    free: bool  # free to read online
    url: str
    why_en: str
    why_de: str
    modules: tuple[int, ...]  # the introduction modules that cite it
    key: str  # BibTeX key

    @property
    def why(self) -> str:
        return L(self.why_en, self.why_de)

    @property
    def short(self) -> str:
        """Author and year, e.g. "Peere et al. 2021"."""
        first = self.authors.split(",")[0].strip()
        more = " et al." if "," in self.authors else ""
        return f"{first}{more} {self.year}"


SOURCES: tuple[Source, ...] = (
    Source(1, "Peere, Picard, Cupeiro Figueroa, Boydens, Helsen",
           "Validated combined first and last year borefield sizing methodology",
           "IBPSA Building Simulation 2021, Bruges", 2021, "EN", True,
           "https://lirias.kuleuven.be/retrieve/672600",
           "The sizing method GHEtool uses: why both the first and the last year are checked.",
           "Die Auslegungsmethode von GHEtool: warum das erste und das letzte Jahr geprüft werden.",
           (3, 4, 5), "peere2021sizing"),
    Source(2, "Peere, Blanke", "GHEtool: An open-source tool for borefield sizing in Python",
           "Journal of Open Source Software 7(76), 4406", 2022, "EN", True,
           "https://joss.theoj.org/papers/10.21105/joss.04406",
           "What the calculation engine behind this app does, in four pages.",
           "Was der Rechenkern hinter dieser Anwendung macht, auf vier Seiten.",
           (0,), "peere2022ghetool"),
    Source(3, "Eskilson", "Thermal analysis of heat extraction boreholes",
           "PhD thesis, Lund University", 1987, "EN", True,
           "https://lup.lub.lu.se/search/publication/2536225",
           "Origin of the g-function: how a borefield responds to heat extraction over decades.",
           "Ursprung der g-Funktion: wie ein Sondenfeld über Jahrzehnte auf Wärmeentzug reagiert.",
           (1, 2), "eskilson1987"),
    Source(4, "VDI", "VDI 4640 Blatt 2: Thermische Nutzung des Untergrunds – Erdgekoppelte Wärmepumpenanlagen",
           "VDI guideline", 2019, "DE", False,
           "https://www.vdi.de/richtlinien/details/vdi-4640-blatt-2-thermische-nutzung-des-untergrunds-"
           "erdgekoppelte-waermepumpenanlagen",
           "The German design guideline for borehole heat exchanger systems.",
           "Die deutsche Planungsrichtlinie für Erdwärmesondenanlagen.",
           (2, 3, 4), "vdi4640-2"),
    Source(5, "Umweltministerium Baden-Württemberg", "Leitlinien Qualitätssicherung Erdwärmesonden (LQS EWS)",
           "State guideline", 2018, "DE", True,
           "https://lgrbwissen.lgrb-bw.de/sites/default/files/public/lgrbwissen/dokumente/"
           "190601leitlinienqualitaetssicherungerdwaermesondenpdf.pdf",
           "Quality requirements for drilling, grouting and documentation.",
           "Qualitätsanforderungen an Bohrung, Verpressung und Dokumentation.",
           (1, 6), "lqsews2018"),
    Source(6, "Bundesverband Wärmepumpe, Bavarian state ministries", "Leitfaden Erdwärmesonden in Bayern",
           "State guideline, 4th edition", 2012, "DE", True,
           "https://www.stmwi.bayern.de/fileadmin/user_upload/stmwi/Energie/Rohstoffe/"
           "2021-10-20_Leitfaden_Erdwaermesonden.pdf",
           "Planning and permits in Bavaria.", "Planung und Genehmigung in Bayern.",
           (3, 6), "leitfaden-bayern2012"),
    Source(7, "Cimmino", "pygfunction documentation", "Software documentation, version 2.3", 2025, "EN", True,
           "https://pygfunction.readthedocs.io/en/stable/",
           "How the g-functions and the borehole resistance are calculated.",
           "Wie die g-Funktionen und der Bohrlochwiderstand berechnet werden.",
           (2,), "pygfunction"),
    Source(8, "VDI", "VDI 4640 Blatt 1: Thermische Nutzung des Untergrunds – Grundlagen, Genehmigungen, "
           "Umweltaspekte", "VDI guideline", 2010, "DE", False,
           "https://www.vdi.de/richtlinien/details/vdi-4640-blatt-1-thermische-nutzung-des-untergrunds-"
           "grundlagen-genehmigungen-umweltaspekte",
           "Ground properties by rock type (table of thermal conductivities), permits.",
           "Kennwerte nach Gesteinsart (Tabelle der Wärmeleitfähigkeiten), Genehmigungen.",
           (1, 6), "vdi4640-1"),
    Source(9, "HLNUG", "Erdwärmenutzung in Hessen – Leitfaden für Erdwärmesondenanlagen zum Heizen und Kühlen",
           "State guideline, 5th edition", 2017, "DE", True,
           "https://www.hlnug.de/fileadmin/dokumente/geologie/erdwaerme/Erdwaermeleitfaden_01_2017.pdf",
           "Planning and permits in Hesse, including cooling.", "Planung und Genehmigung in Hessen, auch Kühlen.",
           (6,), "hlnug2017"),
    Source(10, "Rhineland-Palatinate ministries (LGB, LfU)",
           "Leitfaden zur Nutzung von oberflächennaher Geothermie mit Erdwärmesonden",
           "State guideline, 7th update", 2020, "DE", True,
           "https://lfu.rlp.de/fileadmin/lfu/KLIMA/Geothermie/Leitfaden_Erdwaeme_2020.pdf",
           "Groundwater protection and the permit procedure.", "Grundwasserschutz und Erlaubnisverfahren.",
           (6,), "leitfaden-rlp2020"),
    Source(11, "LANUV NRW",
           "Wasserwirtschaftliche Anforderungen an die Nutzung von oberflächennaher Erdwärme (Arbeitsblatt 39)",
           "State guideline", 2024, "DE", True,
           "https://lanuk.nrw.de/fileadmin/lanuvpubl/4_arbeitsblaetter/LANUV-Arbeitsblatt_39.pdf",
           "What the water authority requires in North Rhine-Westphalia, also for wells.",
           "Was die Wasserbehörde in Nordrhein-Westfalen verlangt, auch für Brunnen.",
           (6, 7), "lanuv-ab39"),
    Source(12, "GHEtool team", "GHEtool in literature", "List of papers", 2024, "EN", True,
           "https://ghetool.readthedocs.io/en/stable/sources/articles.html",
           "Further papers on the method and its validation.", "Weitere Veröffentlichungen zur Methode und Validierung.",
           (0, 5), "ghetool-literature"),
)

BY_NUMBER = {s.number: s for s in SOURCES}


def get(number: int) -> Source:
    return BY_NUMBER[number]


def cite(numbers) -> str:
    """Markdown for a short source line: "[1] Peere et al. 2021 · [4] VDI 2019", each linked."""
    return " · ".join(f"[[{n}]]({get(n).url}) {get(n).short}" for n in numbers)


def for_module(module: int) -> list[Source]:
    return [s for s in SOURCES if module in s.modules]


def bibtex() -> str:
    """The whole list as BibTeX, for a report or thesis."""
    out = []
    for s in SOURCES:
        kind = "phdthesis" if "thesis" in s.venue.lower() else "misc"
        authors = " and ".join(a.strip() for a in s.authors.split(","))
        out.append(f"@{kind}{{{s.key},\n  author = {{{authors}}},\n  title = {{{s.title}}},\n"
                   f"  howpublished = {{{s.venue}}},\n  year = {{{s.year}}},\n  url = {{{s.url}}}\n}}")
    return "\n\n".join(out) + "\n"


def plain_list() -> str:
    """The whole list as text, one entry per line."""
    return "\n".join(f"[{s.number}] {s.authors} ({s.year}): {s.title}. {s.venue}. {s.url}" for s in SOURCES) + "\n"
