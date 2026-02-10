import sys
import os
import io
import time
import shutil
import msvcrt

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
    ROCKET   = "🚀"
    FOLDER   = "📁"
    SPARKLE  = "✨"
    WARN     = "⚠"
    CLOCK    = "⏱"
    BAR_FULL = "█"
    BAR_EMPTY= "░"

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
        print(f"  {Style.WHITE}{Style.BOLD}  [LEERTASTE]{Style.RESET}  Starten     {Style.WHITE}{Style.BOLD}[ESC]{Style.RESET}  Beenden")
        print(f"  {Style.DIM}{'─' * 54}{Style.RESET}\n")

def wait_for_key(prompt_message="", allow_esc=True):
    """Wait for spacebar (proceed) or ESC (exit). Returns True to proceed, False to exit."""
    if prompt_message:
        print(prompt_message)
    while True:
        key = msvcrt.getch()
        if key == b' ':      # Spacebar
            return True
        elif key == b'\x1b' and allow_esc:  # ESC
            return False
        elif key == b'\x00' or key == b'\xe0':  # Special keys (arrows etc.) – consume second byte
            msvcrt.getch()
            continue

def print_section(title, icon=""):
    """Print a styled section header."""
    print(f"\n{Style.BOLD}{Style.BLUE}{'─' * 58}{Style.RESET}")
    print(f"  {icon}  {Style.BOLD}{Style.WHITE}{title}{Style.RESET}")
    print(f"{Style.BOLD}{Style.BLUE}{'─' * 58}{Style.RESET}")

def print_step(number, total, message):
    """Print a numbered step."""
    print(f"  {Style.CYAN}[{number}/{total}]{Style.RESET} {message}")

def print_success(message):
    """Print a success message."""
    print(f"  {Style.GREEN}{Style.CHECK}  {message}{Style.RESET}")

def print_skip(message):
    """Print a skip/info message."""
    print(f"  {Style.YELLOW}{Style.ARROW}  {message}{Style.RESET}")

def print_error(message):
    """Print an error message."""
    print(f"  {Style.RED}{Style.CROSS}  {message}{Style.RESET}")

def print_info(message):
    """Print an info message."""
    print(f"  {Style.GRAY}{Style.DOTS}  {message}{Style.RESET}")

def progress_bar(current, total, width=30, label=""):
    """Print a dynamic progress bar."""
    filled = int(width * current / total)
    bar = Style.GREEN + Style.BAR_FULL * filled + Style.GRAY + Style.BAR_EMPTY * (width - filled) + Style.RESET
    percent = current / total * 100
    sys.stdout.write(f"\r  {Style.GEAR}  {bar}  {Style.BOLD}{percent:5.1f}%{Style.RESET}  {Style.DIM}{label}{Style.RESET}  ")
    sys.stdout.flush()
    if current == total:
        sys.stdout.write("\n")

def format_size(size_bytes):
    """Format file size in human-readable form."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

def format_duration(seconds):
    """Format duration in human-readable form."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m {secs:.0f}s"

# ─── Dependencies Check ─────────────────────────────────────────────────────
try:
    from pypdf import PdfReader, PdfWriter
    import pytesseract
    from PIL import Image
    import fitz  # PyMuPDF – renders pages as images (preserves orientation)
except ImportError:
    print(f"\n  {Style.RED}{Style.CROSS}  Fehlende Abhängigkeiten! Bitte installieren:{Style.RESET}")
    print(f"  {Style.YELLOW}     pip install pypdf pytesseract Pillow PyMuPDF{Style.RESET}\n")
    sys.exit(1)

# ─── Tesseract Configuration ────────────────────────────────────────────────
possible_tesseract_paths = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Users\danie\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
]

tesseract_cmd = None
if shutil.which("tesseract"):
    tesseract_cmd = "tesseract"
else:
    for path in possible_tesseract_paths:
        if os.path.exists(path):
            tesseract_cmd = path
            break

if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
else:
    print(f"\n  {Style.RED}{Style.CROSS}  Tesseract-OCR nicht gefunden!{Style.RESET}")
    print(f"  {Style.YELLOW}     Installation: winget install UB-Mannheim.TesseractOCR{Style.RESET}")
    print(f"  {Style.GRAY}     https://github.com/UB-Mannheim/tesseract/wiki{Style.RESET}\n")
    sys.exit(1)

# ─── Core Functions ──────────────────────────────────────────────────────────
def is_pdf_searchable(pdf_path):
    """Checks if a PDF has significant text content."""
    try:
        reader = PdfReader(pdf_path)
        text_content = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_content += text
        return len(text_content.strip()) > 50
    except Exception:
        return False

def ocr_pdf(input_path, output_path, pages_done_before=0, total_pages_all=0):
    """Performs OCR on a PDF file with progress reporting.
    
    Uses PyMuPDF to render each page as an image (preserving all
    transformations like rotation/mirroring) before passing to Tesseract.
    The resulting OCR pages are scaled back to the original page dimensions.
    
    Args:
        pages_done_before: Number of pages already processed in previous files.
        total_pages_all:   Total pages across all files to process (for global progress).
    """
    try:
        doc = fitz.open(input_path)
        writer = PdfWriter()

        total_pages = len(doc)
        # Fall back to per-file progress if no global total provided
        if total_pages_all <= 0:
            total_pages_all = total_pages
            pages_done_before = 0

        for i, page in enumerate(doc):
            global_done = pages_done_before + i + 1
            progress_bar(
                global_done, total_pages_all,
                label=f"Seite {i+1}/{total_pages} · Gesamt {global_done}/{total_pages_all}"
            )

            # Remember original page dimensions (in points, 72 DPI)
            orig_width = page.rect.width
            orig_height = page.rect.height

            # Render page at 300 DPI – exactly as it visually appears
            mat = fitz.Matrix(300 / 72, 300 / 72)
            pix = page.get_pixmap(matrix=mat)
            pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            try:
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(pil_image, extension='pdf', lang='eng+deu')
            except pytesseract.TesseractError:
                pdf_bytes = pytesseract.image_to_pdf_or_hocr(pil_image, extension='pdf', lang='eng')

            ocr_page = PdfReader(io.BytesIO(pdf_bytes)).pages[0]

            # Scale OCR page back to original dimensions
            ocr_mb = ocr_page.mediabox
            ocr_width = float(ocr_mb.width)
            if ocr_width > 0:
                scale = orig_width / ocr_width
                ocr_page.scale_by(scale)

            writer.add_page(ocr_page)

        doc.close()

        with open(output_path, "wb") as f:
            writer.write(f)

        return True

    except Exception as e:
        print_error(f"Fehler: {e}")
        return False

# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    # ── Clear screen and show banner ──────────────────────────────────────
    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner(show_hint=True)

    # ── Wait for user to start ───────────────────────────────────────────
    if not wait_for_key():
        print(f"\n  {Style.YELLOW}{Style.ARROW}  Programm beendet.{Style.RESET}\n")
        return

    os.system('cls' if os.name == 'nt' else 'clear')
    print_banner(show_hint=False)
    total_start = time.time()

    current_dir = os.getcwd()

    # ── Step 1: Setup ────────────────────────────────────────────────────
    print_section("Konfiguration", Style.GEAR)
    print_info(f"Tesseract:  {Style.WHITE}{tesseract_cmd}{Style.RESET}")
    print_info(f"Verzeichnis: {Style.WHITE}{current_dir}{Style.RESET}")

    # ── Step 2: Scan ─────────────────────────────────────────────────────
    print_section("Verzeichnis scannen", Style.FOLDER)
    all_pdfs = sorted([f for f in os.listdir(current_dir) if f.lower().endswith('.pdf')])
    # Filter out already-processed files
    pdf_files = [f for f in all_pdfs if not f.endswith("_searchable.pdf")]

    if not pdf_files:
        print_skip("Keine PDF-Dateien in diesem Verzeichnis gefunden.")
        return

    print_info(f"{Style.WHITE}{len(pdf_files)}{Style.RESET}{Style.GRAY} PDF-Dateien gefunden:")
    for pdf in pdf_files:
        size = format_size(os.path.getsize(pdf))
        print(f"      {Style.DOC}  {Style.WHITE}{pdf}{Style.RESET}  {Style.DIM}({size}){Style.RESET}")

    # ── Step 3: Analyze & Process ────────────────────────────────────────
    print_section("Analyse & Verarbeitung", Style.SEARCH)

    results_ocr = []       # Successfully OCR'd
    results_skipped = []   # Already searchable
    results_exists = []    # Output already exists
    results_failed = []    # Errors

    # ── Pre-scan: determine which files need OCR and count total pages ──
    files_to_ocr = []      # (pdf_file, output_file, page_count)
    for pdf_file in pdf_files:
        base_name = os.path.splitext(pdf_file)[0]
        output_file = f"{base_name}_searchable.pdf"

        if os.path.exists(output_file):
            results_exists.append(pdf_file)
            continue
        if is_pdf_searchable(pdf_file):
            results_skipped.append(pdf_file)
            continue

        try:
            tmp_doc = fitz.open(pdf_file)
            page_count = len(tmp_doc)
            tmp_doc.close()
        except Exception:
            page_count = 1  # fallback
        files_to_ocr.append((pdf_file, output_file, page_count))

    total_pages_all = sum(pc for _, _, pc in files_to_ocr)

    # Report skipped / existing files
    if results_exists:
        for f in results_exists:
            print_skip(f"Übersprungen: {Style.DIM}{os.path.splitext(f)[0]}_searchable.pdf existiert bereits.{Style.RESET}")
    if results_skipped:
        for f in results_skipped:
            print_skip(f"Übersprungen: {Style.DIM}{f} – bereits durchsuchbar.{Style.RESET}")

    if not files_to_ocr:
        print_skip("Keine Dateien benötigen OCR.")
    else:
        print_info(f"{Style.WHITE}{len(files_to_ocr)}{Style.RESET}{Style.GRAY} Datei(en) mit insgesamt {Style.WHITE}{total_pages_all}{Style.RESET}{Style.GRAY} Seiten werden verarbeitet.")

    # ── Process files that need OCR ──────────────────────────────────────
    pages_done = 0
    for idx, (pdf_file, output_file, page_count) in enumerate(files_to_ocr, 1):
        print_step(idx, len(files_to_ocr), f"{Style.WHITE}{pdf_file}{Style.RESET}")
        print_info(f"Starte OCR  {Style.ARROW}  {Style.CYAN}{output_file}{Style.RESET}")

        start_time = time.time()
        success = ocr_pdf(pdf_file, output_file, pages_done, total_pages_all)
        elapsed = time.time() - start_time
        pages_done += page_count

        if success:
            in_size = format_size(os.path.getsize(pdf_file))
            out_size = format_size(os.path.getsize(output_file))
            print_success(f"Fertig in {Style.BOLD}{format_duration(elapsed)}{Style.RESET}{Style.GREEN}  ({in_size} → {out_size}){Style.RESET}")
            results_ocr.append((pdf_file, output_file, elapsed))
        else:
            print_error(f"Fehler bei der Verarbeitung von {pdf_file}")
            results_failed.append(pdf_file)

    # ── Step 4: Summary ──────────────────────────────────────────────────
    total_elapsed = time.time() - total_start

    print_section("Zusammenfassung", Style.SPARKLE)

    # Stats line
    total = len(pdf_files)
    print(f"""
  {Style.BOLD}{Style.WHITE}Ergebnis:{Style.RESET}
      Dateien gesamt:       {Style.BOLD}{total}{Style.RESET}
      {Style.GREEN}{Style.CHECK}  OCR durchgeführt:    {len(results_ocr)}{Style.RESET}
      {Style.YELLOW}{Style.ARROW}  Bereits durchsuchbar: {len(results_skipped)}{Style.RESET}
      {Style.YELLOW}{Style.ARROW}  Bereits vorhanden:   {len(results_exists)}{Style.RESET}
      {Style.RED}{Style.CROSS}  Fehler:              {len(results_failed)}{Style.RESET}
""")

    # List of processed files
    if results_ocr:
        print(f"  {Style.BOLD}{Style.GREEN}Bearbeitete Dateien:{Style.RESET}")
        print(f"  {Style.GREEN}{'─' * 54}{Style.RESET}")
        for original, output, elapsed in results_ocr:
            print(f"      {Style.DOC}  {Style.WHITE}{original}{Style.RESET}")
            print(f"         {Style.ARROW}  {Style.CYAN}{output}{Style.RESET}  {Style.DIM}({format_duration(elapsed)}){Style.RESET}")
        print(f"  {Style.GREEN}{'─' * 54}{Style.RESET}")

    if results_skipped:
        print(f"\n  {Style.BOLD}{Style.YELLOW}Übersprungen (bereits durchsuchbar):{Style.RESET}")
        for f in results_skipped:
            print(f"      {Style.DOC}  {Style.DIM}{f}{Style.RESET}")

    if results_failed:
        print(f"\n  {Style.BOLD}{Style.RED}Fehlgeschlagen:{Style.RESET}")
        for f in results_failed:
            print(f"      {Style.CROSS}  {f}")

    # Footer
    print(f"""
{Style.CYAN}{Style.BOLD}╔══════════════════════════════════════════════════════════╗
║  {Style.WHITE}{Style.CLOCK}  Gesamtdauer: {format_duration(total_elapsed):<42}{Style.CYAN}║
╚══════════════════════════════════════════════════════════╝{Style.RESET}
""")

    # ── Wait for user to close ───────────────────────────────────────────
    print(f"  {Style.DIM}{'─' * 54}{Style.RESET}")
    print(f"  {Style.WHITE}{Style.BOLD}  [LEERTASTE]{Style.RESET}  Programm beenden")
    print(f"  {Style.DIM}{'─' * 54}{Style.RESET}")
    wait_for_key(allow_esc=False)
    print(f"\n  {Style.GREEN}{Style.CHECK}  Auf Wiedersehen!{Style.RESET}\n")

if __name__ == "__main__":
    main()
