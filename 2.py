from paddleocr import PaddleOCR

# Use OCR with CPU only, English language
ocr = PaddleOCR(use_angle_cls=False, lang='en')  # set use_angle_cls=False to avoid warnings

# Run OCR on marksheet image
results = ocr.ocr("marksheet.png", cls=False)

# Extract text line by line
print("\n=== Extracted Text from Marksheet ===")
for res in results[0]:
    box, (text, confidence) = res
    print(f"{text}  (confidence: {confidence:.2f})")

# Example: filter subject - marks pairs
print("\n=== Subject : Marks ===")
for res in results[0]:
    _, (text, _) = res
    if any(ch.isdigit() for ch in text):  # crude filter for marks (numbers)
        print(text)

