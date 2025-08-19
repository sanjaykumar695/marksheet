import re
from paddleocr import PaddleOCR

# Initialize OCR (CPU only, English)
ocr = PaddleOCR(use_angle_cls=True, lang='en')

# Run OCR on the marksheet image
image_path = "marksheet.png"   # Change filename if needed
results = ocr.ocr(image_path)

# Dictionary to store subject -> marks
marks_dict = {}

# Extract text line by line
for res in results:
    for line in res:
        text = line[1][0]  # Extract recognized text
        # Match subject + marks (e.g., "Maths 95", "Science: 88")
        match = re.match(r"([A-Za-z\s]+)[:\-]?\s*(\d{1,3})$", text)
        if match:
            subject = match.group(1).strip()
            marks = int(match.group(2))
            marks_dict[subject] = marks

# Print extracted results
print("\n📘 Subject-wise Marks:", marks_dict)

if marks_dict:
    total = sum(marks_dict.values())
    percentage = total / (len(marks_dict) * 100) * 100
    print("✅ Total:", total)
    print("✅ Percentage:", round(percentage, 2), "%")
else:
    print("⚠️ No marks found in the document.")
