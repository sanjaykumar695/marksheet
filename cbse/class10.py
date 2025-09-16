import os
import re
from typing import Dict, List, Any
from paddleocr import PaddleOCR

# Initialize PaddleOCR once
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

def _word_to_num(word_num: str) -> int:
    """Converts a number spelled out in words to an integer."""
    word_to_digit = {
        'ZERO': 0, 'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5,
        'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10,
        'ELEVEN': 11, 'TWELVE': 12, 'THIRTEEN': 13, 'FOURTEEN': 14,
        'FIFTEEN': 15, 'SIXTEEN': 16, 'SEVENTEEN': 17, 'EIGHTEEN': 18,
        'NINETEEN': 19, 'TWENTY': 20, 'THIRTY': 30, 'FORTY': 40, 'FIFTY': 50,
        'SIXTY': 60, 'SEVENTY': 70, 'EIGHTY': 80, 'NINETY': 90,
    }
    total = 0
    words = word_num.upper().replace('-', ' ').split()
    if not words:
        return -1
    
    current_num = 0
    for word in words:
        if word in word_to_digit:
            current_num += word_to_digit[word]
        elif 'HUNDRED' in word:
            total += current_num * 100
            current_num = 0
    return total + current_num

def extract_marks_paddle(image_path: str) -> Dict[str, Any]:
    """
    Extracts marks, student name, medium, and class from a marksheet image using PaddleOCR.
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

        # --- Student Name Extraction Logic from Code 1 ---
        name = "Not Found"
        name_candidates = []
        anchor_rx = re.compile(r"(?i)this\W*is\W*to\W*(?:c(?:e|s)rtif|certif|sertif)[a-z]*\W*that\W*")

        for idx, ln in enumerate(lines_raw):
            m = anchor_rx.search(ln)
            if not m:
                continue
            pool = ln[m.end():].strip()

            # merge next 2-3 lines if too short
            for extra_idx in range(1, 4):
                if len(pool) < 5 and idx + extra_idx < len(lines_raw):
                    pool += " " + lines_raw[idx + extra_idx]

            segment = _clip_at_stop(pool)
            candidate = _clean_name(segment)

            if candidate and (len(candidate.split()) >= 2 or len(candidate) >= 5):
                name_candidates.append(candidate)

        # fallback regex search on full text
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
        
        # choose best candidate
        if name_candidates:
            name = max(name_candidates, key=len)

        # --- Extracting Marks with Double-Check Logic ---
        subjects_to_check = {
            "ENGLISH": "English",
            "TAMIL": "Tamil",
            "HINDI": "Hindi",
            "MATHEMATICS": "Mathematics",
            "SCIENCE": "Science",
            "SOCIAL": "Social"
        }
        
        final_subjects = {}

        for subject_name, display_name in subjects_to_check.items():
            found_subject = False
            for text_item in text_data:
                if subject_name in text_item["text"].upper():
                    found_subject = True
                    subject_bbox = text_item["bbox"]
                    
                    # 1. Find the rightmost number (candidate for total marks)
                    possible_marks = [
                        item for item in text_data if 
                        item["bbox"][0][0] > subject_bbox[0][0] and
                        abs(item["bbox"][0][1] - subject_bbox[0][1]) < 20 and
                        item["text"].isdigit() and len(item["text"]) <= 3
                    ]
                    num_mark = None
                    if possible_marks:
                        rightmost_mark = max(possible_marks, key=lambda x: x["bbox"][0][0])
                        num_mark = rightmost_mark["text"]

                    # 2. Find the total mark in words (next to the number)
                    possible_word_marks = [
                        item for item in text_data if
                        item["bbox"][0][0] > subject_bbox[0][0] and
                        abs(item["bbox"][0][1] - subject_bbox[0][1]) < 20 and
                        not item["text"].isdigit() and len(item["text"]) > 3
                    ]
                    word_mark_text = None
                    if possible_word_marks:
                        rightmost_word = max(possible_word_marks, key=lambda x: x["bbox"][0][0])
                        word_mark_text = rightmost_word["text"]

                    # 3. Verify the numerical mark with the word-based mark
                    if num_mark and word_mark_text:
                        word_value = _word_to_num(word_mark_text)
                        if word_value == int(num_mark):
                            final_subjects[display_name] = num_mark
                        else:
                            final_subjects[display_name] = str(word_value)
                    elif num_mark:
                        final_subjects[display_name] = num_mark
                    elif word_mark_text:
                        final_subjects[display_name] = str(_word_to_num(word_mark_text))
                    
                    break
            
            # If both TAMIL and HINDI are in the list, and one is found, we should skip the other
            if (subject_name == "TAMIL" and "Hindi" in final_subjects) or \
               (subject_name == "HINDI" and "Tamil" in final_subjects):
                continue

        # --- Calculate Total and Percentage ---
        total_marks = 0
        valid_subjects = 0
        for mark in final_subjects.values():
            if mark and isinstance(mark, str) and mark.isdigit():
                total_marks += int(mark)
                valid_subjects += 1
        
        percentage = (total_marks / (valid_subjects * 100)) * 100 if valid_subjects > 0 else 0

        final_data = {
            "Medium": medium,
            "Class": marksheet_class,
            "Student name": name,
            **final_subjects,
            "Total": total_marks,
            "Percentage": f"{percentage:.2f}%"
        }
        
        return final_data

    except Exception as e:
        print(f"An error occurred: {e}")
        return {
            "Status": "Failed",
            "Error": str(e)
        }

# --- Main loop for multiple images ---
if __name__ == "__main__":
    marksheet_files = ["nandhini10.jpeg"]
    
    for file_name in marksheet_files:
        if os.path.exists(file_name):
            print(f"\n--- Processing {file_name} ---")
            extracted_data = extract_marks_paddle(file_name)
            if extracted_data:
                for key, value in extracted_data.items():
                    print(f"{key}: {value}")
        else:
            print(f"Error: File '{file_name}' not found.")