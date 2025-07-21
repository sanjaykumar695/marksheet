import easyocr
import cv2
import numpy as np
from PIL import Image
from difflib import get_close_matches
from collections import defaultdict
import re
import matplotlib.pyplot as plt

# ------------- Image Preprocessing Function -------------
def preprocess_image(input_path, output_path='processed.png'):
    image = cv2.imread(input_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Remove noise but preserve edges
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)

    # Increase contrast
    #contrast = cv2.equalizeHist(filtered)

    # Thresholding (Otsu Binarization)
    _, thresh = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Resize if height is too small
    h, w = thresh.shape
    if h < 1000:
        scale = 1000 / h
        thresh = cv2.resize(thresh, (int(w * scale), 1000), interpolation=cv2.INTER_CUBIC)

    # Save processed image
    cv2.imwrite(output_path, thresh)
    return output_path

# ------------- Mark Extraction Function -------------
def extract_marks(image_path):
    # Load processed image
    img = Image.open(image_path)
    image_height = img.height
    adaptive_y_threshold = image_height // 50  # dynamic row grouping

    # Load OCR reader
    reader = easyocr.Reader(['en'])

    # Run OCR
    results = reader.readtext(image_path)

    # Extract confident text
    lines = []
    min_confidence = 0.5
    for (tl, tr, br, bl), text, conf in results:
        if conf >= min_confidence:
            x, y = int(tl[0]), int(tl[1])
            lines.append({'text': text.strip().upper(), 'x': x, 'y': y})

    # Sort and group lines into rows
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

    # List of possible subjects
    common_subjects = [
        'TAMIL', 'ENGLISH', 'PHYSICS', 'CHEMISTRY',
        'BIOLOGY', 'MATHEMATICS', 'MATHS', 'COMPUTER SCIENCE',
        'HISTORY', 'GEOGRAPHY', 'ECONOMICS', 'COMMERCE',
        'ACCOUNTANCY', 'SCIENCE', 'SOCIAL SCIENCE'
    ]

    # Match subjects and extract marks
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

        for item in sorted(row, key=lambda i: i['x'], reverse=True):
            if re.fullmatch(r'\d{2,3}', item['text']):
                mark_guess = item['text']
                break

        if subject_guess and mark_guess:
            subject_marks[subject_guess] = mark_guess

    # Normalize alias
    if "MATHS" in subject_marks:
        subject_marks["MATHEMATICS"] = subject_marks.pop("MATHS")

    # Display results
    print("\n📄 Extracted Subject Marks:")
    for subj, mark in subject_marks.items():
        print(f"{subj:<20}: {mark}")

    # Calculate total
    try:
        numeric_marks = [int(mark) for mark in subject_marks.values()]
        print(f"\n🧮 Total Marks         : {sum(numeric_marks)}")
    except:
        print("\n❌ Total: Could not calculate (non-numeric mark found)")

# ------------- Optional: Visual Debugging -------------
def show_image_comparison(original, processed):
    orig = cv2.imread(original)
    proc = cv2.imread(processed)

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.imshow(cv2.cvtColor(orig, cv2.COLOR_BGR2RGB))
    plt.title("Original")

    plt.subplot(1, 2, 2)
    plt.imshow(cv2.cvtColor(proc, cv2.COLOR_BGR2RGB))
    plt.title("Preprocessed")

    plt.tight_layout()
    plt.show()

# ------------- Main Execution -------------
if __name__ == "__main__":
    original_image = 'saran12.jpeg'  # <- change this to your image file
    processed_image = preprocess_image(original_image)
    show_image_comparison(original_image, processed_image)
    extract_marks(processed_image)
