"""Rock types with their thermal properties, and a classifier that turns borehole log descriptions into them.

Thermal conductivity k [W/(m·K)] and volumetric heat capacity C [MJ/(m³·K)] are the recommended design values of
VDI 4640 Blatt 1 (2010), table 1, where the table has the rock. Rocks it does not list carry typical literature
values and are marked "estimate". Loose sediments have two sets: below the groundwater table (water saturated, the
VDI value) and above it (moist; between the VDI values for dry and saturated, an estimate).
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Rock:
    name: str
    k: float  # W/(m·K), water saturated for loose sediments
    c: float  # MJ/(m³·K)
    color: str
    hatch: str = ""
    loose: bool = False  # unconsolidated: thermal values depend on the groundwater table
    k_unsat: float | None = None  # above the groundwater table
    c_unsat: float | None = None
    source: str = "VDI 4640"

    def values(self, saturated: bool = True) -> tuple[float, float]:
        if self.loose and not saturated and self.k_unsat is not None:
            return self.k_unsat, self.c_unsat or self.c
        return self.k, self.c


_ROCKS = [
    # loose sediments
    Rock("Made ground / fill", 1.0, 1.8, "#9e9e9e", "xx", True, 0.8, 1.6, "estimate"),
    Rock("Topsoil / humus", 0.8, 2.2, "#5d4037", "", True, 0.6, 1.8, "estimate"),
    Rock("Peat", 0.4, 3.0, "#3e2723", "--", True, 0.4, 2.0),
    Rock("Clay", 1.7, 2.4, "#90a4ae", "--", True, 1.2, 2.0),
    Rock("Silt / loess", 1.7, 2.4, "#c5b98e", "-.", True, 1.2, 2.0),
    Rock("Sand", 2.4, 2.5, "#f4d35e", "..", True, 1.0, 1.7),
    Rock("Gravel", 1.8, 2.4, "#ee964b", "oo", True, 0.7, 1.6),
    Rock("Till / boulder clay", 2.4, 2.3, "#a1887f", "x.", True, 2.0, 2.1),
    # sedimentary rocks
    Rock("Claystone / siltstone", 2.2, 2.3, "#78909c", "-"),
    Rock("Shale / slate", 2.1, 2.3, "#546e7a", "--"),
    Rock("Marl", 2.1, 2.25, "#b0bec5", "-."),
    Rock("Sandstone", 2.3, 2.2, "#e9c46a", "."),
    Rock("Greywacke", 2.6, 2.3, "#8d8a6f", ".-", source="estimate"),
    Rock("Conglomerate / breccia", 2.3, 2.2, "#d4a373", "o"),
    Rock("Limestone", 2.8, 2.2, "#7fb3d5", "++"),
    Rock("Chalk", 2.0, 2.2, "#e3f2fd", "+", source="estimate"),
    Rock("Dolomite", 3.2, 2.5, "#5dade2", "x"),
    Rock("Anhydrite", 4.1, 2.0, "#ce93d8", "\\\\"),
    Rock("Gypsum", 1.6, 2.0, "#f3e5f5", "\\"),
    Rock("Rock salt", 5.4, 2.0, "#f8bbd0", "++"),
    Rock("Coal / lignite", 0.4, 1.6, "#212121", "", source="estimate"),
    # igneous rocks
    Rock("Granite", 3.4, 2.4, "#ef9a9a", "+"),
    Rock("Diorite", 2.6, 2.9, "#bcaaa4", "+"),
    Rock("Gabbro", 1.9, 2.6, "#6d4c41", "+"),
    Rock("Rhyolite / porphyry", 3.3, 2.1, "#f48fb1", "v"),
    Rock("Basalt", 1.7, 2.6, "#455a64", "v"),
    Rock("Diabase", 2.1, 2.6, "#37474f", "v", source="estimate"),
    Rock("Andesite", 2.2, 2.5, "#8e7cc3", "v", source="estimate"),
    Rock("Tuff", 1.1, 2.0, "#d7ccc8", "..", source="estimate"),
    # metamorphic rocks
    Rock("Phyllite", 2.5, 2.2, "#80cbc4", "//", source="estimate"),
    Rock("Mica schist", 2.0, 2.2, "#4db6ac", "//"),
    Rock("Gneiss", 2.9, 2.2, "#e57373", "/+"),
    Rock("Migmatite", 2.9, 2.2, "#d32f2f", "/+", source="estimate"),
    Rock("Amphibolite", 2.6, 2.7, "#2e7d32", "//", source="estimate"),
    Rock("Quartzite", 6.0, 2.1, "#fff59d", "||"),
    Rock("Marble", 2.1, 2.0, "#eceff1", "++"),
]
ROCKS: dict[str, Rock] = {r.name: r for r in _ROCKS}
UNKNOWN = "Unknown"

# Petrography codes of the German borehole log key (SEP 3, used in BoreholeML and the state databases).
# Case matters: capitals are the main component, lower case letters are admixtures ("u" = silty).
_CODES = {
    "A": "Made ground / fill", "AA": "Made ground / fill", "AY": "Made ground / fill", "Bau": "Made ground / fill",
    "Mu": "Topsoil / humus", "Hu": "Topsoil / humus", "Mb": "Topsoil / humus",
    "H": "Peat", "Hn": "Peat", "Hh": "Peat", "F": "Silt / loess",  # F: mud (Mudde)
    "T": "Clay", "U": "Silt / loess", "Lö": "Silt / loess", "Lol": "Silt / loess", "L": "Silt / loess",
    "S": "Sand", "fS": "Sand", "mS": "Sand", "gS": "Sand",
    "G": "Gravel", "fG": "Gravel", "mG": "Gravel", "gG": "Gravel", "X": "Gravel", "Y": "Gravel",
    "Mg": "Till / boulder clay", "Lg": "Till / boulder clay",
    "Tst": "Claystone / siltstone", "Ust": "Claystone / siltstone", "Tsst": "Claystone / siltstone",
    "Tsf": "Shale / slate", "Sf": "Shale / slate", "Ts": "Shale / slate",
    "Mst": "Marl", "Me": "Marl", "Mm": "Marl",
    "Sst": "Sandstone", "Qs": "Sandstone", "Grwk": "Greywacke", "Gw": "Greywacke",
    "Kgl": "Conglomerate / breccia", "Brk": "Conglomerate / breccia", "Br": "Conglomerate / breccia",
    "Kst": "Limestone", "K": "Limestone", "Kk": "Chalk", "Kr": "Chalk", "Dst": "Dolomite", "D": "Dolomite",
    "Anh": "Anhydrite", "Gi": "Gypsum", "Gip": "Gypsum", "Sa": "Rock salt", "Na": "Rock salt",
    "Bk": "Coal / lignite", "Sk": "Coal / lignite", "Kh": "Coal / lignite",
    "Gr": "Granite", "Gd": "Granite", "Di": "Diorite", "Gb": "Gabbro", "Gab": "Gabbro",
    "Rh": "Rhyolite / porphyry", "Po": "Rhyolite / porphyry", "Qp": "Rhyolite / porphyry",
    "B": "Basalt", "Ba": "Basalt", "Dia": "Diabase", "Db": "Diabase", "An": "Andesite", "Tf": "Tuff",
    "Phy": "Phyllite", "Ph": "Phyllite", "Gl": "Mica schist", "Gs": "Mica schist", "Gn": "Gneiss",
    "Mig": "Migmatite", "Am": "Amphibolite", "Amp": "Amphibolite", "Qzt": "Quartzite", "Q": "Quartzite",
    "Mr": "Marble", "Mar": "Marble",
}

# Words in German and English (INSPIRE lithology terms of the BGR map). Checked in this order, so compound
# words come before their parts ("sandstein" before "sand", "kalkmergel" before "kalk").
_WORDS = [
    ("auffüllung|aufschüttung|bauschutt|made ground|fill|anthropogen|artificial", "Made ground / fill"),
    ("mutterboden|oberboden|humus|topsoil", "Topsoil / humus"),
    ("torf|peat|moor", "Peat"),
    ("geschiebemergel|geschiebelehm|till|diamict|boulder clay", "Till / boulder clay"),
    ("tonschiefer|schiefer(?!ton)|slate|shale", "Shale / slate"),
    ("glimmerschiefer|mica schist|schist", "Mica schist"),
    ("phyllit|phyllite", "Phyllite"),
    ("tonstein|schluffstein|siltstein|claystone|siltstone|mudstone|pelit|schieferton", "Claystone / siltstone"),
    ("kalkmergel|mergelstein|mergel|marl", "Marl"),
    ("sandstein|sandstone|arkose|quarzsandstein", "Sandstone"),
    ("grauwacke|greywacke|graywacke|wacke", "Greywacke"),
    ("konglomerat|brekzie|breccie|conglomerate|breccia", "Conglomerate / breccia"),
    ("dolomit|dolomite|dolostone", "Dolomite"),
    ("kreide|chalk", "Chalk"),
    ("kalkstein|kalk|limestone|carbonate|karbonat|travertin|muschelkalk", "Limestone"),
    ("anhydrit|anhydrite", "Anhydrite"),
    ("gips|gypsum", "Gypsum"),
    ("steinsalz|salz|rock salt|halite|evaporite", "Rock salt"),
    ("braunkohle|steinkohle|kohle|lignite|coal", "Coal / lignite"),
    ("granodiorit|granit|granite|granodiorite|syenit|syenite|plutonic", "Granite"),
    ("diorit|diorite", "Diorite"),
    ("gabbro", "Gabbro"),
    ("rhyolith|rhyolite|porphyr|porphyry|quarzporphyr|ignimbrit", "Rhyolite / porphyry"),
    ("diabas|diabase|dolerite|spilit", "Diabase"),
    ("basalt|basanit|basanite|tephrit|nephelinit|phonolith|phonolite|trachyt|trachyte", "Basalt"),
    ("andesit|andesite", "Andesite"),
    ("tuff|tuffit|pyroclast|volcaniclastic", "Tuff"),
    ("migmatit|migmatite", "Migmatite"),
    ("gneis|gneiss|granulit|granulite", "Gneiss"),
    ("amphibolit|amphibolite|metabasit|metabasite", "Amphibolite"),
    ("quarzit|quartzite", "Quartzite"),
    ("marmor|marble", "Marble"),
    ("kies|gravel|schotter|geröll|blöcke|steine|cobbles|boulders", "Gravel"),
    ("sand", "Sand"),
    ("löss|loess|lehm|loam|schluff|silt|mudde|mud", "Silt / loess"),
    ("ton|clay", "Clay"),
]
_WORD_RES = [(re.compile(rf"(?<![a-zäöüß])({pattern})", re.IGNORECASE), rock) for pattern, rock in _WORDS]
_TOKEN = re.compile(r"[A-Za-zÄÖÜäöüß]+")


def classify(text: str | None) -> str:
    """The rock type of a log description: a SEP 3 code ("mS,g", "Tst"), German or English words. The main
    component decides; returns UNKNOWN when nothing matches."""
    if not text:
        return UNKNOWN
    text = str(text).strip()
    # SEP 3: the first capitalised token is the main component, e.g. "fS,ms,u'" or "U,AY,3".
    for match in _TOKEN.finditer(text):
        token = match.group()
        sentence = re.match(r" [a-zäöüß]{4,}", text[match.end():])  # "A sandy clay" is English, not code A
        if token in _CODES and not sentence:
            return _CODES[token]
        if match.start() > 0 or len(token) > 4 or not token[:1].isupper():
            break  # not a code: read the words instead
    # words: the one that comes first in the text is the main component ("Ton, sandig" is clay)
    best = None
    for order, (pattern, rock) in enumerate(_WORD_RES):
        found = pattern.search(text)
        if found and (best is None or found.start() < best[0]):
            best = (found.start(), order, rock)
    if best:
        return best[2]
    return UNKNOWN


def values(rock: str, saturated: bool = True) -> tuple[float, float]:
    """(k, C) of a rock type; UNKNOWN gets the VDI 4640 default of 2.0 W/(m·K) and 2.4 MJ/(m³·K)."""
    r = ROCKS.get(rock)
    return r.values(saturated) if r else (2.0, 2.4)


def color(rock: str) -> str:
    r = ROCKS.get(rock)
    return r.color if r else "#e0e0e0"


def hatch(rock: str) -> str:
    r = ROCKS.get(rock)
    return r.hatch if r else ""


def is_loose(rock: str) -> bool:
    r = ROCKS.get(rock)
    return bool(r and r.loose)


NAMES = list(ROCKS) + [UNKNOWN]
