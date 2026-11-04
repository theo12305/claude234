"""German texts of the material list (VDI 4640 terms). The key is the English text exactly as in the code."""

DE: dict[str, str] = {
    # view, plan and tools
    "Material list": "Materialliste",
    "Material list (CSV)": "Materialliste (CSV)",
    "Material list (Excel)": "Materialliste (Excel)",
    "Plan of the horizontal piping": "Lageplan der horizontalen Anbindung",
    "Quantities from the sizing result and the horizontal piping on the plan. Click the building entrance on the "
    "plan; the trenches are routed automatically, or draw them yourself. No prices: export the list and price it in "
    "your own tools.":
        "Mengen aus dem Auslegungsergebnis und der horizontalen Anbindung im Lageplan. Klicken Sie die Hauseinführung "
        "im Plan an; die Gräben werden automatisch geführt, oder Sie zeichnen sie selbst. Ohne Preise: exportieren "
        "Sie die Liste und bepreisen Sie sie in Ihren eigenen Programmen.",
    "Click on the plan to set": "Im Plan setzen",
    "Building entrance": "Hauseinführung",
    "Manifold": "Verteiler",
    "Draw trench": "Graben zeichnen",
    "Finish line": "Linie beenden",
    "Undo last point": "Letzten Punkt zurück",
    "Delete drawn trenches (automatic routing)": "Gezeichnete Gräben löschen (automatische Trasse)",
    "Click where the header pipes enter the building.": "Klicken Sie, wo die Hauptleitungen ins Gebäude führen.",
    "Click where the manifold shaft goes.": "Klicken Sie, wo der Verteilerschacht hinkommt.",
    "Click the corners of a trench one after the other, then Finish line. Lines that touch or cross are joined; each "
    "BHE and the manifold are joined to the nearest trench.":
        "Klicken Sie die Eckpunkte eines Grabens nacheinander an, dann Linie beenden. Linien, die sich berühren oder "
        "kreuzen, werden verbunden; jede EWS und der Verteiler werden an den nächsten Graben angeschlossen.",
    "Dark blue: BHEs. Teal: trenches, thicker with more circuits. Orange dashed: header pipe. Click resolution {s:g} m.":
        "Dunkelblau: EWS. Petrol: Gräben, dicker mit mehr Kreisen. Orange gestrichelt: Hauptleitung. "
        "Klickauflösung {s:g} m.",
    "The building entrance is assumed 10 m west of the field. Click it on the plan for the real lengths.":
        "Die Hauseinführung ist 10 m westlich des Sondenfelds angenommen. Klicken Sie sie im Plan an, um die "
        "tatsächlichen Längen zu erhalten.",
    "{n} BHE(s) are not reached by the drawn trenches and are joined straight to the manifold: no. {nos}.":
        "{n} EWS werden von den gezeichneten Gräben nicht erreicht und gerade an den Verteiler angeschlossen: "
        "Nr. {nos}.",
    "The material list and the plan settings are saved with the project (menu ☰ > Save project) and are part of the "
    "Excel export under Export.":
        "Materialliste und Planeinstellungen werden mit dem Projekt gespeichert (Menü ☰ > Projekt speichern) und sind "
        "Teil des Excel-Exports unter Export.",
    "BHE no.": "EWS Nr.",
    "Circuits in the trench": "Kreise im Graben",
    "Length [m]": "Länge [m]",
    "Table {n}": "Tabelle {n}",
    "Trench length": "Grabenlänge",
    "circuits and header": "Anbindung und Hauptleitung",
    "Connection pipe": "Anbindeleitung",
    "longest circuit {x:.0f} m": "längster Kreis {x:.0f} m",
    "Header pipe": "Hauptleitung",
    "manifold to building, single length": "Verteiler bis Gebäude, einfache Länge",
    "manifold in the building": "Verteiler im Gebäude",
    "System volume": "Anlagenvolumen",
    "heat transfer fluid": "Wärmeträgerfluid",
    # settings
    "Manifold position": "Lage des Verteilers",
    "Manifold shaft beside the field (automatic)": "Verteilerschacht neben dem Sondenfeld (automatisch)",
    "Manifold shaft where you click": "Verteilerschacht an der angeklickten Stelle",
    "Manifold in the building (one circuit per BHE to the plant room)":
        "Verteiler im Gebäude (jeder Sondenkreis bis in den Technikraum)",
    "Every BHE is one circuit with its own supply and return pipe to the manifold. A manifold shaft near the field "
    "needs only one pair of header pipes to the building; a manifold in the plant room needs a wall penetration for "
    "every circuit.":
        "Jede EWS ist ein Kreis mit eigenem Vor- und Rücklauf zum Verteiler. Ein Verteilerschacht am Sondenfeld "
        "braucht nur ein Paar Hauptleitungen zum Gebäude; ein Verteiler im Technikraum braucht eine "
        "Mauerdurchführung für jeden Kreis.",
    "Connection pipe (BHE to manifold)": "Anbindeleitung (EWS bis Verteiler)",
    "Header pipe (manifold to building)": "Hauptleitung (Verteiler bis Gebäude)",
    "Automatic: the smallest PE100 SDR 11 pipe that keeps the flow velocity at the design flow per BHE below the "
    "maximum.":
        "Automatisch: das kleinste PE100-SDR-11-Rohr, in dem die Strömungsgeschwindigkeit beim Auslegungsvolumenstrom "
        "je EWS unter dem Höchstwert bleibt.",
    "Automatic: the smallest PE100 SDR 11 pipe for the flow of all BHEs together within the maximum velocity.":
        "Automatisch: das kleinste PE100-SDR-11-Rohr für den Volumenstrom aller EWS zusammen innerhalb der "
        "Höchstgeschwindigkeit.",
    "automatic (v ≤ {v:g} m/s)": "automatisch (v ≤ {v:g} m/s)",
    "More options": "Weitere Optionen",
    "Trench depth": "Grabentiefe",
    "Frost-free depth for the horizontal pipes; 1.0 to 1.5 m is common.":
        "Frostfreie Tiefe der horizontalen Leitungen; üblich sind 1,0 bis 1,5 m.",
    "Trench width": "Grabenbreite",
    "Sand bedding and cover (height)": "Sandbettung und -abdeckung (Höhe)",
    "Sand under and over the pipes, e.g. 0.1 m below and 0.2 m above.":
        "Sand unter und über den Rohren, z. B. 0,1 m darunter und 0,2 m darüber.",
    "Pipe reserve per circuit and line": "Rohrzuschlag je Kreis und Leitung",
    "Extra pipe for each supply and return line: up from the trench at the BHE head and at the manifold.":
        "Zusätzliches Rohr für jeden Vor- und Rücklauf: Hochführung aus dem Graben am Sondenkopf und am Verteiler.",
    "BHE delivery length step": "Lieferlängen-Raster der EWS",
    "BHEs are delivered in fixed lengths; the length is rounded up to the next step.":
        "EWS werden in festen Längen geliefert; die Länge wird auf das nächste Rastermaß aufgerundet.",
    "Grout loss factor": "Verfüllmehrmenge",
    "Extra grout above the annulus volume for fissures, karst or loss into the formation. 10 to 20 % in solid rock; "
    "more in karst.":
        "Mehrmenge an Verfüllbaustoff über dem Ringraumvolumen für Klüfte, Karst oder Verluste ins Gebirge. 10 bis "
        "20 % im Festgestein, im Karst mehr.",
    "Maximum flow velocity (automatic pipe size)": "Maximale Strömungsgeschwindigkeit (automatische Rohrwahl)",
    "Higher velocity: smaller pipes, more pressure drop. 0.8 to 1.5 m/s is common.":
        "Höhere Geschwindigkeit: kleinere Rohre, mehr Druckverlust. Üblich sind 0,8 bis 1,5 m/s.",
    "Snap distance when drawing": "Fangradius beim Zeichnen",
    "A click this close to the end or corner of a trench joins it.":
        "Ein Klick so nah an einem Ende oder Eckpunkt eines Grabens wird mit ihm verbunden.",
    # table
    "Basis of quantity": "Mengenansatz",
    "Item no.": "Pos.",
    "Quantity": "Menge",
    "pcs": "Stk.",
    "LS": "psch.",
    "l": "l",
    "kg": "kg",
    "m³": "m³",
    # groups and items
    "Drilling": "Bohrung",
    "Borehole heat exchangers": "Erdwärmesonden",
    "Grouting": "Verfüllung",
    "Horizontal piping": "Horizontale Anbindung",
    "Heat transfer fluid": "Wärmeträgerfluid",
    "Tests and documentation": "Prüfungen und Dokumentation",
    "Boreholes Ø {d:g} mm": "Bohrungen Ø {d:g} mm",
    "from the sizing": "aus der Auslegung",
    "Drilled length": "Bohrmeter",
    "{n} × ({H:.1f} m + {D:.1f} m buried depth)": "{n} × ({H:.1f} m + {D:.1f} m Überdeckung)",
    "Borehole volume (cuttings, solid)": "Bohrlochvolumen (Bohrgut, fest)",
    "π × r² × drilled length": "π × r² × Bohrmeter",
    "Notification under mining law (BBergG, boreholes deeper than 100 m)":
        "Bergrechtliche Anzeige (BBergG, Bohrungen tiefer als 100 m)",
    "{x:.0f} m deep": "{x:.0f} m tief",
    "Double U-tube BHE": "Doppel-U-Sonde",
    "Single U-tube BHE": "Einfach-U-Sonde",
    "{name}, length {L:g} m, with BHE foot": "{name}, Länge {L:g} m, mit Sondenfuß",
    "{x:.1f} m rounded up to the next {step:g} m": "{x:.1f} m auf die nächsten {step:g} m aufgerundet",
    "pipe assumed (measured Rb)": "Rohr angenommen (gemessener Rb)",
    "PE pipe in the BHEs ({name})": "PE-Rohr in den EWS ({name})",
    "{n} × {legs} legs × {L:g} m": "{n} × {legs} Schenkel × {L:g} m",
    "Spacers": "Abstandhalter",
    "one every 2 m": "einer alle 2 m",
    "Y-pieces at the BHE head (2 legs to 1 pipe)": "Hosenstücke am Sondenkopf (2 Schenkel auf 1 Rohr)",
    "supply and return per BHE": "Vor- und Rücklauf je EWS",
    "Grouting pipe (tremie), lost or recovered": "Verpressrohr, verlorenes oder rückgewonnenes",
    "one per BHE, full length": "eines je EWS, volle Länge",
    "Grout suspension, {name}": "Verfüllsuspension, {name}",
    "{a:.2f} m³ annulus per BHE × {n} × (1 + {loss:g} % loss)":
        "{a:.2f} m³ Ringraum je EWS × {n} × (1 + {loss:g} % Mehrmenge)",
    "Trench, depth {d:g} m, width {w:g} m": "Rohrgraben, Tiefe {d:g} m, Breite {w:g} m",
    "drawn on the plan": "im Plan gezeichnet",
    "shortest trench network (automatic)": "kürzeste Grabentrasse (automatisch)",
    "Excavation": "Aushub",
    "length × width × depth": "Länge × Breite × Tiefe",
    "Sand bedding and cover": "Sandbettung und -abdeckung",
    "length × width × {h:g} m": "Länge × Breite × {h:g} m",
    "Warning tape": "Trassenwarnband",
    "trench length": "Grabenlänge",
    "Connection pipe {name}": "Anbindeleitung {name}",
    "supply + return per BHE, path to the manifold + {r:g} m each; longest circuit {x:.0f} m; v = {v:.2f} m/s":
        "Vor- + Rücklauf je EWS, Weg bis zum Verteiler + je {r:g} m; längster Kreis {x:.0f} m; v = {v:.2f} m/s",
    "Electrofusion couplers / transition fittings": "Elektroschweißmuffen / Übergangsformstücke",
    "2 at the BHE head and 2 at the manifold per circuit": "je Kreis 2 am Sondenkopf und 2 am Verteiler",
    "Manifold with {n} circuits (flow meters, balancing and isolation valves)":
        "Verteiler mit {n} Kreisen (Durchflussanzeiger, Strangregulier- und Absperrventile)",
    "in the plant room": "im Technikraum",
    "in the manifold shaft": "im Verteilerschacht",
    "Wall penetrations, gas- and watertight": "Mauerdurchführungen, gas- und wasserdicht",
    "supply and return of every circuit": "Vor- und Rücklauf jedes Kreises",
    "Header pipe {name}": "Hauptleitung {name}",
    "supply + return, manifold to the building entrance {x:.1f} m; v = {v:.2f} m/s":
        "Vor- + Rücklauf, Verteiler bis Hauseinführung {x:.1f} m; v = {v:.2f} m/s",
    "Manifold shaft (PE or concrete)": "Verteilerschacht (PE oder Beton)",
    "header supply and return": "Vor- und Rücklauf der Hauptleitung",
    "System volume (without manifold and heat pump)": "Anlagenvolumen (ohne Verteiler und Wärmepumpe)",
    "BHEs {a:.2f} + connection pipes {b:.2f} + header {c:.2f} m³":
        "EWS {a:.2f} + Anbindeleitungen {b:.2f} + Hauptleitung {c:.2f} m³",
    "Antifreeze {name}, concentrate": "Frostschutzmittel {name}, Konzentrat",
    "{x:g} % by mass of the system volume, {kg:,.0f} kg": "{x:g} Massen-% des Anlagenvolumens, {kg:,.0f} kg",
    "{x:g} % by mass of the system volume": "{x:g} Massen-% des Anlagenvolumens",
    "Pressure and flow test of each BHE (VDI 4640-2)": "Druck- und Durchflussprüfung jeder EWS (VDI 4640-2)",
    "one per BHE": "eine je EWS",
    "Pressure test of the horizontal piping": "Druckprüfung der horizontalen Anbindung",
    "Layer documentation (Schichtenverzeichnis) to the state geological survey":
        "Schichtenverzeichnis an den Geologischen Dienst des Landes",
    "Geologiedatengesetz (GeolDG)": "Geologiedatengesetz (GeolDG)",
}
