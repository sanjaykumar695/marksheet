# import os
# import re
# import sys
# import glob
# import json
# import tempfile
# import statistics
# import difflib
# from typing import Optional, Dict, List, Any
# from paddleocr import PaddleOCR

# # Optional: OpenCV for preprocessing (install with `pip install opencv-python`)
# try:
#     import cv2
#     _HAS_CV2 = True
# except Exception:
#     _HAS_CV2 = False

# ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

# # Tuning parameters (you can change these)
# VERTICAL_MULTIPLIER = 0.7   # grouping threshold = median_box_height * multiplier
# SUBJECT_MATCH_RATIO = 0.55  # fuzzy match threshold (difflib)
# MARKS_MIN = 0               # minimum plausible mark
# MARKS_MAX = 500             # maximum plausible mark (keeps out roll numbers/IDs)
# DEBUG = False               # set True to print debug info about rows/boxes

# def _normalize_letters(text: str) -> str:
#     return re.sub(r'[^a-z]', '', text.lower() if text else "")

# def _fix_or_suggest_path(path_in: str) -> Optional[str]:
#     if os.path.exists(path_in):
#         return path_in
#     base_dir = os.path.dirname(path_in) or "."
#     base_name = os.path.basename(path_in)
#     stem, ext = os.path.splitext(base_name)
#     if ext.lower() == ".jepg":
#         for alt_ext in (".jpeg", ".jpg"):
#             fixed = os.path.join(base_dir, stem + alt_ext)
#             if os.path.exists(fixed):
#                 return fixed
#     for ext_try in ALLOWED_EXTS:
#         try_path = os.path.join(base_dir, stem + ext_try)
#         if os.path.exists(try_path):
#             return try_path
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

# # Name helpers (kept from your original)
# HONORIFICS_RE = re.compile(r"(?i)^(mr|mrs|ms|miss|master|mast|dr|prof|sir|madam|sri|shri|smt|kum|kumari|ku\.)\s+")
# LEAD_NOISE_RE = re.compile(
#     r"(?i)^(the\s+candidate\s+named\s+|the\s+candidate\s+|the\s+name\s+of\s+the\s+candidate\s+is\s+|"
#     r"the\s+name\s+of\s+candidate\s+is\s+|candidate\s+name\s+|student\s+name\s+|named\s+)"
# )

# def _clean_name(candidate: str) -> str:
#     if not candidate:
#         return ""
#     candidate = candidate.strip().strip('\'"“”‘’')
#     candidate = HONORIFICS_RE.sub("", candidate)
#     candidate = LEAD_NOISE_RE.sub("", candidate)
#     candidate = re.sub(r"\s{2,}", " ", candidate)
#     candidate = re.sub(r"[,\.;:]+$", "", candidate).strip()
#     candidate = re.sub(r"[^A-Za-z.\- ]", "", candidate).strip()
#     if candidate.isupper():
#         candidate = candidate.title()
#     return candidate

# def preprocess_image_if_available(path: str) -> str:
#     """
#     If OpenCV is installed, read the image, apply grayscale + denoise + adaptive threshold or Otsu,
#     save to a temp file and return the temp path. If cv2 not available or preprocessing fails,
#     returns original path.
#     """
#     if not _HAS_CV2:
#         return path

#     try:
#         img = cv2.imread(path)
#         if img is None:
#             return path
#         # Resize if very large (speeds processing)
#         h, w = img.shape[:2]
#         max_dim = 1600
#         if max(h, w) > max_dim:
#             scale = max_dim / max(h, w)
#             img = cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_AREA)

#         gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#         # Denoise
#         gray = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
#         # Use adaptive threshold if lighting is uneven, else Otsu
#         try:
#             th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
#                                        cv2.THRESH_BINARY, 15, 8)
#         except Exception:
#             _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
#         out_fd, out_path = tempfile.mkstemp(suffix=".png")
#         os.close(out_fd)
#         cv2.imwrite(out_path, th)
#         return out_path
#     except Exception:
#         return path

# def _extract_candidate_name_from_text(full_text_raw: str) -> str:
#     """Original anchor-based approach kept as fallback for student name."""
#     anchor_rx = re.compile(r"(?i)this\W*is\W*to\W*(?:c(?:e|s)rtif|certif|sertif)[a-z]*\W*that\W*")
#     lines = re.split(r'\n|\r|\r\n', full_text_raw)
#     for ln in lines:
#         m = anchor_rx.search(ln)
#         if m:
#             pool = ln[m.end():].strip()
#             seg = re.sub(r"\s{2,}", " ", pool)
#             cand = _clean_name(seg)
#             if cand and (len(cand.split()) >= 2 or len(cand) >= 5):
#                 return cand
#     # fallback regex on the whole text
#     text_clean = re.sub(r"\s+", " ", full_text_raw)
#     pattern = re.compile(r"(?i)this\s+is\s+to\s+c(?:e|s)rtif[a-z]*\s+that[:,\-]?\s*([A-Za-z.\- ]{3,120})")
#     m2 = pattern.search(text_clean)
#     if m2:
#         seg = re.sub(r"\s{2,}", " ", m2.group(1)).strip()
#         cand = _clean_name(seg)
#         if cand:
#             return cand
#     return "Not Found"

# def extract_marksheet_details(image_path: str) -> Dict[str, Any]:
#     """
#     Improved extraction:
#       - preprocess image if cv2 available
#       - cluster OCR boxes into rows using vertical threshold
#       - within each row, pair subject (left) with marks (right)
#       - fuzzy subject match and fallbacks
#     """
#     preproc_path = preprocess_image_if_available(image_path)
#     ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
#     results = ocr.ocr(preproc_path, cls=True)

#     # If we created a temp preprocessed file, remove it later
#     if preproc_path != image_path and os.path.exists(preproc_path):
#         try:
#             os.remove(preproc_path)
#         except Exception:
#             pass

#     if not results or not results[0]:
#         return {"Medium": "Unknown", "Class": "Unknown", "Student Name": "Not Found", "Marks": {}, "Total": 0, "Percentage": 0.0}

#     # Build box list with centroids and heights
#     boxes = []
#     for item in results[0]:
#         box_pts = item[0]  # list of 4 points [[x,y],...]
#         text, conf = item[1]
#         xs = [p[0] for p in box_pts]
#         ys = [p[1] for p in box_pts]
#         cx = sum(xs) / 4.0
#         cy = sum(ys) / 4.0
#         h = max(ys) - min(ys)
#         w = max(xs) - min(xs)
#         boxes.append({"text": text.strip(), "conf": float(conf), "cx": cx, "cy": cy, "h": h, "w": w, "box": box_pts})

#     if not boxes:
#         return {"Medium": "Unknown", "Class": "Unknown", "Student Name": "Not Found", "Marks": {}, "Total": 0, "Percentage": 0.0}

#     # Determine vertical grouping threshold
#     heights = [b["h"] for b in boxes if b["h"] > 0]
#     median_h = statistics.median(heights) if heights else 10.0
#     line_thresh = median_h * VERTICAL_MULTIPLIER

#     # Group boxes into rows (top to bottom)
#     boxes_sorted = sorted(boxes, key=lambda x: x["cy"])
#     rows: List[List[Dict[str, Any]]] = []
#     for b in boxes_sorted:
#         if not rows:
#             rows.append([b])
#             continue
#         last_row = rows[-1]
#         row_cy = statistics.mean([x["cy"] for x in last_row])
#         if abs(b["cy"] - row_cy) <= line_thresh:
#             last_row.append(b)
#         else:
#             rows.append([b])

#     # Build textual rows (ordered left->right)
#     textual_rows: List[Dict[str, Any]] = []
#     for r in rows:
#         r_sorted = sorted(r, key=lambda x: x["cx"])
#         row_texts = [x["text"] for x in r_sorted if x["text"].strip()]
#         combined = " ".join(row_texts)
#         textual_rows.append({
#             "boxes": r_sorted,
#             "text": combined,
#             "cy": statistics.mean([x["cy"] for x in r_sorted]),
#             "cxs": [x["cx"] for x in r_sorted],
#         })

#     if DEBUG:
#         print("---- Rows detected ----")
#         for i, rr in enumerate(textual_rows):
#             print(i, f"cy={rr['cy']:.1f}", "text:", rr["text"])

#     # Full raw text for name/class/medium detection
#     full_text_raw = " ".join([r["text"] for r in textual_rows])
#     full_text_norm = _normalize_letters(full_text_raw)

#     # Medium detection (CBSE variants)
#     medium = "Unknown"
#     cbse_variants = ["centralboardofsecondaryeducation", "centeralboardofsecondaryeducation", "cbse"]
#     if any(v in full_text_norm for v in cbse_variants):
#         medium = "CBSE"

#     # Class detection heuristic
#     marksheet_class = "Unknown"
#     if "secondaryschoolexamination" in full_text_norm or "aisse" in full_text_norm or "class10" in full_text_norm:
#         marksheet_class = "Class 10"
#     if "seniorschoolcertificateexamination" in full_text_norm or "aissce" in full_text_norm or "class12" in full_text_norm:
#         marksheet_class = "Class 12"

#     # Student name extraction (fallback to anchor approach)
#     student_name = _extract_candidate_name_from_text(full_text_raw)

#     # Subjects list (expand as needed)
#     SUBJECTS = [
#         "English", "Hindi", "Tamil", "Telugu", "Malayalam", "Kannada",
#         "Mathematics", "Maths", "Science", "Social Science", "Physics",
#         "Chemistry", "Biology", "Computer Science", "Information Technology",
#         "Accountancy", "Economics", "Business Studies", "Political Science",
#         "History", "Geography", "Sanskrit", "Urdu", "English Core", "English Elective"
#     ]
#     subj_norms = {s: _normalize_letters(s) for s in SUBJECTS}

#     # Regex to capture candidate marks (handles 84, 84/100, 084)
#     marks_re = re.compile(r"(\d{1,3})(?:\s*/\s*(\d{1,3}))?")

#     # Scan rows for subject+marks
#     marks: Dict[str, int] = {}

#     for rr in textual_rows:
#         text = rr["text"]
#         if not text or len(text.strip()) < 1:
#             continue
#         # Skip rows that look like headers
#         if re.search(r"(?i)subject|marks|maximum|total|max\s*marks|grade", text):
#             continue

#         # Find numeric tokens in the row
#         nums = []
#         for m in marks_re.finditer(text):
#             num_str = m.group(1)
#             try:
#                 val = int(num_str)
#             except:
#                 continue
#             if MARKS_MIN <= val <= MARKS_MAX:
#                 nums.append((val, m.group(0), m.start()))

#         # Try to identify subject by normalized substring match first
#         norm_row = _normalize_letters(text)
#         found_subject = None
#         for s, sn in subj_norms.items():
#             if sn and sn in norm_row:
#                 found_subject = s
#                 break

#         # Fuzzy match fallback
#         if not found_subject:
#             # try difflib against the entire row letters
#             for s, sn in subj_norms.items():
#                 if not sn:
#                     continue
#                 ratio = difflib.SequenceMatcher(None, sn, norm_row).ratio()
#                 if ratio >= SUBJECT_MATCH_RATIO:
#                     found_subject = s
#                     break

#         # If subject found and at least one numeric, choose last numeric (usually student marks)
#         if found_subject and nums:
#             chosen = nums[-1][0]
#             marks[found_subject] = chosen
#             if DEBUG:
#                 print(f"Row matched SUBJECT '{found_subject}' -> {chosen}  (row: {text})")
#             continue

#     # Fallback: if no marks found via rows, try box-level pairing:
#     if not marks:
#         if DEBUG:
#             print("No marks found via row-scan, trying box-level pairing fallback")
#         # find numeric-only boxes and pair with nearest text box on same row / above
#         numeric_boxes = [b for b in boxes if re.fullmatch(r"\d{1,3}(/?\d{1,3})?", b["text"].strip())]
#         text_boxes = [b for b in boxes if re.search(r"[A-Za-z]", b["text"])]
#         for nb in numeric_boxes:
#             # parse numeric value (numerator if fraction)
#             t = nb["text"].strip()
#             m = marks_re.search(t)
#             if not m:
#                 continue
#             val = int(m.group(1))
#             if not (MARKS_MIN <= val <= MARKS_MAX):
#                 continue
#             # find nearest text box in vertical proximity
#             candidates = []
#             for tb in text_boxes:
#                 dy = abs(tb["cy"] - nb["cy"])
#                 dx = abs(tb["cx"] - nb["cx"])
#                 candidates.append((dy, dx, tb))
#             if not candidates:
#                 continue
#             candidates.sort(key=lambda x: (x[0], x[1]))
#             tb = candidates[0][2]
#             # see if tb looks like a subject
#             norm_tb = _normalize_letters(tb["text"])
#             assigned_subj = None
#             for s, sn in subj_norms.items():
#                 if sn and sn in norm_tb:
#                     assigned_subj = s
#                     break
#             if not assigned_subj:
#                 # difflib fallback
#                 for s, sn in subj_norms.items():
#                     ratio = difflib.SequenceMatcher(None, sn, norm_tb).ratio()
#                     if ratio >= SUBJECT_MATCH_RATIO:
#                         assigned_subj = s
#                         break
#             if assigned_subj:
#                 marks[assigned_subj] = val
#                 if DEBUG:
#                     print(f"Paired numeric box '{t}' with subject box '{tb['text']}' -> {assigned_subj}: {val}")

#     # Final: if still empty, attempt a very permissive scan: any row that contains subject token anywhere (looser)
#     if not marks:
#         if DEBUG:
#             print("Final permissive scan across rows")
#         for rr in textual_rows:
#             norm_row = _normalize_letters(rr["text"])
#             for s, sn in subj_norms.items():
#                 if sn and sn in norm_row:
#                     # check for any numbers in the document after this row (small vertical window)
#                     # simple: search the same row for numbers
#                     nums = marks_re.findall(rr["text"])
#                     if nums:
#                         # nums is list of tuples (num, denom?) from findall; choose first plausible
#                         for n in nums:
#                             try:
#                                 val = int(n[0])
#                                 if MARKS_MIN <= val <= MARKS_MAX:
#                                     marks[s] = val
#                                     break
#                             except:
#                                 continue

#     # Compute total and percentage
#     total = sum(marks.values()) if marks else 0
#     percentage = round((total / (len(marks) * 100)) * 100, 2) if marks else 0.0

#     return {
#         "Medium": medium,
#         "Class": marksheet_class,
#         "Student Name": student_name,
#         "Marks": marks,
#         "Total": total,
#         "Percentage": percentage
#     }

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


#----------------------------------------------------------------------------------------------------




import os
import re
import cv2
import json
import numpy as np
from paddleocr import PaddleOCR

ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp"}

# Initialize OCR
ocr = PaddleOCR(use_angle_cls=False, lang='en')

# Subjects we want to extract
SUBJECTS = ["ENGLISH", "TAMIL", "MATHEMATICS", "SCIENCE", "SOCIAL"]

def preprocess_image(image_path):
    """Convert to grayscale + threshold for cleaner OCR"""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    img = cv2.threshold(img, 150, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    temp_path = "temp_processed.png"
    cv2.imwrite(temp_path, img)
    return temp_path

def extract_text(image_path):
    """Run OCR and return text lines"""
    result = ocr.ocr(image_path, cls=False)
    lines = []
    for page in result:
        for line in page:
            lines.append(line[1][0])
    return "\n".join(lines)

def extract_student_name(text):
    """Extract student name after 'certify that' or similar"""
    match = re.search(r"certify that\s+([A-Z ]+)", text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        # Clean extra roll no / parents
        name = re.split(r"Roll|Mother|Father|Date", name, flags=re.IGNORECASE)[0]
        return " ".join(name.split())
    return "Unknown"

def extract_class(text):
    if re.search(r"Class\s*XII", text, re.IGNORECASE):
        return "Class 12"
    elif re.search(r"Class\s*X", text, re.IGNORECASE):
        return "Class 10"
    return "Unknown"

def extract_medium(text):
    if re.search(r"central board of secondary education", text, re.IGNORECASE):
        return "CBSE"
    return "State Board"

def extract_marks(text):
    marks = {}
    total = 0
    for subj in SUBJECTS:
        # Search subject and number near it
        pattern = rf"{subj}.*?(\d{{2,3}})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            marks[subj.capitalize()] = score
            total += score
    return marks, total

def main():
    inp = input("Enter path to CBSE marksheet image: ").strip()
    ext = ".jpeg"
    filename = os.path.join(".", inp + ext)

    # Preprocess & OCR
    processed_img = preprocess_image(filename)
    text = extract_text(processed_img)

    # Extract details
    student_name = extract_student_name(text)
    class_name = extract_class(text)
    medium = extract_medium(text)
    marks, total = extract_marks(text)

    percentage = (total / (len(SUBJECTS) * 100)) * 100 if marks else 0.0

    output = {
        "Medium": medium,
        "Class": class_name,
        "Student Name": student_name,
        "Marks": marks,
        "Total": total,
        "Percentage": round(percentage, 2)
    }

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
