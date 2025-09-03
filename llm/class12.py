import os
import re
import json
from typing import Dict, Any, Optional
from paddleocr import PaddleOCR

# Initialize PaddleOCR once globally
ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

def _normalize_letters(text: str) -> str:
    """Removes non-alphabetic characters and converts text to lowercase."""
    return re.sub(r'[^a-z]', '', text.lower())

def _clean_name(candidate: str) -> str:
    """Cleans up a potential student name string."""
    candidate = candidate.strip().strip('\'"“”‘’')
    candidate = re.sub(r"(?i)^(mr|mrs|ms|miss|master|mast|dr|prof|sir|madam|sri|shri|smt|kum|kumari|ku\.)\s+", "", candidate)
    candidate = re.sub(r"(?i)^(the\s+candidate\s+named\s+|the\s+candidate\s+|the\s+name\s+of\s+the\s+candidate\s+is\s+|"
                       r"the\s+name\s+of\s+candidate\s+is\s+|candidate\s+name\s+|student\s+name\s+|named\s+)", "", candidate)
    candidate = re.sub(r"\s{2,}", " ", candidate)
    candidate = re.sub(r"[,\.;:]+$", "", candidate).strip()
    candidate = re.sub(r"[^A-Za-z.\- ]", "", candidate).strip()
    if candidate.isupper():
        candidate = candidate.title()
    return candidate

def _clip_at_stop(pool: str) -> str:
    """Clips text at common stop words to isolate the name."""
    STOP_WORDS = [
        r"s\/o", r"d\/o", r"w\/o", r"son", r"daughter", r"wife", r"husband",
        r"father", r"mother", r"guardian", r"roll", r"regn", r"registration",
        r"enrol", r"admission", r"has", r"have", "is", "was",
        r"of\s+class", r"class\s+\d{1,2}", r"vide", r"dated", r"dob", r"born",
        r"candidate", r"student", r"exam", r"examination", r"marks?", r"year",
        r"subject", r"bearing", r"school", r"board", r"regd", r"regn", r"roll\s+no"
    ]
    STOP_TOKENS_RE = re.compile(r"\b(?:" + "|".join(STOP_WORDS) + r")\b", flags=re.I)
    m = STOP_TOKENS_RE.search(pool)
    if m:
        return pool[:m.start()].strip()
    return pool.strip()

def extract_marks_paddle_class12(image_path: str) -> Dict[str, Any]:
    """
    Extracts marks, student name, medium, and class from a CBSE Class 12 marksheet image.
    """
    try:
        result = ocr.ocr(image_path, cls=True)

        if not result or not result[0]:
            return {
                "Medium": "Unknown",
                "Class": "Unknown",
                "Student name": "Not Found",
                "Status": "OCR failed to find any text."
            }

        text_data = [{
            "text": line[1][0],
            "confidence": line[1][1],
            "bbox": line[0]
        } for line in result[0] if line and line[1] and line[1][0]]
        
        lines_raw = [item["text"] for item in text_data]
        full_text_raw = " ".join(lines_raw)
        full_text_norm = _normalize_letters(full_text_raw)

        # --- Medium and Class Detection ---
        medium = "Unknown"
        marksheet_class = "Unknown"
        cbse_variants = ["centralboardofsecondaryeducation", "centeralboardofsecondaryeducation", "cbse"]
        if any(v in full_text_norm for v in cbse_variants):
            medium = "CBSE"

        if "secondaryschoolexamination" in full_text_norm or "aisse" in full_text_norm:
            marksheet_class = "Class 10"
        elif "seniorschoolcertificateexamination" in full_text_norm or "aissce" in full_text_norm:
            marksheet_class = "Class 12"

        # --- Student Name Extraction Logic ---
        name = "Not Found"
        name_candidates = []
        anchor_rx = re.compile(r"(?i)this\W*is\W*to\W*(?:c(?:e|s)rtif|certif|sertif)[a-z]*\W*that\W*")

        for idx, ln in enumerate(lines_raw):
            m = anchor_rx.search(ln)
            if not m:
                continue
            pool = ln[m.end():].strip()

            for extra_idx in range(1, 4):
                if len(pool) < 5 and idx + extra_idx < len(lines_raw):
                    pool += " " + lines_raw[idx + extra_idx]

            segment = _clip_at_stop(pool)
            candidate = _clean_name(segment)

            if candidate and (len(candidate.split()) >= 2 or len(candidate) >= 5):
                name_candidates.append(candidate)

        if not name_candidates:
            text_clean = re.sub(r"\s+", " ", full_text_raw)
            pattern = re.compile(
                r"(?i)this\s+is\s+to\s+c(?:e|s)rtif[a-z]*\s+that[:,\-]?\s*([A-Za-z.\- ]{3,120})"
            )
            m2 = pattern.search(text_clean)
            if m2:
                seg = _clip_at_stop(m2.group(1))
                candidate = _clean_name(seg)
                if candidate:
                    name_candidates.append(candidate)
        
        if name_candidates:
            name = max(name_candidates, key=len)

        # --- Extracting Marks with Debugging Logic and Subject Flexibility ---
        subjects_to_check = [
            ("ENGLISH", "English"),
            ("MATHEMATICS", "Mathematics"),
            ("PHYSICS", "Physics"),
            ("CHEMISTRY", "Chemistry"),
            ("COMPUTER SCIENCE", "Computer Science")
        ]
        
        # Add Biology as a fallback for Computer Science
        subjects_to_check_flexible = subjects_to_check[:-1] + [
            ("COMPUTER SCIENCE", "Computer Science"),
            ("BIOLOGY", "Biology")
        ]

        final_subjects = {}
        
        # Flag to check if Computer Science was found
        cs_found = False

        for subject_keyword, display_name in subjects_to_check_flexible:
            
            # Skip Biology search if Computer Science has already been found
            if cs_found and display_name == "Biology":
                continue

            for text_item in text_data:
                if subject_keyword in text_item["text"].upper():
                    subject_bbox = text_item["bbox"]
                    
                    possible_marks = [
                        item for item in text_data if 
                        item["bbox"][0][0] > subject_bbox[0][0] and
                        abs(item["bbox"][0][1] - subject_bbox[0][1]) < 20 and
                        item["text"].replace(' ', '').isdigit()
                    ]

                    numeric_marks = [
                        item for item in possible_marks if len(item["text"]) <= 3
                    ]
                    
                    if numeric_marks:
                        rightmost_mark = max(numeric_marks, key=lambda x: x["bbox"][0][0])
                        mark_text = rightmost_mark["text"]
                        
                        # Apply debugging logic for common OCR errors
                        if len(mark_text) == 3 and int(mark_text) > 100:
                            corrected_mark = mark_text[:2]
                            if corrected_mark.isdigit():
                                mark_text = corrected_mark
                        
                        final_subjects[display_name] = mark_text
                        if display_name == "Computer Science":
                            cs_found = True

                    break # Move to the next subject once one is found

        # --- Calculate Total and Percentage ---
        total_marks = 0
        valid_subjects = 0
        for mark in final_subjects.values():
            if mark and isinstance(mark, str) and mark.isdigit():
                if int(mark) <= 100:
                    total_marks += int(mark)
                    valid_subjects += 1
        
        percentage = (total_marks / (valid_subjects * 100)) * 100 if valid_subjects > 0 else 0

        final_data = {
            "Medium": medium,
            "Class": marksheet_class,
            "Student name": name,
        }
        
        # Add subjects in the requested order (including either CS or Biology)
        for _, display_name in subjects_to_check:
            if display_name == "Computer Science" and "Biology" in final_subjects:
                final_data["Biology"] = final_subjects["Biology"]
            else:
                final_data[display_name] = final_subjects.get(display_name, "Not Found")
        
        # Clean up the output to remove "Computer Science" if Biology was found
        if "Biology" in final_data:
             final_data.pop("Computer Science", None)

        final_data["Total"] = total_marks
        final_data["Percentage"] = f"{percentage:.2f}%"
        
        return final_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return {
            "Status": "Failed",
            "Error": str(e)
        }

if __name__ == "__main__":
    file_name = "vinoth12.jpeg"
    if os.path.exists(file_name):
        print(f"\n--- Processing {file_name} ---")
        extracted_data = extract_marks_paddle_class12(file_name)
        if extracted_data:
            print(json.dumps(extracted_data, indent=2))
    else:
        print(f"Error: File '{file_name}' not found.")