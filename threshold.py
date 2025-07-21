import easyocr
from difflib import get_close_matches
from collections import defaultdict
from PIL import Image
import re

# Load OCR reader
reader = easyocr.Reader(['en'])

# Image path
image_path = 'sanjay12.jpeg'  # change as needed

# Read image size to adapt threshold
img = Image.open(image_path)
image_height = img.height
adaptive_y_threshold = image_height // 50  # works well across resolutions

# Read text from image
results = reader.readtext(image_path)

# Step 1: Extract confident lines
lines = []
min_confidence = 0.5  # skip bad OCR lines

for (tl, tr, br, bl), text, conf in results:
    if conf >= min_confidence:
        x, y = int(tl[0]), int(tl[1])
        lines.append({'text': text.strip().upper(), 'x': x, 'y': y})

# Step 2: Sort and cluster lines into rows by Y proximity
lines_sorted = sorted(lines, key=lambda l: (l['y'], l['x']))
rows = []
current_row = []

for line in lines_sorted:
    if not current_row:
        current_row.append(line)
    else:
        if abs(line['y'] - current_row[-1]['y']) <= adaptive_y_threshold:
            current_row.append(line)
        else:
            rows.append(current_row)
            current_row = [line]
if current_row:
    rows.append(current_row)

# Step 3: Define possible subject names
common_subjects = [
    'TAMIL', 'ENGLISH', 'PHYSICS', 'CHEMISTRY',
    'BIOLOGY', 'MATHEMATICS', 'MATHS', 'COMPUTER SCIENCE',
    'HISTORY', 'GEOGRAPHY', 'ECONOMICS', 'COMMERCE',
    'ACCOUNTANCY', 'SCIENCE', 'SOCIAL SCIENCE'
]

# Step 4: Detect subjects and marks
subject_marks = {}

for row in rows:
    texts = [item['text'] for item in row]
    subject_guess = None
    mark_guess = None

    for text in texts:
        match = get_close_matches(text, common_subjects, n=1, cutoff=0.6)
        if match:
            subject_guess = match[0]
            break

    # Try finding the right-most numeric value (2-3 digits)
    for item in sorted(row, key=lambda i: i['x'], reverse=True):
        if re.fullmatch(r'\d{2,3}', item['text']):
            mark_guess = item['text']
            break

    if subject_guess and mark_guess:
        subject_marks[subject_guess] = mark_guess

# Step 5: Handle alias "MATHS" → "MATHEMATICS"
if "MATHS" in subject_marks:
    subject_marks["MATHEMATICS"] = subject_marks.pop("MATHS")

# Step 6: Display results
print("\n📄 Extracted Subject Marks:")
for subj, mark in subject_marks.items():
    print(f"{subj:<20}: {mark}")

# Step 7: Calculate total
try:
    numeric_marks = [int(mark) for mark in subject_marks.values()]
    print(f"\n🧮 Total Marks         : {sum(numeric_marks)}")
except:
    print("\n❌ Total: Could not calculate (non-numeric mark found)")
