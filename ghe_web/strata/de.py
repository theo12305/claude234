"""German texts of the ground layers panel added after the move to the feature's own table. The key is the English
text exactly as in the code; the older texts of the panel are in i18n/de.py."""

DE: dict[str, str] = {
    # reading logs automatically
    "Logs read automatically": "Automatisch gelesene Bohrprofile",
    "Berlin and Schleswig-Holstein publish their logs as sheets, not as data. The app reads the logs of this many "
    "nearest boreholes itself (Berlin: text recognition of the log sheet; Schleswig-Holstein: text layer of the log "
    "column PDF) and adds them to 'Logs to check'. 0: none. Other states: logs with layers come as data (NRW, "
    "Baden-Württemberg) or are entered by hand.":
        "Berlin und Schleswig-Holstein veröffentlichen ihre Schichtenverzeichnisse als Blätter, nicht als Daten. Die "
        "App liest die Profile so vieler nächstgelegener Bohrungen selbst (Berlin: Texterkennung des Profilblatts; "
        "Schleswig-Holstein: Textebene des Säulenprofils als PDF) und legt sie unter „Zu prüfende Bohrprofile“ ab. "
        "0: keine. Andere Länder: Profile mit Schichten kommen als Daten (NRW, Baden-Württemberg) oder werden von "
        "Hand eingegeben.",
    "{service}, read by the app": "{service}, von der App gelesen",
    "Read {n} of {m} logs of the nearest boreholes automatically ({how}). Check them under 'Logs to check' below.":
        "{n} von {m} Bohrprofilen der nächstgelegenen Bohrungen automatisch gelesen ({how}). Prüfen Sie sie unten "
        "unter „Zu prüfende Bohrprofile“.",
    "Not read: {which}": "Nicht gelesen: {which}",
    "text recognition of the log sheets": "Texterkennung der Profilblätter",
    "text layer of the log column PDFs": "Textebene der Säulenprofile (PDF)",
    "Text recognition (Tesseract) is not installed on this server, so the log sheets of the state service were not "
    "read.":
        "Die Texterkennung (Tesseract) ist auf diesem Server nicht installiert; die Profilblätter des Landesdienstes "
        "wurden daher nicht gelesen.",
    "Text recognition (Tesseract) is not installed on this server, so pictures cannot be read. Type the layers into "
    "the box instead.":
        "Die Texterkennung (Tesseract) ist auf diesem Server nicht installiert; Bilder können daher nicht gelesen "
        "werden. Geben Sie die Schichten stattdessen in das Feld ein.",
    "The layers read go deeper than the borehole ({d:.1f} m); check the log by hand.":
        "Die gelesenen Schichten reichen tiefer als die Bohrung ({d:.1f} m); prüfen Sie das Profil von Hand.",
    "The service did not return the log column.": "Der Dienst hat kein Säulenprofil geliefert.",
    "The service did not return the log sheet.": "Der Dienst hat kein Profilblatt geliefert.",
    "The log column could not be split into layers ({n} names, {m} depths).":
        "Das Säulenprofil ließ sich nicht in Schichten zerlegen ({n} Bezeichnungen, {m} Tiefen).",
    "No layers were recognised in the picture. Type the layers into the box, or try a sharper picture of the "
    "Schichtenverzeichnis.":
        "Im Bild wurden keine Schichten erkannt. Geben Sie die Schichten in das Feld ein oder verwenden Sie ein "
        "schärferes Bild des Schichtenverzeichnisses.",
    "Reading the picture took too long.": "Das Lesen des Bildes hat zu lange gedauert.",
    "This picture could not be opened ({error}).": "Dieses Bild ließ sich nicht öffnen ({error}).",
    "This PDF is a scan and no text was recognised in it. Type its layers into the box instead.":
        "Dieses PDF ist ein Scan, in dem kein Text erkannt wurde. Geben Sie die Schichten stattdessen in das Feld "
        "ein.",
    "The log behind this link could not be read. Open the link and type its layers into the box.":
        "Das Profil hinter diesem Link ließ sich nicht lesen. Öffnen Sie den Link und geben Sie die Schichten in das "
        "Feld ein.",
    "Reading the log...": "Profil wird gelesen ...",
    "Reads the layer list behind the link (web page or PDF text, a picture by text recognition) and adds it to "
    "'Logs to check' and to the prediction.":
        "Liest das Schichtenverzeichnis hinter dem Link (Webseite oder PDF-Text, ein Bild per Texterkennung) und "
        "übernimmt es in „Zu prüfende Bohrprofile“ und in die Prognose.",
    # entering logs by hand
    "One layer per line with the depth first, as Schichtenverzeichnisse are written: '0,40 - 6,50 m Sand, kiesig' "
    "or 'bis 6,50 m Sand'. Descriptions in words or SEP 3 codes.":
        "Eine Schicht je Zeile, die Tiefe zuerst, wie in Schichtenverzeichnissen: „0,40 - 6,50 m Sand, kiesig“ oder "
        "„bis 6,50 m Sand“. Beschreibung in Worten oder als SEP-3-Kürzel.",
    "Or a file of the log: PDF, picture or screenshot, text":
        "Oder eine Datei des Profils: PDF, Bild oder Bildschirmfoto, Text",
    "PDFs with a text layer are read directly; pictures, screenshots and scanned PDFs by text recognition "
    "(Tesseract, open source). Every log goes into a table to check before it is used.":
        "PDFs mit Textebene werden direkt gelesen, Bilder, Bildschirmfotos und gescannte PDFs per Texterkennung "
        "(Tesseract, Open Source). Jedes Profil kommt vor der Verwendung in eine Tabelle zur Prüfung.",
    "Type a log into a table": "Profil in Tabelle eingeben",
    "Adds an empty log at the position above (or at the site). Type the bottom depth and the description or SEP 3 "
    "code of each layer; the rock is recognised from the description.":
        "Legt ein leeres Profil an der Position oben an (oder am Standort). Geben Sie je Schicht die Unterkante und "
        "die Beschreibung oder das SEP-3-Kürzel ein; das Gestein wird aus der Beschreibung erkannt.",
    "Log {n}": "Profil {n}",
    "typed in": "eingegeben",
    "Logs to check ({n})": "Zu prüfende Bohrprofile ({n})",
    "Read automatically, from files or typed in. Check the depths and rocks against the log; an empty rock is "
    "recognised from the description. The logs are used in the prediction.":
        "Automatisch gelesen, aus Dateien oder eingegeben. Prüfen Sie Tiefen und Gesteine am Original; ein leeres "
        "Gestein wird aus der Beschreibung erkannt. Die Profile gehen in die Prognose ein.",
    "Opens the log entry above, placed at this borehole: paste, upload a screenshot, or type the layers.":
        "Öffnet die Profileingabe oben, an dieser Bohrung verortet: Text einfügen, Bildschirmfoto hochladen oder "
        "Schichten eingeben.",
    # state overview
    "Connected: boreholes with a picture of the log sheet; the app reads the nearest sheets by text recognition.":
        "Angebunden: Bohrungen mit Bild des Profilblatts; die App liest die nächstgelegenen Blätter per "
        "Texterkennung.",
    "Connected: boreholes with the log column; the app reads the nearest columns from their PDF.":
        "Angebunden: Bohrungen mit Säulenprofil; die App liest die nächstgelegenen Profile aus deren PDF.",
    "Connected: boreholes with a link to the released log (the log viewer only answers from German networks, so "
    "open it yourself).":
        "Angebunden: Bohrungen mit Link zum freigegebenen Schichtenverzeichnis (der Profilbetrachter antwortet nur "
        "aus deutschen Netzen; bitte selbst öffnen).",
}
