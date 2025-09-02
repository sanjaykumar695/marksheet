# from paddleocr import PaddleOCR
# import re
# import json

# # Initialize PaddleOCR (English)
# ocr = PaddleOCR(use_angle_cls=True, lang='en')

# # Load image
# image_path = "sanjay10.jpeg"

# # Run OCR
# results = ocr.ocr(image_path, cls=True)

# # Collect all text lines
# lines = []
# for res in results[0]:
#     text, confidence = res[1]
#     lines.append(text)

# full_text = " ".join(lines)

# # Regex to extract marks table
# pattern = re.compile(
#     r"(\d{3})\s+([A-Za-z\s\.\&]+)\s+(\d{2,3})\s+(\d{2,3})\s+(\d{2,3})\s+([A-Z0-9]+)"
# )

# marks_data = []
# for match in pattern.finditer(full_text):
#     sub_code, subject, theory, ia, total, grade = match.groups()
#     marks_data.append({
#         "Subject Code": sub_code.strip(),
#         "Subject": subject.strip(),
#         "Theory": int(theory),
#         "IA/Practical": int(ia),
#         "Total": int(total),
#         "Grade": grade
#     })

# print(json.dumps(marks_data, indent=4))


#------------------------------------------------------------------------------------------------------

# from paddleocr import PaddleOCR
# import re
# import json

# # Initialize PaddleOCR (English)
# ocr = PaddleOCR(use_angle_cls=True, lang='en')

# # Load image
# image_path = "sanjay10.jpeg"

# # Run OCR
# results = ocr.ocr(image_path, cls=True)

# # Collect all text lines
# lines = []
# for res in results[0]:
#     text, confidence = res[1]
#     lines.append(text)

# full_text = " ".join(lines)

# # Regex to capture subject + total marks (ignore other fields)
# pattern = re.compile(
#     r"(\d{3})\s+([A-Za-z\s\.&]+?)\s+\d{2,3}\s+\d{2,3}\s+(\d{2,3})"
# )

# marks_data = []
# for match in pattern.finditer(full_text):
#     sub_code, subject, total = match.groups()
#     marks_data.append({
#         "Subject": subject.strip(),
#         "Total": int(total)
#     })

# # Print results
# print(json.dumps(marks_data, indent=4))

#-----------------------------------------------------------------------------------------------------


# extract_subject_total_robust.py
# Works fully offline with PaddleOCR
# pip install paddleocr paddlepaddle

# from paddleocr import PaddleOCR
# from statistics import median
# import re
# import json
# import argparse

# # --- Canonical subject names by code (extend as you wish) ---
# SUBJECT_BY_CODE = {
#     "184": "ENGLISH LNG & LIT.",
#     "006": "TAMIL",
#     "041": "MATHEMATICS STANDARD",   # change to "MATHEMATICS BASIC" if needed
#     "086": "SCIENCE",
#     "087": "SOCIAL SCIENCE",
#     "402": "INFORMATION TECHNOLOGY",
# }

# # Words OCR sometimes puts in place of numbers (we ignore these in subject names)
# NUMBER_WORDS = {
#     "ZERO","ONE","TWO","THREE","FOUR","FIVE","SIX","SEVEN","EIGHT","NINE",
#     "TEN","ELEVEN","TWELVE","THIRTEEN","FOURTEEN","FIFTEEN","SIXTEEN",
#     "SEVENTEEN","EIGHTEEN","NINETEEN","TWENTY","THIRTY","FORTY","FIFTY",
#     "SIXTY","SEVENTY","EIGHTY","NINETY","HUNDRED"
# }

# def sanitize_number_str(s: str) -> str:
#     """Fix common OCR confusions and strip to digits only."""
#     s = s.strip()
#     # Common OCR swaps
#     s = s.replace('O', '0').replace('o', '0')
#     s = s.replace('I', '1').replace('l', '1').replace('|', '1')
#     s = s.replace('S', '5')
#     s = s.replace('B', '8')
#     # Remove non-digits
#     s = ''.join(ch for ch in s if ch.isdigit())
#     return s

# def is_number_token(tok: str) -> bool:
#     """Is this token a numeric or written-number-like token?"""
#     t = tok.strip().upper()
#     if t.isdigit():
#         return True
#     # Tokens like "8I" or "8l" etc—sanitize and re-check
#     if sanitize_number_str(t).isdigit():
#         return True
#     # Pure number words (EIGHTY, SIX, etc.)
#     if t in NUMBER_WORDS:
#         return True
#     return False

# def group_boxes_into_rows(ocr_result):
#     """
#     Group OCR boxes into rows by vertical proximity.
#     Each item of ocr_result[0] is [bbox, (text, conf)].
#     """
#     items = []
#     for box, (text, conf) in ocr_result[0]:
#         if not text.strip():
#             continue
#         xs = [p[0] for p in box]
#         ys = [p[1] for p in box]
#         x_min, x_max = min(xs), max(xs)
#         y_min, y_max = min(ys), max(ys)
#         y_center = (y_min + y_max) / 2.0
#         height = y_max - y_min
#         items.append({
#             "text": text.strip(),
#             "conf": conf,
#             "x_min": x_min,
#             "x_max": x_max,
#             "y_min": y_min,
#             "y_max": y_max,
#             "y_center": y_center,
#             "height": height
#         })

#     if not items:
#         return []

#     # Row threshold based on median box height
#     h_med = median([it["height"] for it in items])
#     row_thresh = max(10, h_med * 0.8)

#     # Sort by vertical position then group
#     items.sort(key=lambda it: it["y_center"])
#     rows = []
#     current_row = [items[0]]
#     current_y = items[0]["y_center"]

#     for it in items[1:]:
#         if abs(it["y_center"] - current_y) <= row_thresh:
#             current_row.append(it)
#             # keep running average to be stable
#             current_y = (current_y + it["y_center"]) / 2.0
#         else:
#             rows.append(current_row)
#             current_row = [it]
#             current_y = it["y_center"]
#     rows.append(current_row)

#     # Sort each row left→right
#     for r in rows:
#         r.sort(key=lambda it: it["x_min"])

#     return rows

# def extract_row_fields(row_items):
#     """
#     From a row (list of boxes left→right), find:
#       - subject code (3-digit)
#       - numbers in the row (theory, IA, total; last one considered total)
#       - subject name guess (tokens between code and first number)
#     Returns dict or None.
#     """
#     tokens = [it["text"] for it in row_items]
#     # Flatten minor splits: join single-char tokens that are clearly broken words?
#     # Keep it simple: just use tokens as-is.

#     # 1) Find first 3-digit subject code token
#     code_idx = None
#     code_val = None
#     for i, tok in enumerate(tokens):
#         m = re.fullmatch(r"\D*(\d{3})\D*", tok)  # allow stray chars
#         if m:
#             code_val = m.group(1)
#             code_idx = i
#             break
#     if code_idx is None:
#         return None  # not a subject line

#     # 2) Collect all numeric-like tokens (after the code)
#     numeric_positions = []
#     for j in range(code_idx + 1, len(tokens)):
#         tok = tokens[j]
#         if is_number_token(tok):
#             numeric_positions.append(j)

#     if not numeric_positions:
#         # No numbers found → hard to get totals
#         number_vals = []
#     else:
#         number_vals = []
#         for j in numeric_positions:
#             tok = tokens[j].upper()
#             # Try numeric first
#             num_str = sanitize_number_str(tok)
#             if num_str.isdigit():
#                 number_vals.append(int(num_str))
#             else:
#                 # Could convert number words to numbers if needed; for now, ignore
#                 pass

#     # 3) Guess subject name: tokens between code and first numeric token
#     if numeric_positions:
#         subject_tokens = tokens[code_idx + 1:numeric_positions[0]]
#     else:
#         # If no numeric tokens, take a few tokens after code as subject guess
#         subject_tokens = tokens[code_idx + 1:]

#     # Filter out tokens that are actually numbers/number-words
#     subj_clean_tokens = [t for t in subject_tokens if not is_number_token(t)]
#     subject_guess = " ".join(subj_clean_tokens).strip()
#     # If subject guess is empty, but we do have a code, we'll fill from map later.

#     # 4) Decide total:
#     total_val = None
#     if number_vals:
#         # Usually the last number in row is the Total
#         total_val = number_vals[-1]
#         # But if there are exactly 2 numbers, it could be (Theory, Total) instead of (Theory, IA, Total)
#         # If there are 3, it's (Theory, IA, Total)
#         # If there is only 1, assume it's Total.

#     return {
#         "code": code_val,
#         "subject_guess": subject_guess,
#         "numbers": number_vals,
#         "total": total_val
#     }

# def main():
#     ap = argparse.ArgumentParser()
#     ap.add_argument("--image", "-i", default="sanjay10.jpeg", help="Path to marksheet image")
#     ap.add_argument("--debug", action="store_true", help="Print row-wise OCR text for debugging")
#     args = ap.parse_args()

#     ocr = PaddleOCR(use_angle_cls=True, lang='en')
#     results = ocr.ocr(args.image, cls=True)

#     if not results or not results[0]:
#         print("[]")
#         return

#     rows = group_boxes_into_rows(results)

#     extracted = []
#     for row in rows:
#         fields = extract_row_fields(row)
#         if not fields:
#             continue

#         code = fields["code"]
#         total = fields["total"]

#         # Fix subject via code map (this addresses 'Tamil'/'Science' issues)
#         subject = SUBJECT_BY_CODE.get(code, None)
#         if not subject:
#             # Fallback to OCR guess if unknown code
#             subject = fields["subject_guess"] if fields["subject_guess"] else f"SUBJECT {code}"

#         if total is None:
#             # Try reconstruct from first two numbers if present (theory + IA)
#             nums = fields["numbers"]
#             if len(nums) >= 2:
#                 total = nums[-1]  # often the second of two or third of three is total
#             elif len(nums) == 1:
#                 total = nums[0]

#         if total is None:
#             # If still unknown, skip this row
#             continue

#         extracted.append({"Subject": subject, "Total": int(total)})

#     # Deduplicate by subject code (keep last occurrence)
#     # Build code->index map while we loop again
#     final_by_subject = {}
#     for row in extracted:
#         final_by_subject[row["Subject"]] = row["Total"]

#     # Preserve a friendly order based on our known subjects (if present), then others
#     ordered_subjects = [SUBJECT_BY_CODE[c] for c in SUBJECT_BY_CODE if SUBJECT_BY_CODE[c] in final_by_subject]
#     others = [s for s in final_by_subject.keys() if s not in ordered_subjects]

#     final_list = [{"Subject": s, "Total": final_by_subject[s]} for s in ordered_subjects + others]

#     # Optional debug print
#     if args.debug:
#         print("\n--- DEBUG: Reconstructed rows (left→right text) ---")
#         for r in rows:
#             print(" | ".join(it["text"] for it in r))
#         print("---------------------------------------------------\n")

#     print(json.dumps(final_list, indent=4))

# if __name__ == "__main__":
#     main()


#-----------------------------------------------------------------------------------------------------------------

# from paddleocr import PaddleOCR
# import re
# import json

# # Initialize PaddleOCR (English)
# ocr = PaddleOCR(use_angle_cls=True, lang='en')

# # Load image
# image_path = "sanjay10.jpeg"

# # Run OCR
# results = ocr.ocr(image_path, cls=True)

# lines = []
# for res in results[0]:
#     text, confidence = res[1]
#     lines.append(text.strip())

# subjects = []
# marks_data = []

# # Join line fragments into a single string
# for line in lines:
#     # Look for subject keywords
#     if any(word in line.upper() for word in ["ENGLISH", "TAMIL", "MATHEMATICS", "SCIENCE", "SOCIAL", "INFORMATION"]):
#         subjects.append(line.strip())

# # Now extract marks from lines
# for line in lines:
#     # Extract only numbers from line
#     nums = re.findall(r"\d+", line)

#     if nums:
#         # Join single digits into full numbers (like 6 and 2 → 62)
#         joined_nums = []
#         i = 0
#         while i < len(nums):
#             if i < len(nums) - 1 and len(nums[i]) == 1 and len(nums[i + 1]) == 1:
#                 joined_nums.append(int(nums[i] + nums[i + 1]))
#                 i += 2
#             else:
#                 joined_nums.append(int(nums[i]))
#                 i += 1

#         # The last number is usually the total marks
#         total = joined_nums[-1]
#         marks_data.append(total)

# # Match subjects with marks
# final_output = []
# for i in range(min(len(subjects), len(marks_data))):
#     final_output.append({
#         "Subject": subjects[i],
#         "Total": marks_data[i]
#     })

# print(json.dumps(final_output, indent=4))

#-------------------------------------------------------------------------------------------------------------------

# from paddleocr import PaddleOCR
# import re
# import json

# # Initialize PaddleOCR (English)
# ocr = PaddleOCR(use_angle_cls=True, lang='en')

# # Load image
# image_path = "sanjay10.jpeg"

# # Run OCR
# results = ocr.ocr(image_path, cls=True)

# lines = []
# for res in results[0]:
#     text, confidence = res[1]
#     lines.append(text.strip())

# subjects_keywords = ["ENGLISH", "TAMIL", "MATHEMATICS", "SCIENCE", "SOCIAL", "INFORMATION"]

# final_output = []

# for line in lines:
#     upper_line = line.upper()

#     # Check if line contains subject name
#     if any(sub in upper_line for sub in subjects_keywords):
#         # Extract last 2–3 digit number in the line (this is usually the Total mark)
#         nums = re.findall(r"\b\d{2,3}\b", line)
#         if nums:
#             total = int(nums[-1])  # take the last number as Total
#             final_output.append({
#                 "Subject": line,
#                 "Total": total
#             })

# print(json.dumps(final_output, indent=4))

#------------------------------------------------------------------------------------------------------------------------

# from paddleocr import PaddleOCR
# import re
# import json

# # Initialize PaddleOCR (English)
# ocr = PaddleOCR(use_angle_cls=True, lang='en')

# # Load image
# image_path = "sanjay10.jpeg"

# # Run OCR
# results = ocr.ocr(image_path, cls=True)

# lines = []
# for res in results[0]:
#     text, confidence = res[1]
#     lines.append(text.strip())

# final_output = []

# # Mapping to clean subject names (you can expand this)
# subject_map = {
#     "ENGLISH": "ENGLISH LANGUAGE & LITERATURE",
#     "TAMIL": "TAMIL",
#     "MATHEMATICS": "MATHEMATICS STANDARD",
#     "SCIENCE": "SCIENCE",
#     "SOCIAL": "SOCIAL SCIENCE",
#     "INFORMATION": "INFORMATION TECHNOLOGY"
# }

# for line in lines:
#     # Extract last 2-3 digit number (possible Total mark)
#     nums = re.findall(r"\b\d{2,3}\b", line)

#     if nums:
#         # Try to detect subject name by partial match
#         for key, clean_name in subject_map.items():
#             if key in line.upper():
#                 total = int(nums[-1])  # last number = Total
#                 final_output.append({
#                     "Subject": clean_name,
#                     "Total": total
#                 })

# print(json.dumps(final_output, indent=4))

#---------------------------------------------------------------------------------------------------------------

# extract_marks.py
from paddleocr import PaddleOCR
import re
import json
import argparse
import sys

# -------------------------
# Helpers
# -------------------------
NUMBER_PATTERN = re.compile(r'\d+(?:/\d+)?')  # matches 32 or 32/40

DEFAULT_SUBJECT_KEYWORDS = [
    "ENGLISH", "TAMIL", "MATHEMATICS", "MATHEMATICS STANDARD", "SCIENCE",
    "SOCIAL", "SOCIAL SCIENCE", "INFORMATION", "INFORMATION TECHNOLOGY",
    "HINDI", "PHYSICS", "CHEMISTRY", "BIOLOGY", "COMPUTER", "COMPUTER SCIENCE"
]

def load_ocr(image_path, use_angle_cls=True, lang='en'):
    ocr = PaddleOCR(use_angle_cls=use_angle_cls, lang=lang)
    results = ocr.ocr(image_path, cls=use_angle_cls)
    # results may be [lines] or []. Normalize to a list-of-lines
    if not results:
        return []
    # PaddleOCR returns a nested structure: results[0] is the list of line entries
    # but some builds may return slightly different structures — handle both.
    if isinstance(results[0], list) and results[0] and isinstance(results[0][0], list):
        lines = results[0]
    else:
        # fallback: if results is already a list of line entries
        lines = results
    return lines

def build_entries(ocr_lines):
    """
    Convert raw PaddleOCR line entries into a list of dicts:
    { idx, text, conf, cx, cy, box, tokens: [ {raw, val, cx, cy, idx} ] }
    """
    entries = []
    for i, line in enumerate(ocr_lines):
        # line is like: [box, (text, confidence)] (or similar)
        try:
            box = line[0]
            td = line[1]
            if isinstance(td, (list, tuple)):
                text = td[0]
                conf = td[1] if len(td) > 1 else None
            else:
                text = str(td)
                conf = None
        except Exception:
            # robust fallback
            text = str(line)
            box = [(0, 0), (0, 0), (0, 0), (0, 0)]
            conf = None

        # center of box (approx)
        cx = sum([pt[0] for pt in box]) / 4.0
        cy = sum([pt[1] for pt in box]) / 4.0

        # extract numeric tokens in this line
        tokens = []
        for m in NUMBER_PATTERN.finditer(text):
            raw = m.group()
            # if fraction like 32/40, use numerator (marks obtained)
            val = int(raw.split('/')[0])
            tokens.append({'raw': raw, 'val': val, 'cx': cx, 'cy': cy, 'idx': i})

        entries.append({
            'idx': i,
            'text': text.strip(),
            'conf': conf,
            'cx': cx,
            'cy': cy,
            'box': box,
            'tokens': tokens
        })
    return entries

def match_subject_marks(entries, subject_keywords=None, window=2, max_mark=1000):
    """
    For each entry whose text contains a subject keyword, find the
    best numeric token nearby (prefer rightmost and <= max_mark).
    """
    if subject_keywords is None:
        subject_keywords = DEFAULT_SUBJECT_KEYWORDS

    # flatten tokens for fast searching
    tokens_all = [t for e in entries for t in e['tokens']]

    results = []
    seen_subject_texts = set()

    for e in entries:
        text_upper = e['text'].upper()
        matched_kw = None
        for kw in subject_keywords:
            if kw in text_upper:
                matched_kw = kw
                break
        if not matched_kw:
            continue

        # avoid duplicates if OCR split the subject across multiple near-identical lines
        if e['text'] in seen_subject_texts:
            continue
        seen_subject_texts.add(e['text'])

        # gather candidate tokens near this line by index-window
        candidates = [t for t in tokens_all if abs(t['idx'] - e['idx']) <= window]

        # if none, try vertical proximity
        if not candidates:
            candidates = [t for t in tokens_all if abs(t['cy'] - e['cy']) < 50]

        # prefer realistic marks (0 <= val <= max_mark)
        pref = [t for t in candidates if 0 <= t['val'] <= max_mark]
        chosen = None
        if pref:
            # choose the rightmost (largest cx) among preferred
            chosen = max(pref, key=lambda t: t['cx'])
        elif candidates:
            chosen = max(candidates, key=lambda t: t['cx'])

        # fallback: try to find explicit phrases like "Total" or "Marks" in the same line
        if not chosen:
            m = re.search(r'(?:Total|Marks(?: Obtained)?|Obtained|Out of)\s*[:\-]?\s*(\d{1,3})', e['text'], re.I)
            if m:
                chosen = {'raw': m.group(1), 'val': int(m.group(1)), 'cx': e['cx'], 'cy': e['cy'], 'idx': e['idx']}

        total_value = None
        if chosen:
            # if token was a fraction like "32/40", preserve raw and prefer int
            try:
                if '/' in chosen['raw']:
                    # store numerator (obtained marks) as int, and optionally keep raw string
                    total_value = int(chosen['raw'].split('/')[0])
                else:
                    total_value = int(chosen['raw'])
            except Exception:
                total_value = chosen['raw']

        results.append({
            "Subject": e['text'],
            "Total": total_value
        })

    return results

# -------------------------
# Main CLI
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="Extract subject-wise marks from a marksheet image using PaddleOCR.")
    parser.add_argument("image", help="Path to marksheet image (jpg/png/jpeg)")
    parser.add_argument("--max-mark", type=int, default=1000, help="Maximum plausible mark to prefer (default: 1000). Reduce to 100 if each subject max is 100.")
    parser.add_argument("--window", type=int, default=2, help="How many OCR-lines away to consider numeric tokens (default: 2). Increase if marks are on far-right columns.")
    parser.add_argument("--lang", default="en", help="PaddleOCR lang (default 'en')")
    parser.add_argument("--debug", action="store_true", help="Print debug info")
    args = parser.parse_args()

    ocr_lines = load_ocr(args.image, lang=args.lang)
    if not ocr_lines:
        print("[]")
        print("No OCR output detected. Check image path or OCR initialization.", file=sys.stderr)
        return

    entries = build_entries(ocr_lines)
    output = match_subject_marks(entries, window=args.window, max_mark=args.max_mark)

    if args.debug:
        print(">>>> OCR lines (index: text)")
        for e in entries:
            print(f"{e['idx']:02d}: {e['text']}  tokens={[(t['raw'], t['cx']) for t in e['tokens']]}")
        print(">>>> Extracted subject marks")
    print(json.dumps(output, indent=4))

if __name__ == "__main__":
    main()
