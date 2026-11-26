# FM27 Face Generator

🇬🇧 *English version: [README.md](README.md)*

Erzeugt **realistische Spielergesichter für Football Manager 27** im passenden Format
(**250 × 250 px, PNG**), z. B. für deine neuen Jugendspieler. Die Bilder ziehst du anschließend
mit der Mod **FaceDrop** einfach auf den Spieler im Spiel.

**Funktionen im Überblick**

- **Geburtsland** (alle 211 FIFA-Länder) und **Ethnie** – automatisch passend zum Land oder fest eingestellt
- **Doppelte Herkunft**, z. B. „geboren in Deutschland, Eltern aus Ghana“ oder „ein Elternteil aus Marokko“
- **Alter** (auch als Bereich), **Geschlecht**, Haarfarbe, Frisur, Bart, Ausdruck, Kleidung/Farbe, Hintergrund
- **Spielerliste aus FM importieren** – für jeden Jugendspieler automatisch ein passendes Bild mit seinem Namen
- **Persönlichkeit** aus FM (z. B. Söldner → Halstattoo & Goldkette, Musterprofi → gepflegt & konzentriert)
- **Alterungs-Set** – dasselbe Gesicht mit 16, 20, 25, 30 … Jahren
- **Speicherort frei wählbar**, inkl. automatischer Suche nach deinem FM-Ordner
- **FM-Cut-out-Stil** wie bei echten Facepacks: Kopf füllt das Bild, Hintergrund per KI **transparent freigestellt**
- Galerie mit „Neu würfeln“, „Löschen“, „Im Ordner zeigen“; Protokoll `generiert.csv`
- **Bereits erstellte Bilder wieder laden** – z. B. um Jahre später ein Alterungs-Set zu erstellen
- **20 Sprachen** – alle Sprachen von FM27 (außer Arabisch); alle Übersetzungen außer Deutsch sind KI-erstellt

---

## Installation (Schritt für Schritt)

Du brauchst **Windows 10 oder 11** und eine **Internetverbindung** (für die kostenlose Online-Bild-KI).
Python oder andere Programme musst du **nicht** installieren.

### 1. Programm herunterladen

**Variante A – Release (am einfachsten, falls vorhanden):**
1. Auf der GitHub-Seite dieses Projekts rechts auf **Releases** klicken.
2. Beim neuesten Release die Datei **`FM27-FaceGenerator-win.zip`** herunterladen.

**Variante B – aus dem automatischen Build:**
1. Auf GitHub angemeldet sein (Downloads aus „Actions“ gehen nur mit Konto).
2. Oben auf den Reiter **Actions** klicken → links **„Windows-EXE bauen“** wählen.
3. Den obersten Lauf mit grünem Haken ✅ öffnen.
4. Ganz unten bei **Artifacts** auf **FM27-FaceGenerator-windows** klicken → eine ZIP-Datei wird geladen.

### 2. Entpacken

1. Die ZIP-Datei im Download-Ordner mit **Rechtsklick → „Alle extrahieren…“** entpacken.
2. Den entpackten Ordner an einen festen Ort verschieben, z. B. `C:\Programme (eigene)\FM27 Face Generator`
   oder einfach auf den Desktop. (Nicht direkt aus der ZIP heraus starten!)
3. Im Ordner **„FM27 Face Generator“** liegen: `FM27-FaceGenerator.exe`, der Unterordner `_internal`
   (gehört zum Programm – nicht löschen oder verschieben!), diese Anleitung (`LIESMICH.md`, Deutsch), die englische
   `README.md`, die PatchNotes und `laender.beispiel.json`. Immer den **ganzen Ordner** zusammen lassen.

### 3. Erster Start

1. **Doppelklick** auf `FM27-FaceGenerator.exe`. Der Generator startet nach wenigen Sekunden im Vordergrund.
2. Erscheint **„Der Computer wurde durch Windows geschützt“** (SmartScreen):
   auf **„Weitere Informationen“** → **„Trotzdem ausführen“** klicken.
   Das passiert, weil das Programm nicht kostenpflichtig signiert ist.
3. Meldet sich der **Virenscanner**: Manche Scanner reagieren auf selbstentpackende Programme
   (PyInstaller). Die EXE wird automatisch und öffentlich nachvollziehbar aus diesem Quellcode gebaut.
4. Es erscheint ein kleines Fenster zur **Sprachauswahl** (Standard: Deutsch). Sprache wählen, **OK** klicken.
   Mit dem Häkchen **„Beim Start nicht mehr fragen“** kommt das Fenster künftig nicht mehr.
5. Optional: Rechtsklick auf die EXE → **„Senden an“ → „Desktop (Verknüpfung erstellen)“**.

### 4. Speicherort einstellen

Unten im Fenster bei **„Speichern in:“**:

- **„FM-Ordner suchen“** – findet automatisch `Dokumente\Sports Interactive\Football Manager …`
  (oder deinen eigenen FM-Benutzerordner, falls du ihn per Steam-Startoption `user_data_location="…"` verlegt hast)
  und schlägt `…\graphics\faces\FM27 Face Generator` vor (mit „Nein“ wählst du selbst einen Ordner innerhalb des FM-Verzeichnisses).
- **„Ordner wählen…“** – beliebigen Ordner auswählen.
- **„Öffnen“** – öffnet den Ordner im Explorer.

Der Speicherort und alle anderen Einstellungen werden automatisch gemerkt.

> **Tipp:** Da du die Bilder mit FaceDrop ins Spiel ziehst, kann der Ordner prinzipiell überall liegen.
> Ein eigener Unterordner (z. B. `FM27 Faces`) hält aber Ordnung.

### Updates

Gibt es eine neue Version, erscheint beim Start ein Hinweis:

- **„Jetzt aktualisieren“** lädt die neue Version herunter, tauscht das Programm im Ordner aus und startet
  den Generator neu – fertig. Deine Einstellungen und eigene Dateien wie `laender.json` bleiben erhalten. (Geht nur, wenn der Programmordner beschreibbar ist, also z. B. nicht unter
  `C:\Programme`. Dann fehlt der Button und es bleibt der Weg über die Download-Seite.)
- **„Download-Seite öffnen“** öffnet die Seite im Browser.
- **„Nein, will zocken“** schließt das Fenster.

 Mit **„Diese Version nicht mehr anzeigen“** wird genau diese
Version nicht mehr gemeldet – die nächste neuere aber wieder. (Ausschalten: Tab **Ausgabe** → „Beim Start nach
Updates suchen“. Gesendet wird dabei nur eine Anfrage an GitHub, keine persönlichen Daten.)

Von Hand: neue Version herunterladen, entpacken und den Inhalt des Ordners „FM27 Face Generator“ über den
alten Programmordner kopieren (oder den alten Ordner durch den neuen ersetzen).

> **Einmalig beim Wechsel von 1.8.7.1 oder älter auf 1.8.7.2+:** Ab 1.8.7.2 ist der Generator ein Programmordner
> (EXE + `_internal`) statt einer einzelnen EXE – dadurch startet er viel schneller. Diesen einen Wechsel bitte
> **von Hand** machen: neue ZIP laden, entpacken, alte `FM27-FaceGenerator.exe` löschen und den neuen Ordner
> nutzen. Ab dann klappt „Jetzt aktualisieren“ wieder automatisch.
Was sich geändert hat, steht in `PatchNotes_DE.txt`.

**Testschalter:** Mit **„Auch Testversionen“** (Tab **Ausgabe**, neben „Beim Start nach Updates suchen“) meldet der
Update-Hinweis auch Testversionen (Pre-Releases). Normalerweise ausgeschaltet lassen.
Deine Einstellungen bleiben erhalten (gespeichert unter `%APPDATA%\FM27FaceGenerator`).

### Deinstallation

Programmordner löschen. Optional auch `%APPDATA%\FM27FaceGenerator` (Einstellungen und Freistell-Modell) löschen.

### Sprache ändern

Jederzeit unten rechts über den Button **„Sprache: …“**. Die Oberfläche wird sofort umgestellt –
Einstellungen, Galerie und geladene Spielerliste bleiben erhalten.

Verfügbar: Deutsch, English, Español (España), Español (Latinoamérica), Français, Italiano, Nederlands, Dansk, Norsk, Svenska, Polski, Português (Brasil), Português (Portugal), Русский, Türkçe, Ελληνικά, Bahasa Indonesia, 日本語, 한국어, 简体中文.

> **Hinweis:** Alle Übersetzungen außer Deutsch wurden mit KI erstellt und sind in der Sprachauswahl so
> gekennzeichnet (z. B. „Nederlands (AI-vertaald)“). Verbesserungsvorschläge sind willkommen.
Auch Länder, Haarfarben, Persönlichkeiten usw. werden übersetzt. Persönlichkeiten zeigen in den
übrigen Sprachen zusätzlich den englischen FM-Namen, z. B. „Mercenario (Mercenary)“.

---

## Benutzung

### Einzelne Bilder / ganzer Jahrgang

1. Tab **Spieler**: **Geburtsland** wählen (Tippen filtert die Liste), Alter einstellen (Standard 15–17).
2. Optional im Tab **Aussehen** Details festlegen, z. B. Shirt in Vereinsfarben.
3. Unten **Anzahl** eintragen und **„Bilder generieren“** klicken.
4. Gefällt ein Bild nicht: in der Galerie anklicken → **„Neu würfeln“** (ersetzt die Datei).
5. Im Spiel das passende PNG per FaceDrop auf den Spieler ziehen – **direkt aus der Galerie** (Vorschaubild
   oder großes Bild mit der Maus ins FM-Fenster ziehen) oder wie bisher aus dem Ordner.

### Die Tabs „Neu erstellt“ und „Galerie“

- **Neu erstellt**: die Bilder dieser Sitzung (und alles, was du über „Bilder laden…“ holst) – neueste zuerst.
- **Galerie**: **alle Bilder aus deinem Speicherort** (inkl. Unterordner je Land), neueste zuerst. Mit dem
  **Suchfeld** filterst du nach Dateinamen – z. B. `Söldner`, `Niederlande` oder `16J`. Von hier aus kannst du
  genauso ziehen, umbenennen, löschen und **direkt ein Alterungs-Set starten**. „Aktualisieren“ liest den Ordner neu ein.

**Dateinamen**: Standard ist jetzt `Land_AlterJ_Persönlichkeit_ID`, z. B. `Niederlande_16J_Sehr-ehrgeizig_2106529392.png`
(ohne Persönlichkeit: `Niederlande_16J_2106529392.png`). Lässt du z. B. 4 Bilder erstellen und brauchst nur eins,
erkennst du die übrigen später am Namen wieder. Anpassbar im Tab **Ausgabe** → „Dateiname“.

### Galerie: ziehen, umbenennen, löschen

- **Ziehen**: Bild mit gedrückter linker Maustaste aus der Galerie in ein anderes Programm ziehen
  (FM mit FaceDrop, Explorer …). Mehrere markierte Bilder werden zusammen gezogen.
  FM muss dafür im **Fenstermodus** laufen. Startet eines der Programme „als Administrator“ und das andere nicht,
  blockiert Windows das Ziehen – dann beide gleich starten.
- **Mehrere auswählen**: **Strg + Klick** (einzeln dazu/weg) oder **Shift + Klick** (Bereich).
- **Umbenennen**: Button **„Umbenennen (F2)“** oder Taste **F2** – z. B. in den Spielernamen. Das Alterungs-Set
  funktioniert danach weiter (die Infos stecken in der Datei).
- **Löschen**: Button **„Löschen“** oder Taste **Entf** – nach Rückfrage landen die Bilder im **Papierkorb**
  (wiederherstellbar).
- **Kopieren**: Button **„Kopieren (Strg+C)“** oder **Strg+C** – kopiert die Bilddatei wie im Explorer.
  In FM dann Maus aufs Porträt und **Strg+V** (FaceDrop). Praktisch, wenn Ziehen nicht geht (z. B. Vollbild).

### Zusammenarbeit mit FaceDrop

Der Generator erkennt FaceDrop automatisch – auch wenn dein FM-Benutzerordner per Steam-Startoption
(`user_data_location="…"`) woanders liegt. Gibt es mehrere FaceDrop-Ordner (z. B. alter Ort als Sicherung nach
einem Umzug), nimmt er den, den FaceDrop zuletzt benutzt hat. Anzeige und Einstellungen: Tab **Ausgabe** → **FaceDrop**
(„Ordner wählen …“ falls nötig, „Automatisch suchen“ setzt das zurück).

> **Wichtig:** In FaceDrops Ordnern wird **nie etwas verändert** – dort wird nur gelesen.

- **Galerie → Zeigen: Speicherort | FaceDrop**: Mit „FaceDrop“ siehst du die Bilder, die schon **im Spiel** sind –
  je **Karriere** (Spielstand) oder „Echte Spieler“. **„Öffnen“** neben der Karriere-Auswahl öffnet den
  passenden Ordner im Explorer (zum Entfernen im Spiel besser: Maus aufs Porträt + Strg+Entf). Angezeigt wird auch die **Spieler-ID**. Diese Bilder lassen
  sich ansehen, kopieren, ziehen und für ein **Alterungs-Set** nutzen (die neuen Bilder landen im Speicherort),
  aber nicht umbenennen, löschen oder neu würfeln.
- **✓ im Spiel**: Eigene Bilder, die FaceDrop schon übernommen hat, bekommen in der Galerie des Generators einen
  grünen Haken (sichtbar, solange du deine Kopie behältst – also bei „Nein“ beim Aufräumen oder Einstellung „Aus“).
- **Doppelte Bilder aufräumen**: Legst du ein Bild per FaceDrop auf einen Spieler, kopiert FaceDrop es in seinen
  Ordner – es liegt dann doppelt auf der Platte. Der Generator merkt das (beim Start und laufend) und fragt, ob
  **deine** Kopie in den Papierkorb soll. FaceDrops Kopie bleibt, im Spiel ändert sich nichts. Einstellbar unter
  **Ausgabe → FaceDrop → Doppelte Bilder**: *Nachfragen* (Standard), *Automatisch aufräumen* oder *Aus*.
  Angefasst werden nur Bilder, die der Generator selbst erstellt hat.

### Doppelte Herkunft (Eltern aus einem anderen Land)

Im Tab **Spieler** bei **„Herkunft Eltern“** ein zweites Land wählen und bei **„Eltern“** festlegen:

| Einstellung | Ergebnis | Beispiel |
|---|---|---|
| **Beide Eltern aus diesem Land** | Aussehen wie im Herkunftsland der Eltern | geboren in Deutschland, Eltern aus Ghana |
| **Ein Elternteil (gemischt)** | Gemischte Herkunft aus beiden Ländern | Vater Franzose, Mutter Marokkanerin |
| **Zufällig** | je Bild eins von beidem | für einen bunten Jahrgang |

Die Verteilung wird direkt unter der Auswahl angezeigt. „—“ bedeutet: keine zweite Herkunft.

### Spielerliste aus Football Manager importieren

So bekommt jeder deiner Jugendspieler automatisch ein passendes Gesicht – mit seinem Namen als Dateiname.

**In Football Manager exportieren:**
1. Die Spielerliste öffnen (z. B. Jugendmannschaft oder Jugendspieler-Vorschau).
2. Die Ansicht so anpassen, dass mindestens die Spalten **Name**, **Nat** (Nationalität) und **Alter**
   sichtbar sind. Optional: **2. Nationalität**, **Persönlichkeit** und **UID** (Eindeutige ID).
3. Alle Spieler markieren (**Strg + A**), dann **Strg + P** („Bildschirm drucken“).
4. **Webseite** (`.html`) oder **Textdatei** (`.txt`) wählen und speichern.

**Im Generator:**
1. Rechts den Tab **„Spielerliste (FM-Import)“** öffnen → **„Liste laden…“** → Datei wählen.
2. Prüfen: Spieler mit **orangem** Land wurden nicht erkannt – markieren und unten bei „Land … setzen“ korrigieren.
3. **Dateiname** wählen: `Name` (z. B. `Jonas Müller.png`), `UID` oder `Name_UID`.
4. **„Bei 2. Nationalität“** legt fest, wie Spieler mit zwei Nationalitäten aussehen (siehe Tabelle oben).
5. **„Für alle generieren“** (oder „Für Auswahl“ / „Nur ohne Bild“). Der Status zeigt ✓ und den Dateinamen.
   Doppelklick auf einen Spieler öffnet sein Bild.

Alter, Land, 2. Nationalität und Persönlichkeit kommen aus der Liste; Geschlecht, Aussehen und Hintergrund aus
den Einstellungen links. Spieler ohne Persönlichkeit in der Liste bekommen die Einstellung aus dem Abschnitt „Persönlichkeit“ im Tab **Spieler**.
Unter der Liste kannst du Land, 2. Land und Persönlichkeit für markierte Spieler nachträglich ändern.
Eine eigene CSV-Datei (z. B. aus Excel) geht auch – Kopfzeile z. B. `Name;Nation;Alter;2. Nation;Persönlichkeit;UID`.

**FM in einer anderen Sprache?** Meist kein Problem: Spaltennamen (z. B. *Nome/Età/Nazionalità*, *Nom/Âge*, *名前/年齢/国籍*),
Ländernamen (z. B. *Germania*, *Allemagne*, *ドイツ*, *독일*) und Persönlichkeiten werden in den Sprachen erkannt –
ebenso die üblichen FIFA-Kürzel wie `GER`, `FRA`, `JPN`. Bei den mit 1.8.7.1 dazugekommenen Sprachen (Niederländisch,
Dänisch, Norwegisch, Schwedisch, Polnisch, Russisch, Türkisch, Griechisch, Indonesisch, Chinesisch) sind die
Spaltennamen geschätzt und noch nicht mit echten FM-Exporten geprüft – klappt es nicht, im Zweifel FM für den Export
kurz auf Englisch stellen.

### Persönlichkeit

Im Tab **Spieler** unter der Überschrift **Persönlichkeit** wählst du eine der 40 FM-Persönlichkeiten – mit den offiziellen deutschen Namen
(Quelle: fm.zweierkette.de) und dem englischen Namen in Klammern. Beim Import werden beide Sprachen erkannt,
auch ältere Namen wie „Ausgeglichen“ (heute „Ausgewogen“) oder „Unbeständig“ (heute „Opportunist“).
Sie bestimmt den **Gesichtsausdruck** und fügt passende **Merkmale** hinzu, zum Beispiel:

| Persönlichkeit | Typische Merkmale |
|---|---|
| Söldner | Halstattoo, Goldkette, Diamant-Ohrstecker, Designer-Haarschnitt, selbstgefälliges Grinsen |
| Musterprofi / Modellbürger | gepflegt, ordentliche Frisur, kein Schmuck, ruhig-konzentriert bzw. freundlich |
| Perfektionist | perfekt gestylt, gezupfte Augenbrauen, intensiver Blick |
| Natürliche Autorität / Charismatischer Führer | selbstbewusste Haltung, souveräner Blick |
| Temperamentvoll / Unsportlich | gerunzelte Stirn, Narbe, finsterer Blick, ggf. Tattoo |
| Lässig / Nachlässig | zerzauste Haare, müder Blick, zerknittertes Shirt |
| Frohnatur / Unbeschwert | breites, herzliches Lächeln |
| Geringes Selbstvertrauen | schüchterner, unsicherer Ausdruck |

- **Ausprägung**: Dezent (1 Merkmal), Normal (2), Deutlich (3) – welche Merkmale es werden, wird je Bild ausgewürfelt.
- **Tattoos ab**: Mindestalter für Tattoos (Standard 16). Jüngere bekommen stattdessen z. B. Ohrstecker oder Kette.
- **Zufällig**: jedes Bild bekommt eine zufällige Persönlichkeit.
- Die Merkmale aller Persönlichkeiten werden im Tab angezeigt, sobald du eine auswählst.

### Alterungs-Set (dasselbe Gesicht in verschiedenen Altern)

1. In der Galerie ein oder **mehrere Bilder markieren** (Strg/Shift + Klick, **„Alle markieren“** oder **Strg+A**).
2. Unter der Galerie bei **„Alterungs-Set“** entweder feste Alter eintragen, z. B. `16, 20, 25, 30, 34`
   (Bereiche wie `25-28` gehen auch) – **oder** im Pfeilfeld **„oder älter um … Jahre“** z. B. `4` wählen:
   Dann wird jedes markierte Bild um 4 Jahre älter, egal wie alt es vorher war (die feste Liste wird ausgegraut).
3. **„Erstellen“** klicken. Im Dateinamen wird das Alter mitgeändert: aus `Deutschland_16J_Ehrgeizig_123.png`
   wird `Deutschland_20J_Ehrgeizig_123.png`. Steht kein Alter im Namen (z. B. umbenannt), wird `_20J` angehängt.

### Im Spiel ersetzen, Saison und Rückgängig (Galerie → FaceDrop)

- **„Im Spiel ersetzen“** anhaken: Das neue Bild bekommt den FaceDrop-Namen (z. B. `newgen_2002044702.png`) und
  ersetzt das Bild im Spiel – FM zeigt es sofort. Werden mehrere Alter erzeugt, kommt das **niedrigste** ins Spiel,
  die übrigen landen im Speicherort.
- Die alten Bilder werden vorher gesichert: **Speicherort\Sicherungskopie\<Datum Uhrzeit>\<Karriere>\**.
- Alle neuen Bilder entstehen zuerst in einer Warteschlange und werden erst **am Ende in einem Rutsch** ins Spiel
  geschoben. Es gibt **nur eine Rückfrage am Anfang** – danach läuft alles durch (ideal über Nacht). Schlägt ein
  Bild fehl, wird es noch einmal versucht und sonst übersprungen; am Ende kommt eine Zusammenfassung.
- **„Saison: Karriere +1 Jahr“**: alle Spieler der gewählten Karriere um 1 Jahr altern lassen und ersetzen.
- **„Letzte Ersetzung rückgängig“** holt die gesicherten Bilder zurück.
- Unten steht die **Restzeit** („noch ca. 9 Min.“) und am Ende die Durchschnittszeit pro Bild.
- Nur mit **lokalem Stable Diffusion (Forge)** – online wäre es zu langsam und sähe künstlicher aus.

Herkunft, Haare, Kleidung, Persönlichkeit usw. bleiben gleich; ab Mitte 20 kommen reifere Gesichtszüge, ab Anfang 30
feine Falten und später graue Schläfen dazu.

**Alterungs-Set für ältere Bilder (nachträglich):** Oben rechts in der Galerie auf **„Bilder laden…“** klicken
und bereits erstellte Bilder auswählen (Mehrfachauswahl mit Strg/Shift). Danach wie oben ein Bild auswählen und
„Erstellen“ klicken. Die neuen Bilder landen im selben Ordner wie das geladene Bild.

| Bild | Was passiert |
|---|---|
| Ab **Version 1.7** erstellt | Alle Infos stecken unsichtbar in der PNG-Datei – das Alterungs-Set trifft exakt dieselbe Person. FM und FaceDrop stört das nicht. |
| Mit einer **älteren Version** erstellt | Die Infos (Seed, Beschreibung) kommen aus der `generiert.csv` im selben Ordner – nur das Alter wird ausgetauscht. |
| **Fremdes Bild** ohne Infos | Nur mit **lokalem Stable Diffusion** möglich: Das Bild selbst dient als Vorlage, Beschreibung aus den aktuellen Einstellungen. |

Tipp: Lass die `generiert.csv` im Bilderordner liegen – sie ist das „Gedächtnis“ für ältere Bilder.

> **Ehrlicher Hinweis:** Mit der **Online-KI** sieht die Person in jedem Alter *ähnlich* aus, ist aber nicht
> immer exakt dieselbe. Mit **lokalem Stable Diffusion** wird das Ausgangsbild als Vorlage verwendet
> (Bild-zu-Bild) – das Gesicht bleibt dann deutlich besser erhalten.

---

## Welche Bild-KI wird verwendet?

Die Gesichter erzeugt eine Bild-KI; das Programm schneidet sie danach zu und skaliert auf 250 × 250 px.
Auswahl im Tab **KI**:

| Option | Vorteile | Nachteile |
|---|---|---|
| **Pollinations (online, kostenlos)** – Standard | Kein Konto, keine Grafikkarte nötig, sofort startklar | Internet nötig, ohne Key nur **1 Bild alle 45 Sekunden** |
| **Lokal: Stable Diffusion WebUI** (AUTOMATIC1111 / Forge) | Offline, kein Limit, beste Qualität mit Fotorealismus-Modellen, bessere Alterungs-Sets | Eigene Installation + NVIDIA-Grafikkarte (ab ca. 6–8 GB VRAM) |

**Pollinations ohne Key:** Erlaubt ist 1 Bild alle 45 Sekunden. Das Programm hält das automatisch ein und
zeigt unten die Wartezeit an („Gratis-Limit … noch 30 s“). 20 Bilder dauern so etwa 15 Minuten – einfach laufen lassen.
Das Wasserzeichen „pollinations.ai“, das ohne Key unten rechts ins Bild kommt, schneidet das Programm automatisch weg.

**Schneller mit Key:** Unter *enter.pollinations.ai* einen Key holen (die Bilder kosten dann etwas Guthaben)
und im Tab *KI* bei „API-Key“ eintragen.
Dann entfallen Wartezeit und Wasserzeichen.

**Lokal:** siehe nächster Abschnitt.

---

## Lokales Stable Diffusion einrichten (kostenlos, unbegrenzt, beste Qualität)

Läuft komplett auf deinem PC: kein Internet nötig, keine Wartezeit, kein Wasserzeichen, keine Kosten außer Strom.
Das Alterungs-Set klappt damit deutlich besser (das Gesicht bleibt erkennbar dieselbe Person).

**Voraussetzung:** NVIDIA-Grafikkarte mit mindestens 6 GB Grafikspeicher (empfohlen 8 GB+), ca. 25 GB freier Speicher.
Eine RTX 3060 / 4060 oder besser ist ideal – z. B. eine **RTX 4080 Laptop GPU (12 GB)** schafft ein Bild in ca. 5–10 Sekunden.

> Windows zeigt bei großen Grafikkarten unter „Adapter-RAM“ manchmal einen falschen Wert (z. B. 1.048.576 Bytes) an –
> das ist ein bekannter Anzeigefehler und kein Problem.

### Schritt 1 – Grafikkartentreiber aktualisieren
Über die **NVIDIA App** (oder nvidia.de → Treiber) den aktuellen Treiber installieren. Danach neu starten.

### Schritt 2 – Stable Diffusion WebUI Forge herunterladen
1. Die GitHub-Seite **„lllyasviel/stable-diffusion-webui-forge“** öffnen.
2. Im Abschnitt **„Installing Forge“** (bzw. unter *Releases*) **ein** One-Click-Paket herunterladen –
   empfohlen: **`webui_forge_cu121_torch231.7z`** (ca. 1,7 GB, Python ist schon enthalten).
   Die anderen Varianten brauchst du nicht.
   > **Download bleibt bei „1,7 GB von 1,7 GB“ / „Nicht bestätigt … .crdownload“ hängen?**
   > Die Datei ist vollständig, Chrome wartet nur auf deine Bestätigung: In Chrome **Strg + J** drücken
   > und beim Download auf **„Behalten“** bzw. **„Trotzdem herunterladen“** klicken. Ggf. auch kurz warten,
   > bis der Virenscanner fertig ist. Danach heißt die Datei richtig `webui_forge_….7z`.
3. Mit **7-Zip** (kostenlos, 7-zip.org) entpacken – am besten in einen kurzen Pfad **ohne Leerzeichen**,
   z. B. `C:\AI\Forge`. Nicht in „Programme“ oder auf den Desktop.

### Schritt 3 – Einmalig einrichten
1. Im Forge-Ordner **`update.bat`** doppelklicken und warten, bis sich das Fenster schließt.
2. **`run.bat`** doppelklicken. Der erste Start dauert **10–20 Minuten** (lädt Pakete und ein Standardmodell).
   Fertig ist es, wenn sich der Browser mit der Forge-Oberfläche öffnet bzw. im schwarzen Fenster
   `Running on local URL: http://127.0.0.1:7860` steht.
3. Forge wieder schließen (schwarzes Fenster schließen).

### Schritt 4 – Schnittstelle für den Generator einschalten
1. Im Forge-Ordner den Unterordner **`webui`** öffnen.
2. **Rechtsklick auf `webui-user.bat` → „Bearbeiten“** (öffnet den Editor).
3. Die Zeile `set COMMANDLINE_ARGS=` ändern in:
   ```
   set COMMANDLINE_ARGS=--api
   ```
4. Speichern und schließen.

### Schritt 5 – Fotorealistisches Modell laden
Das mitgelieferte Standardmodell erzeugt eher künstliche Gesichter. Viel besser für echte Spielerfotos ist **RealVisXL**:
1. Auf **civitai.com** (kostenloses Konto) oder **huggingface.co** nach **„RealVisXL V5.0“** suchen.
2. Die Datei `RealVisXL_V5.0…safetensors` herunterladen (ca. 6,5 GB).
3. In den Ordner **`webui\models\Stable-diffusion`** im Forge-Verzeichnis legen.

Alternativen mit ähnlich guten Ergebnissen: „Juggernaut XL“, „epiCRealism XL“.

**Normal oder „Lightning“?** Beide Varianten von RealVisXL funktionieren. *Lightning* ist ca. 5× schneller
(nur ~6 Schritte), die normale Version etwas detailreicher. Der Generator erkennt Lightning-/Turbo-Modelle
automatisch und verwendet dann passende Werte (6 Schritte, CFG 1,5, Sampler DPM++ SDE Karras) –
du musst nichts umstellen.

### Schritt 6 – Starten und verbinden
1. **`run.bat`** starten und warten, bis die Forge-Oberfläche im Browser erscheint.
2. In Forge im Tab **„Txt2img“** ganz oben in der Leiste bei **„UI“** auf **„xl“** stellen und bei
   **„Checkpoint“** das Modell **RealVisXL** auswählen (einmalig, wird gemerkt).
   Die Tabs „Checkpoint-Fusion“, „Img2img“, „Extras“ usw. brauchst du nicht.
3. Im FM27 Face Generator: Tab **KI** → Bild-KI **„Lokal: Stable Diffusion WebUI“** wählen.
   Größe 1024 px und „keine Pause“ werden automatisch eingestellt.
4. **„Verbindung testen“** klicken – es sollte „Verbindung OK“ und das Modell RealVisXL erscheinen.
5. Bilder generieren wie gewohnt. Forge (schwarzes Fenster) muss dabei geöffnet bleiben.

**Empfohlene Werte** (sind voreingestellt): Generier-Größe 1024, Schritte 30, CFG 5
(bei Lightning-Modellen automatisch 6 Schritte, CFG 1,5).

| Problem | Lösung |
|---|---|
| „Keine Verbindung zu http://127.0.0.1:7860“ | Forge läuft nicht – `run.bat` starten und warten, bis die Oberfläche erscheint |
| „Die Schnittstelle (API) ist aus“ | Schritt 4: `--api` in `webui\webui-user.bat` eintragen, Forge neu starten |
| Gesichter wirken künstlich/gemalt | In Forge oben links das Modell RealVisXL auswählen (Schritt 5/6) |
| Fehler „out of memory“ | Generier-Größe auf 768 stellen oder andere Programme (Spiele!) schließen |
| Laptop: sehr langsam | Laptop ans Netzteil, Windows-Energiemodus „Beste Leistung“ |

Tipp: Football Manager und Forge gleichzeitig laufen zu lassen geht, aber Bilder lieber vorab erzeugen –
beide brauchen Grafikspeicher.

### Forge automatisch mit dem Generator starten

Tab **KI** → bei **„Forge-Ordner“** auf **„…“** klicken und den Forge-Hauptordner wählen (dort liegen `run.bat`
und `update.bat`, z. B. `C:\AI\Forge`). Dann **„Forge mit dem Generator starten und beenden“** anhaken.

- Ab dem nächsten Start läuft Forge **unsichtbar im Hintergrund** hoch (unten steht „Forge startet …“,
  meist 30–90 Sekunden), ohne dass sich ein Browserfenster öffnet.
- Beim **Schließen des Generators** wird Forge wieder beendet – aber nur, wenn der Generator es selbst
  gestartet hat. Lief Forge schon vorher, bleibt es an.
- Mit **„Jetzt starten“** startet Forge sofort, ohne Neustart des Generators.
- Läuft etwas schief, steht das Protokoll von Forge in `%APPDATA%\FM27FaceGenerator\forge.log`.

---

## Eigene Länder / Verteilungen anpassen

Die Ethnien-Verteilungen pro Land sind grobe Näherungen. Anpassen oder ergänzen:
`laender.beispiel.json` in **`laender.json`** umbenennen, **neben die EXE** legen und bearbeiten (z. B. mit dem Editor).

```json
{
  "Färöer": { "en": "Faroe Islands", "mix": { "EUR_N": 100 } }
}
```

Ethnien-Kürzel: `EUR_N` (Nordeuropa), `EUR_W` (West-/Mitteleuropa), `EUR_S` (Südeuropa), `EUR_E` (Osteuropa),
`BALKAN`, `CAUCASUS`, `MIDEAST`, `AFR_N` (Nordafrika), `AFR_W` (Westafrika), `AFR_C` (Zentral-/Südafrika),
`AFR_E` (Ostafrika), `AFRO_DIA` (afrokaribisch/-amerikanisch), `LAT` (Lateinamerika), `INDIG` (indigen),
`ASIA_E`, `ASIA_SE`, `ASIA_S`, `ASIA_C`, `PACIFIC`, `MIXED`.

Länder, die das Programm nicht kennt, funktionieren trotzdem – dann entscheidet die KI allein anhand des Ländernamens.

---

## Bedienung per Tastatur

- **Länder- und Persönlichkeitsfelder**: ins Feld klicken und tippen (z. B. `Elf` oder `söl`) – die Liste öffnet sich gefiltert und der beste Treffer ist markiert (Elfenbeinküste). **↑/↓** wählt in der Liste, **Enter** übernimmt, **Esc** schließt.
- **Alle anderen Auswahlfelder**: anklicken und tippen – die Liste öffnet sich und springt zum passenden Eintrag (z. B. `bl` → Blond), **Enter** übernimmt.
- **Galerie**: **F2** = umbenennen, **Entf** = in den Papierkorb, **Strg+C** = Bild kopieren (in FM: Strg+V), **Strg/Shift + Klick** = mehrere auswählen.

## Trikot in Vereinsfarben

Tab **Aussehen**: **Kleidung** (z. B. „Trikot ohne Logo“), **Shirt-Farbe**, **Muster** (einfarbig, Längsstreifen,
Querstreifen, andersfarbige Ärmel, andersfarbiger Kragen) und **Zweitfarbe** wählen.
Mit **„Vereins-Vorlage → Speichern…“** merkt sich der Generator die Kombination unter einem Namen
(z. B. „Mein Verein“) – später einfach in der Liste auswählen.

## Tipps für realistische Ergebnisse

- Standard ist **„Transparent (FM-Cut-out)“** – Zuschnitt und Freistellung sind an echten FM-Facepack-Bildern
  ausgerichtet (Kopf füllt das Bild, Haare reichen bis zum oberen Rand, unten Hals und Kragen).
- **Zoom** und **Gesichtshöhe** (Tab Ausgabe) bei Bedarf an deine übrigen Facepack-Bilder anpassen
  (Standard: Zoom 1,6 / Gesichtshöhe 0,56).
- **Trainingsshirt** in Vereinsfarben (Tab Aussehen → Shirt-Farbe) wirkt wie beim Vereins-Fototermin.
- **Hautdetails** aktiviert lassen – leichte Unreinheiten/Sommersprossen wirken weniger „KI-glatt“.
- Im Feld **Zusatz** eigene englische Stichworte ergänzen, z. B. `green eyes, small scar on chin`.

## Problemlösung

**Bilder dauern zu lange (lokal)?** Nach jedem Durchlauf steht unten z. B. „Ø 6,1 s pro Bild (KI 4,9 s,
Nachbearbeitung 1,2 s)“, jede Einzelzeit steht in `%APPDATA%\FM27FaceGenerator\timing.log`. Ist der KI-Anteil hoch:
Laptop ans Netzteil und in den Höchstleistungs-Modus, in Forge ein Lightning-/Turbo-Modell (z. B. RealVisXL
Lightning) aktiv haben, „Generier-Größe“ 1024 oder 896. Die Pause zwischen Bildern gilt nur noch online.

| Problem | Lösung |
|---|---|
| Lange Wartezeit zwischen den Bildern | Normal ohne Key (Gratis-Limit 45 s). Für mehr Tempo: API-Key eintragen (Tab KI) |
| „Pollinations hat die Anfrage abgelehnt“ (HTTP 401/403) | API-Key im Tab KI prüfen bzw. eintragen |
| Merkmale (z. B. Tattoo) fehlen im Bild | Ausprägung „Deutlich“ wählen oder „Neu würfeln“ – die KI setzt nicht jedes Detail jedes Mal um |
| „Lokale Stable-Diffusion-WebUI nicht erreichbar“ | WebUI läuft nicht oder wurde ohne `--api` gestartet; Adresse prüfen |
| Gesicht nicht mittig | Zoom/Gesichtshöhe im Tab Ausgabe anpassen oder „Neu würfeln“ |
| Erstes Bild dauert lange („Einmaliger Download des Freistell-Modells“) | Normal: Beim ersten transparenten Bild wird das KI-Freistellmodell (ca. 170 MB) einmalig geladen und unter `%APPDATA%\FM27FaceGenerator\models` gespeichert |
| Reste vom Hintergrund an Haaren/Rändern | „Neu würfeln“ oder Hintergrund „Weiß“/„Hellgrau“ wählen (dann ohne Freistellung) |
| Spieler in der Liste orange | Land nicht erkannt → markieren und „Land … setzen“ |
| Liste wird nicht erkannt | In FM mindestens die Spalten Name + Nat (oder Alter) einblenden und erneut exportieren |

## Selbst bauen (nur für Bastler)

Python 3.10+ installieren und `build.bat` doppelklicken → Ordner `dist\FM27-FaceGenerator\` (mit der EXE).
Ohne EXE starten: `pip install -r requirements.txt` und `python run.py`.

**Übersetzungen ergänzen/verbessern:** Alle Texte stehen in `fm27facegen/locales.py` (eine Zeile pro Text, die
ersten 8 Sprachen nebeneinander), weitere Sprachen je Datei in `fm27facegen/lang/`, Ländernamen in
`fm27facegen/country_names.py` bzw. `country_names_extra.py`. Ein Test prüft, dass jeder Text in allen
Sprachen mit denselben Platzhaltern vorhanden ist.

## Weitere Ideen

- **Klassisches Facepack-Format**: Dateien als `r-<UID>.png` + automatisch erzeugte `config.xml` (ohne FaceDrop nutzbar).
- **Weitere KI-Anbieter**: ComfyUI (lokal) oder kostenpflichtige Dienste mit sehr hoher Qualität.
- **Stilangleichung**: Farblook/Helligkeit automatisch an ein Referenzbild aus deinem Facepack anpassen.

## Hinweise

- Die Gesichter sind KI-generiert und zeigen keine realen Personen.
- Bei Online-Generierung wird nur die Beschreibung des Gesichts an den Dienst gesendet – keine Spielernamen
  und keine persönlichen Daten.
