import os
import re
import sys
import glob
import json
from typing import Optional, Dict
from paddleocr import PaddleOCR

ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

def _normalize_letters(text: str) -> str:
    # Keep only a-z for robust contains checks (removes spaces/punct/diacritics)
    return re.sub(r'[^a-z]', '', text.lower())

def _fix_or_suggest_path(path_in: str) -> Optional[str]:
    """
    Try to fix common extension typos and find a matching file in the same folder.
    Returns a corrected path if found; otherwise None.
    """
    candidate = path_in
    if os.path.exists(candidate):
        return candidate

    base_dir = os.path.dirname(candidate) or "."
    base_name = os.path.basename(candidate)
    stem, ext = os.path.splitext(base_name)

    # Fix the common .jepg typo
    if ext.lower() == ".jepg":
        for alt_ext in (".jpeg", ".jpg"):
            fixed = os.path.join(base_dir, stem + alt_ext)
            if os.path.exists(fixed):
                return fixed

    # If extension missing or wrong, try any allowed extension with same stem
    for ext_try in ALLOWED_EXTS:
        try_path = os.path.join(base_dir, stem + ext_try)
        if os.path.exists(try_path):
            return try_path

    # Last chance: glob nearby similar names (case-insensitive)
    pattern = os.path.join(base_dir, f"{stem}.*")
    for found in glob.glob(pattern):
        if os.path.splitext(found)[1].lower() in ALLOWED_EXTS:
            return found

    return None

def _friendly_missing_message(bad_path: str):
    base_dir = os.path.dirname(bad_path) or "."
    msg = [f"File not found: {bad_path}"]
    msg.append("Tips:")
    msg.append("  • Check spelling (.jpeg/.jpg, not .jepg).")
    msg.append("  • Put quotes around paths with spaces.")
    msg.append(f"  • Looked in: {os.path.abspath(base_dir)}")
    # Show up to 10 image files in that directory
    imgs = []
    for ext in ALLOWED_EXTS:
        imgs.extend(glob.glob(os.path.join(base_dir, f"*{ext}")))
    imgs = sorted(imgs)[:10]
    if imgs:
        msg.append("  • Nearby image files:")
        for f in imgs:
            msg.append(f"      - {os.path.basename(f)}")
    print("\n".join(msg))

def extract_marksheet_details(image_path: str) -> Dict[str, str]:
    # Initialize OCR (CPU by default). Suppress verbose logs for clarity.
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

    # Run OCR
    results = ocr.ocr(image_path, cls=True)
    if not results or not results[0]:
        return {"Medium": "Unknown", "Class": "Unknown", "Student Name": "Not Found"}

    # Collect text lines in reading order
    lines_raw = [box[1][0] for box in results[0] if box and box[1] and box[1][0]]
    full_text_raw = " ".join(lines_raw)
    full_text_lc = full_text_raw.lower()
    full_text_norm = _normalize_letters(full_text_raw)

    # -------- 1) Medium (CBSE) --------
    # Handle OCR spacing/typos like "centeral board ofsecondary education"
    medium = "Unknown"
    cbse_patterns_norm = [
        "centralboardofsecondaryeducation",
        "centeralboardofsecondaryeducation",  # common misspelling "centeral"
    ]
    if any(pat in full_text_norm for pat in cbse_patterns_norm):
        medium = "CBSE"

    # -------- 2) Class (10 or 12) --------
    # Class 10: "secondary school examination"
    # Class 12: "senior school certificate examination"
    marksheet_class = "Unknown"
    if "secondaryschoolexamination" in full_text_norm:
        marksheet_class = "Class 10"
    if "seniorschoolcertificateexamination" in full_text_norm:
        # If both appear (rare in templates), Class 12 should take precedence
        marksheet_class = "Class 12"

    # -------- 3) Student Name (after "this is to c/sertify that") --------
    # Be tolerant to OCR mistakes: 'certify' vs 'sertify', punctuation/noises.
    # Stop extraction before common tokens like S/O, Roll, has, of class, etc.
    name = "Not Found"
    name_patterns = [
        r"(?i)this\s+is\s+to\s+c(?:e|s)rtify\s+that[:,\-]?\s*"
        r"([A-Za-z.\- ]{3,80}?)(?=\s+(?:s\/o|d\/o|w\/o|son|daughter|roll|regn|registration|has|of\s+class|vide|dated|dob|born|candidate|enrol|admission|exam|mark|year|the)|\s*$)"
    ]
    for pat in name_patterns:
        m = re.search(pat, full_text_raw)
        if m:
            candidate = m.group(1).strip()

            # Remove leading honorifics
            candidate = re.sub(
                r"(?i)^(?:mr|mrs|ms|miss|master|mast|kum|ku\.|sri|shri|smt)\s+",
                "",
                candidate,
            )

            # Clean duplicates/spaces and trailing punctuation
            candidate = re.sub(r"\s{2,}", " ", candidate)
            candidate = re.sub(r"[,\.;:]+$", "", candidate).strip()

            # If the whole certificate is uppercase, title-case it; otherwise keep as is
            if candidate.isupper():
                candidate = candidate.title()

            # Keep only reasonable name chars
            candidate = re.sub(r"[^A-Za-z.\- ]", "", candidate).strip()

            # Sanity: require at least one space (first + last)
            if len(candidate.split()) >= 2:
                name = candidate
            else:
                # Sometimes OCR splits badly; accept single token but keep it
                name = candidate if candidate else "Not Found"
            break

    return {"Medium": medium, "Class": marksheet_class, "Student Name": name}


def main():
    # Read image path (CLI arg preferred; falls back to prompt)
    if len(sys.argv) >= 2:
        inp_path = sys.argv[1]
    else:
        inp_path = input("Enter path to CBSE marksheet image: ").strip()

    fixed = _fix_or_suggest_path(inp_path)
    if not fixed:
        _friendly_missing_message(inp_path)
        sys.exit(1)

    print(f"Using file: {fixed}")
    details = extract_marksheet_details(fixed)
    print(json.dumps(details, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
