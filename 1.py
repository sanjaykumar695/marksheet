import cv2
import pytesseract
import re
from PIL import Image
from pdf2image import convert_from_path

# Set Tesseract path (if needed)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_path):
    image = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Auto contrast using histogram equalization
    equalized = cv2.equalizeHist(gray)

    # Adaptive Thresholding
    thresh = cv2.adaptiveThreshold(equalized, 255, 
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY, 11, 2)
    return thresh

def extract_text(image):
    return pytesseract.image_to_string(image)

def extract_details(text):
    # Try to find name
    name_match = re.search(r'Name\s*[:\-]?\s*([A-Za-z ]+)', text, re.IGNORECASE)
    name = name_match.group(1).strip() if name_match else "Not Found"

    # Extract subject and marks (works for lines like: English 95)
    marks = re.findall(r'([A-Za-z ]+)\s+(\d{1,3})', text)

    return name, marks

# Example usage
image_path = "praveen 12.jpeg"  # Replace with your file
processed_img = preprocess_image(image_path)
text = extract_text(processed_img)
name, marks = extract_details(text)

print("Name:", name)
print("Marks:")
for subject, mark in marks:
    print(f"{subject.strip()} - {mark}")
