import easyocr
from difflib import get_close_matches
from collections import defaultdict

# Initialize OCR reader
reader = easyocr.Reader(['en'])

# Path to image
image_path = 'saran12.jpeg'
results = reader.readtext(image_path)

# Target subjects list (including BIOLOGY)
target_subjects = ['TAMIL', 'ENGLISH', 'PHYSICS', 'CHEMISTRY', 'COMPUTER SCIENCE', 'BIOLOGY', 'MATHEMATICS', 'MATHS']

# Step 1: Extract all text elements
lines = []
for (tl, tr, br, bl), text, conf in results:
    x, y = int(tl[0]), int(tl[1])
    lines.append({'text': text.strip().upper(), 'x': x, 'y': y})

# Step 2: Group text into rows using Y-coordinate proximity
row_map = defaultdict(list)
y_threshold = 99  # Pixels tolerance to group into a row

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
for subj in ['TAMIL', 'ENGLISH', 'PHYSICS', 'CHEMISTRY', 'MATHEMATICS']:
    if subj in subject_marks:
        print(f"{subj:<18}: {subject_marks[subj]}")
    else:
        print(f"{subj:<18}: Not detected")

# Step 6: Detect and print either COMPUTER SCIENCE or BIOLOGY
if 'COMPUTER SCIENCE' in subject_marks:
    print(f"{'COMPUTER SCIENCE':<18}: {subject_marks['COMPUTER SCIENCE']}")
elif 'BIOLOGY' in subject_marks:
    print(f"{'BIOLOGY':<18}: {subject_marks['BIOLOGY']}")
else:
    print(f"{'COMPUTER SCIENCE / BIOLOGY':<18}: Not detected")

# Step 7: Calculate total
try:
    total_subjects = ['TAMIL', 'ENGLISH', 'PHYSICS', 'CHEMISTRY', 'MATHEMATICS']
    if 'COMPUTER SCIENCE' in subject_marks:
        total_subjects.append('COMPUTER SCIENCE')
    elif 'BIOLOGY' in subject_marks:
        total_subjects.append('BIOLOGY')
    total = sum(int(subject_marks[s]) for s in total_subjects if s in subject_marks)
    print(f"\nCalculated Total     : {total}")
except:
    print("\nTotal: Not available")
