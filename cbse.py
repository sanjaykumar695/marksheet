#----------------no name ---------------------------------------------

# import os
# import re
# import sys
# import glob
# import json
# from typing import Optional, Dict
# from paddleocr import PaddleOCR

# ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

# def _normalize_letters(text: str) -> str:
#     # Keep only a-z for robust contains checks (removes spaces/punct/diacritics)
#     return re.sub(r'[^a-z]', '', text.lower())

# def _fix_or_suggest_path(path_in: str) -> Optional[str]:
#     """
#     Try to fix common extension typos and find a matching file in the same folder.
#     Returns a corrected path if found; otherwise None.
#     """
#     candidate = path_in
#     if os.path.exists(candidate):
#         return candidate

#     base_dir = os.path.dirname(candidate) or "."
#     base_name = os.path.basename(candidate)
#     stem, ext = os.path.splitext(base_name)

#     # Fix the common .jepg typo
#     if ext.lower() == ".jepg":
#         for alt_ext in (".jpeg", ".jpg"):
#             fixed = os.path.join(base_dir, stem + alt_ext)
#             if os.path.exists(fixed):
#                 return fixed

#     # If extension missing or wrong, try any allowed extension with same stem
#     for ext_try in ALLOWED_EXTS:
#         try_path = os.path.join(base_dir, stem + ext_try)
#         if os.path.exists(try_path):
#             return try_path

#     # Last chance: glob nearby similar names (case-insensitive)
#     pattern = os.path.join(base_dir, f"{stem}.*")
#     for found in glob.glob(pattern):
#         if os.path.splitext(found)[1].lower() in ALLOWED_EXTS:
#             return found

#     return None

# def _friendly_missing_message(bad_path: str):
#     base_dir = os.path.dirname(bad_path) or "."
#     msg = [f"File not found: {bad_path}"]
#     msg.append("Tips:")
#     msg.append("  • Check spelling (.jpeg/.jpg, not .jepg).")
#     msg.append("  • Put quotes around paths with spaces.")
#     msg.append(f"  • Looked in: {os.path.abspath(base_dir)}")
#     # Show up to 10 image files in that directory
#     imgs = []
#     for ext in ALLOWED_EXTS:
#         imgs.extend(glob.glob(os.path.join(base_dir, f"*{ext}")))
#     imgs = sorted(imgs)[:10]
#     if imgs:
#         msg.append("  • Nearby image files:")
#         for f in imgs:
#             msg.append(f"      - {os.path.basename(f)}")
#     print("\n".join(msg))

# def extract_marksheet_details(image_path: str) -> Dict[str, str]:
#     # Initialize OCR (CPU by default). Suppress verbose logs for clarity.
#     ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

#     # Run OCR
#     results = ocr.ocr(image_path, cls=True)
#     if not results or not results[0]:
#         return {"Medium": "Unknown", "Class": "Unknown", "Student Name": "Not Found"}

#     # Collect text lines in reading order
#     lines_raw = [box[1][0] for box in results[0] if box and box[1] and box[1][0]]
#     full_text_raw = " ".join(lines_raw)
#     full_text_lc = full_text_raw.lower()
#     full_text_norm = _normalize_letters(full_text_raw)

#     # -------- 1) Medium (CBSE) --------
#     # Handle OCR spacing/typos like "centeral board ofsecondary education"
#     medium = "Unknown"
#     cbse_patterns_norm = [
#         "centralboardofsecondaryeducation",
#         "centeralboardofsecondaryeducation",  # common misspelling "centeral"
#     ]
#     if any(pat in full_text_norm for pat in cbse_patterns_norm):
#         medium = "CBSE"

#     # -------- 2) Class (10 or 12) --------
#     # Class 10: "secondary school examination"
#     # Class 12: "senior school certificate examination"
#     marksheet_class = "Unknown"
#     if "secondaryschoolexamination" in full_text_norm:
#         marksheet_class = "Class 10"
#     if "seniorschoolcertificateexamination" in full_text_norm:
#         # If both appear (rare in templates), Class 12 should take precedence
#         marksheet_class = "Class 12"

#     # -------- 3) Student Name (after "this is to c/sertify that") --------
#     # Be tolerant to OCR mistakes: 'certify' vs 'sertify', punctuation/noises.
#     # Stop extraction before common tokens like S/O, Roll, has, of class, etc.
#     name = "Not Found"
#     name_patterns = [
#         r"(?i)this\s+is\s+to\s+c(?:e|s)rtify\s+that[:,\-]?\s*"
#         r"([A-Za-z.\- ]{3,80}?)(?=\s+(?:s\/o|d\/o|w\/o|son|daughter|roll|regn|registration|has|of\s+class|vide|dated|dob|born|candidate|enrol|admission|exam|mark|year|the)|\s*$)"
#     ]
#     for pat in name_patterns:
#         m = re.search(pat, full_text_raw)
#         if m:
#             candidate = m.group(1).strip()

#             # Remove leading honorifics
#             candidate = re.sub(
#                 r"(?i)^(?:mr|mrs|ms|miss|master|mast|kum|ku\.|sri|shri|smt)\s+",
#                 "",
#                 candidate,
#             )

#             # Clean duplicates/spaces and trailing punctuation
#             candidate = re.sub(r"\s{2,}", " ", candidate)
#             candidate = re.sub(r"[,\.;:]+$", "", candidate).strip()

#             # If the whole certificate is uppercase, title-case it; otherwise keep as is
#             if candidate.isupper():
#                 candidate = candidate.title()

#             # Keep only reasonable name chars
#             candidate = re.sub(r"[^A-Za-z.\- ]", "", candidate).strip()

#             # Sanity: require at least one space (first + last)
#             if len(candidate.split()) >= 2:
#                 name = candidate
#             else:
#                 # Sometimes OCR splits badly; accept single token but keep it
#                 name = candidate if candidate else "Not Found"
#             break

#     return {"Medium": medium, "Class": marksheet_class, "Student Name": name}


# def main():
#     # Read image path (CLI arg preferred; falls back to prompt)
#     if len(sys.argv) >= 2:
#         inp_path = sys.argv[1]
#     else:
#         inp_path = input("Enter path to CBSE marksheet image: ").strip()

#     fixed = _fix_or_suggest_path(inp_path)
#     if not fixed:
#         _friendly_missing_message(inp_path)
#         sys.exit(1)

#     print(f"Using file: {fixed}")
#     details = extract_marksheet_details(fixed)
#     print(json.dumps(details, indent=2, ensure_ascii=False))


# if __name__ == "__main__":
#     main()



#------------------------------------------------------------------------------------------------------------------
#-----------------------no initial gap-------------------------------------------------------------

# import os
# import re
# import sys
# import glob
# import json
# from typing import Optional, Dict, List
# from paddleocr import PaddleOCR

# ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

# def _normalize_letters(text: str) -> str:
#     return re.sub(r'[^a-z]', '', text.lower())

# def _fix_or_suggest_path(path_in: str) -> Optional[str]:
#     if os.path.exists(path_in):
#         return path_in
#     base_dir = os.path.dirname(path_in) or "."
#     base_name = os.path.basename(path_in)
#     stem, ext = os.path.splitext(base_name)
#     # common typo
#     if ext.lower() == ".jepg":
#         for alt_ext in (".jpeg", ".jpg"):
#             fixed = os.path.join(base_dir, stem + alt_ext)
#             if os.path.exists(fixed):
#                 return fixed
#     # try other extensions
#     for ext_try in ALLOWED_EXTS:
#         try_path = os.path.join(base_dir, stem + ext_try)
#         if os.path.exists(try_path):
#             return try_path
#     # glob near matches
#     pattern = os.path.join(base_dir, f"{stem}.*")
#     for found in glob.glob(pattern):
#         if os.path.splitext(found)[1].lower() in ALLOWED_EXTS:
#             return found
#     return None

# def _friendly_missing_message(bad_path: str):
#     base_dir = os.path.dirname(bad_path) or "."
#     msg = [f"File not found: {bad_path}",
#            "Tips:",
#            "  • Check spelling (.jpeg/.jpg, not .jepg).",
#            "  • Put quotes around paths with spaces.",
#            f"  • Looked in: {os.path.abspath(base_dir)}"]
#     imgs = []
#     for ext in ALLOWED_EXTS:
#         imgs.extend(glob.glob(os.path.join(base_dir, f"*{ext}")))
#     imgs = sorted(imgs)[:10]
#     if imgs:
#         msg.append("  • Nearby image files:")
#         for f in imgs:
#             msg.append(f"      - {os.path.basename(f)}")
#     print("\n".join(msg))

# # Tokens where the student's name should stop before
# STOP_WORDS = [
#     r"s\/o", r"d\/o", r"w\/o", r"son", r"daughter", r"wife", r"husband",
#     r"father", r"mother", r"guardian", r"roll", r"regn", r"registration",
#     r"enrol", r"enrollment", r"admission", r"has", r"have", r"is", r"was",
#     r"of\s+class", r"class\s+\d{1,2}", r"vide", r"dated", r"dob", r"born",
#     r"candidate", r"student", r"exam", r"examination", r"marks?", r"year",
#     r"subject", r"bearing", r"school", r"board", r"regd", r"regn", r"roll\s+no"
# ]
# STOP_TOKENS_RE = re.compile(r"\b(?:" + "|".join(STOP_WORDS) + r")\b", flags=re.I)

# # Honorifics and noisy lead-ins to remove from candidate name
# HONORIFICS_RE = re.compile(r"(?i)^(mr|mrs|ms|miss|master|mast|dr|prof|sir|madam|sri|shri|smt|kum|kumari|ku\.)\s+")
# LEAD_NOISE_RE = re.compile(
#     r"(?i)^(the\s+candidate\s+named\s+|the\s+candidate\s+|the\s+name\s+of\s+the\s+candidate\s+is\s+|"
#     r"the\s+name\s+of\s+candidate\s+is\s+|candidate\s+name\s+|student\s+name\s+|named\s+)"
# )

# def _clean_name(candidate: str) -> str:
#     candidate = candidate.strip().strip('\'"“”‘’')
#     candidate = HONORIFICS_RE.sub("", candidate)
#     candidate = LEAD_NOISE_RE.sub("", candidate)
#     candidate = re.sub(r"\s{2,}", " ", candidate)
#     candidate = re.sub(r"[,\.;:]+$", "", candidate).strip()
#     candidate = re.sub(r"[^A-Za-z.\- ]", "", candidate).strip()
#     if candidate.isupper():
#         candidate = candidate.title()
#     return candidate

# def _clip_at_stop(pool: str) -> str:
#     m = STOP_TOKENS_RE.search(pool)
#     if m:
#         return pool[:m.start()].strip()
#     return pool.strip()

# def extract_marksheet_details(image_path: str) -> Dict[str, str]:
#     ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

#     results = ocr.ocr(image_path, cls=True)
#     if not results or not results[0]:
#         return {"Medium": "Unknown", "Class": "Unknown", "Student Name": "Not Found"}

#     # lines in reading order
#     lines_raw = [box[1][0] for box in results[0] if box and box[1] and box[1][0]]
#     full_text_raw = " ".join(lines_raw)
#     full_text_norm = _normalize_letters(full_text_raw)

#     # Medium detection (CBSE)
#     medium = "Unknown"
#     cbse_variants = ["centralboardofsecondaryeducation", "centeralboardofsecondaryeducation", "cbse"]
#     if any(v in full_text_norm for v in cbse_variants):
#         medium = "CBSE"

#     # Class detection
#     marksheet_class = "Unknown"
#     if "secondaryschoolexamination" in full_text_norm or "aisse" in full_text_norm:
#         marksheet_class = "Class 10"
#     if "seniorschoolcertificateexamination" in full_text_norm or "aissce" in full_text_norm:
#         marksheet_class = "Class 12"

#     # Name extraction — line-oriented anchor search
#     name = None
#     anchor_rx = re.compile(r"(?i)this\W*is\W*to\W*(?:c(?:e|s)rtif|certif|sertif)[a-z]*\W*that\W*")
#     for idx, ln in enumerate(lines_raw):
#         m = anchor_rx.search(ln)
#         if not m:
#             continue
#         after = ln[m.end():].strip()
#         pool = after
#         # If current line doesn't have enough, append next up to 2 lines
#         if len(pool) < 3 and idx + 1 < len(lines_raw):
#             pool = (pool + " " + lines_raw[idx + 1]).strip()
#         if len(pool) < 3 and idx + 2 < len(lines_raw):
#             pool = (pool + " " + lines_raw[idx + 2]).strip()
#         # Clip at stop tokens
#         segment = _clip_at_stop(pool)
#         candidate = _clean_name(segment)
#         # Accept if reasonably looks like a name
#         if candidate and (len(candidate.split()) >= 2 or len(candidate) >= 5):
#             name = candidate
#             break
#         # If we got a short token but there is more text later on the same line, try to extend by tokenizing next words
#         # (already tried next two lines so skip)
#     # Fallback: whole-text regex
#     if not name:
#         text_clean = re.sub(r"\s+", " ", full_text_raw)
#         pattern = re.compile(
#             r"(?i)this\s+is\s+to\s+(?:c(?:e|s)rtif[a-z]*)\s+that[:,\-]?\s*([A-Za-z.\- ]{3,120}?)",
#             flags=re.I
#         )
#         m2 = pattern.search(text_clean)
#         if m2:
#             seg = _clip_at_stop(m2.group(1))
#             candidate = _clean_name(seg)
#             if candidate and (len(candidate.split()) >= 2 or len(candidate) >= 5):
#                 name = candidate

#     if not name or name.strip() == "":
#         name = "Not Found"

#     return {"Medium": medium, "Class": marksheet_class, "Student Name": name}

# def main():
#     if len(sys.argv) >= 2:
#         inp_path = sys.argv[1]
#     else:
#         inp_path = input("Enter path to CBSE marksheet image: ").strip()

#     fixed = _fix_or_suggest_path(inp_path)
#     if not fixed:
#         _friendly_missing_message(inp_path)
#         sys.exit(1)

#     print(f"Using file: {fixed}")
#     details = extract_marksheet_details(fixed)
#     print(json.dumps(details, indent=2, ensure_ascii=False))

# if __name__ == "__main__":
#     main()



#--------------------------------------------------------------------------------------------------
#-----------------------------fine tuned with gap for initial-------------------------------------

import os
import re
import sys
import glob
import json
from typing import Optional, Dict
from paddleocr import PaddleOCR

ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

def _normalize_letters(text: str) -> str:
    return re.sub(r'[^a-z]', '', text.lower())

def _fix_or_suggest_path(path_in: str) -> Optional[str]:
    if os.path.exists(path_in):
        return path_in
    base_dir = os.path.dirname(path_in) or "."
    base_name = os.path.basename(path_in)
    stem, ext = os.path.splitext(base_name)
    if ext.lower() == ".jepg":
        for alt_ext in (".jpeg", ".jpg"):
            fixed = os.path.join(base_dir, stem + alt_ext)
            if os.path.exists(fixed):
                return fixed
    for ext_try in ALLOWED_EXTS:
        try_path = os.path.join(base_dir, stem + ext_try)
        if os.path.exists(try_path):
            return try_path
    pattern = os.path.join(base_dir, f"{stem}.*")
    for found in glob.glob(pattern):
        if os.path.splitext(found)[1].lower() in ALLOWED_EXTS:
            return found
    return None

def _friendly_missing_message(bad_path: str):
    base_dir = os.path.dirname(bad_path) or "."
    msg = [f"File not found: {bad_path}",
           "Tips:",
           "  • Check spelling (.jpeg/.jpg, not .jepg).",
           "  • Put quotes around paths with spaces.",
           f"  • Looked in: {os.path.abspath(base_dir)}"]
    imgs = []
    for ext in ALLOWED_EXTS:
        imgs.extend(glob.glob(os.path.join(base_dir, f"*{ext}")))
    imgs = sorted(imgs)[:10]
    if imgs:
        msg.append("  • Nearby image files:")
        for f in imgs:
            msg.append(f"      - {os.path.basename(f)}")
    print("\n".join(msg))

STOP_WORDS = [
    r"s\/o", r"d\/o", r"w\/o", r"son", r"daughter", r"wife", r"husband",
    r"father", r"mother", r"guardian", r"roll", r"regn", r"registration",
    r"enrol", r"enrollment", r"admission", r"has", r"have", r"is", r"was",
    r"of\s+class", r"class\s+\d{1,2}", r"vide", r"dated", r"dob", r"born",
    r"candidate", r"student", r"exam", r"examination", r"marks?", r"year",
    r"subject", r"bearing", r"school", r"board", r"regd", r"regn", r"roll\s+no"
]
STOP_TOKENS_RE = re.compile(r"\b(?:" + "|".join(STOP_WORDS) + r")\b", flags=re.I)

HONORIFICS_RE = re.compile(r"(?i)^(mr|mrs|ms|miss|master|mast|dr|prof|sir|madam|sri|shri|smt|kum|kumari|ku\.)\s+")
LEAD_NOISE_RE = re.compile(
    r"(?i)^(the\s+candidate\s+named\s+|the\s+candidate\s+|the\s+name\s+of\s+the\s+candidate\s+is\s+|"
    r"the\s+name\s+of\s+candidate\s+is\s+|candidate\s+name\s+|student\s+name\s+|named\s+)"
)

def _clean_name(candidate: str) -> str:
    candidate = candidate.strip().strip('\'"“”‘’')
    candidate = HONORIFICS_RE.sub("", candidate)
    candidate = LEAD_NOISE_RE.sub("", candidate)

    # Replace dots between letters with spaces ("A.K." -> "A K")
    candidate = re.sub(r"(?<=\w)\.(?=\w)", " ", candidate)
    # Remove leftover dots at end
    candidate = candidate.replace(".", " ")

    candidate = re.sub(r"\s{2,}", " ", candidate)
    candidate = re.sub(r"[,\.;:]+$", "", candidate).strip()
    candidate = re.sub(r"[^A-Za-z\- ]", "", candidate).strip()

    if candidate.isupper():
        candidate = candidate.title()

    return candidate

def _clip_at_stop(pool: str) -> str:
    m = STOP_TOKENS_RE.search(pool)
    if m:
        return pool[:m.start()].strip()
    return pool.strip()

def extract_marksheet_details(image_path: str) -> Dict[str, str]:
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    results = ocr.ocr(image_path, cls=True)
    if not results or not results[0]:
        return {"Medium": "Unknown", "Class": "Unknown", "Student Name": "Not Found"}

    lines_raw = [box[1][0] for box in results[0] if box and box[1] and box[1][0]]
    full_text_raw = " ".join(lines_raw)
    full_text_norm = _normalize_letters(full_text_raw)

    medium = "Unknown"
    cbse_variants = ["centralboardofsecondaryeducation", "centeralboardofsecondaryeducation", "cbse"]
    if any(v in full_text_norm for v in cbse_variants):
        medium = "CBSE"

    marksheet_class = "Unknown"
    if "secondaryschoolexamination" in full_text_norm or "aisse" in full_text_norm:
        marksheet_class = "Class 10"
    if "seniorschoolcertificateexamination" in full_text_norm or "aissce" in full_text_norm:
        marksheet_class = "Class 12"

    name = None
    anchor_rx = re.compile(r"(?i)this\W*is\W*to\W*(?:c(?:e|s)rtif|certif|sertif)[a-z]*\W*that\W*")
    for idx, ln in enumerate(lines_raw):
        m = anchor_rx.search(ln)
        if not m:
            continue
        after = ln[m.end():].strip()
        pool = after
        if len(pool) < 3 and idx + 1 < len(lines_raw):
            pool = (pool + " " + lines_raw[idx + 1]).strip()
        if len(pool) < 3 and idx + 2 < len(lines_raw):
            pool = (pool + " " + lines_raw[idx + 2]).strip()
        segment = _clip_at_stop(pool)
        candidate = _clean_name(segment)
        if candidate and (len(candidate.split()) >= 2 or len(candidate) >= 5):
            name = candidate
            break

    if not name:
        text_clean = re.sub(r"\s+", " ", full_text_raw)
        pattern = re.compile(
            r"(?i)this\s+is\s+to\s+(?:c(?:e|s)rtif[a-z]*)\s+that[:,\-]?\s*([A-Za-z.\- ]{3,120}?)",
            flags=re.I
        )
        m2 = pattern.search(text_clean)
        if m2:
            seg = _clip_at_stop(m2.group(1))
            candidate = _clean_name(seg)
            if candidate and (len(candidate.split()) >= 2 or len(candidate) >= 5):
                name = candidate

    if not name or name.strip() == "":
        name = "Not Found"

    return {"Medium": medium, "Class": marksheet_class, "Student Name": name}

def main():
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
