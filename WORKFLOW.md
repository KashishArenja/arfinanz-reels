# @arfinanz – Wochen-Workflow (12 Reels + 2 Karussells)

Jeden Montag bis 08:00 (Europe/Berlin) vorbereiten, Kashish gibt frei, dann über Metricool einplanen.

## Quellen
- Clips: Google-Drive-Ordner „01_Clips roh“ – ID `1VrlzH-tNNoF0emWmWnrY0l8vUKsCQeZs` (per Link freigegeben)
  - Liste: Google-Drive-Connector `search_files` mit `parentId = '<ID>'`
  - Download (jede Größe): `curl -sSL "https://drive.usercontent.google.com/download?id=<FILE_ID>&export=download&confirm=t" -o clip.mov`
- Clip-Nutzung: `used_clips.json` (nach dem Einplanen jeden verwendeten Abschnitt eintragen: Datei, start, dur, Datum, Thema, und pushen)
- Metricool-Brand: blogId `7984611` (Instagram @arfinanz, Facebook-Seite verbunden → Sounds möglich), Zeitzone Europe/Berlin

## Reel-Format
- Genau 5,1 s, 1080×1920, stumme Clips (Originalton wird entfernt)
- Bau: `python3 tools/make_reel.py clip.mov spec.json out.mp4` (braucht `pip install --break-system-packages opencv-python-headless`)
  - spec.json: `{"blocks": [["Hook", 62, "white"], ["Auflösung", 58, "blue"], ["Here's how: see caption", 42, "blue"]]}`
  - Hook oben, Rest unten, nie über Gesichtern (YuNet-Erkennung), immer in der Safe Zone (oben 250 px, unten ab 1440 px, rechts 230 px frei)
  - Danach `out_check.jpg` ansehen: Gesichter frei? Text lesbar?
- Text: Englisch, max. ~18 Wörter gesamt, Hook im POV-Stil, leicht verständlich, keine unerklärten Fachbegriffe
- Thema passend zum Clip wählen (z. B. Dachboden → Ausbau/Wertsteigerung, Auto → Kfz-Versicherung, Telefonat → Finanzierungszusage)
- Keine erfundenen Kundenfälle: Beispielrechnungen als Beispiel kennzeichnen („can be enough“, nicht „this couple did it“), außer Kashish bestätigt einen echten Fall

## Vergleichs-Reels (Clips mit beiden Personen)
- Bei Clips mit zwei Personen gern Vergleiche: über jedem Kopf ein Label, z. B. India / Germany, Renter / Owner, Poor / Rich, Employee / Self-employed, Bank / Broker, Single / Married.
- spec.json: `"labels": ["India", "Germany"]` (links → rechts). Hook + Hinweis werden dann automatisch unten platziert.
- Labels kurz halten (1–2 Wörter). Der konkrete Vergleich mit Zahlen steht in der Caption.
- Bei „Poor / Rich“ nichts Abwertendes: es geht um Verhalten (z. B. „Spends the bonus“ / „Invests the bonus“), nicht um Menschen.

## Caption
- Zeile 1 = Aufruf mit Stichwort, dann 2–5 kurze Absätze mit konkretem Mehrwert (was tun, warum es nützt)
- Stichwort nach Thema:
  - Eigenheim / selbst bewohnte Immobilie → **HOME**
  - Kapitalanlage-Immobilie → **STRATEGY** oder **TAX**
  - Rente / Altersvorsorge → **PENSION**
- Pflicht-Fußzeile bei Zahlen: „Example calculation, not a guarantee …“ + „Arenja & Raj Finanz GmbH – Immobiliardarlehensvermittler §34i GewO, Versicherungsmakler §34d GewO. No tax advice.“
- Genau 5 Hashtags, unten

## Sound
- Metricool `instagramData.audioConfiguration.audioId`: erst mit Suchbegriff aufrufen → Kandidatenliste → numerische ID wählen. Ruhig/positiv, passend zum Thema. `videoVolume: 0`.

## Upload für Metricool
- Fertiges MP4 nach `reels/` in diesem Repo pushen, Metricool-Media-URL:
  `https://raw.githubusercontent.com/KashishArenja/arfinanz-reels/main/reels/<datei>.mp4`
- Metricool kopiert die Datei beim Einplanen → danach aus `reels/` löschen und pushen.

## Wochenplan
- 12 Reels Mo–So: 1–2 pro Tag, nie 3+ (Daten: ab dem 3. Reel pro Tag sinken die Aufrufe)
- Uhrzeiten zwischen 08:00 und 14:00; 11:00 lief am besten
- 2 Karussells (1080×1350, 6–10 Folien: Cover ≤ 6 Wörter, Stake, je eine Idee, Recap, CTA; Handle klein auf jeder Folie), z. B. Di und Fr
- Themen-Mix: Proof, Teach, Opinion; Immobilie (Eigenheim + Kapitalanlage), Steuern, Rente, Versicherung
- Freigabe: Kashish bekommt alle Vorschauen + Captions; erst nach „Ja“ einplanen

## Clips mehrfach nutzen und kombinieren (von Kashish ausdrücklich erlaubt)
- Ein Clip darf mehrfach verwendet werden, auch in derselben Woche – dann aber mit einem anderen Abschnitt (`start`) und anderem Thema.
- Mehrere Clips dürfen zu einem Reel geschnitten werden (`segments` in spec.json, z. B. 2 × ~2,5 s). Schnitte möglichst auf ruhige Momente legen.
- Derselbe Abschnitt (gleicher Clip + ähnlicher start) frühestens nach 3 Wochen wieder, und nie zweimal direkt hintereinander im Feed.
- Ziel: jede Woche 12 Reels, auch bei wenigen Clips. Neue, noch nie genutzte Clips zuerst einsetzen.

## Clip-Vorrat
- Weniger als 6 noch nie genutzte Clips → Kashish freundlich Bescheid geben, dass neues Material die Reels abwechslungsreicher macht (kein Blocker).
