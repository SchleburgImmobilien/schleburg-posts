# schleburg-posts

Vorlagen, Render-Skript und fertige Post-Bilder für die Social-Media-Automation von Schleburg Immobilien.

## Ablauf
1. Spec schreiben (JSON, siehe unten).
2. Bilder aus dem Drive-Bildpool nach `/tmp/pool/<Drive-ID>.jpg` laden (Freisteller als `.png`).
3. `python3 render.py spec.json out/<datum>_<name>.png --pool /tmp/pool`
4. PNG in dieses Repo committen und pushen. Raw-URL für Metricool:
   `https://raw.githubusercontent.com/SchleburgImmobilien/schleburg-posts/main/out/<datei>.png`

Format: `"format": "portrait"` (1080x1350, Facebook/Instagram) oder `"landscape"` (1200x900, Google-Profil).

## Vorlagen (`template`)
| template | Felder |
|---|---|
| zahl | number, unit, headline, accent, headline_post, text, source |
| diagramm | headline, accent, subtitle, pill, bars [[Label, Wert],...] (2-5), source |
| tipp | pill, headline, accent, headline_post, text, image |
| liste | headline, accent, headline_post, items [bis 4], image |
| mythos | myth, fact, accent, fact_post, image |
| gesicht | quote, accent, quote_post, role (Freisteller-Portrait, Standard Anzug) |
| objekt | kicker, headline, accent, headline_post, text, stamp ["NEU IM","ANGEBOT"], image |
| bewertung | headline, accent, headline_post, text, stamp, device (Laptop-Freisteller) |
| marktwert | Alternative zu bewertung (hoch + quer): fertige Specs in assets/marktwert/ (a, g), Preis-Kacheln mit Pin-Koordinaten pro Bild, Felder image, cards (x, y, v, d), off (nur quer), pin, headline, source |

Optional überall: `hl_style` ("italic" Standard oder "marker" = Textmarker-Effekt), `accent_dark` / `accent_light` (Themenfarbe als Hex), `marker_color`, `focus` ({driveId:[x,y]} überschreibt focus.json).

## Bildfokus
`focus.json` enthält pro Drive-ID den Fokuspunkt (x,y als Anteil 0..1). Das Render-Skript schneidet so zu, dass dieser Punkt sichtbar bleibt. Für neue Bilder Fokus bestimmen und in `focus` der Spec angeben.

## Ordner
- `fonts/`, `assets/`: Schrift und Logo
- `out/`: fertige PNGs (öffentlich; bei Bedarf alte Dateien nach ca. 60 Tagen löschen)
