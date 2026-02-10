#!/usr/bin/env python3
"""
Intelligente PDF-Umbenennung basierend auf Inhaltsanalyse.
Schema: JJJJ-MM-DD_Firma_Dokumenttyp-Details[_SeiteX].pdf
"""

import os
import re
import sys
import datetime
from collections import defaultdict, Counter
from pypdf import PdfReader


PDF_DIR = os.path.dirname(os.path.abspath(__file__))


def extract_text(filepath, max_pages=3):
    """Extrahiert Text aus den ersten Seiten einer PDF."""
    try:
        reader = PdfReader(filepath)
        text = ""
        for page in reader.pages[:max_pages]:
            t = page.extract_text()
            if t:
                text += t + "\n"
        return text
    except Exception as e:
        return f"FEHLER: {e}"


MONATE = {
    'januar': '01', 'februar': '02', 'märz': '03', 'maerz': '03', 'mõrz': '03',
    'april': '04', 'mai': '05', 'juni': '06', 'juli': '07',
    'august': '08', 'september': '09', 'oktober': '10',
    'november': '11', 'dezember': '12'
}
MONATE_PATTERN = '|'.join(MONATE.keys())


def find_full_date(text, filepath=None):
    """
    Findet das beste vollständige Datum (YYYY, MM, DD).
    Gibt IMMER ein vollständiges Datum mit Jahr, Monat und Tag zurück.
    Priorität:
      1. Explizites Briefdatum (Westerstede/Datum mit Monat)
      2. "Erstellt am"-Datum
      3. Explizites "Datum: DD.MM.YYYY"
      4. Abrechnungszeitraum-Ende
      5. Irgendein plausibles Datum im Text
      6. Datei-Änderungsdatum als Fallback
    """
    
    # 1. Brief-Datum: "Westerstede, DD. Monat YYYY"
    m = re.search(r'Westerstede[,\s]+(\d{1,2})\.\s*(' + MONATE_PATTERN + r')\s+(\d{4})', text, re.IGNORECASE)
    if m:
        return (m.group(3), MONATE[m.group(2).lower()], m.group(1).zfill(2))
    
    # 2. "Erstellt am DD.MM.YYYY" (Techem-Abrechnungen)
    m = re.search(r'Erstellt\s+am\s+(\d{2})\.(\d{2})\.(\d{4})', text)
    if m:
        return (m.group(3), m.group(2), m.group(1))
    
    # 3. "Datum DD. Monat YYYY" (z.B. "Datum 9. Oktober 2023")
    m = re.search(r'Datum[:\s]+(\d{1,2})\.\s*(' + MONATE_PATTERN + r')\s+(\d{4})', text, re.IGNORECASE)
    if m:
        return (m.group(3), MONATE[m.group(2).lower()], m.group(1).zfill(2))
    
    # 4. "Datum: DD.MM.YYYY" oder "Datum DD.MM.YYYY"
    m = re.search(r'Datum[:\s]+(\d{1,2})\.(\d{1,2})\.(\d{4})', text)
    if m:
        y = m.group(3)
        if 2015 <= int(y) <= 2030:
            return (y, m.group(2).zfill(2), m.group(1).zfill(2))
    
    # 5. "Von DD.MM.YYYY" (Arbeitsagentur)
    m = re.search(r'Von\s+(\d{2})\.(\d{2})\.(\d{4})', text)
    if m:
        return (m.group(3), m.group(2), m.group(1))
    
    # 6. "fällig am DD.MM.YYYY" (EWE)
    m = re.search(r'f[aä]llig\s+am\s+(\d{2})\.(\d{2})\.(\d{4})', text)
    if m:
        return (m.group(3), m.group(2), m.group(1))
    
    # 7. Abrechnungszeitraum-Ende: "01.01.YYYY - 31.12.YYYY"
    m = re.search(r'Abrechnungszeitraum[:\s]*(\d{2})\.(\d{2})\.(\d{4})\s*[-–ù]\s*(\d{2})\.(\d{2})\.(\d{4})', text)
    if m:
        return (m.group(6), m.group(5), m.group(4))
    
    # 8. Nutzungszeitraum-Ende
    m = re.search(r'Nutzungszeitraum[:\s]*(\d{2})\.(\d{2})\.(\d{4})\s*[-–ù]\s*(\d{2})\.(\d{2})\.(\d{4})', text)
    if m:
        return (m.group(6), m.group(5), m.group(4))
    
    # 9. "Abrechnung YYYY" -> 31.12.YYYY
    m = re.search(r'[Aa]brechnung\s+(\d{4})', text)
    if m:
        return (m.group(1), '12', '31')
    
    # 10. "Monat MM YYYY" (Lohnabrechnung)
    m = re.search(r'Monat\s+(\d{2})\s+(\d{4})', text)
    if m:
        return (m.group(2), m.group(1), '01')
    
    # 11. Häufigstes plausibles vollständiges Datum im Text
    dates = re.findall(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', text)
    valid = [(d, mo, y) for d, mo, y in dates if 2015 <= int(y) <= 2030 and 1 <= int(mo) <= 12 and 1 <= int(d) <= 31]
    if valid:
        # Nimm das häufigste Datum
        date_strs = [f'{y}-{mo.zfill(2)}-{d.zfill(2)}' for d, mo, y in valid]
        most_common = Counter(date_strs).most_common(1)[0][0]
        parts = most_common.split('-')
        return (parts[0], parts[1], parts[2])
    
    # 12. Letzter Fallback: Datei-Änderungsdatum
    if filepath and os.path.exists(filepath):
        mtime = os.path.getmtime(filepath)
        dt = datetime.datetime.fromtimestamp(mtime)
        return (str(dt.year), str(dt.month).zfill(2), str(dt.day).zfill(2))
    
    # Absoluter Fallback
    return ('0000', '00', '00')


def classify_document(text):
    """
    Klassifiziert ein Dokument.
    Gibt (firma, dokumenttyp_mit_details) zurück.
    """
    t = text.lower()

    # Minimaler Text -> Unlesbar
    clean_t = re.sub(r'[^a-zäöüß]', '', t)
    if len(clean_t) < 30:
        return ('Unbekannt', 'Unlesbares-Dokument')

    # --- Bundesagentur für Arbeit ---
    if 'bemessungsentgelt' in t or 'sozialversicherungspauschale' in t:
        return ('Arbeitsagentur', 'Bewilligungsbescheid-ALG')

    if ('bundesagentur' in t and 'arbeit' in t) or \
       ('agentur f' in t and 'arbeit' in t):
        if 'berechnungsgrundlagen' in t or 'leistungsentgelt' in t:
            return ('Arbeitsagentur', 'Berechnungsgrundlagen-ALG')
        if 'leistungsanspruch' in t:
            return ('Arbeitsagentur', 'Leistungsbescheid-ALG')
        return ('Arbeitsagentur', 'Bescheid')

    if 'leistungsentgelt' in t and ('lohnsteuer' in t or 'anrechnungsbetrag' in t):
        return ('Arbeitsagentur', 'Berechnungsgrundlagen-ALG')

    # --- Deutsche Rentenversicherung ---
    if 'rentenversicherung' in t or 'rentenberechnung' in t:
        if 'versicherungsnummer' in t or 'versicherungsverlauf' in t:
            return ('Deutsche-Rentenversicherung', 'Versicherungsverlauf')
        if 'rentenberechnung' in t or 'grundlagen der renten' in t or 'entgeltpunkte' in t:
            return ('Deutsche-Rentenversicherung', 'Rentenberechnung')
        if 'online-rechner' in t or 'online-dienste' in t:
            return ('Deutsche-Rentenversicherung', 'Renteninformation')
        return ('Deutsche-Rentenversicherung', 'Dokument')

    # --- DORMA Hüppe / dormakaba ---
    if 'dorma' in t or 'dormakaba' in t:
        m = re.search(r'Monat\s+(\d{2})\s+\d{4}', text)
        monat_map = {
            '01': 'Januar', '02': 'Februar', '03': 'Maerz',
            '04': 'April', '05': 'Mai', '06': 'Juni',
            '07': 'Juli', '08': 'August', '09': 'September',
            '10': 'Oktober', '11': 'November', '12': 'Dezember'
        }
        monat_name = monat_map.get(m.group(1), '') if m else ''

        if 'lohnsteuerbescheinigung' in t:
            if 'korrektur' in t or 'stornierung' in t:
                return ('DORMA-Hueppe', 'Lohnsteuerbescheinigung-Korrektur')
            return ('DORMA-Hueppe', 'Lohnsteuerbescheinigung')
        if 'verdienstabrechnung' in t:
            s = f'-{monat_name}' if monat_name else ''
            return ('DORMA-Hueppe', f'Verdienstabrechnung{s}')
        if 'zeitnachweis' in t:
            s = f'-{monat_name}' if monat_name else ''
            return ('DORMA-Hueppe', f'Zeitnachweis{s}')
        s = f'-{monat_name}' if monat_name else ''
        return ('DORMA-Hueppe', f'Lohnunterlagen{s}')

    # --- Eigenkorrespondenz ---
    if 'crypto-burri' in t or \
       ('terminvereinbarung' in t and 'belegeinsicht' in t):
        if 'terminvereinbarung' in t:
            return ('Ammerlaender-Wohnungsbau', 'Terminvereinbarung-Belegeinsicht')
        if 'berpr' in t or ('kl' in t and 'rung' in t):
            return ('Ammerlaender-Wohnungsbau', 'Anfrage-Betriebskostenpruefung')
        return ('Ammerlaender-Wohnungsbau', 'Eigenes-Schreiben')

    # --- Betriebskostenabrechnung ---
    if 'betriebskostenabrechnung' in t:
        return ('Ammerlaender-Wohnungsbau', 'Betriebskostenabrechnung')

    # --- Techem = Ammerländer Wohnungsbau ---
    if ('heizkostenabrechnung' in t or 'heiz- und kaltwasser' in t or
        ('kostenabrechnung' in t and ('heiz' in t or 'kaltwasser' in t))):
        if ('erläuterung' in t or ('erl' in t and 'uterung' in t)) and 'co' in t:
            return ('Ammerlaender-Wohnungsbau', 'Heizkostenabrechnung-CO2-Aufteilung')
        return ('Ammerlaender-Wohnungsbau', 'Heizkostenabrechnung-Uebersicht')

    if 'kostenaufstellung' in t and ('erdgas' in t or 'nutzer-nr' in t):
        return ('Ammerlaender-Wohnungsbau', 'Heizkostenabrechnung-Kostenaufstellung')

    if ('energiekosten' in t or 'energieverbrauch' in t) and 'nutzer-nr' in t:
        if 'wasserverbrauch' in t or 'kaltwasser' in t:
            return ('Ammerlaender-Wohnungsbau', 'Heizkostenabrechnung-Wasserverbrauch')
        return ('Ammerlaender-Wohnungsbau', 'Heizkostenabrechnung-Energiekosten')

    if 'verbrauchsanalyse' in t:
        return ('Ammerlaender-Wohnungsbau', 'Heizkostenabrechnung-Verbrauchsanalyse')

    if ('auftraggeber' in t and ('ammerlõnder' in t or 'ammerlander' in t or 'ammerl' in t)):
        return ('Ammerlaender-Wohnungsbau', 'Heizkostenabrechnung-Detail')

    if 'nutzer-nr' in t and ('techem' in t or 'verteilschl' in t or ('abk' in t and 'rzung' in t)):
        return ('Ammerlaender-Wohnungsbau', 'Heizkostenabrechnung-Abkuerzungen')

    # --- Ammerländer Wohnungsbau Schreiben ---
    if ('ammerlõnder' in t or 'ammerlaender' in t or 'ammerlander' in t or
        ('ammerl' in t and 'wohnungsbau' in t)):
        if 'mietverhõltnis' in t or 'mietverh' in t:
            if 'dachboden' in t:
                return ('Ammerlaender-Wohnungsbau', 'Mietschreiben-Dachbodenraeumung')
            return ('Ammerlaender-Wohnungsbau', 'Mietschreiben')
        if 'mietr³ckstand' in t or 'mietrueckstand' in t or 'zahlungserinnerung' in t:
            return ('Ammerlaender-Wohnungsbau', 'Zahlungserinnerung-Mietrueckstand')
        if 'abrechnung der umlagen' in t or 'betriebskosten' in t:
            return ('Ammerlaender-Wohnungsbau', 'Begleitschreiben-Betriebskostenabrechnung')
        if 'mietanpassung' in t or 'mieterh' in t:
            return ('Ammerlaender-Wohnungsbau', 'Mietanpassung')
        return ('Ammerlaender-Wohnungsbau', 'Schreiben')

    # --- Vodafone ---
    if 'vodafone' in t:
        return ('Vodafone', 'Rechnung')

    # --- EWE ---
    if ('ewe vertrieb' in t or 'ewe netz' in t or
        ('ewe' in t and ('strom' in t or 'abschlag' in t or 'jahresrechnung' in t or 'kunden-nr' in t))):
        if 'abschlag' in t:
            return ('EWE', 'Stromabschlag')
        if 'jahresrechnung' in t:
            return ('EWE', 'Jahresrechnung-Strom')
        return ('EWE', 'Stromrechnung')

    # --- Fallback ---
    return ('Unbekannt', 'Dokument')


def generate_rename_map(pdf_dir):
    """Generiert eine Map von altem zu neuem Dateinamen."""
    files = sorted([f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')])

    classifications = []
    for f in files:
        filepath = os.path.join(pdf_dir, f)
        text = extract_text(filepath)
        firma, doktyp = classify_document(text)
        year, month, day = find_full_date(text, filepath)
        date_str = f'{year}-{month}-{day}'
        base_name = f'{date_str}_{firma}_{doktyp}'
        classifications.append((f, base_name, text[:100]))

    # Gruppierung und Nummerierung
    name_counts = defaultdict(list)
    for old_name, base_name, preview in classifications:
        name_counts[base_name].append((old_name, preview))

    rename_map = {}
    for base_name, entries in name_counts.items():
        if len(entries) == 1:
            old_name = entries[0][0]
            rename_map[old_name] = f'{base_name}.pdf'
        else:
            for idx, (old_name, preview) in enumerate(entries, 1):
                rename_map[old_name] = f'{base_name}_Seite{idx}.pdf'

    return rename_map


def main():
    print("=" * 70)
    print("  PDF-Analyse und intelligente Umbenennung")
    print("=" * 70)
    print(f"\nVerzeichnis: {PDF_DIR}")
    print("Analysiere PDFs...\n")

    rename_map = generate_rename_map(PDF_DIR)
    sorted_renames = sorted(rename_map.items(), key=lambda x: x[1])

    print(f"{'Nr':>3}  {'Neuer Name':<80}  {'Alter Name'}")
    print("-" * 160)

    for i, (old_name, new_name) in enumerate(sorted_renames, 1):
        print(f"{i:>3}  {new_name:<80}  {old_name}")

    print(f"\n{len(rename_map)} Dateien werden umbenannt.")

    new_names = list(rename_map.values())
    duplicates = [n for n in new_names if new_names.count(n) > 1]
    if duplicates:
        print(f"\n⚠ WARNUNG: Namenskonflikte gefunden: {set(duplicates)}")
        return

    if '--dry-run' in sys.argv:
        print("\n(Dry-Run Modus - keine Änderungen vorgenommen)")
        return

    print("\nMöchtest du die Umbenennung durchführen? (j/n): ", end="", flush=True)
    answer = input().strip().lower()

    if answer in ('j', 'ja', 'y', 'yes'):
        print("\nBenenne um...")
        success = 0
        for old_name, new_name in sorted_renames:
            old_path = os.path.join(PDF_DIR, old_name)
            new_path = os.path.join(PDF_DIR, new_name)
            try:
                os.rename(old_path, new_path)
                print(f"  ✓ {new_name}")
                success += 1
            except Exception as e:
                print(f"  ✗ {old_name} -> {new_name}: {e}")
        print(f"\n{success}/{len(rename_map)} Dateien erfolgreich umbenannt.")
    else:
        print("Umbenennung abgebrochen.")


if __name__ == "__main__":
    main()
