# PDF OCR Tool – Make PDFs Searchable

Dieses Python-Skript (`make_pdfs_searchable.py`) durchsucht den aktuellen Ordner nach PDF-Dateien und wandelt **Bild-basierte PDFs** (z. B. Scans) automatisch in **durchsuchbare PDFs** um – inklusive Texterkennung (OCR) via Tesseract.

Bereits durchsuchbare PDFs werden automatisch erkannt und übersprungen.

---

## Voraussetzungen

### 1. Python (≥ 3.8)

Python muss installiert sein. Prüfen via Terminal:

```powershell
python --version
```

Falls nicht vorhanden → [python.org/downloads](https://www.python.org/downloads/)

> **Hinweis:** Bei der Installation das Häkchen **"Add Python to PATH"** setzen.

### 2. Tesseract OCR

Das Skript benötigt die Tesseract OCR-Engine zur Texterkennung.

**Installation (Windows, via Winget – empfohlen):**

```powershell
winget install UB-Mannheim.TesseractOCR
```

**Alternative:** Installationsprogramm von [github.com/UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) herunterladen und ausführen.

> **Wichtig:** Bei der Installation die gewünschten **Sprachpakete** auswählen (mindestens `eng` – Englisch und `deu` – Deutsch). Ohne Sprachpakete kann Tesseract keinen Text erkennen.

Das Skript sucht Tesseract automatisch an folgenden Orten:
1. Im System-PATH (`tesseract` direkt aufrufbar)
2. `C:\Program Files\Tesseract-OCR\tesseract.exe`
3. `C:\Users\<Benutzername>\AppData\Local\Programs\Tesseract-OCR\tesseract.exe`

Falls Tesseract an einem anderen Ort installiert ist, den Pfad im Skript unter `possible_tesseract_paths` ergänzen.

### 3. Python-Bibliotheken

Alle benötigten Abhängigkeiten mit einem Befehl installieren:

```powershell
pip install pypdf pytesseract Pillow PyMuPDF
```

| Paket          | Zweck                                             |
|----------------|---------------------------------------------------|
| `pypdf`        | PDF lesen/schreiben, Seiten zusammenfügen          |
| `pytesseract`  | Python-Wrapper für die Tesseract OCR-Engine        |
| `Pillow`       | Bildverarbeitung (PIL-Fork)                        |
| `PyMuPDF`      | PDF-Seiten als Bilder rendern (Import: `fitz`)     |

---

## Nutzung

1. Das Skript `make_pdfs_searchable.py` in den Ordner mit den PDF-Dateien kopieren.
2. Ein Terminal (PowerShell oder CMD) **in diesem Ordner** öffnen.
3. Skript starten:

```powershell
python make_pdfs_searchable.py
```

4. Mit **Leertaste** den Vorgang starten oder mit **ESC** abbrechen.

Die Ausgabedateien erhalten die Endung `_searchable.pdf` und werden im selben Ordner abgelegt.

**Beispiel:** `Scan_20260210-01.pdf` → `Scan_20260210-01_searchable.pdf`

---

## Funktionsweise

1. **Scan** – Alle PDF-Dateien im aktuellen Verzeichnis werden aufgelistet (Dateien mit `_searchable.pdf` werden ignoriert).
2. **Analyse** – Jede Datei wird geprüft:
   - Enthält sie bereits durchsuchbaren Text (> 50 Zeichen) → Übersprungen.
   - Existiert bereits eine `_searchable.pdf`-Version → Übersprungen.
3. **OCR-Verarbeitung** – Für jede Bild-basierte PDF:
   - Jede Seite wird mit PyMuPDF bei **300 DPI** gerendert (für bestmögliche Texterkennung).
   - Tesseract führt die Texterkennung durch (Sprachen: Deutsch + Englisch).
   - Die OCR-Seite wird auf die **Originalgröße** zurückskaliert, sodass das Layout erhalten bleibt.
   - Eine neue, durchsuchbare PDF wird erstellt.
4. **Zusammenfassung** – Übersicht aller verarbeiteten, übersprungenen und fehlgeschlagenen Dateien.

---

## Fehlerbehebung

| Problem | Lösung |
|---------|--------|
| `Tesseract-OCR nicht gefunden!` | Tesseract installieren (s. oben) und ggf. Terminal neu starten. |
| `Fehlende Abhängigkeiten!` | `pip install pypdf pytesseract Pillow PyMuPDF` ausführen. |
| Schlechte Texterkennung | Prüfen, ob bei der Tesseract-Installation die **Sprachpakete** (`deu`, `eng`) gewählt wurden. |
| `TesseractError` / Sprache nicht gefunden | Das Skript fällt automatisch auf `eng` zurück. Für deutsche Dokumente muss `deu` installiert sein. |
| Skript startet, aber findet keine PDFs | Sicherstellen, dass das Terminal im **selben Ordner** wie die PDFs geöffnet wurde. |

---

## Hinweise

- Das Skript ist für **Windows** konzipiert (nutzt `msvcrt` für Tastatureingaben und `cls` zum Leeren der Konsole).
- Originaldateien werden **nicht verändert** – es werden immer neue `_searchable.pdf`-Dateien erstellt.
- Bereits vorhandene `_searchable.pdf`-Dateien werden **nicht überschrieben**.

---

<sub>powered by [crypto-burri.de](https://crypto-burri.de)</sub>
