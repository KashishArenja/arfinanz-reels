# @arfinanz – Wochen-Workflow (12 Reels + 2 Karussells)

Jeden Montag bis 08:00 (Europe/Berlin) vorbereiten, Kashish gibt frei, dann über Metricool einplanen.

## Quellen
- Clips: Google-Drive-Ordner „01_Clips roh“ – ID `1VrlzH-tNNoF0emWmWnrY0l8vUKsCQeZs` (per Link freigegeben)
  - Liste: Google-Drive-Connector `search_files` mit `parentId = '<ID>'`
  - Download (jede Größe): `curl -sSL "https://drive.usercontent.google.com/download?id=<FILE_ID>&export=download&confirm=t" -o clip.mov`
- Clip-Nutzung: `used_clips.json` (nach dem Einplanen jeden verwendeten Abschnitt eintragen: Datei, start, dur, Datum, Thema, und pushen)
- Metricool-Brand: blogId `7984611` (Instagram @arfinanz, Facebook-Seite verbunden → Sounds möglich), Zeitzone Europe/Berlin

## Pflicht: Skills nutzen und Expat-Bezug
- Für jedes Reel den Reel-Skill (ig-reel) anwenden: 3 Hooks aus verschiedenen Formeln, jeweils bewerten (LENGTH, SPECIFICITY, STAKES, FRONTLOAD, ADDRESS; Gesamt = Mittel × 0,6 + schwächster × 0,4), nur STRONG (≥ 70) verwenden, Ranking in der Montags-Übersicht zeigen. Captions mit ig-caption, Karussells mit ig-content.
- Jedes Thema muss einen klaren Expat-Bezug haben (was ist für Inder/Expats in Deutschland anders: später angekommen → weniger Beitragsjahre, Visum/Blue Card, Familie in Indien, Steuerklasse, Bank ohne SCHUFA-Historie, Rückkehr nach Indien …). Allgemeine Finanztipps ohne Expat-Dreh sind nicht gut genug.
- Deutschland-Bezug mit reinnehmen: der Vergleich „du als Expat“ vs. „der deutsche Kollege / das deutsche System“ macht es greifbar.
- Flaggen 🇮🇳 🇩🇪 gezielt einsetzen (Labels, Tabellenzeilen, Hook), z. B. „🇮🇳 India“ / „🇩🇪 Germany“, „22 🇩🇪“ vs. „30 🇮🇳“. Das Skript rendert Emoji-Flaggen sauber (Noto Color Emoji). Sparsam: max. 2 Flaggen pro Textblock.
- Muss interessant sein: ein überraschender Vergleich oder eine konkrete Zahl, die weh tut (z. B. „€340 less pension than your German colleague“).

## Reel-Format
- Genau 5,1 s, 1080×1920, stumme Clips (Originalton wird entfernt)
- Bau: `python3 tools/make_reel.py clip.mov spec.json out.mp4` (braucht `pip install --break-system-packages opencv-python-headless`)
  - spec.json: `{"blocks": [["Hook", 62, "white"], ["Auflösung", 58, "yellow"], ["More in the caption 👇", 42, "white"]]}` (Stile: white / red / yellow, siehe Design-Vorlage)
  - Hook oben, Rest unten, nie über Gesichtern (YuNet-Erkennung), immer in der Safe Zone (oben 250 px, unten ab 1440 px, rechts 230 px frei)
  - Auch Köpfe von Personen, die mit dem Rücken/seitlich zur Kamera stehen, bleiben frei (Personen-Erkennung, Kopf = oberer Teil des Körpers; Feedback Kashish 10.11.: Text nie über dem Kopf). Bei Bedarf zusätzlich `"avoid": [[x0, y0, x1, y1]]` in spec.json für Zonen, die frei bleiben sollen.
  - Danach `out_check.jpg` ansehen: Gesichter frei? Text lesbar? Sieht es clean aus?
  - Clean-Regeln (Kashish): alle Textboxen exakt mittig im Bild, Zeilen gleichmäßig umbrochen (kein einzelnes Wort allein in der letzten Zeile), Hinweiszeile („see caption“) immer einzeilig, Vergleichs-Labels auf gleicher Höhe und gleich breit. Das Skript macht das automatisch – trotzdem jedes Ergebnis ansehen.
- Text: Englisch, Menge siehe Design-Vorlage (Vergleichs-Reels ca. 30–40 Wörter, einfache Reels ~18), Hook im POV-Stil, leicht verständlich, keine unerklärten Fachbegriffe
- Thema passend zum Clip wählen (z. B. Dachboden → Ausbau/Wertsteigerung, Auto → Kfz-Versicherung, Telefonat → Finanzierungszusage)
- Keine erfundenen Kundenfälle: Beispielrechnungen als Beispiel kennzeichnen („can be enough“, nicht „this couple did it“), außer Kashish bestätigt einen echten Fall

## DESIGN-VORLAGE (fest, Stand 10.11.2026 – im Skript eingebaut)
Abgeleitet aus unseren Top-Reels (DdGbZA8Nxpn Ehegattenschaukel, DfNDc8eNan9 Urlaubsplanung, Deg3pQLt-I4 Millionaire Couple, Dd1PbGrMz7w Augsburg) und den Konkurrenz-Hits (expats.phil DdMXq3BCitY, iamsarahrahimi DdrI9dxKYAx, fionn_kelly_de Dd6XvODMom5).
Gemeinsamer Nenner: Text sieht aus wie nativer Instagram-Text – kein Grafik-Panel, keine großen Karten.
- **Schrift:** Barlow Condensed Bold (`tools/fonts/`, OFL) – schmal und fett wie der Instagram-Text in unseren Hits. Emoji/Flaggen über Noto Color Emoji.
- **Boxen:** pro Textzeile eine eng anliegende Box (kleiner Radius 10 px, wenig Innenabstand), Zeilen stoßen direkt aneinander, alles mittig.
- **Farben (nur diese drei):**
  - `white` – weiß / schwarze Schrift: Hook, Infos, CTA
  - `red` – Rot #E4002B / weiße Schrift: Problem, schlechtere Seite, Akzent-Headline („Millionaire Couple“, „Not-So-Smart Man“)
  - `yellow` – Gelb #FFD000 / schwarze Schrift: Lösung, bessere Seite, Ergebnis („Smart Man“, „Net wealth effect“)
  - Navy (`blue`) nur noch für Poster/Karussells, nicht mehr in Reels.
- **Aufbau (von oben nach unten):** Hook oben (größte Schrift, weiß oder rot) → Vergleich/Inhalt direkt darunter (Kopf-Box pro Seite in Rot bzw. Gelb, darunter je Stichpunkt eine eigene Box) → kleine CTA-Zeile („Comment HOME for the free PDF guide 👇“), die bei 1,5 s eingeblendet wird (wie „Read the Caption 👇“ / „SAVE this“ bei den Hits). Hook und Inhalt stehen ab Bild 1.
- **Vergleichs-Karte:** `"compare": {"left": {"title": "Renting", "points": [...], "style": "red", "point_style": "white"}, "right": {"title": "Buying", "points": [...], "style": "yellow"}}` – Standard links rot, rechts gelb, Stichpunkte in der Kopf-Farbe, außer `point_style` ist gesetzt. Bei India vs Germany: India rot mit weißen Punkten (nicht abwertend), Germany gelb.
- **Textmenge:** Unsere Hits haben deutlich mehr Text als 18 Wörter (Ehegattenschaukel ~60, Millionaire Couple ~80 Wörter) – die Leute pausieren und schauen das 5-s-Reel mehrfach. Für Vergleichs-Reels daher: Hook ≤ 12 Wörter + 3–4 Stichpunkte je Seite (≤ 22 Zeichen) + CTA, insgesamt ca. 30–40 Wörter. Keine Fließtext-Absätze. (Kashish entscheidet, ob wir noch mehr Text testen.)
- **Was die Konkurrenz zusätzlich zeigt:** Phil – Labels „Dumb“/„Smart“ farbig über den Köpfen (= unsere `labels`); Sara – große Tabelle zum Screenshotten + „SAVE this“ am Ende (= `table` + CTA); Fionn – rotes Banner mit Emoji-Flagge + kleine weiße Datums-Pille darunter.

## STANDARD: Vergleichs-Reel mit Stichpunkten (von Kashish festgelegt, immer so)
Der Mehrwert steht IM VIDEO, nicht in der Caption.
```
Oben:   Hook (POV, konkrete Zahl), weiße Box
Mitte:  Vergleichs-Karte: 🇮🇳 India | 🇩🇪 Germany – je 3–4 kurze Stichpunkte (max. ~22 Zeichen, parallel formuliert, z. B. „10 months deposit“ | „3 months deposit“)
Unten:  „More in the caption 👇“
Caption: Zeile 1 „Comment HOME/STRATEGY/TAX/PENSION for the free PDF guide 👇“, dann dieselben Stichpunkte ausführlich + nächster Schritt + Compliance + 5 Hashtags
```
spec.json: `{"compare": {"left": {"title": "🇮🇳 India", "points": [...], "style": "red", "point_style": "white"}, "right": {"title": "🇩🇪 Germany", "points": [...], "style": "yellow"}}, "blocks": [["POV: …", 56, "white"], ["Comment HOME for the free PDF guide 👇", 44, "white"]]}`
Das Skript hält die Lesereihenfolge (Hook → Karte → Hinweis) und lässt Gesichter frei. Stichpunkte so kurz, dass nichts umbricht.
Spalten nach Stimmung (Regel Kashish): Bei zwei Personen bekommt die lachende/zufriedene Person die bessere Seite (meist 🇩🇪 bzw. die Lösung, z. B. „Buying“), die ernste/genervte Person die schlechtere (🇮🇳 bzw. das Problem, z. B. „Renting“). Vor dem Rendern im Vorschaubild prüfen, wer links/rechts wie schaut, und „left“/„right“ entsprechend setzen.
Zielgruppe (Regel Kashish): Kunden sind Expats, die IN DEUTSCHLAND leben. Jedes Thema muss ihnen bei einer Entscheidung hier helfen (kaufen, Steuern, Rente, Versicherung in DE). India vs. Germany nur, wenn der Vergleich zeigt, was in Deutschland möglich/besser ist – keine Themen, die nur das Leben in Indien betreffen (z. B. Mieten in Bangalore).
Nicht machen (Feedback Kashish 10.11.): Infos nur in die Caption schieben; Hooks ohne klaren Sinn („8 leave days. 16 days in India“); Stichwort, das nicht zum Thema passt (HOME unter Urlaub). Themen ohne passendes PDF-Stichwort gar nicht erst planen.

## Vergleichs-Reels mit Labels über Personen (Variante)
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
- Zu jedem Stichwort gibt es einen kostenlosen PDF-Guide (Kashish bestätigt). Aufruf immer konkret: „Comment HOME / STRATEGY / TAX / PENSION and we'll send you the free PDF guide 👇“ – in Zeile 1 der Caption und kurz im Reel-Text unten.
- Pflicht-Fußzeile bei Zahlen: „Example calculation, not a guarantee …“ + „Arenja & Raj Finanz GmbH – Immobiliardarlehensvermittler §34i GewO, Versicherungsmakler §34d GewO. No tax advice.“
- Genau 5 Hashtags, unten

## Sound
- Metricool `instagramData.audioConfiguration.audioId`: erst mit Suchbegriff aufrufen → Kandidatenliste → numerische ID wählen. `videoVolume: 0`.
- **Trend-Sounds statt ruhiger Standardmusik (Kashish 10.11.: „die Sounds sind langweilig“).** Vor dem Einplanen die aktuellen Instagram-Trend-Sounds der Woche recherchieren (z. B. Buffer, Later, SocialPilot, Kabo – Wochen-Charts). **Keine Bollywood-Lieder** (Kashish 10.11.).
- Chart-Songs als „music“ gibt es im Business-Katalog meist nicht. Dann: (1) `original_sound` des Trend-Songs aus der Kandidatenliste (Risiko: Instagram kann den Ton bei Business-Accounts stummschalten), oder (2) Metas Trend-Format-Sounds „… (Reels Sound - Listicle/Reaction/Photo Dump)“ – sicher und gemacht für Listen/Vergleiche.
- Nicht zweimal am selben Tag denselben Sound.

## Upload für Metricool
- Fertiges MP4 nach `reels/` in diesem Repo pushen, Metricool-Media-URL:
  `https://raw.githubusercontent.com/KashishArenja/arfinanz-reels/main/reels/<datei>.mp4`
- Metricool kopiert die Datei beim Einplanen → danach aus `reels/` löschen und pushen.

## Datenbasis für jede Woche (Pflicht, vor dem Planen)
Kashish: „Du siehst, was bei uns und bei der Konkurrenz gut läuft – darauf baust du unseren Content.“
1. **Eigene Zahlen** (Metricool, letzte 4 Wochen, Reels: IGRE02, IGRE06, IGRE11, IGRE23, IGRE07, IGRE12, IGRE21, IGRE24, IGRE28; Captions per IGRE03 tageweise): typischer Wert = Median der Aufrufe; Ausreißer = Aufrufe ÷ Median. Für Top 5 und Flop 5 ansehen: Thema, Hook-Art, 3-Sekunden-Rate (IGRE28), Shares, Saves, Kommentare.
2. **Konkurrenz** (IGCR01/04/05/07/08/09, Texte per IGCR03 tageweise): Ausreißer je Account gegen dessen eigenen Normalwert.
3. **Daraus der Plan:** Gewinner-Themen und -Muster bekommen den meisten Platz (neuer Hook/Clip, gleiches Muster), Flop-Muster fallen raus. In der Montags-Übersicht pro Reel eine kurze Begründung: „basiert auf …“ (eigener Hit X / Konkurrenz-Muster Y / neuer Test).
4. Etwa 2 von 12 Reels bewusst als Test für neue Formate/Themen.

## Tabellen-Reels (Clips ohne Personen)
- Clips, auf denen niemand zu sehen ist (Dachboden, Wohnung, Straße, Auto ohne Personen), eignen sich für Tabellen.
- spec.json: `"table": {"title": "...", "headers": [...], "rows": [[...]], "highlight": 1, "note": "Example: …"}`, dazu in `blocks` nur die Stichwort-Zeile (z. B. „Comment PENSION for the free PDF guide“).
- Tabelle sitzt optisch mittig (so tief wie möglich über der Button-Leiste), nicht oben am Rand.
- Spalten kurz halten (max. ~12 Zeichen), damit die Schrift groß bleibt; zusammengehörige Wörter im Titel mit „~“ verbinden (z. B. „at~30“).
- Titel = die Pointe mit Zahl im POV-Stil (z. B. „POV: You start at 30 instead of 25 and lose €190,000“), nie nur das Thema oder eine harmlose Frage. Die hervorgehobene Zeile ist genau der Fall aus dem Titel.
- Bevorzugt ruhige Clips ohne Personen (Schreibtisch, Laptop, Stadt) als Hintergrund.
- Max. 3 Spalten, 3–6 Zeilen, eine hervorgehobene Zeile. Alle Zahlen per Python ausrechnen bzw. mit Quelle belegen, nie schätzen; Annahmen in `note`.
- Ideen: Brutto→Netto nach Gehalt, Sparen ab Alter X bis 67, Kaufnebenkosten nach Bundesland, Rentenpunkte pro Kind, Steuerersparnis nach Steuersatz.

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

## Konkurrenz-Learnings (Stand 10.11.2026, Metricool-Wettbewerber, 3 Monate)
Wettbewerber in Metricool: fionn_kelly_de, expats.phil, iamsarahrahimi, realestate.sandeep_ (nicht „realestate.sandeep“ ohne Unterstrich – falscher Account).
Gemessen wird der Ausreißer-Faktor: Interaktionen eines Reels ÷ typischer Wert desselben Accounts. Nur Muster übernehmen, nie Texte kopieren.
1. **Zielgruppen-Callout + Gratis-Guide** (Fionn: AVD-Guide ~3.000 Kommentare, V0800 „Parents, pay attention“ ~1.800, Kinderzuschlag „KID“ ~900): Gruppe direkt ansprechen („POV: You're a parent in Germany…“), konkreter €-Betrag, in Zeile 1 der Caption ein konkretes Gratis-Ding fürs Stichwort (Guide, Checkliste, Rechner) – nicht nur „we'll calculate“. Nur versprechen, was es wirklich gibt.
2. **Gleiches Gehalt, anderes Ergebnis** (expats.phil: „€1,624 in taxes vs €12. Same salary“ ≈ 40× sein Normalwert, zweimal gepostet): ideal für Vergleichs-Reels mit Labels, z. B. „Employee“ / „Employee + rental flat“, Stichwort TAX.
3. **Zahlen-Tabellen zum Screenshotten** (Sara: Netto-Gehaltstabelle ≈ 380× Normalwert): als Karussell (Brutto→Netto, Rentenlücke nach Gehalt, Steuerersparnis nach Gehalt).
4. **Gewinner wiederholen** mit neuem Hook/Clip (expats.phil und wir selbst: Ehegattenschaukel).
5. **Familien-Themen** ziehen stark: Kindererziehungszeiten, Kinderzuschlag + Bildungspaket, Elternzeit/Elterngeld, Kinder und Rente.
Monatlich (erster Montag im Monat): Wettbewerber-Reels der letzten 4 Wochen abrufen (IGCR-Metriken), Ausreißer lesen, diese Liste aktualisieren und 2–3 Reels der Woche danach ausrichten. In der Montags-Übersicht kurz sagen, welches Reel von welchem Muster kommt.
