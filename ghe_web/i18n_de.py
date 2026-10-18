"""German texts. The key is the English text exactly as in the code; placeholders such as {n} or {x:.1f} must stay.

Terms follow German practice for borehole heat exchangers (VDI 4640): Erdwärmesonde (EWS), Sondenfeld,
Wärmeleitfähigkeit, ungestörte Untergrundtemperatur, thermischer Bohrlochwiderstand, Verfüllung, Wärmeträgerfluid,
Entzug / Eintrag, Jahresarbeitszahl (JAZ), Volllaststunden, Jahresdauerlinie. tests/test_i18n.py checks that every
English text has an entry here.
"""

DE: dict[str, str] = {
    # ------------------------------------------------------------ units and short words
    "%": "%",
    "% (mass)": "% (Masse)",
    "°C": "°C",
    "h": "h",
    "kW": "kW",
    "kWh": "kWh",
    "kg/s": "kg/s",
    "m": "m",
    "mm": "mm",
    "m·K/W": "m·K/W",
    "MJ/(m³·K)": "MJ/(m³·K)",
    "W/(m·K)": "W/(m·K)",
    "W/m²": "W/m²",
    "K/100 m": "K/100 m",
    "MWh/yr": "MWh/a",
    "years": "Jahre",
    "yes": "ja",
    "no": "nein",
    "heating": "Heizen",
    "cooling": "Kühlen",
    "hot water": "Trinkwarmwasser",
    "laminar": "laminar",
    "transitional": "Übergangsbereich",
    "turbulent": "turbulent",
    "passed": "erfüllt",
    "failed": "nicht erfüllt",
    "unknown": "unbekannt",
    "quick": "schnell",
    "normal": "normal",
    "thorough": "gründlich",

    # ------------------------------------------------------------ page, steps, sidebar
    "⓪ Site plan": "⓪ Lageplan",
    "① Ground & borefield": "① Untergrund & Sondenfeld",
    "② Borehole & fluid": "② Sonde & Fluid",
    "③ Loads": "③ Lasten",
    "④ Limits & calculation": "④ Grenzwerte & Berechnung",
    "More inputs": "Weitere Eingaben",
    "📊 Results": "📊 Ergebnisse",
    "Project": "Projekt",
    "Project name": "Projektname",
    "Open a saved project": "Gespeichertes Projekt öffnen",
    "Could not open this file: {error}": "Diese Datei konnte nicht geöffnet werden: {error}",
    "Save project": "Projekt speichern",
    "Projects are saved as a file on your computer, including the language. Nothing is stored on the server.":
        "Projekte werden als Datei auf Ihrem Rechner gespeichert, einschließlich der Sprache. Auf dem Server wird "
        "nichts gespeichert.",
    "Borehole heat exchanger sizing": "Auslegung von Erdwärmesonden",
    "Fill in the four input steps, then press **Size borefield** on the left. Every field has a question mark with "
    "an explanation; the drop-downs fill in typical values.":
        "Füllen Sie die vier Eingabeschritte aus und klicken Sie dann links auf **Sondenfeld auslegen**. Jedes Feld "
        "hat ein Fragezeichen mit einer Erläuterung; die Auswahllisten setzen typische Werte ein.",
    "How to use this tool": "So arbeiten Sie mit diesem Werkzeug",
    "1. **⓪ Site plan** (optional): find the parcel and place as many boreholes as fit.\n"
    "2. **① Ground & borefield**: ground properties (or predicted layers) and the borefield layout.\n"
    "3. **② Borehole & fluid**: borehole heat exchanger, heat transfer fluid and flow rate.\n"
    "4. **③ Loads**: the heat extracted from and injected into the ground, or the building demand with the heat "
    "pump efficiency.\n"
    "5. **④ Limits & calculation**: the allowed fluid temperatures, and whether to size the length or check a given "
    "one.\n"
    "6. Press **Size borefield** in the sidebar. The **📊 Results** tab shows key figures, charts, further analysis "
    "and the PDF report and Excel export.\n\n"
    "Save the project in the sidebar to continue later. Calculations use the open-source "
    "[GHEtool](https://github.com/wouterpeere/GHEtool).":
        "1. **⓪ Lageplan** (optional): Flurstück finden und so viele Sonden wie möglich platzieren.\n"
        "2. **① Untergrund & Sondenfeld**: Untergrundeigenschaften (oder prognostizierte Schichten) und die "
        "Anordnung des Sondenfelds.\n"
        "3. **② Sonde & Fluid**: Erdwärmesonde, Wärmeträgerfluid und Durchfluss.\n"
        "4. **③ Lasten**: Wärmeentzug aus dem und Wärmeeintrag in den Untergrund, oder der Gebäudebedarf mit der "
        "Effizienz der Wärmepumpe.\n"
        "5. **④ Grenzwerte & Berechnung**: die zulässigen Fluidtemperaturen und ob die Länge ausgelegt oder eine "
        "vorgegebene Länge geprüft wird.\n"
        "6. In der Seitenleiste auf **Sondenfeld auslegen** klicken. Der Reiter **📊 Ergebnisse** zeigt Kennwerte, "
        "Diagramme, weitere Analysen sowie PDF-Bericht und Excel-Export.\n\n"
        "Speichern Sie das Projekt in der Seitenleiste, um später weiterzuarbeiten. Die Berechnungen nutzen das "
        "Open-Source-Programm [GHEtool](https://github.com/wouterpeere/GHEtool).",
    "Input method": "Eingabeart",
    "Choose to fill in typical values…": "Auswählen, um typische Werte einzusetzen …",
    "Fills in the fields below with typical values.": "Setzt typische Werte in die Felder darunter ein.",
    "Monthly values. Click a cell to edit; you can paste a column from Excel.":
        "Monatswerte. Zum Bearbeiten in eine Zelle klicken; Sie können eine Spalte aus Excel einfügen.",
    "Calculation": "Berechnung",
    "{n} input(s) need attention:": "{n} Eingabe(n) prüfen:",
    "Size borefield": "Sondenfeld auslegen",
    "Check temperatures": "Temperaturen prüfen",
    "Calculating... hourly sizing can take up to a minute.":
        "Berechnung läuft … eine stündliche Auslegung kann bis zu einer Minute dauern.",
    "Calculating... hourly sizing with a temperature-dependent COP takes one to two minutes.":
        "Berechnung läuft … eine stündliche Auslegung mit temperaturabhängigem COP dauert ein bis zwei Minuten.",
    "The calculation failed: {error}": "Die Berechnung ist fehlgeschlagen: {error}",
    "The inputs changed since the last calculation.": "Die Eingaben wurden seit der letzten Berechnung geändert.",
    "See the **📊 Results** tab for details.": "Details im Reiter **📊 Ergebnisse**.",
    "{n} boreholes, {total:,.0f} m in total": "{n} Sonden, insgesamt {total:,.0f} m",
    "Borefield set to an irregular field with the {n} positions from the site plan.":
        "Das Sondenfeld wurde auf ein unregelmäßiges Feld mit den {n} Positionen aus dem Lageplan gesetzt.",

    # ------------------------------------------------------------ input sections (properties)
    "Ground": "Untergrund",
    "Constant ground temperature": "Konstante Untergrundtemperatur",
    "Surface temperature + heat flux": "Oberflächentemperatur + Wärmestromdichte",
    "Ground temperature rises with depth because of the geothermal heat flux (as in EED).":
        "Die Untergrundtemperatur steigt durch die geothermische Wärmestromdichte mit der Tiefe an (wie in EED).",
    "Surface temperature + gradient": "Oberflächentemperatur + Gradient",
    "Ground temperature rises linearly with depth. Recommended for boreholes deeper than about 150 m.":
        "Die Untergrundtemperatur steigt linear mit der Tiefe an. Empfohlen für Sonden tiefer als etwa 150 m.",
    "Ground thermal conductivity": "Wärmeleitfähigkeit des Untergrunds",
    "Undisturbed ground temperature": "Ungestörte Untergrundtemperatur",
    "Ground surface temperature": "Temperatur an der Geländeoberfläche",
    "Average yearly temperature at the surface; it increases with depth.":
        "Jahresmitteltemperatur an der Geländeoberfläche; sie nimmt mit der Tiefe zu.",
    "Volumetric heat capacity": "Volumetrische Wärmekapazität",
    "Ground layers": "Untergrundschichten",
    "Layers from the surface down, each with its own conductivity and heat capacity. Predicted from nearby borehole "
    "logs or entered by hand.":
        "Schichten von der Geländeoberfläche abwärts, jede mit eigener Wärmeleitfähigkeit und Wärmekapazität. "
        "Aus Bohrprofilen in der Nähe prognostiziert oder von Hand eingegeben.",
    "Geothermal heat flux": "Geothermische Wärmestromdichte",
    "Geothermal gradient": "Geothermischer Gradient",
    "Rock type": "Gesteinsart",
    "Typical values (VDI 4640). Use measured values if you have them.":
        "Typische Werte (VDI 4640). Verwenden Sie Messwerte, wenn vorhanden.",
    "A ground thermal conductivity of {k:g} W/(m·K) is unusually high. Is it from a thermal response test?":
        "Eine Wärmeleitfähigkeit des Untergrunds von {k:g} W/(m·K) ist ungewöhnlich hoch. Stammt sie aus einem "
        "Thermal Response Test?",
    "A ground thermal conductivity below 1 W/(m·K) is typical of dry soil only; the boreholes will be long.":
        "Eine Wärmeleitfähigkeit unter 1 W/(m·K) ist nur für trockene Lockergesteine typisch; die Sonden werden "
        "lang.",
    "Borefield": "Sondenfeld",
    "Rectangular field": "Rechteckiges Feld",
    "Irregular field (shapefile)": "Unregelmäßiges Feld (Shapefile)",
    "Upload a point shapefile with one point per borehole, or edit the coordinates directly.":
        "Laden Sie ein Punkt-Shapefile mit einem Punkt je Sonde hoch, oder bearbeiten Sie die Koordinaten direkt.",
    "Boreholes in x direction": "Sonden in x-Richtung",
    "Boreholes in y direction": "Sonden in y-Richtung",
    "Spacing in x direction": "Abstand in x-Richtung",
    "Spacing in y direction": "Abstand in y-Richtung",
    "Borehole positions": "Sondenpositionen",
    "Borehole length": "Sondenlänge",
    "Start value; sizing calculates the required length.": "Startwert; die Auslegung berechnet die erforderliche Länge.",
    "Buried depth": "Überdeckung (Tiefe Sondenkopf)",
    "Depth of the top of the borehole below ground level.":
        "Tiefe der Sondenoberkante unter Geländeoberkante (GOK).",
    "Borehole radius": "Bohrlochradius",
    "Half the drilling diameter.": "Halber Bohrdurchmesser.",
    "Drilling diameter": "Bohrdurchmesser",
    "Boreholes {a} and {b} overlap ({d:.2f} m apart).": "Die Sonden {a} und {b} überschneiden sich ({d:.2f} m Abstand).",
    "With a spacing below 4.5 m the boreholes influence each other strongly; 5 to 8 m is common.":
        "Bei einem Abstand unter 4,5 m beeinflussen sich die Sonden stark; üblich sind 5 bis 8 m.",
    "Boreholes {a} and {b} are only {d:.1f} m apart; 5 to 8 m is common.":
        "Die Sonden {a} und {b} sind nur {d:.1f} m voneinander entfernt; üblich sind 5 bis 8 m.",
    "Borehole heat exchanger": "Erdwärmesonde",
    "Single U-tube": "Einfach-U-Sonde",
    "Double U-tube": "Doppel-U-Sonde",
    "Coaxial": "Koaxialsonde",
    "Known borehole resistance (TRT)": "Bekannter Bohrlochwiderstand (TRT)",
    "Use a measured borehole resistance instead of calculating it from the pipe and fluid.":
        "Gemessenen Bohrlochwiderstand verwenden, statt ihn aus Rohr und Fluid zu berechnen.",
    "Grout thermal conductivity": "Wärmeleitfähigkeit der Verfüllung",
    "Pipe thermal conductivity": "Wärmeleitfähigkeit des Sondenrohrs",
    "Pipe inner radius": "Innenradius Sondenrohr",
    "Pipe outer radius": "Außenradius Sondenrohr",
    "Shank spacing (pipe centre to borehole centre)": "Schenkelabstand (Rohrmitte bis Bohrlochmitte)",
    "Inner pipe, inner radius": "Innenrohr, Innenradius",
    "Inner pipe, outer radius": "Innenrohr, Außenradius",
    "Outer pipe, inner radius": "Außenrohr, Innenradius",
    "Outer pipe, outer radius": "Außenrohr, Außenradius",
    "Effective borehole thermal resistance": "Effektiver thermischer Bohrlochwiderstand",
    "From a thermal response test. Inlet/outlet temperatures and pressure drop cannot be calculated in this mode.":
        "Aus einem Thermal Response Test. Ein- und Austrittstemperaturen sowie der Druckverlust können in dieser "
        "Betriebsart nicht berechnet werden.",
    "Pipe": "Sondenrohr",
    "Grout": "Verfüllung",
    "The outer radius of the pipe must be larger than its inner radius.":
        "Der Außenradius des Rohrs muss größer als sein Innenradius sein.",
    "The coaxial radii must increase from the inside out: inner pipe inner < inner pipe outer < outer pipe inner < "
    "outer pipe outer.":
        "Die Radien der Koaxialsonde müssen von innen nach außen zunehmen: Innenrohr innen < Innenrohr außen < "
        "Außenrohr innen < Außenrohr außen.",
    "Fluid": "Wärmeträgerfluid",
    "Water / antifreeze mixture": "Wasser-Frostschutz-Gemisch",
    "MPG = propylene glycol, MEG = ethylene glycol, MEA = ethanol, MMA = methanol. The others are commercial "
    "products.":
        "MPG = Propylenglykol, MEG = Ethylenglykol, MEA = Ethanol, MMA = Methanol. Die übrigen sind Handelsprodukte.",
    "Antifreeze concentration": "Frostschutzkonzentration",
    "Share of antifreeze by mass. GHEtool converts it to volume for the commercial products, whose data sheets give "
    "volume percentages.":
        "Massenanteil des Frostschutzmittels. Für die Handelsprodukte, deren Datenblätter Volumenprozent angeben, "
        "rechnet GHEtool in Volumenanteile um.",
    "GHEtool has data for {fluid} between {low} and {high} % by mass.":
        "GHEtool hat Stoffdaten für {fluid} zwischen {low} und {high} Massen-%.",
    "Flow rate": "Durchfluss",
    "Constant flow per borehole": "Konstanter Durchfluss je Sonde",
    "Mass flow rate per borehole": "Massenstrom je Sonde",
    "Pump efficiency": "Pumpenwirkungsgrad",
    "Wire-to-water efficiency of the circulation pump (motor and pump together). Small brine circulators reach 25 to "
    "40 %, large pumps 50 to 70 %. Only used for the pump power and pump energy in the results.":
        "Gesamtwirkungsgrad der Umwälzpumpe (Motor und Pumpe zusammen). Kleine Soleumwälzpumpen erreichen 25 bis "
        "40 %, große Pumpen 50 bis 70 %. Wird nur für Pumpenleistung und Pumpenenergie in den Ergebnissen verwendet.",
    "Pump running hours per year": "Pumpenlaufzeit pro Jahr",
    "How long the borefield pump runs in a year, roughly the heat pump's running hours. Use 8760 if it runs all "
    "year. Only used for the pump energy in the results.":
        "Wie lange die Sondenkreispumpe im Jahr läuft, etwa die Laufzeit der Wärmepumpe. 8760 eintragen, wenn sie "
        "ganzjährig läuft. Wird nur für die Pumpenenergie in den Ergebnissen verwendet.",
    "Ground load": "Wärmeentzug und -eintrag",
    "Heat taken from (extraction) and put into (injection) the ground.":
        "Wärme, die dem Untergrund entzogen (Entzug) bzw. ihm zugeführt (Eintrag) wird.",
    "Monthly energy and peaks": "Monatliche Energie und Spitzenlasten",
    "Extracted energy": "Entzugsenergie",
    "Injected energy": "Eintragsenergie",
    "Peak extraction": "Spitzenentzugsleistung",
    "Peak injection": "Spitzeneintragsleistung",
    "Simulation period": "Simulationszeitraum",
    "Duration of the heating peak": "Dauer der Heizspitze",
    "How long the peak load lasts (as in EED). GHEtool's default is 6 h.":
        "Wie lange die Spitzenlast anhält (wie in EED). Standard in GHEtool sind 6 h.",
    "Duration of the cooling peak": "Dauer der Kühlspitze",
    "Yearly building demand (EED style)": "Jährlicher Gebäudebedarf (wie EED)",
    "Yearly heating and cooling demand of the building, split over the months with a profile. Peaks follow the "
    "profile: the month with the largest share gets the full peak.":
        "Jährlicher Heizwärme- und Kältebedarf des Gebäudes, mit einem Profil auf die Monate verteilt. Die "
        "Spitzenlasten folgen dem Profil: Der Monat mit dem größten Anteil erhält die volle Spitze.",
    "Heating demand": "Heizwärmebedarf",
    "Heating profile": "Heizprofil",
    "Peak heating": "Heizlast (Spitze)",
    "Cooling demand": "Kältebedarf",
    "Cooling profile": "Kühlprofil",
    "Peak cooling": "Kühllast (Spitze)",
    "SCOP heating": "SCOP Heizen",
    "Seasonal efficiency of the heat pump in heating. Ground extraction = heating × (1 − 1/SCOP). Not used when Heat "
    "pump efficiency is set to depend on the fluid temperature.":
        "Jahreseffizienz der Wärmepumpe im Heizbetrieb. Entzug aus dem Untergrund = Heizwärme × (1 − 1/SCOP). Wird "
        "nicht verwendet, wenn die Wärmepumpeneffizienz von der Fluidtemperatur abhängt.",
    "SEER cooling": "SEER Kühlen",
    "Seasonal efficiency in cooling. Use a high value (e.g. 20+) for passive cooling. Ground injection = cooling × "
    "(1 + 1/SEER). Not used when Heat pump efficiency depends on the fluid temperature.":
        "Jahreseffizienz im Kühlbetrieb. Für passive Kühlung einen hohen Wert (z. B. 20 und mehr) verwenden. Eintrag "
        "in den Untergrund = Kälte × (1 + 1/SEER). Wird nicht verwendet, wenn die Wärmepumpeneffizienz von der "
        "Fluidtemperatur abhängt.",
    "Domestic hot water demand": "Trinkwarmwasserbedarf",
    "Spread evenly over the year.": "Gleichmäßig über das Jahr verteilt.",
    "SCOP hot water": "SCOP Trinkwarmwasser",
    "Hourly building demand": "Stündlicher Gebäudebedarf",
    "Heating and cooling demand of the building for every hour of a year. The heat pump efficiency turns it into the "
    "load on the ground.":
        "Heizwärme- und Kältebedarf des Gebäudes für jede Stunde eines Jahres. Mit der Effizienz der Wärmepumpe wird "
        "daraus die Last auf den Untergrund.",
    "Hourly demand": "Stündlicher Bedarf",
    "Size with hourly resolution": "Stündlich auslegen",
    "Slower but catches short peaks. Off: sizes on monthly values derived from the hours.":
        "Langsamer, erfasst aber kurze Spitzen. Aus: Auslegung mit Monatswerten, die aus den Stundenwerten "
        "abgeleitet werden.",
    "Heat pump efficiency": "Wärmepumpeneffizienz",
    "Only used with building demand (yearly or hourly), where the heat pump turns building demand into ground load.":
        "Nur bei Gebäudebedarf (jährlich oder stündlich), wo die Wärmepumpe den Gebäudebedarf in die Last auf den "
        "Untergrund umrechnet.",
    "Fixed SCOP / SEER": "Feste SCOP / SEER",
    "Uses the SCOP and SEER entered with the building demand above.":
        "Verwendet die beim Gebäudebedarf oben eingegebenen Werte für SCOP und SEER.",
    "Depends on the fluid temperature": "Abhängig von der Fluidtemperatur",
    "The COP falls as the borefield gets colder, so more electricity and less ground heat are needed in a cold year. "
    "Replaces the SCOP and SEER above and gives the real seasonal performance factor. Sizing takes longer, with "
    "hourly sizing one to two minutes.":
        "Der COP sinkt, wenn das Sondenfeld kälter wird; in einem kalten Jahr sind also mehr Strom und weniger "
        "Erdwärme nötig. Ersetzt SCOP und SEER oben und liefert die tatsächliche Jahresarbeitszahl. Die Auslegung "
        "dauert länger, stündlich ein bis zwei Minuten.",
    "COP at -5 °C fluid": "COP bei −5 °C Fluid",
    "COP at 0 °C fluid": "COP bei 0 °C Fluid",
    "COP at 5 °C fluid": "COP bei 5 °C Fluid",
    "COP at 10 °C fluid": "COP bei 10 °C Fluid",
    "COP at 15 °C fluid": "COP bei 15 °C Fluid",
    "EER at 10 °C fluid": "EER bei 10 °C Fluid",
    "EER at 15 °C fluid": "EER bei 15 °C Fluid",
    "EER at 20 °C fluid": "EER bei 20 °C Fluid",
    "EER at 25 °C fluid": "EER bei 25 °C Fluid",
    "EER at 30 °C fluid": "EER bei 30 °C Fluid",
    **{f"Heating COP when the average fluid temperature in the borefield is {t} °C (heat pump source side). Take it "
       f"from the data sheet at the supply temperature of your heating system.":
       f"COP im Heizbetrieb bei einer mittleren Fluidtemperatur im Sondenfeld von {t} °C (Quellenseite der "
       f"Wärmepumpe). Aus dem Datenblatt bei der Vorlauftemperatur Ihres Heizsystems entnehmen."
       for t in (-5, 0, 5, 10, 15)},
    **{f"Cooling EER when the average fluid temperature is {t} °C. Passive cooling (only pumps): use a high value "
       f"such as 20.":
       f"EER im Kühlbetrieb bei einer mittleren Fluidtemperatur von {t} °C. Passive Kühlung (nur Pumpen): einen hohen "
       f"Wert wie 20 verwenden."
       for t in (10, 15, 20, 25, 30)},
    "Heating system": "Heizsystem",
    "Typical brine/water heat pump COPs at three supply temperatures (EN 14511 data sheets). Replace them with your "
    "heat pump's values if you have them.":
        "Typische COP von Sole/Wasser-Wärmepumpen bei drei Vorlauftemperaturen (Datenblätter nach EN 14511). Ersetzen "
        "Sie sie durch die Werte Ihrer Wärmepumpe, falls vorhanden.",
    "Cooling": "Kühlen",
    "Passive cooling uses only the circulation pumps; active cooling runs the heat pump as a chiller.":
        "Passive Kühlung nutzt nur die Umwälzpumpen; aktive Kühlung betreibt die Wärmepumpe als Kältemaschine.",
    "The COP usually rises with the fluid temperature. Check the values from left to right.":
        "Der COP steigt normalerweise mit der Fluidtemperatur. Prüfen Sie die Werte von links nach rechts.",
    "Temperature limits": "Temperaturgrenzen",
    "Allowed average fluid temperature in the borefield.": "Zulässige mittlere Fluidtemperatur im Sondenfeld.",
    "Average fluid temperature": "Mittlere Fluidtemperatur",
    "Minimum fluid temperature": "Minimale Fluidtemperatur",
    "Maximum fluid temperature": "Maximale Fluidtemperatur",
    "The maximum fluid temperature must be above the minimum.":
        "Die maximale Fluidtemperatur muss über der minimalen liegen.",
    "Size the borehole length": "Sondenlänge auslegen",
    "Finds the shortest borehole length that keeps the fluid within the temperature limits.":
        "Ermittelt die kürzeste Sondenlänge, bei der das Fluid innerhalb der Temperaturgrenzen bleibt.",
    "Check a given length": "Vorgegebene Länge prüfen",
    "Uses the borehole length from the Borefield section as it is and shows the temperatures, e.g. to check an "
    "existing field or a design from another tool.":
        "Verwendet die Sondenlänge aus dem Abschnitt Sondenfeld unverändert und zeigt die Temperaturen, z. B. um ein "
        "bestehendes Feld oder eine Auslegung aus einem anderen Programm zu prüfen.",

    # ------------------------------------------------------------ validation
    "{label}: the {load} demand needs 8760 hourly values.": "{label}: Der Bedarf {load} braucht 8760 Stundenwerte.",
    "{label}: the {load} demand cannot be negative.": "{label}: Der Bedarf {load} darf nicht negativ sein.",
    "{label}: not a layer table.": "{label}: keine Schichttabelle.",
    "{label}: at least one borehole is needed.": "{label}: Mindestens eine Sonde ist erforderlich.",
    "{label}: every borehole needs a numeric x and y coordinate.":
        "{label}: Jede Sonde braucht eine numerische x- und y-Koordinate.",
    "{label}: 12 monthly values are needed, found {n}.": "{label}: 12 Monatswerte erforderlich, {n} gefunden.",
    "{label}: '{value}' is not one of the options.": "{label}: „{value}“ ist keine der Auswahlmöglichkeiten.",
    "{label}: {value:g} is below the minimum of {limit:g} {unit}.":
        "{label}: {value:g} liegt unter dem Mindestwert von {limit:g} {unit}.",
    "{label}: {value:g} is above the maximum of {limit:g} {unit}.":
        "{label}: {value:g} liegt über dem Höchstwert von {limit:g} {unit}.",
    "{label}: no value given.": "{label}: kein Wert angegeben.",
    "{section}: no input given.": "{section}: keine Eingabe vorhanden.",
    "The pipes stick out of the borehole: shank spacing + outer pipe radius ({size:g} mm) is more than the borehole "
    "radius ({r_b:g} mm).":
        "Die Rohre ragen aus dem Bohrloch: Schenkelabstand + Rohraußenradius ({size:g} mm) ist größer als der "
        "Bohrlochradius ({r_b:g} mm).",
    "The pipe legs overlap: increase the shank spacing to at least {d:.1f} mm or use smaller pipes.":
        "Die Rohrschenkel überschneiden sich: Schenkelabstand auf mindestens {d:.1f} mm erhöhen oder kleinere Rohre "
        "verwenden.",
    "The outer pipe ({r:g} mm radius) does not fit in the borehole ({r_b:g} mm radius).":
        "Das Außenrohr ({r:g} mm Radius) passt nicht in das Bohrloch ({r_b:g} mm Radius).",
    "The ground load is entered directly (monthly energy), so there is no heat pump to apply this to. Choose yearly "
    "or hourly building demand under Ground load to use it.":
        "Die Last auf den Untergrund ist direkt eingegeben (monatliche Energie); es gibt also keine Wärmepumpe, auf "
        "die dies angewendet werden kann. Wählen Sie unter Wärmeentzug und -eintrag einen jährlichen oder stündlichen "
        "Gebäudebedarf.",
    "This file is not a GHEtool Web project.": "Diese Datei ist kein GHEtool-Web-Projekt.",

    # ------------------------------------------------------------ catalog
    "Clay / silt, dry": "Ton / Schluff, trocken",
    "Clay / silt, water saturated": "Ton / Schluff, wassergesättigt",
    "Sand, dry": "Sand, trocken",
    "Sand, moist": "Sand, feucht",
    "Sand, water saturated": "Sand, wassergesättigt",
    "Gravel, water saturated": "Kies, wassergesättigt",
    "Till / loam": "Geschiebemergel / Lehm",
    "Claystone / mudstone": "Tonstein / Schluffstein",
    "Bentonite, standard": "Bentonit, Standard",
    "Bentonite-cement": "Bentonit-Zement",
    "Thermally enhanced grout": "Thermisch verbesserte Verfüllung",
    "High-performance grout": "Hochleistungsverfüllung",
    "Quartz sand, water saturated": "Quarzsand, wassergesättigt",
    "PE100 25 × 2.3 (SDR 11)": "PE100 25 × 2,3 (SDR 11)",
    "PE100 32 × 2.9 (SDR 11)": "PE100 32 × 2,9 (SDR 11)",
    "PE100 32 × 2.0 (SDR 17)": "PE100 32 × 2,0 (SDR 17)",
    "PE100 40 × 3.7 (SDR 11)": "PE100 40 × 3,7 (SDR 11)",
    "PE100 40 × 2.4 (SDR 17)": "PE100 40 × 2,4 (SDR 17)",
    "PE100 50 × 4.6 (SDR 11)": "PE100 50 × 4,6 (SDR 11)",
    "Ø 115 mm": "Ø 115 mm",
    "Ø 140 mm": "Ø 140 mm",
    "Ø 152 mm": "Ø 152 mm",
    "Ø 165 mm": "Ø 165 mm",
    "Ø 180 mm": "Ø 180 mm",
    "Water": "Wasser",
    "MPG": "MPG",
    "MEG": "MEG",
    "MEA": "MEA",
    "MMA": "MMA",
    "Thermox DTX": "Thermox DTX",
    "Coolflow NTP": "Coolflow NTP",
    "Kilfrost GEO": "Kilfrost GEO",
    "Kilfrost GEO Plus": "Kilfrost GEO Plus",
    "GeoPro": "GeoPro",
    "Heating (office, GHEtool example)": "Heizen (Büro, GHEtool-Beispiel)",
    "Cooling (office, GHEtool example)": "Kühlen (Büro, GHEtool-Beispiel)",
    "Constant": "Konstant",
    "Floor heating (35 °C)": "Fußbodenheizung (35 °C)",
    "Low-temperature radiators (45 °C)": "Niedertemperatur-Heizkörper (45 °C)",
    "Radiators (55 °C)": "Heizkörper (55 °C)",
    "Passive cooling (pumps only)": "Passive Kühlung (nur Pumpen)",
    "Active cooling (heat pump as chiller)": "Aktive Kühlung (Wärmepumpe als Kältemaschine)",

    # ------------------------------------------------------------ rocks (VDI 4640)
    "Made ground / fill": "Auffüllung",
    "Topsoil / humus": "Mutterboden / Humus",
    "Peat": "Torf",
    "Clay": "Ton",
    "Silt / loess": "Schluff / Löss",
    "Sand": "Sand",
    "Gravel": "Kies",
    "Till / boulder clay": "Geschiebemergel",
    "Claystone / siltstone": "Tonstein / Schluffstein",
    "Shale / slate": "Tonschiefer",
    "Marl": "Mergel",
    "Sandstone": "Sandstein",
    "Greywacke": "Grauwacke",
    "Conglomerate / breccia": "Konglomerat / Brekzie",
    "Limestone": "Kalkstein",
    "Chalk": "Kreide",
    "Dolomite": "Dolomit",
    "Anhydrite": "Anhydrit",
    "Gypsum": "Gips",
    "Rock salt": "Steinsalz",
    "Coal / lignite": "Kohle / Braunkohle",
    "Granite": "Granit",
    "Diorite": "Diorit",
    "Gabbro": "Gabbro",
    "Rhyolite / porphyry": "Rhyolith / Porphyr",
    "Basalt": "Basalt",
    "Diabase": "Diabas",
    "Andesite": "Andesit",
    "Tuff": "Tuff",
    "Phyllite": "Phyllit",
    "Mica schist": "Glimmerschiefer",
    "Gneiss": "Gneis",
    "Migmatite": "Migmatit",
    "Amphibolite": "Amphibolit",
    "Quartzite": "Quarzit",
    "Marble": "Marmor",
    "Unknown": "Unbekannt",
    "Uniform ground": "Homogener Untergrund",
    "🌙 Dark mode: menu **⋮** at the top right > **Settings** > theme **Dark**.":
        "🌙 Dunkelmodus: Menü **⋮** oben rechts > **Settings** > Theme **Dark**.",
    # ------------------------------------------------------------ results, charts, reports, site plan, ground layers
    " (moist)": " (feucht)",
    " average {k:.2f}": " Mittelwert {k:.2f}",
    " – ignored": " – nicht berücksichtigt",
    "##### Site plan: from a Flurstück to borehole positions": "##### Lageplan: vom Flurstück zu den Sondenstandorten",
    "**1 · Parcel**": "**1 · Flurstück**",
    "**2 · Distances**": "**2 · Abstände**",
    "**3 · Check the buildings and mark areas to keep free**":
        "**3 · Gebäude prüfen und freizuhaltende Flächen markieren**",
    "**4 · Result**": "**4 · Ergebnis**",
    "**Average conductivity for other borehole lengths**": "**Mittlere Wärmeleitfähigkeit für andere Sondenlängen**",
    "**CSV files**": "**CSV-Dateien**",
    "**Everything in one zip**": "**Alles in einer ZIP-Datei**",
    "**Excel workbook**": "**Excel-Arbeitsmappe**",
    "**Ground layers**": "**Schichtenfolge**",
    "**PDF report**": "**PDF-Bericht**",
    "**Predicted layers at {place}**": "**Prognostizierte Schichten bei {place}**",
    "**Result: {objective}**": "**Ergebnis: {objective}**",
    "**Share of the heat exchange per layer**": "**Anteil am Wärmeaustausch je Schicht**",
    ", cover": ", Deckschicht",
    ", moist": ", feucht",
    "4 digits, e.g. 3412. It is on the Liegenschaftskarte or in the Grundbuch (Gemarkungsschlüssel), not the Gemarkung name.":
        "4 Ziffern, z. B. 3412. Sie steht auf der Liegenschaftskarte oder im Grundbuch (Gemarkungsschlüssel), "
        "nicht der Name der Gemarkung.",
    "8760 h, heating {heat:,.0f} MWh (peak {heat_peak:,.0f} kW), cooling {cool:,.0f} MWh (peak {cool_peak:,.0f} kW)":
        "8760 h, Heizen {heat:,.0f} MWh (Spitze {heat_peak:,.0f} kW), Kühlen {cool:,.0f} MWh (Spitze {cool_peak:,.0f} kW)",
    "Address": "Adresse",
    "Address not found.": "Adresse nicht gefunden.",
    "Aerial image (Esri, worldwide)": "Luftbild (Esri, weltweit)",
    "Aerial image {state} (DOP)": "Luftbild {state} (DOP)",
    "Allowed area": "Zulässige Fläche",
    "Allowed area: {a:,.0f} m2": "Zulässige Fläche: {a:,.0f} m²",
    "An address": "Eine Adresse",
    "Asking the geological services...": "Geologische Dienste werden abgefragt …",
    "At least the deepest borehole you consider; the last layer continues below.":
        "Mindestens die tiefste betrachtete Sonde; die letzte Schicht setzt sich nach unten fort.",
    "At the coldest fluid temperature, where the fluid is most viscous. The borehole only: add the manifold, header pipes and heat pump evaporator for the pump. The kink is where the flow turns turbulent.":
        "Bei der niedrigsten Fluidtemperatur, wo das Fluid am zähesten ist. Nur die Sonde: Für die Pumpe kommen "
        "Verteiler, Anbindeleitungen und Verdampfer der Wärmepumpe hinzu. Am Knick wird die Strömung turbulent.",
    "Author": "Bearbeiter",
    "Average conductivity": "Mittlere Wärmeleitfähigkeit",
    "Average conductivity [W/(m·K)]": "Mittlere Wärmeleitfähigkeit [W/(m·K)]",
    "Average conductivity along the borehole": "Mittlere Wärmeleitfähigkeit entlang der Sonde",
    "Average fluid": "Mittlere Fluidtemperatur",
    "Average fluid (base load)": "Mittlere Fluidtemperatur (Grundlast)",
    "Average fluid (peak extraction)": "Mittlere Fluidtemperatur (Spitzenentzug)",
    "Average fluid (peak injection)": "Mittlere Fluidtemperatur (Spitzeneintrag)",
    "Average fluid temperature [°C]": "Mittlere Fluidtemperatur [°C]",
    "Average fluid, daily range (hourly)": "Mittlere Fluidtemperatur, Tagesspanne (stündlich)",
    "Average heat capacity": "Mittlere Wärmekapazität",
    "Average over the borehole": "Mittelwert über die Sonde",
    "Average over the {length:.0f} m borehole: k = {k:.2f} W/(m·K), C = {c:.2f} MJ/(m³·K).":
        "Mittelwert über die {length:.0f} m lange Sonde: λ = {k:.2f} W/(m·K), C = {c:.2f} MJ/(m³·K).",
    "BHE shapefile (.zip)": "EWS-Shapefile (.zip)",
    "BHE site plan, created {date} with GHEtool Web": "EWS-Lageplan, erstellt am {date} mit GHEtool Web",
    "BHE {n}": "EWS {n}",
    "Backup cooling": "Zusatzkühlung",
    "Backup heating": "Zusatzheizung",
    "Balanced ground": "Ausgeglichener Untergrund",
    "Base [m]": "Unterkante [m]",
    "Basis": "Grundlage",
    "Blue: coldest fluid (heating peaks). Red: warmest fluid (cooling peaks). Dashed: your limits. Grey dots: the lowest and highest value.":
        "Blau: kältestes Fluid (Heizspitzen). Rot: wärmstes Fluid (Kühlspitzen). Gestrichelt: Ihre Grenzwerte. "
        "Graue Punkte: niedrigster und höchster Wert.",
    "Borefield design": "Auslegung des Sondenfelds",
    "Borefield layout": "Anordnung des Sondenfelds",
    "Borehole": "Sonde",
    "Borehole and hydraulics": "Sonde und Hydraulik",
    "Borehole cross-section": "Sondenquerschnitt",
    "Borehole length [m]": "Sondenlänge [m]",
    "Borehole logs you have (optional): BoreholeML (.xml) from a state portal, or a table (.csv, .xlsx) with one row per layer":
        "Eigene Schichtenverzeichnisse (optional): BoreholeML (.xml) aus einem Landesportal oder eine Tabelle "
        "(.csv, .xlsx) mit einer Zeile je Schicht",
    "Borehole logs: {error}": "Schichtenverzeichnisse: {error}",
    "Borehole resistance ±15 %": "Bohrlochwiderstand ±15 %",
    "Borehole site plan": "Lageplan der Sonden",
    "Borehole thermal resistance": "Thermischer Bohrlochwiderstand",
    "Borehole thermal resistance Rb": "Thermischer Bohrlochwiderstand Rb",
    "Borehole wall": "Bohrlochwand",
    "Borehole {name} has no coordinates. Set the site location first, or add x and y columns.":
        "Bohrung {name} hat keine Koordinaten. Legen Sie zuerst den Standort fest oder ergänzen Sie die Spalten x und y.",
    "Borehole Ø {d:.0f} mm, outer pipe Ø {p:.0f} mm": "Bohrloch Ø {d:.0f} mm, Außenrohr Ø {p:.0f} mm",
    "Borehole Ø {d:.0f} mm, pipe Ø {p:.0f} mm": "Bohrloch Ø {d:.0f} mm, Rohr Ø {p:.0f} mm",
    "Boreholes": "Sonden",
    "Boreholes ({n})": "Sonden ({n})",
    "Boreholes: {n}": "Sonden: {n}",
    "Bottom of the layer. The last layer continues downwards.":
        "Unterkante der Schicht. Die letzte Schicht setzt sich nach unten fort.",
    "Box": "Rahmen",
    "Bremen publishes no fixed value (set in the permit); 5 m is the conservative LAWA value. VDI 4640 Blatt 2 is commonly cited with 3 m to the border; LAWA recommends 5 m.":
        "Bremen nennt keinen festen Wert (Festlegung in der Erlaubnis); 5 m ist der vorsichtige LAWA-Wert. "
        "VDI 4640 Blatt 2 wird meist mit 3 m zur Grundstücksgrenze zitiert; die LAWA empfiehlt 5 m.",
    "Building": "Gebäude",
    "Building cooling [MWh]": "Gebäude Kühlen [MWh]",
    "Building demand [MWh]": "Gebäudebedarf [MWh]",
    "Building demand [MWh] (cooling below zero)": "Gebäudebedarf [MWh] (Kühlen negativ)",
    "Building demand per month (before heat pump efficiency)": "Gebäudebedarf je Monat (vor Wärmepumpeneffizienz)",
    "Building heating [MWh]": "Gebäude Heizen [MWh]",
    "Building load ±10 %": "Gebäudelast ±10 %",
    "Building {n} ({source})": "Gebäude {n} ({source})",
    "Building {n} ({source}, {area:,.0f} m²)": "Gebäude {n} ({source}, {area:,.0f} m²)",
    "Buildings": "Gebäude",
    "Buildings kept free": "Freigehaltene Gebäude",
    "Buildings: {official} from the official cadastre (red), {osm} more from OpenStreetMap. Compare them with the aerial image: draw missing buildings, sheds, trees, pipes or a driveway with the polygon or rectangle tool (left of the map); they are kept free. Remove buildings that no longer exist from the list below the map.":
        "Gebäude: {official} aus dem amtlichen Kataster (rot), {osm} weitere aus OpenStreetMap. Vergleichen Sie sie "
        "mit dem Luftbild: Zeichnen Sie fehlende Gebäude, Schuppen, Bäume, Leitungen oder eine Zufahrt mit dem "
        "Polygon- oder Rechteckwerkzeug (links an der Karte) ein; diese Flächen bleiben frei. Entfernen Sie nicht "
        "mehr vorhandene Gebäude aus der Liste unter der Karte.",
    "Bundesland": "Bundesland",
    "COP at the coldest fluid": "COP beim kältesten Fluid",
    "COP heating": "COP Heizen",
    "Cadastre buildings: {error}": "Gebäude aus dem Kataster: {error}",
    "Calculate the comparison": "Vergleich berechnen",
    "Calculate with the layers (layered ground)": "Mit den Schichten rechnen (geschichteter Untergrund)",
    "Calculated with the finite line source (uniform heat flow per metre, with the mirror image at the surface), which is also the basis of the g-function.":
        "Berechnet mit der finiten Linienquelle (gleichmäßiger Wärmestrom je Meter, mit Spiegelquelle an der "
        "Oberfläche), die auch der g-Funktion zugrunde liegt.",
    "Calculating the ground temperature around the field...": "Untergrundtemperatur um das Sondenfeld wird berechnet …",
    "Case": "Fall",
    "Change %": "Änderung %",
    "Change K": "Änderung K",
    "Change [K]": "Änderung [K]",
    "Change in borehole length [%]": "Änderung der Sondenlänge [%]",
    "Change, higher [%]": "Änderung, höher [%]",
    "Change, lower [%]": "Änderung, niedriger [%]",
    "Chart": "Diagramm",
    "Check against the limits": "Prüfung gegen die Grenzwerte",
    "Check of a given length": "Prüfung einer vorgegebenen Länge",
    "Check the distances with the local water authority (Untere Wasserbehörde) before planning:":
        "Stimmen Sie die Abstände vor der Planung mit der Unteren Wasserbehörde ab:",
    "Check with the Untere Wasserbehörde: districts may ask for more.":
        "Mit der Unteren Wasserbehörde abstimmen: Kreise können größere Abstände fordern.",
    "Choose a location (or upload logs) first.": "Wählen Sie zuerst einen Standort (oder laden Sie Schichtenverzeichnisse hoch).",
    "Choose the Bundesland above to search by Flurstück number.":
        "Wählen Sie oben das Bundesland, um nach der Flurstücksnummer zu suchen.",
    "Choosing a rock fills in its VDI 4640 values.": "Die Wahl eines Gesteins übernimmt dessen Werte nach VDI 4640.",
    "Clear the comparison": "Vergleich löschen",
    "Clear the layers": "Schichten löschen",
    "Clicked at {lat:.6f} N, {lon:.6f} E": "Angeklickt bei {lat:.6f} N, {lon:.6f} O",
    "Client": "Auftraggeber",
    "Coldest fluid entering the borefield": "Kältestes Fluid beim Eintritt ins Sondenfeld",
    "Columns: borehole, x, y (or lon, lat), top, bottom, description (words or SEP 3 code such as 'mS,g' or 'Tst'), groundwater. Rows without coordinates are a log on the site itself.":
        "Spalten: borehole, x, y (oder lon, lat), top, bottom, description (Text oder SEP-3-Kürzel wie 'mS,g' oder "
        "'Tst'), groundwater. Zeilen ohne Koordinaten gelten als Bohrung auf dem Grundstück selbst.",
    "Company": "Firma",
    "Compare variants": "Varianten vergleichen",
    "Compare: the same design with one average value": "Vergleich: dieselbe Auslegung mit einem Mittelwert",
    "Conclusion": "Fazit",
    "Confidence": "Belastbarkeit",
    "Continue the deepest layer": "Tiefste Schicht fortsetzen",
    "Cooling [kW]": "Kühlen [kW]",
    "Cooling covered by the ground": "Vom Untergrund gedeckte Kühlung",
    "Coordinate system of the table": "Koordinatensystem der Tabelle",
    "Coordinates": "Koordinaten",
    "Coordinates: ETRS89 / UTM zone 32N (EPSG:{epsg}).": "Koordinaten: ETRS89 / UTM Zone 32N (EPSG:{epsg}).",
    "Copies the layers into the layer table and calculates with them (and fills in the averages too).":
        "Übernimmt die Schichten in die Schichtentabelle und rechnet mit ihnen (und trägt auch die Mittelwerte ein).",
    "Could not find out the state of this location (the address service did not answer), so no borehole database was asked.":
        "Das Bundesland dieses Standorts war nicht zu ermitteln (der Adressdienst hat nicht geantwortet), daher wurde "
        "keine Bohrungsdatenbank abgefragt.",
    "Could not read the shapefile: {error}": "Das Shapefile konnte nicht gelesen werden: {error}",
    "Could not read this file: {error}": "Diese Datei konnte nicht gelesen werden: {error}",
    "Could not read {name}: {error}": "{name} konnte nicht gelesen werden: {error}",
    "Could not tell which state this is. Choose the Bundesland above.":
        "Das Bundesland ist nicht erkennbar. Wählen Sie es oben aus.",
    "Daily maximum °C": "Tagesmaximum °C",
    "Daily minimum °C": "Tagesminimum °C",
    "Daily peak demand": "Tägliche Spitzenlast",
    "Daily peak demand [kW]": "Tägliche Spitzenlast [kW]",
    "Daily range": "Tagesspanne",
    "Daily range of the hourly average fluid temperature. Dashed: your limits.":
        "Tagesspanne der stündlichen mittleren Fluidtemperatur. Gestrichelt: Ihre Grenzwerte.",
    "Dashed: the calculated length. Where the curve rises, a deeper borehole reaches better ground.":
        "Gestrichelt: die berechnete Länge. Wo die Kurve steigt, erreicht eine tiefere Sonde besser leitenden Untergrund.",
    "Date": "Datum",
    "Day": "Tag",
    "Day of the last year": "Tag des letzten Jahres",
    "Day of the year": "Tag des Jahres",
    "Demand [kW]": "Bedarf [kW]",
    "Depth [m]": "Tiefe [m]",
    "Depth below ground [m]": "Tiefe unter Gelände [m]",
    "Design": "Auslegung",
    "Detect automatically": "Automatisch erkennen",
    "Detect from the location": "Aus dem Standort ermitteln",
    "Detected from the address or the map point; choose it yourself if that fails.":
        "Aus der Adresse oder dem Kartenpunkt ermittelt; wählen Sie es selbst, falls das nicht gelingt.",
    "Distance [m]": "Abstand [m]",
    "Distance between boreholes [m]": "Sondenabstand [m]",
    "Distance between boreholes: {d:g} m": "Sondenabstand: {d:g} m",
    "Distance to areas you draw [m]": "Abstand zu gezeichneten Flächen [m]",
    "Distance to buildings [m]": "Abstand zu Gebäuden [m]",
    "Distance to buildings: {d:g} m": "Abstand zu Gebäuden: {d:g} m",
    "Distance to the parcel border [m]": "Abstand zur Grundstücksgrenze [m]",
    "Distance to the parcel border: {d:g} m": "Abstand zur Grundstücksgrenze: {d:g} m",
    "Distances: parcel border {border:g} m, buildings {buildings:g} m,\nboreholes {spacing:g} m apart":
        "Abstände: Grundstücksgrenze {border:g} m, Gebäude {buildings:g} m,\nSondenabstand {spacing:g} m",
    "Download Excel (.xlsx)": "Excel herunterladen (.xlsx)",
    "Download PDF": "PDF herunterladen",
    "Download template": "Vorlage herunterladen",
    "Download the optimised load, first year hourly (CSV)": "Optimierte Last herunterladen, erstes Jahr stündlich (CSV)",
    "Download zip": "ZIP herunterladen",
    "Draw the parcel with the polygon tool (left of the map), following the parcel lines. In Bayern, choose the Bundesland above to see the parcel lines of the cadastre map.":
        "Zeichnen Sie das Flurstück mit dem Polygonwerkzeug (links an der Karte) entlang der Flurstücksgrenzen. "
        "In Bayern wählen Sie oben das Bundesland, um die Grenzen der Flurkarte zu sehen.",
    "Drawn parcel": "Gezeichnetes Flurstück",
    "EER cooling": "EER Kühlen",
    "ETRS89 / UTM 32N (EPSG:25832)": "ETRS89 / UTM 32N (EPSG:25832)",
    "ETRS89 / UTM 33N (EPSG:25833)": "ETRS89 / UTM 33N (EPSG:25833)",
    "Each cell is one hour of the last year. Blue is cold, red is warm.":
        "Jede Zelle ist eine Stunde des letzten Jahres. Blau ist kalt, Rot ist warm.",
    "Each layer keeps its own conductivity and heat capacity; GHEtool averages them over the borehole length while it sizes, so a deeper borehole reaches other layers. Off: the single values above are used.":
        "Jede Schicht behält ihre eigene Wärmeleitfähigkeit und Wärmekapazität; GHEtool mittelt sie bei der "
        "Auslegung über die Sondenlänge, sodass eine tiefere Sonde andere Schichten erreicht. Aus: Es gelten die "
        "Einzelwerte oben.",
    "Each load sorted from its highest hour to its lowest. Solid: building demand. Dashed: what the ground sees after the heat pump. The area under a curve is the energy per year.":
        "Jede Last nach Stunden absteigend sortiert. Durchgezogen: Gebäudebedarf. Gestrichelt: Last am Untergrund "
        "nach der Wärmepumpe. Die Fläche unter einer Kurve ist die Jahresenergie.",
    "Easting [m] (ETRS89 / UTM 32N)": "Rechtswert [m] (ETRS89 / UTM 32N)",
    "Electricity [MWh/yr]": "Strom [MWh/a]",
    "Electricity per year": "Strombedarf pro Jahr",
    "Energy": "Energie",
    "Energy [kWh]": "Energie [kWh]",
    "Energy taken from (heating) and put into (cooling) the ground, after heat pump efficiency.":
        "Dem Untergrund entzogene (Heizen) und eingetragene (Kühlen) Energie, nach Wärmepumpeneffizienz.",
    "Excel workbook, PDF report and the project file, for archiving a design.":
        "Excel-Arbeitsmappe, PDF-Bericht und Projektdatei, zum Archivieren einer Auslegung.",
    "Excluded area": "Ausschlussfläche",
    "Excluded areas": "Ausschlussflächen",
    "Excluded areas you drew": "Gezeichnete Ausschlussflächen",
    "Expected {hours} hourly values (one year), found {n}.": "Erwartet: {hours} Stundenwerte (ein Jahr), gefunden: {n}.",
    "Export": "Export",
    "External cooling [MWh]": "Zusatzkühlung [MWh]",
    "External heating [MWh]": "Zusatzheizung [MWh]",
    "Extra distance around the areas drawn on the map.": "Zusätzlicher Abstand um die in der Karte gezeichneten Flächen.",
    "Extracted from the ground": "Dem Untergrund entzogen",
    "Extraction": "Entzug",
    "Extraction (from the ground)": "Entzug (aus dem Untergrund)",
    "Extraction (heating)": "Entzug (Heizen)",
    "Extraction [MWh]": "Entzug [MWh]",
    "Fill in the averages": "Mittelwerte übernehmen",
    "Find": "Suchen",
    "Find layouts": "Anordnungen suchen",
    "Find the parcel by": "Flurstück finden über",
    "Flow rate per borehole [l/s]": "Durchfluss je Sonde [l/s]",
    "Fluid going down": "Fluid abwärts",
    "Fluid going down (inner pipe)": "Fluid abwärts (Innenrohr)",
    "Fluid going up": "Fluid aufwärts",
    "Fluid going up (annulus)": "Fluid aufwärts (Ringraum)",
    "Fluid maximum °C": "Fluid Maximum °C",
    "Fluid minimum °C": "Fluid Minimum °C",
    "Fluid temperatures over the simulation period": "Fluidtemperaturen über den Simulationszeitraum",
    "Flur": "Flur",
    "Flurstück (Zähler)": "Flurstück (Zähler)",
    "From [m]": "Von [m]",
    "Full report": "Vollständiger Bericht",
    "Full report: cover page, results, inputs, drawings and all charts. One-page summary: the design, key results and the temperature chart. Fill in the report settings below first.":
        "Vollständiger Bericht: Deckblatt, Ergebnisse, Eingaben, Zeichnungen und alle Diagramme. Einseitige "
        "Zusammenfassung: Auslegung, wichtigste Ergebnisse und Temperaturdiagramm. Füllen Sie zuerst die "
        "Berichtsangaben unten aus.",
    "Full-load hours, heating": "Volllaststunden Heizen",
    "Full-load hours, heating and hot water": "Volllaststunden Heizen und Trinkwarmwasser",
    "Further analysis": "Weitere Auswertungen",
    "GIS project (.zip)": "GIS-Projekt (.zip)",
    "GW ▽": "GW ▽",
    "Gauß-Krüger zone 2 (EPSG:31466)": "Gauß-Krüger Zone 2 (EPSG:31466)",
    "Gauß-Krüger zone 3 (EPSG:31467)": "Gauß-Krüger Zone 3 (EPSG:31467)",
    "Gauß-Krüger zone 4 (EPSG:31468)": "Gauß-Krüger Zone 4 (EPSG:31468)",
    "Gauß-Krüger zone 5 (EPSG:31469)": "Gauß-Krüger Zone 5 (EPSG:31469)",
    "Gemarkung number": "Gemarkungsnummer",
    "Geological map (BGR GÜK250) at the site: {units}": "Geologische Karte (BGR GÜK250) am Standort: {units}",
    "Geological map: {error}": "Geologische Karte: {error}",
    "Geologischer Dienst NRW, borehole database (BoreholeML)": "Geologischer Dienst NRW, Bohrungsdatenbank (BoreholeML)",
    "Go": "Los",
    "Go to an address": "Zu einer Adresse springen",
    "Grid": "Raster",
    "Ground conductivity ±15 %": "Wärmeleitfähigkeit des Untergrunds ±15 %",
    "Ground cooling": "Kühlen über den Untergrund",
    "Ground cooling [MWh]": "Untergrund Kühlen [MWh]",
    "Ground energy": "Energie am Untergrund",
    "Ground energy [MWh]": "Energie am Untergrund [MWh]",
    "Ground energy balance (yearly imbalance {x:+,.0f} MWh)": "Energiebilanz des Untergrunds (jährliches Ungleichgewicht {x:+,.0f} MWh)",
    "Ground energy per year": "Energie am Untergrund pro Jahr",
    "Ground extraction": "Entzug aus dem Untergrund",
    "Ground heating": "Heizen über den Untergrund",
    "Ground heating [MWh]": "Untergrund Heizen [MWh]",
    "Ground injection": "Eintrag in den Untergrund",
    "Ground layers (not used: switch on the layered calculation)":
        "Schichtenfolge (nicht verwendet: geschichtete Berechnung einschalten)",
    "Ground temperature change at {depth:.0f} m depth after {years} years":
        "Änderung der Untergrundtemperatur in {depth:.0f} m Tiefe nach {years} Jahren",
    "Ground temperature ±1 K": "Untergrundtemperatur ±1 K",
    "Ground °C": "Untergrund °C",
    "Groundwater depth [m]": "Grundwasserflurabstand [m]",
    "Groundwater table from the logs: about {d:.1f} m below ground.":
        "Grundwasserspiegel laut Schichtenverzeichnissen: etwa {d:.1f} m unter Gelände.",
    "Group": "Gruppe",
    "Grout conductivity ±25 %": "Wärmeleitfähigkeit der Verfüllung ±25 %",
    "HLNUG Leitfaden Erdwärmenutzung, 6th edition 2019: 5 m to the border (up to 30 kW).":
        "HLNUG Leitfaden Erdwärmenutzung, 6. Auflage 2019: 5 m zur Grundstücksgrenze (bis 30 kW).",
    "Handlungsempfehlung Erdwärmenutzung in Brandenburg (2023, updated 2025): 3 m to the border.":
        "Handlungsempfehlung Erdwärmenutzung in Brandenburg (2023, aktualisiert 2025): 3 m zur Grundstücksgrenze.",
    "Heat map": "Wärmekarte",
    "Heat pump": "Wärmepumpe",
    "Heat pump electricity per year": "Strombedarf der Wärmepumpe pro Jahr",
    "Heating": "Heizen",
    "Heating [kW]": "Heizen [kW]",
    "Heating covered by the ground": "Vom Untergrund gedeckte Heizung",
    "Higher input": "Höherer Eingabewert",
    "Highest": "Höchste",
    "Highest [°C]": "Höchste [°C]",
    "Highest average fluid temperature": "Höchste mittlere Fluidtemperatur",
    "Highest fluid temperature": "Höchste Fluidtemperatur",
    "Highest temp. [°C]": "Höchste Temp. [°C]",
    "Hot water": "Trinkwarmwasser",
    "Hour": "Stunde",
    "Hour of the day": "Stunde des Tages",
    "Hourly": "Stündlich",
    "Hourly demand file: 8760 rows, column 1 heating [kW], column 2 cooling [kW]":
        "Datei mit Stundenbedarf: 8760 Zeilen, Spalte 1 Heizen [kW], Spalte 2 Kühlen [kW]",
    "Hourly fluid temperature (daily range)": "Stündliche Fluidtemperatur (Tagesspanne)",
    "Hourly temperatures": "Stündliche Temperaturen",
    "Hourly temperatures (CSV)": "Stündliche Temperaturen (CSV)",
    "Hourly temperatures in the last year (band: fluid, line: borehole wall)":
        "Stündliche Temperaturen im letzten Jahr (Band: Fluid, Linie: Bohrlochwand)",
    "Hours": "Stunden",
    "Hours per year": "Stunden pro Jahr",
    "How many grid rotations and shifts are tried for the largest count.":
        "Wie viele Drehungen und Verschiebungen des Rasters für die größte Anzahl ausprobiert werden.",
    "How the yearly imbalance warms (red) or cools (blue) the ground around the field at the end of the simulation, halfway down the boreholes. Each dot is a borehole. Boreholes in the middle change most because their neighbours add up. The seasonal swing on top of this averages out over a year and is left out.":
        "Wie das jährliche Ungleichgewicht den Untergrund um das Feld am Ende der Simulation in halber Sondentiefe "
        "erwärmt (rot) oder abkühlt (blau). Jeder Punkt ist eine Sonde. Sonden in der Mitte ändern sich am "
        "stärksten, weil sich die Nachbarn aufsummieren. Der jahreszeitliche Wechsel darüber mittelt sich über ein "
        "Jahr aus und ist nicht dargestellt.",
    "Hydraulics": "Hydraulik",
    "If the lowest temperature keeps falling (or the highest keeps rising) every year, the ground is out of balance. A longer simulation period shows whether it levels off.":
        "Sinkt die niedrigste Temperatur (oder steigt die höchste) Jahr für Jahr weiter, ist der Untergrund nicht im "
        "Gleichgewicht. Ein längerer Simulationszeitraum zeigt, ob sie sich einpendelt.",
    "Imbalance": "Ungleichgewicht",
    "Include the ground temperature map": "Karte der Untergrundtemperatur einfügen",
    "Injected into the ground": "In den Untergrund eingetragen",
    "Injection": "Eintrag",
    "Injection (cooling)": "Eintrag (Kühlen)",
    "Injection (into the ground)": "Eintrag (in den Untergrund)",
    "Injection [MWh]": "Eintrag [MWh]",
    "Input": "Eingabe",
    "Input borehole positions": "Eingegebene Sondenstandorte",
    "Input ground layers": "Eingegebene Schichtenfolge",
    "Input higher [m]": "Eingabe höher [m]",
    "Input hourly demand": "Eingegebener Stundenbedarf",
    "Input lower [m]": "Eingabe niedriger [m]",
    "Input {section}": "Eingabe {section}",
    "Inputs": "Eingaben",
    "Into borefield (peak extraction)": "Eintritt ins Sondenfeld (Spitzenentzug)",
    "Into borefield (peak injection)": "Eintritt ins Sondenfeld (Spitzeneintrag)",
    "Into the borefield = supply from the heat pump; out of the borefield = return to the heat pump.":
        "Eintritt ins Sondenfeld = Vorlauf von der Wärmepumpe; Austritt aus dem Sondenfeld = Rücklauf zur Wärmepumpe.",
    "Introduction": "Einleitung",
    "Item": "Größe",
    "Keep this result": "Dieses Ergebnis behalten",
    "Keep this result, change the inputs, size again and keep that one too. The comparison stays until you close the page and is part of the Excel export.":
        "Behalten Sie dieses Ergebnis, ändern Sie die Eingaben, legen Sie neu aus und behalten Sie auch dieses. Der "
        "Vergleich bleibt bis zum Schließen der Seite erhalten und ist Teil des Excel-Exports.",
    "Keeps the borefield as designed and works out how much of the hourly building demand it can take within the temperature limits. The rest comes from a backup boiler, gas or electric, or a chiller (a hybrid system). This answers: how far does a smaller or cheaper field get me?":
        "Behält das Sondenfeld wie ausgelegt bei und ermittelt, wie viel des stündlichen Gebäudebedarfs es innerhalb "
        "der Temperaturgrenzen decken kann. Den Rest liefert ein Zusatzkessel (Gas oder elektrisch) oder eine "
        "Kältemaschine (bivalentes System). Das beantwortet: Wie weit komme ich mit einem kleineren oder günstigeren "
        "Feld?",
    "L-shape": "L-Form",
    "LANUV-Arbeitsblatt 39 (2024), section 3.1.5: 3 m to the border.":
        "LANUV-Arbeitsblatt 39 (2024), Abschnitt 3.1.5: 3 m zur Grundstücksgrenze.",
    "LBEG GeoBerichte 24 (Niedersachsen): 5 m to the border; less only with the neighbour's consent.":
        "LBEG GeoBerichte 24 (Niedersachsen): 5 m zur Grundstücksgrenze; weniger nur mit Zustimmung des Nachbarn.",
    "LQS Bohrungen/Erdwärmesonden Sachsen-Anhalt 2016, section 2.1.3: 5 m to the border.":
        "LQS Bohrungen/Erdwärmesonden Sachsen-Anhalt 2016, Abschnitt 2.1.3: 5 m zur Grundstücksgrenze.",
    "LQS EWS Baden-Württemberg 2018, section 2.1.3: half the borehole spacing of VDI 4640, typically 3 m.":
        "LQS EWS Baden-Württemberg 2018, Abschnitt 2.1.3: halber Sondenabstand nach VDI 4640, meist 3 m.",
    "Largest change": "Größte Änderung",
    "Last year": "Letztes Jahr",
    "Last year of the simulation": "Letztes Jahr der Simulation",
    "Latitude [°]": "Breitengrad [°]",
    "Layer": "Schicht",
    "Layer table: edit the depths and rocks, add or delete rows. Tops follow from the row above.":
        "Schichtentabelle: Tiefen und Gesteine bearbeiten, Zeilen hinzufügen oder löschen. Die Oberkante ergibt sich "
        "aus der Zeile darüber.",
    "Layer {n} starts at {top:g} m, but layer {prev} ends at {bottom:g} m.":
        "Schicht {n} beginnt bei {top:g} m, Schicht {prev} endet aber bei {bottom:g} m.",
    "Layer {n}: a heat capacity of {c:g} MJ/(m³·K) is outside 0.5 to 5.":
        "Schicht {n}: Eine Wärmekapazität von {c:g} MJ/(m³·K) liegt außerhalb von 0,5 bis 5.",
    "Layer {n}: a thermal conductivity of {k:g} W/(m·K) is outside 0.1 to 10.":
        "Schicht {n}: Eine Wärmeleitfähigkeit von {k:g} W/(m·K) liegt außerhalb von 0,1 bis 10.",
    "Layer {n}: every layer needs a depth, a conductivity and a heat capacity.":
        "Schicht {n}: Jede Schicht braucht eine Tiefe, eine Wärmeleitfähigkeit und eine Wärmekapazität.",
    "Layer {n}: the bottom ({bottom:g} m) has to be below the top ({top:g} m).":
        "Schicht {n}: Die Unterkante ({bottom:g} m) muss unter der Oberkante ({top:g} m) liegen.",
    "Layered ground is switched on, but there are no layers.":
        "Der geschichtete Untergrund ist eingeschaltet, es gibt aber keine Schichten.",
    "Layers": "Schichten",
    "Layers reached": "Erreichte Schichten",
    "Layout": "Anordnung",
    "Layout optimisation": "Feldoptimierung",
    "Leave empty in states without Flur (e.g. Bayern).": "In Ländern ohne Flur (z. B. Bayern) leer lassen.",
    "Leitfaden Erdwärmenutzung Hamburg 2021, section 5.7: 5 m to the border.":
        "Leitfaden Erdwärmenutzung Hamburg 2021, Abschnitt 5.7: 5 m zur Grundstücksgrenze.",
    "Leitfaden Mecklenburg-Vorpommern (2006): 5 m to the border.":
        "Leitfaden Mecklenburg-Vorpommern (2006): 5 m zur Grundstücksgrenze.",
    "Leitfaden Schleswig-Holstein: 6 m to the border (5 m for probes shallower than 50 m); a revised Leitfaden is in preparation.":
        "Leitfaden Schleswig-Holstein: 6 m zur Grundstücksgrenze (5 m bei Sonden unter 50 m Tiefe); ein "
        "überarbeiteter Leitfaden ist in Vorbereitung.",
    "Leitfaden Thüringen (2007): 5 m to the border.": "Leitfaden Thüringen (2007): 5 m zur Grundstücksgrenze.",
    "Length determined by": "Länge bestimmt durch",
    "Length each [m]": "Länge je Sonde [m]",
    "Length in the layer [m]": "Länge in der Schicht [m]",
    "Length in the layer × its conductivity, as a share of the whole borehole. Layers that conduct well carry more of the heat, so they are worth reaching.":
        "Länge in der Schicht × deren Wärmeleitfähigkeit, als Anteil an der ganzen Sonde. Gut leitende Schichten "
        "übertragen mehr Wärme; es lohnt sich, sie zu erreichen.",
    "Length m": "Länge m",
    "Length, input higher [m]": "Länge, Eingabe höher [m]",
    "Length, input lower [m]": "Länge, Eingabe niedriger [m]",
    "LfU Merkblatt 3.7/2 (Bayern): 3 m recommended (LAWA: 5 m).": "LfU-Merkblatt 3.7/2 (Bayern): 3 m empfohlen (LAWA: 5 m).",
    "Load": "Last",
    "Load a parcel to continue.": "Laden Sie ein Flurstück, um fortzufahren.",
    "Load duration curve": "Jahresdauerlinie",
    "Load duration curve (first year)": "Jahresdauerlinie (erstes Jahr)",
    "Load optimisation": "Lastoptimierung",
    "Load optimisation, monthly": "Lastoptimierung, monatlich",
    "Load optimisation, yearly": "Lastoptimierung, jährlich",
    "Load optimisation: heating {heat:.0%} and cooling {cool:.0%} covered by the ground":
        "Lastoptimierung: Heizen zu {heat:.0%} und Kühlen zu {cool:.0%} vom Untergrund gedeckt",
    "Load the parcel at this address": "Flurstück an dieser Adresse laden",
    "Load the parcel at this point": "Flurstück an diesem Punkt laden",
    "Loading buildings from the cadastre and OpenStreetMap...": "Gebäude aus Kataster und OpenStreetMap werden geladen …",
    "Loading the parcel from the cadastre of {state}...": "Flurstück wird aus dem Kataster von {state} geladen …",
    "Location": "Standort",
    "Logo (PNG or JPEG)": "Logo (PNG oder JPEG)",
    "Logs further away are not used. Nearer logs weigh more (1 / distance²).":
        "Weiter entfernte Bohrungen werden nicht verwendet. Nähere Bohrungen zählen stärker (1 / Abstand²).",
    "Long-term drift": "Langzeitentwicklung",
    "Longitude [°]": "Längengrad [°]",
    "Looks for logged boreholes around the site and interpolates their layers (nearer logs weigh more), then gives every layer its VDI 4640 conductivity and heat capacity. It is a first estimate for planning; a thermal response test measures the real value.":
        "Sucht Bohrungen mit Schichtenverzeichnis um den Standort und interpoliert deren Schichten (nähere zählen "
        "stärker), dann erhält jede Schicht Wärmeleitfähigkeit und Wärmekapazität nach VDI 4640. Das ist eine erste "
        "Abschätzung für die Planung; ein Thermal Response Test misst den tatsächlichen Wert.",
    "Loose sediments above the groundwater table conduct heat worse (VDI 4640). Empty: from the logs, if they have it, else all layers count as water saturated.":
        "Lockergestein über dem Grundwasserspiegel leitet Wärme schlechter (VDI 4640). Leer: aus den "
        "Schichtenverzeichnissen, falls angegeben, sonst gelten alle Schichten als wassergesättigt.",
    "Lower input": "Niedrigerer Eingabewert",
    "Lowest": "Niedrigste",
    "Lowest [°C]": "Niedrigste [°C]",
    "Lowest and highest average fluid temperature per year": "Niedrigste und höchste mittlere Fluidtemperatur pro Jahr",
    "Lowest and highest temperature per year": "Niedrigste und höchste Temperatur pro Jahr",
    "Lowest average fluid temperature": "Niedrigste mittlere Fluidtemperatur",
    "Lowest fluid temperature": "Niedrigste Fluidtemperatur",
    "Lowest temp. [°C]": "Niedrigste Temp. [°C]",
    "Matching places": "Passende Orte",
    "Maximum borehole length [m]": "Maximale Sondenlänge [m]",
    "Maximum number of boreholes (0 = as many as fit)": "Maximale Sondenanzahl (0 = so viele wie passen)",
    "Maximum spacing [m]": "Maximaler Abstand [m]",
    "Minimum borehole length [m]": "Minimale Sondenlänge [m]",
    "Minimum spacing [m]": "Minimaler Abstand [m]",
    "Month": "Monat",
    "Monthly demand": "Monatlicher Bedarf",
    "Monthly ground energy balance": "Monatliche Energiebilanz des Untergrunds",
    "Monthly ground load": "Monatliche Last am Untergrund",
    "Monthly temperatures": "Monatliche Temperaturen",
    "Monthly temperatures (CSV)": "Monatliche Temperaturen (CSV)",
    "Most boreholes used": "Meiste Sonden genutzt",
    "Most geothermal energy": "Meiste geothermische Energie",
    "Most geothermal power": "Höchste geothermische Leistung",
    "Name": "Name",
    "Name for this result": "Name für dieses Ergebnis",
    "Nenner (optional)": "Nenner (optional)",
    "Net heat flow into the ground": "Netto-Wärmestrom in den Untergrund",
    "No .prj file found, so the coordinates are assumed to be in metres.":
        "Keine .prj-Datei gefunden, daher werden die Koordinaten in Metern angenommen.",
    "No Flurstück with this number was found. Check the Gemarkung number, or use the address or the map.":
        "Kein Flurstück mit dieser Nummer gefunden. Prüfen Sie die Gemarkungsnummer oder nutzen Sie die Adresse "
        "bzw. die Karte.",
    "No address found.": "Keine Adresse gefunden.",
    "No address found. Try without the house number, or click the parcel on the map.":
        "Keine Adresse gefunden. Versuchen Sie es ohne Hausnummer oder klicken Sie das Flurstück in der Karte an.",
    "No borehole fits with these distances.": "Mit diesen Abständen passt keine Sonde.",
    "No borehole logs and no geological map data: enter the layers yourself.":
        "Keine Schichtenverzeichnisse und keine Daten der geologischen Karte: Geben Sie die Schichten selbst ein.",
    "No borehole logs within the search radius. The rock of the geological map at the surface is used for the whole depth: please check it, e.g. against a log from the state's borehole portal.":
        "Keine Schichtenverzeichnisse im Suchradius. Das Gestein der geologischen Karte an der Oberfläche wird für "
        "die ganze Tiefe verwendet: Bitte prüfen, z. B. anhand einer Bohrung aus dem Bohrungsportal des Landes.",
    "No layers found in the table.": "Keine Schichten in der Tabelle gefunden.",
    "No layout found: {error}": "Keine Anordnung gefunden: {error}",
    "No published value found for the Saarland; 5 m is the conservative LAWA value. VDI 4640 Blatt 2 is commonly cited with 3 m to the border; LAWA recommends 5 m.":
        "Für das Saarland wurde kein veröffentlichter Wert gefunden; 5 m ist der vorsichtige LAWA-Wert. VDI 4640 "
        "Blatt 2 wird meist mit 3 m zur Grundstücksgrenze zitiert; die LAWA empfiehlt 5 m.",
    "No result yet. Check the inputs in the steps above, then press **{action}**.":
        "Noch kein Ergebnis. Prüfen Sie die Eingaben in den Schritten oben und klicken Sie dann auf **{action}**.",
    "No state known; 3 m is common.": "Kein Bundesland bekannt; 3 m sind üblich.",
    "Northing [m]": "Hochwert [m]",
    "Not recognised (set to Unknown, k = 2.0 W/(m·K)): {which}":
        "Nicht erkannt (als Unbekannt gesetzt, λ = 2,0 W/(m·K)): {which}",
    "Note": "Hinweis",
    "Number of boreholes": "Anzahl der Sonden",
    "Number of trials (more finds better fields, but takes longer)":
        "Anzahl der Versuche (mehr findet bessere Felder, dauert aber länger)",
    "One point per borehole, ETRS89 / UTM 32N. Can be uploaded under Borefield.":
        "Ein Punkt je Sonde, ETRS89 / UTM 32N. Kann unter Sondenfeld hochgeladen werden.",
    "One-page summary": "Einseitige Zusammenfassung",
    "Open site_plan.qgs in QGIS, or load the .shp files in any GIS program.":
        "Öffnen Sie site_plan.qgs in QGIS oder laden Sie die .shp-Dateien in ein beliebiges GIS-Programm.",
    "OpenStreetMap": "OpenStreetMap",
    "OpenStreetMap buildings could not be loaded: {error}": "Gebäude aus OpenStreetMap konnten nicht geladen werden: {error}",
    "Optimise for": "Optimieren auf",
    "Optimise the layout for a plot": "Anordnung für ein Grundstück optimieren",
    "Optimise the load": "Last optimieren",
    "Optimising the load split...": "Lastaufteilung wird optimiert …",
    "Optional. Find your parcel, check the buildings on the aerial image, set the distances, and get the largest number of boreholes that fit, as a shapefile for the irregular borefield.":
        "Optional. Flurstück finden, Gebäude auf dem Luftbild prüfen, Abstände festlegen und die größtmögliche "
        "Sondenanzahl als Shapefile für das unregelmäßige Sondenfeld erhalten.",
    "Out of borefield (peak extraction)": "Austritt aus dem Sondenfeld (Spitzenentzug)",
    "Out of borefield (peak injection)": "Austritt aus dem Sondenfeld (Spitzeneintrag)",
    "Over the years": "Über die Jahre",
    "Overview": "Übersicht",
    "Parcel": "Flurstück",
    "Parcel boundaries (cadastre map)": "Flurstücksgrenzen (Flurkarte)",
    "Parcel outline as GeoJSON, KML or zipped shapefile (any coordinate system with a .prj; GeoJSON and KML in degrees)":
        "Flurstücksumriss als GeoJSON, KML oder gezipptes Shapefile (beliebiges Koordinatensystem mit .prj; GeoJSON "
        "und KML in Grad)",
    "Pattern": "Muster",
    "Peak kW": "Spitze kW",
    "Peak power taken by the ground: heating {heat:,.0f} kW, cooling {cool:,.0f} kW (building side).":
        "Vom Untergrund übernommene Spitzenleistung: Heizen {heat:,.0f} kW, Kühlen {cool:,.0f} kW (gebäudeseitig).",
    "Placing boreholes...": "Sonden werden platziert …",
    "Plain tables for other tools.": "Einfache Tabellen für andere Programme.",
    "Plot length [m]": "Grundstückslänge [m]",
    "Plot width [m]": "Grundstücksbreite [m]",
    "Power [kW]": "Leistung [kW]",
    "Predict down to [m]": "Prognose bis [m]",
    "Predict the layers": "Schichten prognostizieren",
    "Predicted layers": "Prognostizierte Schichten",
    "Prepared by": "Erstellt von",
    "Pressure drop against flow rate": "Druckverlust über dem Durchfluss",
    "Pressure drop against flow rate (at the coldest fluid)": "Druckverlust über dem Durchfluss (beim kältesten Fluid)",
    "Pressure drop per borehole": "Druckverlust je Sonde",
    "Pressure drop per borehole [kPa]": "Druckverlust je Sonde [kPa]",
    "Preview map": "Übersichtskarte",
    "Preview map (.png)": "Übersichtskarte (.png)",
    "Project background, scope of the calculation...": "Projekthintergrund, Umfang der Berechnung …",
    "Pump energy = hydraulic power ÷ pump efficiency × operating hours, both set under Flow rate in step ②.":
        "Pumpenenergie = hydraulische Leistung ÷ Pumpenwirkungsgrad × Betriebsstunden, beides unter Durchfluss in "
        "Schritt ② festgelegt.",
    "Pump energy per year": "Pumpenenergie pro Jahr",
    "Pump power": "Pumpenleistung",
    "Puts the average conductivity and heat capacity into the fields above.":
        "Trägt die mittlere Wärmeleitfähigkeit und Wärmekapazität in die Felder oben ein.",
    "Rb [m·K/W]": "Rb [m·K/W]",
    "Read 8760 hours from {file}.": "8760 Stunden aus {file} gelesen.",
    "Read {n} borehole log(s) from your files.": "{n} Schichtenverzeichnis(se) aus Ihren Dateien gelesen.",
    "Read {n} boreholes from {files}.": "{n} Sonden aus {files} gelesen.",
    "Rectangle": "Rechteck",
    "Remove the {n} drawn area(s)": "Die {n} gezeichnete(n) Fläche(n) entfernen",
    "Report settings: type, title, company, client, logo, introduction and conclusion":
        "Berichtsangaben: Art, Titel, Firma, Auftraggeber, Logo, Einleitung und Fazit",
    "Report type": "Berichtsart",
    "Required borehole length": "Erforderliche Sondenlänge",
    "Results": "Ergebnisse",
    "Reynolds number": "Reynolds-Zahl",
    "Rock": "Gestein",
    "Rock below the logs": "Gestein unterhalb der Bohrungen",
    "Run the sensitivity check": "Sensitivitätsanalyse starten",
    "SEER": "SEER",
    "SGD Nord Leitfaden Erdwärmesonden 2017 and LGB Mindestanforderungen 2024: 3 m to the border.":
        "SGD Nord Leitfaden Erdwärmesonden 2017 und LGB Mindestanforderungen 2024: 3 m zur Grundstücksgrenze.",
    "SPF heating": "JAZ Heizen",
    "SPF heating [-]": "JAZ Heizen [-]",
    "Sachsen: 5 m to the border is a condition for a permit-free probe (e.g. Umweltamt Dresden 2024).":
        "Sachsen: 5 m zur Grundstücksgrenze sind Voraussetzung für eine erlaubnisfreie Sonde (z. B. Umweltamt Dresden 2024).",
    "Search": "Suchen",
    "Search effort": "Suchaufwand",
    "Search radius [m]": "Suchradius [m]",
    "Search the Flurstück": "Flurstück suchen",
    "Searches rectangular, L, U, box and staggered fields that fit in the plot and meet the temperature limits, and lists the ones with the least drilling. Each trial takes a few seconds.":
        "Sucht Rechteck-, L-, U-, Rahmen- und versetzte Felder, die auf das Grundstück passen und die "
        "Temperaturgrenzen einhalten, und listet die mit den wenigsten Bohrmetern auf. Jeder Versuch dauert einige "
        "Sekunden.",
    "Searching by Flurstück number is not available for {state}. Search the address or click the parcel on the map instead.":
        "Die Suche nach Flurstücksnummer ist für {state} nicht verfügbar. Suchen Sie stattdessen die Adresse oder "
        "klicken Sie das Flurstück in der Karte an.",
    "Searching the cadastre of {state}...": "Kataster von {state} wird durchsucht …",
    "Seasonal energy efficiency ratio (SEER), cooling": "Jahresarbeitszahl Kühlen (SEER)",
    "Seasonal performance factor (SPF), heating": "Jahresarbeitszahl (JAZ), Heizen",
    "Seasonal performance factor per year (falls as the ground cools)":
        "Jahresarbeitszahl pro Jahr (sinkt, wenn der Untergrund abkühlt)",
    "Section": "Bereich",
    "Sensitivity": "Sensitivität",
    "Sensitivity check: what the borehole length depends on": "Sensitivitätsanalyse: wovon die Sondenlänge abhängt",
    "Series": "Reihe",
    "Sets Borefield to an irregular field with these positions.":
        "Setzt das Sondenfeld auf ein unregelmäßiges Feld mit diesen Standorten.",
    "Several parcels match": "Mehrere Flurstücke passen",
    "Shapefile with one point per borehole (.zip, or .shp + .shx + .dbf + .prj)":
        "Shapefile mit einem Punkt je Sonde (.zip oder .shp + .shx + .dbf + .prj)",
    "Shapefiles of boreholes, parcel, buildings, drawn areas and allowed area, a QGIS project (site_plan.qgs) with the aerial image, the preview map and a read-me.":
        "Shapefiles der Sonden, des Flurstücks, der Gebäude, der gezeichneten und der zulässigen Fläche, ein "
        "QGIS-Projekt (site_plan.qgs) mit Luftbild, die Übersichtskarte und eine Liesmich-Datei.",
    "Share": "Anteil",
    "Share of the heat exchange": "Anteil am Wärmeaustausch",
    "Showing an example office profile until you upload your own.":
        "Bis Sie ein eigenes hochladen, wird ein Beispielprofil für ein Bürogebäude gezeigt.",
    "Sizes again with a single conductivity and heat capacity, the average over the borehole length found here. The difference shows how much the layering matters.":
        "Legt erneut mit einer einzigen Wärmeleitfähigkeit und Wärmekapazität aus, dem hier ermittelten Mittelwert "
        "über die Sondenlänge. Der Unterschied zeigt, wie stark die Schichtung ins Gewicht fällt.",
    "Sizes the field again with one input changed at a time (monthly sizing for speed). The longest bars are the inputs worth measuring carefully, e.g. with a thermal response test.":
        "Legt das Feld erneut aus und ändert dabei jeweils eine Eingabe (monatliche Auslegung, damit es schnell "
        "geht). Die längsten Balken zeigen die Eingaben, die sorgfältig gemessen werden sollten, z. B. mit einem "
        "Thermal Response Test.",
    "Sizing the variations...": "Varianten werden ausgelegt …",
    "Sizing with the average values...": "Auslegung mit den Mittelwerten …",
    "Sizing, hourly (L4)": "Auslegung, stündlich (L4)",
    "Sizing, monthly (L2/L3)": "Auslegung, monatlich (L2/L3)",
    "Source": "Quelle",
    "Spacing [m]": "Abstand [m]",
    "Specific heat extraction": "Spezifische Entzugsleistung",
    "Specific heat injection": "Spezifische Eintragsleistung",
    "Spread [m]": "Spanne [m]",
    "Staggered": "Versetzt",
    "State": "Bundesland",
    "Street map": "Straßenkarte",
    "Subtitle": "Untertitel",
    "Summary": "Zusammenfassung",
    "Summary, inputs, monthly and yearly temperatures, ground energy, hourly results and your further analysis (included: {included}).":
        "Zusammenfassung, Eingaben, monatliche und jährliche Temperaturen, Energie am Untergrund, stündliche "
        "Ergebnisse und Ihre weiteren Auswertungen (enthalten: {included}).",
    "Switch on the layered calculation above to use the layers.":
        "Schalten Sie oben die geschichtete Berechnung ein, um die Schichten zu verwenden.",
    "Table": "Tabelle",
    "Table template": "Tabellenvorlage",
    "Temperature [°C]": "Temperatur [°C]",
    "Temperatures": "Temperaturen",
    "The .{ext} file is missing. A shapefile needs at least .shp, .shx and .dbf.":
        "Die .{ext}-Datei fehlt. Ein Shapefile braucht mindestens .shp, .shx und .dbf.",
    "The Berlin Merkblatt (2025) names no border value (10 m to neighbouring systems, 2 m to buildings); the earlier Leitfaden asked for 5 m.":
        "Das Berliner Merkblatt (2025) nennt keinen Grenzabstand (10 m zu Nachbaranlagen, 2 m zu Gebäuden); der "
        "frühere Leitfaden forderte 5 m.",
    "The Gemarkung number and the Flurstück number (Zähler) are needed.":
        "Gemarkungsnummer und Flurstücksnummer (Zähler) werden benötigt.",
    "The address search uses OpenStreetMap. The parcel under the address point is loaded; if it is the wrong one (e.g. the street), click the right parcel on the map instead.":
        "Die Adresssuche nutzt OpenStreetMap. Geladen wird das Flurstück unter dem Adresspunkt; ist es das falsche "
        "(z. B. die Straße), klicken Sie stattdessen das richtige Flurstück in der Karte an.",
    "The band spans the lowest and highest fluid temperature of every 3 hours, so all peaks are visible.":
        "Das Band reicht von der niedrigsten bis zur höchsten Fluidtemperatur je 3 Stunden, sodass alle Spitzen "
        "sichtbar sind.",
    "The borehole service reported an error: {error}": "Der Bohrungsdienst meldete einen Fehler: {error}",
    "The cadastre of {state} returned no parcel at this point.":
        "Das Kataster von {state} lieferte an diesem Punkt kein Flurstück.",
    "The coldest fluid ({t_in:.1f} °C) is close to the freezing point of the fluid ({freezing:.1f} °C). Use more antifreeze or a higher minimum temperature.":
        "Das kälteste Fluid ({t_in:.1f} °C) liegt nahe am Gefrierpunkt des Fluids ({freezing:.1f} °C). Erhöhen Sie "
        "den Frostschutzanteil oder die Mindesttemperatur.",
    "The comparison failed: {error}": "Der Vergleich ist fehlgeschlagen: {error}",
    "The coordinates were in degrees and have been converted to metres.":
        "Die Koordinaten waren in Grad und wurden in Meter umgerechnet.",
    "The coordinates were in feet and have been converted to metres.":
        "Die Koordinaten waren in Fuß und wurden in Meter umgerechnet.",
    "The current profile as CSV: one row per hour, heating then cooling in kW.":
        "Das aktuelle Profil als CSV: eine Zeile je Stunde, Heizen und Kühlen in kW.",
    "The deepest log nearby ends at {d:.0f} m. Below that, the last rock type is assumed to continue; set the rock below the logs if you know it.":
        "Die tiefste Bohrung in der Nähe endet bei {d:.0f} m. Darunter wird angenommen, dass sich das letzte Gestein "
        "fortsetzt; geben Sie das Gestein unterhalb der Bohrungen an, wenn Sie es kennen.",
    "The deepest log nearby ends at {d:.0f} m. Below that, {rock} is assumed.":
        "Die tiefste Bohrung in der Nähe endet bei {d:.0f} m. Darunter wird {rock} angenommen.",
    "The demand cannot be negative. Put heating and cooling in separate columns, both positive.":
        "Der Bedarf kann nicht negativ sein. Tragen Sie Heizen und Kühlen in getrennte Spalten ein, beide positiv.",
    "The dimensionless step response of the field. Its rise at large times shows how strongly the boreholes influence each other.":
        "Die dimensionslose Sprungantwort des Feldes. Ihr Anstieg bei langen Zeiten zeigt, wie stark sich die Sonden "
        "gegenseitig beeinflussen.",
    "The file contains no polygon.": "Die Datei enthält kein Polygon.",
    "The file has 8784 hours (leap year); the last day was dropped.":
        "Die Datei hat 8784 Stunden (Schaltjahr); der letzte Tag wurde verworfen.",
    "The file needs two columns with numbers: heating and cooling demand in kW.":
        "Die Datei braucht zwei Zahlenspalten: Heiz- und Kältebedarf in kW.",
    "The files are made when you click, so the page stays fast. The PDF report and the Excel workbook are in the language chosen in the sidebar.":
        "Die Dateien werden erst beim Klick erstellt, damit die Seite schnell bleibt. PDF-Bericht und "
        "Excel-Arbeitsmappe erscheinen in der in der Seitenleiste gewählten Sprache.",
    "The first layer has to start at the surface (0 m).": "Die erste Schicht muss an der Geländeoberfläche (0 m) beginnen.",
    "The flow is laminar (Re = {re:,.0f}). A higher flow rate, smaller pipes or less antifreeze lower the borehole resistance and can shorten the boreholes.":
        "Die Strömung ist laminar (Re = {re:,.0f}). Ein höherer Durchfluss, kleinere Rohre oder weniger "
        "Frostschutzmittel senken den Bohrlochwiderstand und können die Sonden verkürzen.",
    "The geological map service answered with an error: {error}":
        "Der Dienst der geologischen Karte antwortete mit einem Fehler: {error}",
    "The given borehole length does not keep the fluid within the temperature limits.":
        "Mit der vorgegebenen Sondenlänge bleibt das Fluid nicht innerhalb der Temperaturgrenzen.",
    "The given length of {length:.0f} m does not keep the fluid within the limits.":
        "Mit der vorgegebenen Länge von {length:.0f} m bleibt das Fluid nicht innerhalb der Grenzwerte.",
    "The given length of {length:.0f} m keeps the fluid within the limits.":
        "Mit der vorgegebenen Länge von {length:.0f} m bleibt das Fluid innerhalb der Grenzwerte.",
    "The heat pump efficiency is fixed (SCOP/SEER). Choose **Depends on the fluid temperature** under Heat pump efficiency in step ③ to see how the COP changes as the ground cools.":
        "Die Wärmepumpeneffizienz ist fest (SCOP/SEER). Wählen Sie unter Wärmepumpeneffizienz in Schritt ③ "
        "**Abhängig von der Fluidtemperatur**, um zu sehen, wie sich der COP bei Abkühlung des Untergrunds ändert.",
    "The inputs changed since this result was calculated. Press **{action}** to update it.":
        "Die Eingaben haben sich seit dieser Berechnung geändert. Klicken Sie auf **{action}**, um das Ergebnis zu "
        "aktualisieren.",
    "The nearest log ({name}) is {d:,.0f} m away, outside the search radius. Increase the radius to use it.":
        "Die nächste Bohrung ({name}) ist {d:,.0f} m entfernt, außerhalb des Suchradius. Vergrößern Sie den Radius, "
        "um sie zu verwenden.",
    "The number after the slash, e.g. 4 in 123/4.": "Die Zahl nach dem Schrägstrich, z. B. 4 in 123/4.",
    "The number before the slash, e.g. 123 in 123/4.": "Die Zahl vor dem Schrägstrich, z. B. 123 in 123/4.",
    "The optimisation failed: {error}": "Die Optimierung ist fehlgeschlagen: {error}",
    "The outline does not lie in Germany. Check the coordinate system (.prj).":
        "Der Umriss liegt nicht in Deutschland. Prüfen Sie das Koordinatensystem (.prj).",
    "The parcel from the site plan": "Das Flurstück aus dem Lageplan",
    "The service reported an error: {error}": "Der Dienst meldete einen Fehler: {error}",
    "The service sent an answer that could not be read.": "Der Dienst sendete eine Antwort, die nicht gelesen werden konnte.",
    "The service {host} answered with error {code}.": "Der Dienst {host} antwortete mit Fehler {code}.",
    "The service {host} did not answer ({error}).": "Der Dienst {host} hat nicht geantwortet ({error}).",
    "The shapefile contains no points.": "Das Shapefile enthält keine Punkte.",
    "The shapefile contains {kind} features. Each borehole must be a point.":
        "Das Shapefile enthält Objekte vom Typ {kind}. Jede Sonde muss ein Punkt sein.",
    "The table needs at least a column for the bottom depth (e.g. 'bottom' or 'bis') and one for the rock (e.g. 'description', 'petrographie' or 'code'). Download the template.":
        "Die Tabelle braucht mindestens eine Spalte für die Unterkante (z. B. 'bottom' oder 'bis') und eine für das "
        "Gestein (z. B. 'description', 'petrographie' oder 'code'). Laden Sie die Vorlage herunter.",
    "The variations use monthly sizing, which gives {base:.1f} m for these inputs (the result above: {length:.1f} m). Read the changes in percent.":
        "Die Varianten nutzen die monatliche Auslegung, die für diese Eingaben {base:.1f} m ergibt (Ergebnis oben: "
        "{length:.1f} m). Lesen Sie die Änderungen in Prozent.",
    "The zip file contains no .shp file.": "Die ZIP-Datei enthält keine .shp-Datei.",
    "The zip file could not be opened.": "Die ZIP-Datei konnte nicht geöffnet werden.",
    "The zip file must contain exactly one .shp file, found {n}.":
        "Die ZIP-Datei muss genau eine .shp-Datei enthalten, gefunden: {n}.",
    "Thermal conductivity": "Wärmeleitfähigkeit",
    "Thermal conductivity [W/(m·K)]": "Wärmeleitfähigkeit [W/(m·K)]",
    "These are the monthly temperatures with block peaks, shown for comparison. The sizing checked the limits hour by hour: see **Hourly** for those temperatures.":
        "Dies sind die monatlichen Temperaturen mit Blockspitzen, zum Vergleich dargestellt. Die Auslegung hat die "
        "Grenzwerte stündlich geprüft: Diese Temperaturen finden Sie unter **Stündlich**.",
    "These layers were not used: the calculation took the single conductivity from step ①. Switch on **Calculate with the layers** under Ground to size with them.":
        "Diese Schichten wurden nicht verwendet: Die Berechnung nutzte die einzelne Wärmeleitfähigkeit aus Schritt ①. "
        "Schalten Sie unter Untergrund **Mit den Schichten rechnen** ein, um mit ihnen auszulegen.",
    "This is not a readable BoreholeML file ({error}).": "Dies ist keine lesbare BoreholeML-Datei ({error}).",
    "This point is not in Germany.": "Dieser Punkt liegt nicht in Deutschland.",
    "Time [years]": "Zeit [Jahre]",
    "Time h": "Zeit h",
    "Title": "Titel",
    "To [m]": "Bis [m]",
    "To depth [m]": "Bis Tiefe [m]",
    "Total borehole length": "Gesamte Sondenlänge",
    "Total length [m]": "Gesamtlänge [m]",
    "Trying {n} layouts. This takes about {minutes} minute(s)...":
        "{n} Anordnungen werden ausprobiert. Das dauert etwa {minutes} Minute(n) …",
    "Type": "Art",
    "U-shape": "U-Form",
    "Undisturbed ground": "Ungestörter Untergrund",
    "Unit": "Einheit",
    "Upload a GeoJSON, KML or zipped shapefile.": "Laden Sie eine GeoJSON-, KML- oder gezippte Shapefile-Datei hoch.",
    "Use": "Verwenden",
    "Use in the sizing": "In der Auslegung verwenden",
    "Use the drawn outline": "Gezeichneten Umriss verwenden",
    "Use the layers": "Schichten verwenden",
    "Use this outline": "Diesen Umriss verwenden",
    "Use this parcel": "Dieses Flurstück verwenden",
    "VDI 4640 recommends at least 5 m (6 m for longer boreholes); 5 to 8 m is common. Closer boreholes influence each other more.":
        "VDI 4640 empfiehlt mindestens 5 m (6 m bei längeren Sonden); 5 bis 8 m sind üblich. Engere Sonden "
        "beeinflussen sich stärker.",
    "VDI 4640 rule of thumb: 30 to 60 W/m": "Faustwert nach VDI 4640: 30 bis 60 W/m",
    "Value": "Wert",
    "Variant": "Variante",
    "Variant comparison": "Variantenvergleich",
    "Variant {n}": "Variante {n}",
    "View": "Ansicht",
    "Volumetric heat capacity [MJ/(m³·K)]": "Volumetrische Wärmekapazität [MJ/(m³·K)]",
    "WGS84 longitude/latitude (EPSG:4326)": "WGS84 Länge/Breite (EPSG:4326)",
    "Warmest fluid entering the borefield": "Wärmstes Fluid beim Eintritt ins Sondenfeld",
    "Warning": "Warnung",
    "Warnings": "Warnungen",
    "Warnings: ": "Warnungen: ",
    "Weight": "Gewicht",
    "What the borehole length depends on most": "Wovon die Sondenlänge am stärksten abhängt",
    "When it gets cold or warm (average fluid temperature, last year)":
        "Wann es kalt oder warm wird (mittlere Fluidtemperatur, letztes Jahr)",
    "Where the boreholes will be. Find your parcel in step ⓪ Site plan to use it here.":
        "Wo die Sonden liegen sollen. Suchen Sie Ihr Flurstück in Schritt ⓪ Lageplan, um es hier zu verwenden.",
    "Who covers the demand (average year)": "Wer den Bedarf deckt (Durchschnittsjahr)",
    "With a limit, the boreholes kept are spread as far apart as possible.":
        "Mit einer Begrenzung werden die verbleibenden Sonden so weit wie möglich verteilt.",
    "With a measured borehole resistance (TRT) the pipe and flow are not known, so there are no hydraulic results.":
        "Bei einem gemessenen Bohrlochwiderstand (TRT) sind Rohr und Durchfluss nicht bekannt, daher gibt es keine "
        "hydraulischen Ergebnisse.",
    "With layers": "Mit Schichten",
    "With one value ({k:.2f} W/(m·K))": "Mit einem Wert ({k:.2f} W/(m·K))",
    "Year": "Jahr",
    "Yearly imbalance": "Jährliches Ungleichgewicht",
    "Yearly min-max": "Jährlich Min–Max",
    "Yearly min/max": "Jährliche Min./Max.",
    "Years": "Jahre",
    "Zoom in on the aerial image and click inside your parcel.":
        "Zoomen Sie im Luftbild heran und klicken Sie in Ihr Flurstück.",
    "above groundwater": "über dem Grundwasser",
    "after heat pump efficiency": "nach Wärmepumpeneffizienz",
    "after {n} years": "nach {n} Jahren",
    "allowed borehole area": "zulässige Sondenfläche",
    "as entered (ground side)": "wie eingegeben (untergrundseitig)",
    "assumed": "angenommen",
    "at peak cooling": "bei Kühlspitze",
    "at the coldest fluid (highest viscosity); borehole only, without manifold and header pipes":
        "beim kältesten Fluid (höchste Viskosität); nur Sonde, ohne Verteiler und Anbindeleitungen",
    "at the coldest fluid; turbulent flow (above about 4000) transfers heat better":
        "beim kältesten Fluid; turbulente Strömung (über etwa 4000) überträgt Wärme besser",
    "at the limit": "am Grenzwert",
    "at {h:,.0f} operating hours; borehole pressure drop only": "bei {h:,.0f} Betriebsstunden; nur Druckverlust der Sonde",
    "at {t:.1f} °C average fluid temperature": "bei {t:.1f} °C mittlerer Fluidtemperatur",
    "bhe_positions.shp can be uploaded directly under Borefield > Irregular field (shapefile).":
        "bhe_positions.shp kann direkt unter Sondenfeld > Unregelmäßiges Feld (Shapefile) hochgeladen werden.",
    "both limits": "beide Grenzwerte",
    "building": "Gebäude",
    "cadastre": "Kataster",
    "calculated from pipe, grout and flow": "berechnet aus Rohr, Verfüllung und Durchfluss",
    "change of the yearly lowest temperature from year 1 to year {n}; a large drift means the ground is out of balance":
        "Änderung der jährlich niedrigsten Temperatur von Jahr 1 bis Jahr {n}; eine starke Drift bedeutet, dass der "
        "Untergrund nicht im Gleichgewicht ist",
    "cooling (maximum temperature)": "Kühlen (Höchsttemperatur)",
    "design: {dp:.1f} kPa": "Auslegung: {dp:.1f} kPa",
    "e.g. Borefield sizing, design phase": "z. B. Auslegung Sondenfeld, Entwurfsplanung",
    "e.g. Hauptstraße 5, 52062 Aachen": "z. B. Hauptstraße 5, 52062 Aachen",
    "effective Rb": "effektives Rb",
    "entered": "eingegeben",
    "excluded": "ausgeschlossen",
    "extrapolated": "extrapoliert",
    "fixed value from the inputs": "fester Wert aus den Eingaben",
    "from the logs": "aus den Schichtenverzeichnissen",
    "from {top:.1f} to {bottom:.0f} m": "von {top:.1f} bis {bottom:.0f} m",
    "g-function": "g-Funktion",
    "g-function (for specialists)": "g-Funktion (für Fachleute)",
    "g-function of the borefield (thermal interaction of the boreholes)":
        "g-Funktion des Sondenfelds (thermische Wechselwirkung der Sonden)",
    "geological map": "geologische Karte",
    "heating (minimum temperature)": "Heizen (Mindesttemperatur)",
    "heating and cooling need about the same length": "Heizen und Kühlen erfordern etwa dieselbe Länge",
    "hexagonal grid at {angle}": "hexagonales Raster bei {angle}",
    "max. limit {x:g} °C": "max. Grenzwert {x:g} °C",
    "measured value": "Messwert",
    "min. limit {x:g} °C": "min. Grenzwert {x:g} °C",
    "none yet; run them under Further analysis to include them":
        "noch keine; führen Sie sie unter Weitere Auswertungen aus, um sie aufzunehmen",
    "not used: ": "nicht verwendet: ",
    "nothing fits": "nichts passt",
    "outside-in rows": "Reihen von außen nach innen",
    "positive: the ground warms up over the years; negative: it cools down":
        "positiv: Der Untergrund erwärmt sich über die Jahre; negativ: Er kühlt ab",
    "rules differ by state and district, and the parcel and building data may be out of date.":
        "Die Regeln unterscheiden sich je nach Land und Kreis, und Flurstücks- und Gebäudedaten können veraltet sein.",
    "square grid at {angle}": "quadratisches Raster bei {angle}",
    "state unknown": "Bundesland unbekannt",
    "supply from the heat pump at peak heating": "Vorlauf von der Wärmepumpe bei Heizspitze",
    "the VDI 4640 W/m values assume 1800 h (heating only) or 2400 h (with hot water)":
        "die W/m-Werte der VDI 4640 gelten für 1800 h (nur Heizen) bzw. 2400 h (mit Trinkwarmwasser)",
    "the largest share of the peak power": "den größten Anteil der Spitzenleistung",
    "the most energy, month by month": "die meiste Energie, Monat für Monat",
    "the most power with no long-term imbalance (slow, 2 to 3 minutes)":
        "die höchste Leistung ohne langfristiges Ungleichgewicht (langsam, 2 bis 3 Minuten)",
    "the other limit still has {margin:.1f} K margin": "der andere Grenzwert hat noch {margin:.1f} K Reserve",
    "upload ({name})": "Upload ({name})",
    "used: ": "verwendet: ",
    "year 1: {first:.2f}, year {n}: {last:.2f}; heat delivered per kWh of electricity":
        "Jahr 1: {first:.2f}, Jahr {n}: {last:.2f}; gelieferte Wärme je kWh Strom",
    "yearly average per metre of borehole": "Jahresmittel je Meter Sonde",
    "{c:.2f} MJ/(m³·K), {length:.0f} m borehole": "{c:.2f} MJ/(m³·K), {length:.0f} m Sonde",
    "{cold:+.2f} K to the minimum, {warm:+.2f} K to the maximum": "{cold:+.2f} K beim Minimum, {warm:+.2f} K beim Maximum",
    "{h:,.0f} h per year": "{h:,.0f} h pro Jahr",
    "{label}: {n} boreholes (click to edit the coordinates)": "{label}: {n} Sonden (zum Bearbeiten der Koordinaten klicken)",
    "{month}, year {year}": "{month}, Jahr {year}",
    "{name} (grey: fluid temperatures of this design, {lo:.1f} to {hi:.1f} °C)":
        "{name} (grau: Fluidtemperaturen dieser Auslegung, {lo:.1f} bis {hi:.1f} °C)",
    "{name}: no boreholes with layers.": "{name}: keine Bohrungen mit Schichten.",
    "{name}: no coordinates, so it is placed on the site.": "{name}: keine Koordinaten, daher auf dem Grundstück angesetzt.",
    "{n} borehole(s) are closer than {d:g} m to another: {which}":
        "{n} Sonde(n) liegen näher als {d:g} m an einer anderen: {which}",
    "{n} borehole(s) break a distance rule: {which}": "{n} Sonde(n) verletzen eine Abstandsregel: {which}",
    "{n} boreholes": "{n} Sonden",
    "{n} boreholes of {length:.1f} m": "{n} Sonden à {length:.1f} m",
    "{n} boreholes of {length:.1f} m keep the fluid between {t_min:g} and {t_max:g} °C for {years} years ({method}).":
        "{n} Sonden à {length:.1f} m halten das Fluid {years} Jahre lang zwischen {t_min:g} und {t_max:g} °C ({method}).",
    "{n} boreholes, closest {d:.1f} m apart": "{n} Sonden, geringster Abstand {d:.1f} m",
    "{n} boreholes, {b1:g} m × {b2:g} m spacing": "{n} Sonden, Abstand {b1:g} m × {b2:g} m",
    "{n} empty cells were read as 0 kW.": "{n} leere Zellen wurden als 0 kW gelesen.",
    "{n} layers, not used": "{n} Schichten, nicht verwendet",
    "{n} layers, used in the calculation": "{n} Schichten, in der Berechnung verwendet",
    "{n} log": "{n} Bohrung",
    "{n} logs": "{n} Bohrungen",
    "{n} of {total}": "{n} von {total}",
    "{n} years": "{n} Jahre",
    "{out:,.0f} MWh extracted, {inj:,.0f} MWh injected": "{out:,.0f} MWh entzogen, {inj:,.0f} MWh eingetragen",
    "{parts} MWh (average over the years)": "{parts} MWh (Mittel über die Jahre)",
    "{service}: {n} logged borehole(s) within {radius:,.0f} m.":
        "{service}: {n} Bohrung(en) mit Schichtenverzeichnis im Umkreis von {radius:,.0f} m.",
    "{state} does not publish its parcels as open data. Upload the parcel outline or draw it on the map instead.":
        "{state} veröffentlicht seine Flurstücke nicht als offene Daten. Laden Sie stattdessen den Flurstücksumriss "
        "hoch oder zeichnen Sie ihn in der Karte.",
    "{state} has no open building service; buildings come from OpenStreetMap only.":
        "{state} hat keinen offenen Gebäudedienst; Gebäude kommen nur aus OpenStreetMap.",
    "{w:,.0f} W electrical": "{w:,.0f} W elektrisch",
    "{w:,.0f} W hydraulic for the whole field, at {eff:.0%} pump efficiency":
        "{w:,.0f} W hydraulisch für das ganze Feld, bei {eff:.0%} Pumpenwirkungsgrad",
    "{w:.1f} W/m peak": "{w:.1f} W/m Spitze",
    "{w:.1f} W/m peak, {kwh:.0f} kWh/m per year": "{w:.1f} W/m Spitze, {kwh:.0f} kWh/m pro Jahr",
    "{when}; limit {limit:g} °C": "{when}; Grenzwert {limit:g} °C",
    "{x:+,.0f} MWh/yr": "{x:+,.0f} MWh/a",
    "{x:+.1f} K margin": "{x:+.1f} K Reserve",
    "{x:+.1f} m per borehole": "{x:+.1f} m je Sonde",
    "{x:+.2f} from year 1 to the last year": "{x:+.2f} von Jahr 1 bis zum letzten Jahr",
    "{x:,.0f} MWh/yr": "{x:,.0f} MWh/a",
    "{x:,.1f} MWh per year": "{x:,.1f} MWh pro Jahr",
    "{x:.1f} K beyond the limit": "{x:.1f} K über dem Grenzwert",
    "🔮 Predict the layers from nearby borehole logs and the geological map":
        "🔮 Schichten aus nahen Bohrungen und der geologischen Karte prognostizieren",

    # ------------------------------------------------------------ share link, design check, borefield map
    '**Design check**':
        '**Planungsprüfung**',
    '**Design check: {summary}**':
        '**Planungsprüfung: {summary}**',
    '**Share this project**':
        '**Dieses Projekt teilen**',
    'Antifreeze':
        'Frostschutz',
    'Anyone with the link opens the site with your inputs filled in. The project is stored in the link itself; nothing is saved on the server. Copy it with the button at the right of the box.':
        'Wer den Link öffnet, sieht die Seite mit Ihren Eingaben. Das Projekt steckt im Link selbst; auf dem Server wird nichts gespeichert. Kopieren Sie ihn mit der Schaltfläche rechts im Feld.',
    'Borefield map':
        'Sondenfeld-Karte',
    'Calculating each borehole...':
        'Jede Sonde wird berechnet...',
    'Colour by':
        'Einfärben nach',
    'Deeper than 100 m':
        'Tiefer als 100 m',
    'Design check':
        'Planungsprüfung',
    'Download the table (CSV)':
        'Tabelle herunterladen (CSV)',
    'Every check in one place. The temperature, flow, antifreeze and balance checks appear after a calculation.':
        'Alle Prüfungen an einem Ort. Temperatur, Strömung, Frostschutz und Bilanz werden nach einer Berechnung geprüft.',
    'Finite line source with the mirror image at the surface, one segment per borehole (the same model as the g-function). Numbers as in the input table of the borefield.':
        'Finite Linienquelle mit Spiegelquelle an der Oberfläche, ein Segment pro Sonde (dasselbe Modell wie die g-Funktion). Nummern wie in der Eingabetabelle des Sondenfelds.',
    'Flow in the borehole':
        'Strömung in der Sonde',
    'GHEtool sizes the field with one wall temperature for all boreholes. To reach it, boreholes at the edge and in the corners take more heat than those in the middle, because they have fewer neighbours. Red: more than the average, blue: less. The difference grows over the years as the boreholes start to influence each other.':
        'GHEtool legt das Feld mit einer Bohrlochwandtemperatur für alle Sonden aus. Damit diese überall gleich ist, leisten Sonden am Rand und in den Ecken mehr als die in der Mitte, weil sie weniger Nachbarn haben. Rot: mehr als der Durchschnitt, blau: weniger. Der Unterschied wächst mit den Jahren, weil sich die Sonden zunehmend gegenseitig beeinflussen.',
    'Go to {step}':
        'Zu {step}',
    'Ground balance':
        'Bilanz des Untergrunds',
    'Ground conductivity':
        'Wärmeleitfähigkeit des Untergrunds',
    'Hardest-working borehole':
        'Am stärksten belastete Sonde',
    'How much the yearly imbalance warms (red) or cools (blue) the ground at each borehole wall, with the same heat from every borehole. Boreholes in the middle change most, because their neighbours add up; a larger spacing there, or moving boreholes to the edge, helps.':
        'Wie stark das jährliche Ungleichgewicht den Untergrund an jeder Bohrlochwand erwärmt (rot) oder abkühlt (blau), bei gleicher Leistung aller Sonden. Sonden in der Mitte ändern sich am stärksten, weil sich ihre Nachbarn addieren; ein größerer Abstand dort oder Sonden am Rand helfen.',
    'Least-loaded borehole':
        'Am wenigsten belastete Sonde',
    'No. {n}':
        'Nr. {n}',
    'Open the design check':
        'Planungsprüfung öffnen',
    'Opened the project from the link. Hourly demand files are not part of links: upload it again if the project uses one.':
        'Projekt aus dem Link geöffnet. Stündliche Bedarfsdateien sind nicht Teil von Links: Laden Sie die Datei erneut hoch, falls das Projekt eine verwendet.',
    'Re = {re:,.0f} ({regime}) at the coldest fluid.':
        'Re = {re:,.0f} ({regime}) beim kältesten Fluid.',
    'Share link':
        'Link teilen',
    'Share of the load':
        'Anteil an der Last',
    'Share of the load [%]':
        'Anteil an der Last [%]',
    'Spacing between boreholes':
        'Sondenabstand',
    'Temperature change':
        'Temperaturänderung',
    'The boreholes reach {d:.0f} m. In Germany drilling deeper than 100 m must be notified to the mining authority (BBergG §127).':
        'Die Sonden reichen bis {d:.0f} m. Bohrungen tiefer als 100 m sind in Deutschland der Bergbehörde anzuzeigen (§ 127 BBergG).',
    'The coldest fluid ({cold:.1f} °C) is within 3 K of the freezing point ({freezing:.1f} °C). Use more antifreeze or a higher minimum temperature.':
        'Das kälteste Fluid ({cold:.1f} °C) liegt weniger als 3 K über dem Gefrierpunkt ({freezing:.1f} °C). Erhöhen Sie den Frostschutzanteil oder die Mindesttemperatur.',
    'The flow is laminar (Re = {re:,.0f}), which raises the borehole resistance. A higher flow rate, smaller pipes or less antifreeze make it turbulent and can shorten the boreholes.':
        'Die Strömung ist laminar (Re = {re:,.0f}), das erhöht den Bohrlochwiderstand. Ein höherer Volumenstrom, kleinere Rohre oder weniger Frostschutz machen sie turbulent und können die Sonden verkürzen.',
    'The fluid goes beyond the limits: lowest {lo:.1f} °C (limit {t_min:g} °C), highest {hi:.1f} °C (limit {t_max:g} °C). Make the boreholes longer or add boreholes.':
        'Das Fluid überschreitet die Grenzwerte: niedrigste {lo:.1f} °C (Grenze {t_min:g} °C), höchste {hi:.1f} °C (Grenze {t_max:g} °C). Verlängern Sie die Sonden oder fügen Sie Sonden hinzu.',
    'The fluid stays between {lo:.1f} and {hi:.1f} °C (limits {t_min:g} and {t_max:g} °C).':
        'Das Fluid bleibt zwischen {lo:.1f} und {hi:.1f} °C (Grenzen {t_min:g} und {t_max:g} °C).',
    'The hourly demand file is not part of the link (too large): send the file separately.':
        'Die stündliche Bedarfsdatei ist nicht im Link enthalten (zu groß): Senden Sie die Datei separat.',
    'The smallest spacing is {b:.1f} m{where} with {h:.0f} m long boreholes. VDI 4640 asks for at least 6 m for boreholes deeper than 50 m.':
        'Der kleinste Abstand beträgt {b:.1f} m{where} bei {h:.0f} m langen Sonden. Die VDI 4640 fordert mindestens 6 m für Sonden tiefer als 50 m.',
    'The smallest spacing is {b:.1f} m{where}.':
        'Der kleinste Abstand beträgt {b:.1f} m{where}.',
    'The smallest spacing is {b:.1f} m{where}. VDI 4640 asks for at least 5 m (6 m for boreholes deeper than 50 m).':
        'Der kleinste Abstand beträgt {b:.1f} m{where}. Die VDI 4640 fordert mindestens 5 m (6 m für Sonden tiefer als 50 m).',
    'The yearly lowest temperature changes by only {d:+.1f} K over the simulation.':
        'Die jährlich niedrigste Temperatur ändert sich über die Simulation nur um {d:+.1f} K.',
    'The yearly lowest temperature changes by {d:+.1f} K over the simulation: the ground is out of balance ({imb:+,.0f} MWh per year). Cooling in summer or a larger spacing helps.':
        'Die jährlich niedrigste Temperatur ändert sich über die Simulation um {d:+.1f} K: Der Untergrund ist nicht im Gleichgewicht ({imb:+,.0f} MWh pro Jahr). Kühlen im Sommer oder ein größerer Abstand helfen.',
    'This link does not contain a readable project. Ask for a new link or the project file.':
        'Dieser Link enthält kein lesbares Projekt. Bitten Sie um einen neuen Link oder die Projektdatei.',
    'This link is long ({n:,} characters). Some e-mail programs cut long links; if it does not open, send the project file instead.':
        'Dieser Link ist lang ({n:,} Zeichen). Manche E-Mail-Programme kürzen lange Links; falls er sich nicht öffnet, senden Sie stattdessen die Projektdatei.',
    'This list is for the current inputs; the results for them are not calculated yet.':
        'Diese Liste gilt für die aktuellen Eingaben; deren Ergebnisse sind noch nicht berechnet.',
    'Time':
        'Zeitpunkt',
    'Wall temperature change':
        'Änderung der Wandtemperatur',
    'With a single borehole there is nothing to compare.':
        'Bei einer einzelnen Sonde gibt es nichts zu vergleichen.',
    'after 1 year':
        'nach 1 Jahr',
    'boreholes {a} and {b}':
        'Sonden {a} und {b}',
    'from the yearly imbalance':
        'durch das jährliche Ungleichgewicht',
    '{fluid} protects to {freezing:.1f} °C; the coldest fluid is {cold:.1f} °C.':
        '{fluid} schützt bis {freezing:.1f} °C; das kälteste Fluid hat {cold:.1f} °C.',
    '{k:.1f} W/(m·K) is in the usual range of {lo:g} to {hi:g} W/(m·K).':
        '{k:.1f} W/(m·K) liegt im üblichen Bereich von {lo:g} bis {hi:g} W/(m·K).',
    '{n} fine':
        '{n} in Ordnung',
    '{n} problem(s)':
        '{n} Problem(e)',
    '{n} warning(s)':
        '{n} Warnung(en)',
    '{w:.0f} W/m at peak is above the VDI 4640 rule of thumb (30 to 60 W/m). The simulation allows it, but check the peak load and the ground values.':
        '{w:.0f} W/m in der Spitze liegt über dem Richtwert der VDI 4640 (30 bis 60 W/m). Die Simulation lässt das zu, prüfen Sie aber die Spitzenlast und die Untergrundwerte.',
    '{x:.0f} % of the average load':
        '{x:.0f} % der mittleren Last',
    '**Boreholes of the state survey near the site** ({n})':
        '**Bohrungen des Landesdienstes nahe dem Standort** ({n})',
    'Ask the open data services (BGR geological map of Germany; borehole data of the state surveys)':
        'Offene Datendienste abfragen (Geologische Karte der BGR; Bohrdaten der Landesdienste)',
    'Berlin, borehole data (WFS)':
        'Berlin, Bohrdaten (WFS)',
    'Borehole data of the 16 state surveys':
        'Bohrdaten der 16 Landesdienste',
    'Boreholes in the LGB map viewer; no open download service.':
        'Bohrungen im Kartenviewer des LGB; kein offener Downloaddienst.',
    'Boreholes in the LGRB map viewer; no open download service.':
        'Bohrungen im Kartenviewer des LGRB; kein offener Downloaddienst.',
    'Boreholes in the UmweltAtlas (Geologie); no open download service.':
        'Bohrungen im UmweltAtlas (Geologie); kein offener Downloaddienst.',
    'Connected: archive boreholes with depth, unit and groundwater; logs on request.':
        'Angebunden: Archivbohrungen mit Endteufe, Einheit und Grundwasser; Schichtenverzeichnisse auf Anfrage.',
    'Connected: boreholes with a data sheet link.':
        'Angebunden: Bohrungen mit Link zum Datenblatt.',
    'Connected: boreholes with a link to the log column.':
        'Angebunden: Bohrungen mit Link zur Profilsäule.',
    'Connected: boreholes with a link to the released log.':
        'Angebunden: Bohrungen mit Link zum freigegebenen Schichtenverzeichnis.',
    'Connected: boreholes with a picture of the log column.':
        'Angebunden: Bohrungen mit Bild der Profilsäule.',
    'Connected: boreholes with a picture of the log.':
        'Angebunden: Bohrungen mit Bild des Schichtenverzeichnisses.',
    'Connected: logs with layers (BoreholeML), used for the prediction directly.':
        'Angebunden: Schichtenverzeichnisse mit Schichten (BoreholeML), fließen direkt in die Vorhersage ein.',
    'Data sheet in the GeODin portal':
        'Datenblatt im GeODin-Portal',
    'Everywhere else: the BGR geological map gives the rock at the surface, and logs you get from the survey (BoreholeML or a table) can be uploaded. Drilling companies and earlier geothermal projects nearby are often the quickest source of a log.':
        'Überall sonst: Die geologische Karte der BGR liefert das Gestein an der Oberfläche, und Schichtenverzeichnisse vom Landesdienst (BoreholeML oder Tabelle) können hochgeladen werden. Bohrfirmen und frühere Erdwärmeprojekte in der Nähe sind oft die schnellste Quelle für ein Schichtenverzeichnis.',
    'HLNUG Hessen, archive boreholes (ArcGIS)':
        'HLNUG Hessen, Archivbohrungen (ArcGIS)',
    'LBEG Niedersachsen, NIBIS boreholes (WMS feature info)':
        'LBEG Niedersachsen, NIBIS-Bohrungen (WMS-Sachdatenabfrage)',
    'LBGR Brandenburg, borehole points with logs (WFS)':
        'LBGR Brandenburg, Bohrpunkte mit Schichtenverzeichnis (WFS)',
    'LUNG Mecklenburg-Vorpommern, state borehole archive (WFS)':
        'LUNG Mecklenburg-Vorpommern, Landesbohrdatenspeicher (WFS)',
    'LfU Schleswig-Holstein, borehole points (WFS)':
        'LfU Schleswig-Holstein, Bohrpunkte (WFS)',
    'LfULG Sachsen, boreholes (ArcGIS)':
        'LfULG Sachsen, Bohrungen (ArcGIS)',
    'Log':
        'Schichtenverzeichnis',
    'Log (Schichtenverzeichnis) on the LUNG map server':
        'Schichtenverzeichnis auf dem Kartenserver des LUNG',
    'Log as a picture':
        'Schichtenverzeichnis als Bild',
    'Log column in the GeODin portal':
        'Profilsäule im GeODin-Portal',
    'Log column in the NIBIS map server':
        'Profilsäule im NIBIS-Kartenserver',
    'Map of the state borehole database; logs on request.':
        'Karte der Landesbohrdatenbank; Schichtenverzeichnisse auf Anfrage.',
    'No log online; ask HLNUG for it':
        'Kein Schichtenverzeichnis online; beim HLNUG anfragen',
    'No open borehole service found; ask the survey.':
        'Kein offener Bohrdatendienst gefunden; beim Landesdienst anfragen.',
    'None of them is 30 m deep or more; a larger search radius may find deeper ones.':
        'Keine davon ist 30 m oder tiefer; ein größerer Suchradius findet vielleicht tiefere.',
    'Notes':
        'Hinweise',
    'Survey':
        'Landesdienst',
    'The borehole service did not answer with data ({error}).':
        'Der Bohrdatendienst hat keine Daten geliefert ({error}).',
    'These logs are not machine-readable, so they are not in the prediction above. Open the nearest deep ones, then type their layers into the layer table below (or into the table template and upload it). {how}.':
        'Diese Schichtenverzeichnisse sind nicht maschinenlesbar und fließen daher nicht in die Vorhersage oben ein. Öffnen Sie die nächstgelegenen tiefen Bohrungen und tragen Sie die Schichten in die Schichttabelle unten ein (oder in die Tabellenvorlage und laden Sie diese hoch). {how}.',
    'This state survey has no open borehole service that the app can ask. See the overview of the state portals below; logs you get from them can be uploaded above.':
        'Dieser Landesdienst hat keinen offenen Bohrdatendienst, den die App abfragen kann. Siehe die Übersicht der Landesportale unten; Schichtenverzeichnisse von dort können oben hochgeladen werden.',
    'What the app gets':
        'Was die App erhält',
    'groundwater at {gw:.1f} m':
        'Grundwasser bei {gw:.1f} m',
    'open':
        'öffnen',
    '{service}: {error}':
        '{service}: {error}',
    '{service}: {n} borehole(s) within {radius:,.0f} m. This state publishes the logs only as pictures or web pages; see the list below.':
        '{service}: {n} Bohrung(en) im Umkreis von {radius:,.0f} m. Dieses Land veröffentlicht die Schichtenverzeichnisse nur als Bild oder Webseite; siehe Liste unten.',
}
