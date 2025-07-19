import pytesseract
from PIL import Image
import re

# Set the path to Tesseract (adjust if needed)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Load image
image_path = 'sanjay_10.jpeg'
image = Image.open(image_path)

# OCR extract text
text = pytesseract.image_to_string(image)
print("OCR Text:\n", text)

# List of expected subjects (can add other variations)
subjects = ["Tamil", "English", "Maths", "Physics", "Chemistry", "Biology", "Computer Science"]

# Regex to extract subject marks
marks_found = []
for subject in subjects:
    match = re.search(fr"{subject}\s*[-:]\s(\d+)", text, re.IGNORECASE)
    if match:
        marks_found.append(int(match.group(1)))

# Check if 6 subjects found
if len(marks_found) == 6:
    total = sum(marks_found)
    percentage = (total / 600) * 100
    print(f"Marks: {marks_found}")
    print(f"Total: {total}/600")
    print(f"Percentage: {percentage:.2f}%")
else:
    print("⚠ Could not extract all 6 subject marks. Check OCR result or marksheet format.")