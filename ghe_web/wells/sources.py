"""What each part of the well calculation is based on, with the literature. Shown on the page and in the report."""
from __future__ import annotations

from ..i18n import t

# (topic, what the tool does, references). Topic and text are translated; references stay as published.
SOURCES = (
    ("Flow from the load",
     "Peak flow = peak ground load / (ρc of water × temperature spread); the volume per month from the monthly energy "
     "in the same way.",
     ("VDI 4640 Blatt 2 (2019): Thermische Nutzung des Untergrunds – Erdgekoppelte Wärmepumpenanlagen.",)),
    ("Drawdown and rise",
     "Thiem's steady-state equation for every well, summed (superposition). Pumping and injection are equal, so the "
     "radius of influence drops out and the result is exact for a homogeneous aquifer.",
     ("Thiem, G. (1906): Hydrologische Methoden. Gebhardt, Leipzig.",
      "Theis, C. V. (1935): The relation between the lowering of the piezometric surface and the rate and duration "
      "of discharge of a well using ground-water storage. Trans. AGU 16(2), 519–524.")),
    ("Unconfined aquifers",
     "The thinner (or thicker) water column is taken into account with the Dupuit-Jacob correction s = b − √(b² − 2bs').",
     ("Jacob, C. E. (1944): Notes on determining permeability by pumping tests under water-table conditions. "
      "USGS open-file report.",)),
    ("Well losses",
     "Extra drawdown in the well itself C·Q²; about 1800 s²/m⁵ for a properly built well.",
     ("Jacob, C. E. (1947): Drawdown test to determine effective radius of artesian well. Trans. ASCE 112, "
      "1047–1064.",
      "Walton, W. C. (1962): Selected analytical methods for well and aquifer evaluation. Illinois State Water "
      "Survey Bulletin 49.")),
    ("Entrance velocity",
     "Largest velocity at the borehole wall √kf / 15 (m/s); at injection wells the velocity is multiplied by the "
     "clogging reserve first.",
     ("Sichardt, W. (1928): Das Fassungsvermögen von Rohrbrunnen und seine Bedeutung für die Grundwasserabsenkung. "
      "Springer, Berlin.",
      "DVGW W 123 (2001): Bau und Ausbau von Vertikalfilterbrunnen.")),
    ("Pumping test",
     "Transmissivity and storage from the straight line of drawdown against log time (Cooper-Jacob).",
     ("Cooper, H. H., Jacob, C. E. (1946): A generalized graphical method for evaluating formation constants and "
      "summarizing well-field history. Trans. AGU 27(4), 526–534.",)),
    ("Backflow (thermal short circuit)",
     "The injected water is traced along the streamlines of the wells plus the regional groundwater flow (complex "
     "potential of sources and sinks in a uniform flow). Streamlines that end in a production well bring the injected "
     "water back after the hydraulic travel time × C_aquifer / (n · C_water): the rock takes up heat as the water "
     "passes. The production temperature follows month by month. Checked against the doublet breakthrough "
     "π n b L² / 3Q and the critical distance 2Q / (π b q) without backflow.",
     ("Gringarten, A. C., Sauty, J. P. (1975): A theoretical study of heat extraction from aquifers with uniform "
      "regional flow. J. Geophys. Res. 80(35), 4956–4962.",
      "Clyde, C. G., Madabhushi, G. V. (1983): Spacing of wells for heat pumps. J. Water Resour. Plann. Manage. "
      "109(3), 203–212.",
      "Banks, D. (2009): Thermogeological assessment of open-loop well-doublet schemes: a review and synthesis of "
      "analytical approaches. Hydrogeology Journal 17, 1149–1155.")),
    ("Temperature plume",
     "The yearly net heat spreads from the injection wells with the groundwater: a continuous line source over the "
     "aquifer thickness with advection, longitudinal and transverse dispersion and thermal retardation (planar "
     "advective heat transport model). The heat exchange with the layers above and below is left out, so the plume "
     "comes out longer than it is.",
     ("Hähnlein, S., Molina-Giraldo, N., Blum, P., Bayer, P., Grathwohl, P. (2010): Ausbreitung von Kältefahnen im "
      "Grundwasser bei Erdwärmesonden. Grundwasser 15, 123–133.",
      "Kinzelbach, W. (1987): Numerische Methoden zur Modellierung des Transports von Schadstoffen im Grundwasser. "
      "Oldenbourg, München.")),
    ("Typical aquifer values",
     "kf and effective porosity per rock type are the middle of the usual ranges; dispersivity about 1/10 of the "
     "distance looked at. Use a pumping test and the state's groundwater maps where you have them.",
     ("DIN 18130-1 (1998): Bestimmung des Wasserdurchlässigkeitsbeiwerts.",
      "Hölting, B., Coldewey, W. G. (2013): Hydrogeologie. 8. Aufl., Springer Spektrum.",
      "Gelhar, L. W., Welty, C., Rehfeldt, K. R. (1992): A critical review of data on field-scale dispersion in "
      "aquifers. Water Resour. Res. 28(7), 1955–1974.")),
    ("Water quality",
     "Guide values for clogging (iron, manganese with oxygen) and for the heat exchanger material (chloride, sulfate, "
     "pH). Heat pump makers publish their own limits; theirs apply.",
     ("VDI 4640 Blatt 2 (2019), water quality requirements for open-loop systems.",)),
)


def rows() -> list[tuple[str, str, tuple[str, ...]]]:
    """The sources in the current language."""
    return [(t(topic), t(text), refs) for topic, text, refs in SOURCES]


def markdown() -> str:
    parts = []
    for topic, text, refs in rows():
        parts.append(f"**{topic}**  \n{text}\n" + "".join(f"\n- {r}" for r in refs))
    return "\n\n".join(parts)
