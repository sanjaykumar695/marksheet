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

# Initialize OCR reader
reader = easyocr.Reader(['en'])

# Path to image
image_path = 'praveen12.jpeg'
results = reader.readtext(image_path)

# Target subjects list
target_subjects = ['TAMIL', 'ENGLISH', 'PHYSICS', 'CHEMISTRY', 'COMPUTER SCIENCE', 'MATHEMATICS', 'MATHS']

# Step 1: Extract all text elements
lines = []
for (tl, tr, br, bl), text, conf in results:
    x, y = int(tl[0]), int(tl[1])
    lines.append({'text': text.strip().upper(), 'x': x, 'y': y})

# Step 2: Group text into rows using Y-coordinate proximity
row_map = defaultdict(list)
y_threshold = 99 # Pixels tolerance to group into a row

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

# Step 3: Detect subject and mark in each row
subject_marks = {}
for row in row_map.values():
    subject = None
    mark = None
    for item in row:
        # Match subject using fuzzy matching
        match = get_close_matches(item['text'], target_subjects, n=1, cutoff=0.6)
        if match:
            subject = match[0]
        # Look for a 3-digit mark (usually out of 100) on the right side
        if item['x'] > 900 and item['text'].isdigit() and len(item['text']) == 3:
            mark = item['text']
    if subject and mark:
        subject_marks[subject] = mark

# Step 4: Handle alias "MATHS" -> "MATHEMATICS"
if "MATHS" in subject_marks and "MATHEMATICS" not in subject_marks:
    subject_marks["MATHEMATICS"] = subject_marks.pop("MATHS")

# Step 5: Print subject-wise marks
print("\nMarks Obtained for 100:")
for subj in ['TAMIL', 'ENGLISH', 'PHYSICS', 'CHEMISTRY', 'COMPUTER SCIENCE', 'MATHEMATICS']:
    if subj in subject_marks:
        print(f"{subj:<18}: {subject_marks[subj]}")
    else:
        print(f"{subj:<18}: Not detected")

# Step 6: Calculate total
try:
    total = sum(int(subject_marks[s]) for s in ['TAMIL', 'ENGLISH', 'PHYSICS', 'CHEMISTRY', 'COMPUTER SCIENCE', 'MATHEMATICS'] if s in subject_marks)
    print(f"\nCalculated Total     : {total}")
except:
    print("\nTotal: Not available")
