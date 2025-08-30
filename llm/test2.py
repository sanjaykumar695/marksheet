import re
from paddleocr import PaddleOCR

# Initialize PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')

# Path to the image file
image_path = 'sanjay10.jpeg'

# Perform OCR on the image
result = ocr.ocr(image_path, cls=True)

# Function to extract marks for specific subjects
def extract_marks(result):
    subject_marks = {}
    subjects = ["ENGLISH", "TAMIL", "MATHEMATICS", "SCIENCE", "SOCIAL"]
    
    for line in result[0]:
        text = line[1]
        # Check if the subject is in the line and extract marks
        for subject in subjects:
            if subject in text:
                marks = re.findall(r'\d+', text)  # Extract numbers (marks)
                if marks:
                    subject_marks[subject] = marks[-1]  # Get the last number (marks)
    
    return subject_marks

# Extract the marks
marks = extract_marks(result)

# Print the extracted marks
print(marks)
