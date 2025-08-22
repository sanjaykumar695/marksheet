# from paddleocr import PaddleOCR
# import re

# # Use OCR with CPU only, English language
# ocr = PaddleOCR(use_angle_cls=False, lang='en')

# # Run OCR on marksheet image
# results = ocr.ocr("sanjay_10.jpeg", cls=False)

# # Flatten OCR results into plain text lines
# lines = [res[1][0] for res in results[0]]

# print("\n=== Extracted Text from Marksheet ===")
# for line in lines:
#     print(line)

# # Initialize extracted fields
# medium = None
# student_class = None
# student_name = None
# subjects_marks = {}
# total_scored = 0
# total_max = 0

# # 1) Detect medium (board)
# for line in lines:
#     if "CBSE" in line.upper():
#         medium = "CBSE"
#     elif "STATE" in line.upper():
#         medium = "State Board"
#     elif "ICSE" in line.upper():
#         medium = "ICSE"

# # 2) Detect class (10, 11, 12)
# for line in lines:
#     match = re.search(r'Class\s*[:\-]?\s*(\d{1,2})', line, re.IGNORECASE)
#     if match:
#         student_class = match.group(1)

# # 3) Detect student name
# for line in lines:
#     if "NAME" in line.upper():
#         # e.g. "Name: Sanjay Kumar"
#         match = re.search(r'NAME\s*[:\-]?\s*(.*)', line, re.IGNORECASE)
#         if match:
#             student_name = match.group(1).strip()
#         break

# # 4) Extract subject-wise marks
# # Example pattern: "Mathematics 95/100"
# for line in lines:
#     match = re.match(r'([A-Za-z\s]+)\s+(\d+)\s*/\s*(\d+)', line)
#     if match:
#         subject = match.group(1).strip()
#         scored = int(match.group(2))
#         maximum = int(match.group(3))
#         subjects_marks[subject] = (scored, maximum)
#         total_scored += scored
#         total_max += maximum

# # 5) Percentage calculation
# percentage = (total_scored / total_max * 100) if total_max > 0 else None

# print("\n=== Extracted Information ===")
# print("Medium:", medium)
# print("Class:", student_class)
# print("Student Name:", student_name)
# print("\nSubjects and Marks:")
# for subject, (scored, maximum) in subjects_marks.items():
#     print(f"{subject}: {scored}/{maximum}")
# print("\nTotal:", total_scored, "/", total_max)
# if percentage is not None:
#     print("Percentage:", f"{percentage:.2f}%")


#-------------------------------------------------------------------------------------------------------------



# from paddleocr import PaddleOCR
# import re

# # Use OCR with CPU only, English language
# ocr = PaddleOCR(use_angle_cls=False, lang='en')

# # Run OCR on marksheet image
# results = ocr.ocr("sanjay_10.jpeg", cls=False)

# # Flatten OCR results into plain text lines
# lines = [res[1][0] for res in results[0]]

# print("\n=== Extracted Text from Marksheet ===")
# for line in lines:
#     print(line)

# # Initialize extracted fields
# medium = None
# student_class = None
# student_name = None
# subjects_marks = {}
# total_scored = 0
# total_max = 0

# # 1) Detect medium (board)
# for line in lines:
#     if "CENTRAL BOARD OF SECONDARY EDUCATION" in line.upper():
#         medium = "CBSE"
#     elif "STATE" in line.upper():
#         medium = "State Board"
#     elif "ICSE" in line.upper():
#         medium = "ICSE"

# # 2) Detect class (10, 11, 12)
# for line in lines:
#     match = re.search(r'Class\s*[:\-]?\s*(\d{1,2})', line, re.IGNORECASE)
#     if match:
#         student_class = match.group(1)

# # 3) Detect student name (CBSE style: "This is to certify that <name>")
# for line in lines:
#     if "THIS IS TO CERTIFY THAT" in line.upper():
#         # Remove prefix and extract name part
#         name_part = re.sub(r'(?i)this is to certify that', '', line).strip()
#         student_name = name_part
#         break

# # 4) Extract subject-wise marks (format: "Mathematics 95/100")
# for line in lines:
#     match = re.match(r'([A-Za-z\s]+)\s+(\d+)\s*/\s*(\d+)', line)
#     if match:
#         subject = match.group(1).strip()
#         scored = int(match.group(2))
#         maximum = int(match.group(3))
#         subjects_marks[subject] = (scored, maximum)
#         total_scored += scored
#         total_max += maximum

# # 5) Percentage calculation
# percentage = (total_scored / total_max * 100) if total_max > 0 else None

# print("\n=== Extracted Information ===")
# print("Medium:", medium)
# print("Class:", student_class)
# print("Student Name:", student_name)
# print("\nSubjects and Marks:")
# for subject, (scored, maximum) in subjects_marks.items():
#     print(f"{subject}: {scored}/{maximum}")
# print("\nTotal:", total_scored, "/", total_max)
# if percentage is not None:
#     print("Percentage:", f"{percentage:.2f}%")





#---------------------------------------------------------------------------------------------------------------------


from paddleocr import PaddleOCR
import re

# Use OCR with CPU only, English language
ocr = PaddleOCR(use_angle_cls=False, lang='en')

# Run OCR on marksheet image
results = ocr.ocr("sanjay12.jpeg", cls=False)

# Flatten OCR results into plain text lines
lines = [res[1][0] for res in results[0]]

print("\n=== Extracted Text from Marksheet ===")
for line in lines:
    print(line)

# Initialize extracted fields
medium = None
student_class = None
student_name = None
subjects_marks = {}
total_scored = 0
total_max = 0

def normalize_alpha(s: str) -> str:
    """Uppercase and strip all non A–Z to handle OCR spacing/punctuations."""
    return re.sub(r'[^A-Z]', '', s.upper())

# -----------------------------
# 1) Detect medium (board)
# Robust CBSE detection even if OCR merges words or misspells 'CENTRAL' as 'CENTERAL'
cbse_norm_targets = {
    "CENTRALBOARDOFSECONDARYEDUCATION",
    "CENTERALBOARDOFSECONDARYEDUCATION",   # common OCR typo
    "CENTRALBOARDSECONDARYEDUCATION",      # 'OF' dropped
}

# Pass 1: CBSE
for line in lines:
    up = line.upper()
    norm = normalize_alpha(line)
    contains_cbse_tokens = (("CENTRAL" in up) or ("CENTERAL" in up)) and ("BOARD" in up) and ("SECONDARY" in up) and ("EDUCATION" in up)
    contains_cbse_norm = any(t in norm for t in cbse_norm_targets)
    if "CBSE" in up or contains_cbse_tokens or contains_cbse_norm:
        medium = "CBSE"
        break

# Pass 2: ICSE / CISCE
if not medium:
    for line in lines:
        up = line.upper()
        if ("ICSE" in up) or ("CISCE" in up) or (
            "COUNCIL" in up and "INDIAN" in up and "SCHOOL" in up and "CERTIFICATE" in up and ("EXAMINATION" in up or "EXAMINATIONS" in up)
        ):
            medium = "ICSE"
            break

# Pass 3: State Board (only if not already detected as CBSE/ICSE)
if not medium:
    state_patterns = [
        r'\bSTATE\s*BOARD\b',
        r'\bBOARD OF SECONDARY EDUCATION\b',
        r'\bHIGHER SECONDARY\b',
        r'\bBOARD OF INTERMEDIATE EDUCATION\b',
        r'\bDIRECTORATE OF GOVERNMENT EXAMINATIONS\b',
        r'\bBOARD OF SCHOOL EDUCATION\b',
    ]
    for line in lines:
        up = line.upper()
        # Avoid misclassifying a CBSE line that also contains 'BOARD OF SECONDARY EDUCATION'
        if any(re.search(p, up) for p in state_patterns) and ("CENTRAL" not in up and "CENTERAL" not in up):
            medium = "State Board"
            break

# -----------------------------
# 2) Detect class (10, 11, 12)
for line in lines:
    match = re.search(r'\bClass\s*[:\-]?\s*(\d{1,2})\b', line, re.IGNORECASE)
    if match:
        student_class = match.group(1)
        break

# 3) Detect student name (line like: "This is to certify that <NAME> ...")
for line in lines:
    if "THIS IS TO CERTIFY THAT" in line.upper():
        student_name = re.sub(r'(?i)this is to certify that', '', line).strip()
        break

# 4) Extract subject-wise marks (format like: "Mathematics 95/100")
for line in lines:
    m = re.match(r'([A-Za-z][A-Za-z\s.&()-/]+?)\s+(\d{1,3})\s*/\s*(\d{1,3})\b', line.strip())
    if m:
        subject = m.group(1).strip(" .-")
        scored = int(m.group(2))
        maximum = int(m.group(3))
        subjects_marks[subject] = (scored, maximum)
        total_scored += scored
        total_max += maximum

# 5) Percentage calculation
percentage = (total_scored / total_max * 100) if total_max > 0 else None

print("\n=== Extracted Information ===")
print("Medium:", medium)
print("Class:", student_class)
print("Student Name:", student_name)
print("\nSubjects and Marks:")
for subject, (scored, maximum) in subjects_marks.items():
    print(f"{subject}: {scored}/{maximum}")
print("\nTotal:", total_scored, "/", total_max)
if percentage is not None:
    print("Percentage:", f"{percentage:.2f}%")
