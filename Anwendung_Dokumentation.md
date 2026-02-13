# 📄 Benutzerhandbuch: PDF Text-Erkennung (OCR)

Dieses Handbuch erklärt dir Schritt für Schritt, wie du das **PDF OCR Tool** benutzt.  
Das Ziel: **Gescannte Dokumente (Bilder) in durchsuchbaren Text verwandeln.**

---

## 🧐 Was macht dieses Programm?

Stell dir vor, du hast ein Dokument eingescannt. Der Computer sieht das nur als Bild. Du kannst darin keinen Text markieren oder kopieren.

Dieses Programm:
1.  👀 **Liest** dein Dokument Bild für Bild.
2.  🧠 **Erkennt** den Text darauf (OCR-Technologie).
3.  ✍️ **Erstellt** eine neue PDF-Datei, in der der Text **unsichtbar hinter dem Bild** liegt.

Das Ergebnis sieht optisch **exakt gleich** aus wie das Original, aber du kannst den Text jetzt:
*   ✅ Markieren
*   ✅ Kopieren
*   ✅ Durchsuchen (Strg + F)

---

## 🚀 Erste Schritte: Vorbereitung

Bevor du starten kannst, müssen zwei Dinge auf deinem Computer installiert sein. Das musst du nur **einmal** machen.

### 1. Python installieren
Python ist die Sprache, in der das Programm geschrieben ist.
*   Lade es hier herunter: [python.org/downloads](https://www.python.org/downloads/)
*   **WICHTIG:** Beim Installieren unbedingt das Häkchen bei **"Add Python to PATH"** setzen!

### 2. Tesseract OCR installieren
Das ist das "Gehirn", das den Text liest.
Wir empfehlen die Installation über die Eingabeaufforderung (Terminal):

1.  Drücke `Windows-Taste` + `R`, tippe `cmd` ein und drücke Enter.
2.  Kopiere diesen Befehl hinein und drücke Enter:
    ```powershell
    winget install UB-Mannheim.TesseractOCR
    ```
    *(Alternativ kannst du den Installer auch [hier herunterladen](https://github.com/UB-Mannheim/tesseract/wiki).)*
3.  **WICHTIG:** Wähle bei der Installation die Sprachen `German` (Deutsch) und `English` aus.

---

## 🛠️ Programm einrichten

Jetzt machen wir das Programm startklar.

1.  Lade den Ordner mit dem Skript herunter.
2.  Öffne diesen Ordner.
3.  Klicke oben in die Adresszeile des Datei-Explorers, tippe `cmd` ein und drücke Enter.
4.  Gib diesen Befehl ein, um die notwendigen Bausteine zu installieren:
    ```powershell
    pip install -r requirements.txt
    ```

---

## ▶️ Anleitung: Dokumente umwandeln

So benutzt du das Tool im Alltag:

1.  **Dateien sammeln:**
    Kopiere die Datei `make_pdfs_searchable.py` direkt in den Ordner, wo deine gescannten PDFs liegen.

2.  **Terminal öffnen:**
    Klicke in diesem Ordner wieder oben in die Adresszeile, tippe `cmd` und Enter.

3.  **Starten:**
    Tippe folgenden Befehl ein und drücke Enter:
    ```powershell
    python make_pdfs_searchable.py
    ```

4.  **Loslegen:**
    Das Programm zeigt dir eine Begrüßung. Drücke die **Leertaste**, um zu starten.

5.  **Warten & Freuen:**
    Lehn dich zurück. Das Programm arbeitet deine PDFs nacheinander ab.
    Für jede Datei `Dokument.pdf` wird eine neue Datei `Dokument_searchable.pdf` erstellt.

---

## ❓ Hilfe & Lösungen

**Problem: "Befehl 'python' nicht gefunden"**
*   Lösung: Du hast wahrscheinlich beim Installieren von Python das Häkchen bei "Add to PATH" vergessen. Installiere Python neu und achte darauf.

**Problem: "Tesseract nicht gefunden"**
*   Lösung: Installiere Tesseract wie oben beschrieben neu. Starte deinen Computer danach einmal neu.

**Problem: Der Text wird schlecht erkannt**
*   Lösung: Überprüfe, ob du bei der Tesseract-Installation auch das deutsche Sprachpaket (`German`) ausgewählt hast. Ohne das kann es keine Umlaute lesen.

---

 Viel Erfolg beim Digitalisieren! 🚀
