# import easyocr

# # Load EasyOCR reader with only English to reduce model issues
# reader = easyocr.Reader(['en'])

# # Path to image
# image_path = 'mishitha12.jpeg'

# # Run OCR
# results = reader.readtext(image_path)

# # Extract relevant data
# subjects = ['TAMIL', 'ENGLISH', 'PHYSICS', 'CHEMISTRY', 'BIOLOGY','COMPUTER SCIENCE' 'MATHEMATICS', 'MATHS', 'TOTAL']
# marks_data = {}

# for detection in results:
#     text = detection[1].upper()
#     for subject in subjects:
#         if subject in text:
#             # Try to get nearby number (mark)
#             index = results.index(detection)
#             if index + 1 < len(results):
#                 mark_text = results[index + 1][1]
#                 if mark_text.strip().isdigit():
#                     marks_data[subject] = mark_text.strip()

# # Handle alias (MATHEMATICS or MATHS)
# if "MATHS" in marks_data and "MATHEMATICS" not in marks_data:
#     marks_data["MATHEMATICS"] = marks_data.pop("MATHS")

# # Print neatly
# print("Subject-wise Marks:")
# for subj in subjects:
#     if subj in marks_data:
#         print(f"{subj.capitalize():<12}: {marks_data[subj]}")

# # Calculate total if missing
# if 'TOTAL' not in marks_data:
#     try:
#         total = sum(int(m) for s, m in marks_data.items() if s != 'TOTAL')
#         print(f"\nCalculated Total : {total}")
#     except:
#         print("\nTotal: Not available")









# import easyocr
# from difflib import get_close_matches

# # Initialize OCR
# reader = easyocr.Reader(['en'])

# # Image path
# image_path = 'praveen12.jpeg'
# results = reader.readtext(image_path)

# # Subject list
# target_subjects = ['TAMIL', 'ENGLISH', 'PHYSICS', 'CHEMISTRY', 'COMPUTER SCIENCE', 'MATHEMATICS']

# # Extract text lines
# lines = []
# for (tl, tr, br, bl), text, conf in results:
#     x, y = int(tl[0]), int(tl[1])
#     lines.append({'text': text.strip().upper(), 'x': x, 'y': y})

# # Step 1: Detect subject rows using fuzzy matching
# subject_y_map = {}
# for line in lines:
#     # Try to match OCR text to subject using fuzzy match
#     match = get_close_matches(line['text'], target_subjects, n=1, cutoff=0.6)
#     if match:
#         subject = match[0]
#         if subject not in subject_y_map:
#             subject_y_map[subject] = line['y']

# # Step 2: Extract 3-digit marks on the right (x > 900)
# right_marks = []
# for line in lines:
#     if line['x'] > 900 and line['text'].isdigit() and len(line['text']) == 3:
#         right_marks.append({'mark': line['text'], 'y': line['y']})

# # Step 3: Match marks to closest subject row by Y position
# marks_map = {}
# for subj, subj_y in subject_y_map.items():
#     closest_mark = None
#     min_diff = float('inf')
#     for mark in right_marks:
#         diff = abs(mark['y'] - subj_y)
#         if diff < min_diff and diff <= 90:  # increased threshold to 30
#             min_diff = diff
#             closest_mark = mark['mark']
#     if closest_mark:
#         marks_map[subj] = closest_mark
#     else:
#         print(f"⚠️  Mark not matched for subject: {subj} (subject_y={subj_y})")

# # Step 4: Output results
# print("\nMarks Obtained for 100:")
# for subj in target_subjects:
#     if subj in marks_map:
#         print(f"{subj:<18}: {marks_map[subj]}")
#     else:
#         print(f"{subj:<18}: Not detected")

# # Step 5: Total
# try:
#     total = sum(int(m) for m in marks_map.values())
#     print(f"\nCalculated Total     : {total}")
# except:
#     print("\nTotal: Not available")






import easyocr
from difflib import get_close_matches
from collections import defaultdict
import re

# Initialize OCR reader
reader = easyocr.Reader(['en'])

# Path to image
image_path = 'sabesh12.jpeg'  # change this as needed
results = reader.readtext(image_path)

# Step 1: Extract text with coordinates
lines = []
for (tl, tr, br, bl), text, conf in results:
    x, y = int(tl[0]), int(tl[1])
    lines.append({'text': text.strip().upper(), 'x': x, 'y': y})

# Step 2: Group lines by Y-coordinate proximity into rows
row_map = defaultdict(list)
y_threshold = 55

for line in lines:
    y = line['y']
    matched = False
    for row_y in list(row_map.keys()):
        if abs(y - row_y) <= y_threshold:
            row_map[row_y].append(line)
            matched = True
            break
    if not matched:
        row_map[y].append(line)

# Step 3: Extract subjects and marks from each row
subject_marks = {}

# Common subject keywords to assist fuzzy match
common_subjects = [
    'TAMIL', 'ENGLISH', 'PHYSICS', 'CHEMISTRY',
    'BIOLOGY', 'MATHEMATICS', 'MATHS', 'COMPUTER SCIENCE',
    'HISTORY', 'GEOGRAPHY', 'ECONOMICS', 'COMMERCE',
    'ACCOUNTANCY', 'SCIENCE', 'SOCIAL SCIENCE'
]

for row in row_map.values():
    texts = [item['text'] for item in row]
    subject_guess = None
    mark_guess = None

    # 1. Try to match a subject
    for text in texts:
        match = get_close_matches(text, common_subjects, n=1, cutoff=0.6)
        if match:
            subject_guess = match[0]
            break

    # 2. Try to find a mark (prefer 2-3 digit numbers)
    for item in sorted(row, key=lambda i: i['x'], reverse=True):  # rightmost first
        if re.fullmatch(r'\d{2,3}', item['text']):
            mark_guess = item['text']
            break

    if subject_guess and mark_guess:
        subject_marks[subject_guess] = mark_guess

# Step 4: Handle "MATHS" → "MATHEMATICS"
if "MATHS" in subject_marks:
    subject_marks["MATHEMATICS"] = subject_marks.pop("MATHS")

# Step 5: Print extracted marks
print("\n📄 Extracted Subject Marks:")
for subj, mark in subject_marks.items():
    print(f"{subj:<20}: {mark}")

# Step 6: Calculate total
try:
    numeric_marks = [int(m) for m in subject_marks.values()]
    print(f"\n🧮 Total Marks         : {sum(numeric_marks)}")
except:
    print("\n❌ Total: Could not calculate (non-numeric mark found)")
