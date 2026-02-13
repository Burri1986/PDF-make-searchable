import sys
import os
import io
import time
import shutil
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor

# ─── Console Colors & Styling ───────────────────────────────────────────────
class Style:
    """ANSI escape codes for colored & styled console output."""
    RESET    = "\033[0m"
    BOLD     = "\033[1m"
    DIM      = "\033[2m"
    
    # Colors
    GREEN    = "\033[92m"
    YELLOW   = "\033[93m"
    RED      = "\033[91m"
    CYAN     = "\033[96m"
    MAGENTA  = "\033[95m"
    BLUE     = "\033[94m"
    WHITE    = "\033[97m"
    GRAY     = "\033[90m"

    # Icons
    CHECK    = "✔"
    CROSS    = "✘"
    ARROW    = "→"
    DOTS     = "…"
    GEAR     = "⚙"
    DOC      = "📄"
    SEARCH   = "🔍"
    ROCKET   = "🚀"  # War vorhin verschwunden
    FOLDER   = "📁"  # War vorhin verschwunden (Fehlerursache)
    SPARKLE  = "✨"  # War vorhin verschwunden
    WARN     = "⚠"
    CLOCK    = "⏱"
    TRASH    = "🗑"
    SPLIT    = "✂"

def print_banner(show_hint=True):
    """Print a styled application banner."""
    banner = f"""
{Style.CYAN}{Style.BOLD}╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   {Style.WHITE}{Style.BOLD}  PDF OCR Tool  –  Make PDFs Searchable  {Style.CYAN}{Style.BOLD}             ║
║                                                          ║
║   {Style.GRAY}{Style.DIM}  powered by https://crypto-burri.de      {Style.CYAN}{Style.BOLD}             ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝{Style.RESET}
"""
    print(banner)
    if show_hint:
        print(f"  {Style.DIM}{'─' * 54}{Style.RESET}")
        print(f"  {Style.WHITE}{Style.BOLD}  [ENTER]{Style.RESET}  Starten     {Style.WHITE}{Style.BOLD}[STRG+C]{Style.RESET}  Beenden")
        print(f"  {Style.DIM}{'─' * 54}{Style.RESET}\n")

def wait_for_key(prompt_message=""):
    """Wait for user input (Enter) to proceed."""
    if prompt_message:
        print(prompt_message)
    try:
        input()
        return True
    except KeyboardInterrupt:
        return False

def get_user_confirmation(question, default="n"):
    """Ask a yes/no question."""
    valid = {"j": True, "y": True, "n": False}
    prompt = f"  {Style.YELLOW}?{Style.RESET}  {question} [j/n] (Standard: {default}): "
    while True:
        choice = input(prompt).lower().strip()
        if choice == "":
            return valid.get(default, False)
        if choice in valid:
            return valid[choice]
        print(f"  {Style.RED}Bitte 'j' oder 'n' eingeben.{Style.RESET}")

def print_section(title, icon=""):
    print(f"\n{Style.BOLD}{Style.BLUE}{'─' * 58}{Style.RESET}")
    print(f"  {icon}  {Style.BOLD}{Style.WHITE}{title}{Style.RESET}")
    print(f"{Style.BOLD}{Style.BLUE}{'─' * 58}{Style.RESET}")

def print_step(number, total, message):
    print(f"  {Style.CYAN}[{number}/{total}]{Style.RESET} {message}")

def print_success(message):
    print(f"  {Style.GREEN}{Style.CHECK}  {message}{Style.RESET}")

def print_skip(message):
    print(f"  {Style.YELLOW}{Style.ARROW}  {message}{Style.RESET}")

def print_error(message):
    print(f"  {Style.RED}{Style.CROSS}  {message}{Style.RESET}")

def print_info(message):
    print(f"  {Style.GRAY}{Style.DOTS}  {message}{Style.RESET}")

def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def format_duration(seconds):
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.0f}s"

# ─── Dependencies Check & Configuration ─────────────────────────────────────
os.environ["OMP_THREAD_LIMIT"] = "1"

try:
    import pytesseract
    from PIL import Image
    import fitz  # PyMuPDF
except ImportError:
    print(f"\n  {Style.RED}{Style.CROSS}  Fehlende Abhängigkeiten! Bitte installieren:{Style.RESET}")
    print(f"  {Style.YELLOW}     pip install pytesseract Pillow PyMuPDF{Style.RESET}\n")
    sys.exit(1)

# ─── Tesseract Configuration Helper ─────────────────────────────────────────
def get_tesseract_cmd():
    if os.name == 'nt':
        possible_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Users\danie\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
        ]
        if shutil.which("tesseract"):
            return "tesseract"
        for path in possible_paths:
            if os.path.exists(path):
                return path
    else:
        if shutil.which("tesseract"):
            return "tesseract"
    return None

def get_best_language(tesseract_cmd):
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        try:
            langs = pytesseract.get_languages()
            if 'deu' in langs and 'eng' in langs:
                return 'eng+deu'
            elif 'deu' in langs:
                return 'deu'
        except Exception:
            pass
    return 'eng'

# ─── Core Functions ──────────────────────────────────────────────────────────

def is_pdf_searchable(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        text_content = ""
        for page in doc:
            text = page.get_text()
            if text:
                text_content += text
            if len(text_content) > 50:
                break
        doc.close()
        return len(text_content.strip()) > 50
    except Exception:
        return False

def process_single_file(args):
    """
    Worker function. 
    Returns: (Success, InputPath, ListOfOutputPaths, ElapsedTime, ErrorMsg)
    """
    input_path, base_output_path, tesseract_path, lang, split_mode = args
    
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    src_doc = None
    # We might have multiple output docs if splitting
    created_files = [] 
    
    try:
        start_time = time.time()
        src_doc = fitz.open(input_path)
        OCR_DPI = 300
        
        # If splitting is active, we create a file per page.
        # If not, we create one file for all pages.
        
        # Logic for NON-SPLIT (Standard)
        if not split_mode:
            out_doc = fitz.open()
            try:
                for i, page in enumerate(src_doc):
                    # 1. Image Extraction / Rendering
                    images = page.get_images()
                    pil_image = None
                    if len(images) == 1:
                        try:
                            xref = images[0][0]
                            base_image = src_doc.extract_image(xref)
                            pil_image = Image.open(io.BytesIO(base_image["image"]))
                        except Exception: pass
                    
                    if pil_image is None:
                        mat = fitz.Matrix(OCR_DPI/72, OCR_DPI/72)
                        pix = page.get_pixmap(matrix=mat)
                        pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                    # 2. OCR
                    try:
                        pdf_bytes = pytesseract.image_to_pdf_or_hocr(pil_image, extension='pdf', lang=lang)
                    except pytesseract.TesseractError:
                        pdf_bytes = pytesseract.image_to_pdf_or_hocr(pil_image, extension='pdf', lang='eng')

                    # 3. Insert
                    with fitz.open("pdf", pdf_bytes) as ocr_pdf:
                        out_doc.insert_pdf(ocr_pdf)

                # Metadata & Save
                out_doc.set_metadata(src_doc.metadata)
                try: out_doc.set_toc(src_doc.get_toc())
                except: pass
                
                out_doc.save(base_output_path, deflate=True, garbage=4, clean=True)
                created_files.append(base_output_path)
                
            finally:
                out_doc.close()

        # Logic for SPLIT MODE
        else:
            base_name_no_ext = os.path.splitext(base_output_path)[0]
            # Clean up the name if it ends in _searchable to make numbering nicer
            # e.g. "invoice_searchable.pdf" -> "invoice_searchable_p01.pdf"
            
            for i, page in enumerate(src_doc):
                # Page number formatting: 01, 02 etc.
                page_out_path = f"{base_name_no_ext}_p{i+1:02d}.pdf"
                out_doc = fitz.open() # New doc for THIS page
                
                try:
                    # 1. Image Extraction / Rendering
                    images = page.get_images()
                    pil_image = None
                    if len(images) == 1:
                        try:
                            xref = images[0][0]
                            base_image = src_doc.extract_image(xref)
                            pil_image = Image.open(io.BytesIO(base_image["image"]))
                        except Exception: pass
                    
                    if pil_image is None:
                        mat = fitz.Matrix(OCR_DPI/72, OCR_DPI/72)
                        pix = page.get_pixmap(matrix=mat)
                        pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                    # 2. OCR
                    try:
                        pdf_bytes = pytesseract.image_to_pdf_or_hocr(pil_image, extension='pdf', lang=lang)
                    except pytesseract.TesseractError:
                        pdf_bytes = pytesseract.image_to_pdf_or_hocr(pil_image, extension='pdf', lang='eng')

                    # 3. Insert
                    with fitz.open("pdf", pdf_bytes) as ocr_pdf:
                        out_doc.insert_pdf(ocr_pdf)
                    
                    # Metadata (Copy from source to this single page)
                    out_doc.set_metadata(src_doc.metadata)
                    
                    out_doc.save(page_out_path, deflate=True, garbage=4, clean=True)
                    created_files.append(page_out_path)
                    
                finally:
                    out_doc.close()

        elapsed = time.time() - start_time
        return (True, input_path, created_files, elapsed, None)

    except Exception as e:
        # If failed, return what we have (or empty list) so main can decide/report
        return (False, input_path, created_files, 0, str(e))
        
    finally:
        if src_doc:
            src_doc.close()

# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner(show_hint=True)

    if not wait_for_key():
        print(f"\n  {Style.YELLOW}{Style.ARROW}  Programm beendet.{Style.RESET}\n")
        return

    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner(show_hint=False)
    
    current_dir = os.getcwd()

    # ── Step 1: Configuration ────────────────────────────────────────────
    print_section("Konfiguration", Style.GEAR)
    print_info(f"Verzeichnis: {Style.WHITE}{current_dir}{Style.RESET}")
    
    tesseract_cmd = get_tesseract_cmd()
    if not tesseract_cmd:
        print(f"\n  {Style.RED}{Style.CROSS}  Tesseract-OCR nicht gefunden!{Style.RESET}")
        sys.exit(1)
        
    ocr_lang = get_best_language(tesseract_cmd)
    print_info(f"Sprache:    {Style.WHITE}{ocr_lang}{Style.RESET}")

    # ── User Options ─────────────────────────────────────────────────────
    print(f"\n  {Style.BOLD}{Style.WHITE}Optionen:{Style.RESET}")
    split_mode = get_user_confirmation(f"Soll ich mehrseitige PDFs in {Style.BOLD}Einzeldateien{Style.RESET} aufteilen?", default="n")
    delete_mode = get_user_confirmation(f"Soll ich die {Style.BOLD}{Style.RED}Original-Dateien löschen{Style.RESET} (nach Erfolg)?", default="n")

    # ── Step 2: Scan ─────────────────────────────────────────────────────
    print_section("Verzeichnis scannen", Style.FOLDER)
    all_pdfs = sorted([f for f in os.listdir(current_dir) if f.lower().endswith('.pdf')])
    # Filter: Don't process files that look like output files
    pdf_files = [f for f in all_pdfs if "_searchable" not in f]

    if not pdf_files:
        print_skip("Keine passenden PDF-Dateien gefunden.")
        return

    print_info(f"{Style.WHITE}{len(pdf_files)}{Style.RESET}{Style.GRAY} PDF-Dateien gefunden:")
    for pdf in pdf_files:
        print(f"      {Style.DOC}  {Style.WHITE}{pdf}{Style.RESET}")

    # ── Step 3: Analyze & Process ────────────────────────────────────────
    print_section("Verarbeitung", Style.ROCKET)

    tasks_to_process = []
    
    for pdf_file in pdf_files:
        base_name = os.path.splitext(pdf_file)[0]
        output_file = f"{base_name}_searchable.pdf"

        # Check: If not splitting, does output exist?
        if not split_mode and os.path.exists(output_file):
            print_skip(f"Übersprungen: {output_file} existiert.")
            continue
        
        # Check: If splitting, we can't easily check all page files in advance without opening doc.
        # So we process and overwrite if necessary, or check is_searchable.
        if is_pdf_searchable(pdf_file):
            print_skip(f"Übersprungen: {pdf_file} ist schon durchsuchbar.")
            continue
            
        tasks_to_process.append((pdf_file, output_file, tesseract_cmd, ocr_lang, split_mode))

    if not tasks_to_process:
        print_skip("Nichts zu tun.")
        wait_for_key()
        return

    max_workers = min(os.cpu_count(), len(tasks_to_process))
    print_info(f"Starte {max_workers} Worker Prozesse...")
    
    results_stats = {"ocr": 0, "failed": 0, "deleted": 0}
    total_start = time.time()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_file, task): task for task in tasks_to_process}
        
        completed_count = 0
        for future in concurrent.futures.as_completed(futures):
            completed_count += 1
            result = future.result()
            success, in_path, out_paths, elapsed, error = result
            
            if success:
                results_stats["ocr"] += 1
                
                # Feedback Output
                if split_mode:
                    msg = f"{Style.WHITE}{in_path}{Style.RESET} {Style.ARROW} {Style.MAGENTA}{len(out_paths)} Seiten{Style.RESET} ({format_duration(elapsed)})"
                else:
                    msg = f"{Style.WHITE}{in_path}{Style.RESET} {Style.ARROW} {Style.GREEN}Fertig{Style.RESET} ({format_duration(elapsed)})"
                
                print_step(completed_count, len(tasks_to_process), msg)
                
                # ── SAFE DELETE LOGIC ──
                if delete_mode:
                    try:
                        # Double check: does input exist?
                        if os.path.exists(in_path):
                            os.remove(in_path)
                            print(f"        {Style.RED}{Style.TRASH}  Original gelöscht.{Style.RESET}")
                            results_stats["deleted"] += 1
                    except Exception as del_err:
                        print_error(f"Konnte Original nicht löschen: {del_err}")

            else:
                results_stats["failed"] += 1
                print_error(f"Fehler bei {in_path}: {error}")

    # ── Step 4: Summary ──────────────────────────────────────────────────
    total_elapsed = time.time() - total_start
    print_section("Zusammenfassung", Style.SPARKLE)
    
    print(f"""
  {Style.BOLD}{Style.WHITE}Statistik:{Style.RESET}
      Dateien bearbeitet:   {results_stats['ocr']}
      {Style.RED}{Style.TRASH}  Originale gelöscht:   {results_stats['deleted']}{Style.RESET}
      {Style.RED}{Style.CROSS}  Fehler:               {results_stats['failed']}{Style.RESET}
""")

    print(f"""
{Style.CYAN}{Style.BOLD}╔══════════════════════════════════════════════════════════╗
║  {Style.WHITE}{Style.CLOCK}  Gesamtdauer: {format_duration(total_elapsed):<42}{Style.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET}
""")

    print(f"  {Style.DIM}{'─' * 54}{Style.RESET}")
    print(f"  {Style.WHITE}{Style.BOLD}  [ENTER]{Style.RESET}  Beenden")
    wait_for_key()

if __name__ == "__main__":
    main()