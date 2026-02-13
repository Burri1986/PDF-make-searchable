# PDF OCR Tool – Make PDFs Searchable

Dieses Python-Skript (`make_pdfs_searchable.py`) durchsucht den aktuellen Ordner nach PDF-Dateien und wandelt **Bild-basierte PDFs** (z. B. Scans) automatisch in **durchsuchbare PDFs** um – inklusive Texterkennung (OCR) via Tesseract.

✅ Bereits durchsuchbare PDFs werden automatisch erkannt und übersprungen.
🚀 Originaldateien bleiben unverändert – es werden immer neue Dateien erstellt.

---

## 📋 Voraussetzungen

### 1. Python (≥ 3.8)

Python muss installiert sein. Prüfen via Terminal:
```powershell
python --version
```
Falls nicht vorhanden → [python.org/downloads](https://www.python.org/downloads/)
> **Hinweis:** Bei der Installation das Häkchen **"Add Python to PATH"** setzen.

### 2. Tesseract OCR

Das Skript benötigt die **Tesseract OCR-Engine** zur Texterkennung.

**Installation (Windows, via Winget – empfohlen):**
```powershell
winget install UB-Mannheim.TesseractOCR
```

**Alternative:** Installationsprogramm von [github.com/UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) herunterladen.

> **⚠️ Wichtig:** Bei der Installation die gewünschten **Sprachpakete** auswählen (mindestens `eng` – Englisch und `deu` – Deutsch). Ohne Sprachpakete kann Tesseract keinen Text erkennen.

---

## 🛠️ Installation

1. Projekt herunterladen oder klonen.
2. Terminal im Projektordner öffnen.
3. Abhängigkeiten installieren:

```powershell
pip install -r requirements.txt
```

---

## 🚀 Nutzung

1. Kopiere `make_pdfs_searchable.py` in den Ordner mit deinen PDF-Dateien.
2. Öffne ein Terminal in diesem Ordner.
3. Starte das Skript:

```powershell
python make_pdfs_searchable.py
```

4. Drücke **Leertaste**, um den Vorgang zu starten.

Die Ausgabedateien erhalten die Endung `_searchable.pdf` und werden im selben Ordner gespeichert.
**Beispiel:** `Rechnung.pdf` → `Rechnung_searchable.pdf`

---

## ⚙️ Funktionsweise

| Schritt | Beschreibung |
| :--- | :--- |
| **1. Scan** | Alle PDF-Dateien im Ordner werden aufgelistet. |
| **2. Analyse** | Prüft, ob die PDF bereits durchsuchbaren Text enthält (>50 Zeichen). Falls ja, wird sie übersprungen. |
| **3. OCR** | Rendert jede Seite als Bild (300 DPI) und führt Texterkennung durch (Deutsch + Englisch). |
| **4. Erstellung** | Erstellt eine neue PDF mit dem originalen Layout und hinterlegtem Textlayer (unsichtbar). |
| **5. Optimierung** | Die neue PDF wird komprimiert gespeichert. |

---

## ❓ Fehlerbehebung

| Problem | Lösung |
| :--- | :--- |
| **Tesseract-OCR nicht gefunden** | Tesseract installieren (s. oben) und Terminal neu starten. |
| **Fehlende Abhängigkeiten** | `pip install -r requirements.txt` ausführen. |
| **Schlechte Texterkennung** | Prüfen, ob Sprachpakete (`deu`, `eng`) bei Tesseract installiert wurden. |
| **Skript findet keine PDFs** | Terminal muss im selben Ordner wie die PDF-Dateien geöffnet sein. |

---

<sub>powered by [crypto-burri.de](https://crypto-burri.de)</sub>
