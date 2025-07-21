import easyocr

# Load EasyOCR reader with only English to reduce model issues
reader = easyocr.Reader(['en'])

# Path to image
image_path = 'mishitha12.jpeg'

# Run OCR
results = reader.readtext(image_path)

# Extract relevant data
subjects = ['TAMIL', 'ENGLISH', 'PHYSICS', 'CHEMISTRY', 'BIOLOGY','COMPUTER SCIENCE' 'MATHEMATICS', 'MATHS', 'TOTAL']
marks_data = {}

for detection in results:
    text = detection[1].upper()
    for subject in subjects:
        if subject in text:
            # Try to get nearby number (mark)
            index = results.index(detection)
            if index + 1 < len(results):
                mark_text = results[index + 1][1]
                if mark_text.strip().isdigit():
                    marks_data[subject] = mark_text.strip()

# Handle alias (MATHEMATICS or MATHS)
if "MATHS" in marks_data and "MATHEMATICS" not in marks_data:
    marks_data["MATHEMATICS"] = marks_data.pop("MATHS")

# Print neatly
print("Subject-wise Marks:")
for subj in subjects:
    if subj in marks_data:
        print(f"{subj.capitalize():<12}: {marks_data[subj]}")

# Calculate total if missing
if 'TOTAL' not in marks_data:
    try:
        total = sum(int(m) for s, m in marks_data.items() if s != 'TOTAL')
        print(f"\nCalculated Total : {total}")
    except:
        print("\nTotal: Not available")
