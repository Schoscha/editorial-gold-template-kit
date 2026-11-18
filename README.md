# Editorial Gold – Wiederverwendbare Design- & Dashboard-Vorlage

Saubere, eigenständige Design-Vorlage im Stil **Warm-Anthrazit · Gebürstetes Gold · Champagner-Creme** inklusive animiertem **Golden Data Streams**-Canvas – sowohl als **eigenständige Web-/Mock-Seite** (`index.html`) als auch als **Home-Assistant-Generator-Kit**.

---

## Inhalt dieser Vorlage
- `index.html` – Komplette, offlinefähige HTML/CSS/JS-Mock-Seite (Doppelklick genügt, **0 externe Abhängigkeiten**). Enthält Umschalter für **Desktop**, **Tablet** und **Handy**, animierte **Golden Data Streams**, alle 4 Ansichten (*Home, Räume, Medien, Status & Sicherheit*) und zentrale `:root`-Design-Tokens zum schnellen Umfärben.
- `themes/editorial_gold.yaml` – Das komplette Home-Assistant-Theme (inkl. dunkler Eingabe-/Dialogfelder für HA 2026+).
- `www/golden-streams-card.js` – Custom-Card-Modul für Home Assistant (`custom:golden-streams-card` und `custom:editorial-hero-card`).
- `configs/template_mock.json` – Neutrale Beispiel-Konfiguration mit Mock-Entitäten als Startpunkt für neue Projekte.
- `generate_dashboards.py` – Python-Generator, der aus jeder passenden JSON-Konfiguration automatisch die drei Dashboards (`Desktop`, `Tablet`, `Handy`) erzeugt.
- `output/` – Vorgefertigte Mock-Lovelace-Dateien aus `template_mock.json`.

---

## Nutzung für ein neues Projekt

### Option A: Als Web- / UI-Design-Vorlage (`index.html`)
1. `index.html` direkt im Browser öffnen.
2. Oben in `index.html` die `:root`-Variablen anpassen:
   - `--eg-bg-deep` (`#12161c`) – Hintergrundfarbe
   - `--eg-bg-surface` (`#1a2028`) – Dunkle Kartenflächen
   - `--eg-gold` (`#d4af37`) – Primärer Gold-Akzent
   - `--eg-cream` (`#f3ead8`) – Champagner-Creme-Karten
   - `--eg-ink` (`#181c22`) – Dunkle Schrift auf hellen Karten
3. Die `MOCK_DATA`-Struktur im `<script>` durch deine eigenen Bereiche, Kennzahlen oder API-Daten ersetzen.

### Option B: Für ein neues Home-Assistant-Projekt
1. `configs/template_mock.json` kopieren (z. B. `configs/mein_projekt.json`) und Titel sowie `entity_id`s eintragen.
2. Optional Farben in `themes/editorial_gold.yaml` oben anpassen.
3. Ausrollen:
   ```bash
   python3 generate_dashboards.py configs/mein_projekt.json --apply --ha-dir /opt/homeassistant
   ```
   *(Vorher `themes/editorial_gold.yaml` nach `/opt/homeassistant/themes/editorial_gold/` und `www/golden-streams-card.js` nach `/opt/homeassistant/www/editorial-gold/` kopieren.)*

