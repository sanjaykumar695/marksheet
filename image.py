import easyocr
import cv2
import numpy as np
from PIL import Image
from difflib import get_close_matches
import re
import matplotlib.pyplot as plt

def preprocess_certificate_image(input_path, output_path='preprocessed_certificate.png'):
    """
    Enhanced preprocessing pipeline for certificate images with:
    - Standardized color conversion
    - Adaptive contrast enhancement
    - Noise reduction optimized for text
    - Improved binarization
    - Size normalization
    """
    # Read image
    image = cv2.imread(input_path)
    
    # 1. Standardize size (maintain aspect ratio)
    target_height = 1500
    h, w = image.shape[:2]
    scale = target_height / h
    image = cv2.resize(image, (int(w * scale), target_height), interpolation=cv2.INTER_AREA)
    
    # 2. Convert to grayscale using luminosity method (better for human perception)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 3. Contrast Limited Adaptive Histogram Equalization (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrast = clahe.apply(gray)
    
    # 4. Denoising - Non-local Means for better text preservation
    denoised = cv2.fastNlMeansDenoising(contrast, None, h=10, templateWindowSize=7, searchWindowSize=21)
    
    # 5. Adaptive thresholding with optimized parameters
    thresh = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=11,  # Odd size, larger for more consistent backgrounds
        C=2  # Fine-tuned for certificate text
    )
    
    # 6. Morphological operations to clean up text
    kernel = np.ones((2, 2), np.uint8)
    processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # 7. Standardize output to black text on white background
    final_image = cv2.bitwise_not(processed)
    
    # Save
    cv2.imwrite(output_path, final_image)
    return output_path

def extract_subject_marks(image_path):
    """
    Enhanced mark extraction with:
    - Better text grouping
    - Improved subject matching
    - More robust mark detection
    """
    img = Image.open(image_path)
    image_height = img.height
    y_threshold = image_height // 40  # More precise line grouping
    
    # Initialize EasyOCR with optimized settings
    reader = easyocr.Reader(['en'], 
                          gpu=True,
                          model_storage_directory='./model',
                          download_enabled=True)
    
    # Read text with confidence threshold
    results = reader.readtext(image_path, 
                            paragraph=False,
                            min_size=10,
                            text_threshold=0.7,
                            low_text=0.4,
                            link_threshold=0.4,
                            canvas_size=2560)
    
    # Extract and filter text
    lines = []
    for (bbox, text, conf) in results:
        if conf >= 0.6:  # Higher confidence threshold
            x, y = int(bbox[0][0]), int(bbox[0][1])
            lines.append({'text': text.strip().upper(), 'x': x, 'y': y})
    
    # Group lines into rows with dynamic threshold
    lines_sorted = sorted(lines, key=lambda l: (l['y'], l['x']))
    rows = []
    if lines_sorted:
        current_row = [lines_sorted[0]]
        for line in lines_sorted[1:]:
            # Dynamic threshold based on average height of current row
            avg_height = sum(abs(l['y'] - current_row[0]['y']) for l in current_row) / len(current_row)
            threshold = max(y_threshold, avg_height * 1.5)
            
            if abs(line['y'] - current_row[0]['y']) <= threshold:
                current_row.append(line)
            else:
                rows.append(current_row)
                current_row = [line]
        if current_row:
            rows.append(current_row)
    
    # Enhanced subject list with common variations
    common_subjects = {
        'TAMIL': ['TAMIL', 'TML', 'TAMIZH'],
        'ENGLISH': ['ENGLISH', 'ENG', 'ENGL'],
        'MATHEMATICS': ['MATHEMATICS', 'MATHS', 'MATH', 'MATHEMATIC'],
        'PHYSICS': ['PHYSICS', 'PHY', 'PHYS'],
        'CHEMISTRY': ['CHEMISTRY', 'CHEM', 'CHY'],
        'BIOLOGY': ['BIOLOGY', 'BIO', 'BIOL'],
        'COMPUTER SCIENCE': ['COMPUTER SCIENCE', 'COMPUTER', 'CS', 'COMP SCI'],
        'HISTORY': ['HISTORY', 'HIST', 'HIS'],
        'GEOGRAPHY': ['GEOGRAPHY', 'GEOG', 'GEO'],
        'ECONOMICS': ['ECONOMICS', 'ECON', 'ECO'],
        'COMMERCE': ['COMMERCE', 'COMM', 'COMRCE'],
        'ACCOUNTANCY': ['ACCOUNTANCY', 'ACCOUNT', 'ACC', 'ACCNT'],
        'SCIENCE': ['SCIENCE', 'SCI', 'SCE'],
        'SOCIAL SCIENCE': ['SOCIAL SCIENCE', 'SOCIAL', 'SST', 'SOC SCI']
    }
    
    # Extract subject-mark pairs with improved logic
    subject_marks = {}
    for row in rows:
        row_text = ' '.join([item['text'] for item in row])
        
        # Find best subject match
        best_subject = None
        best_score = 0
        
        for subject, variants in common_subjects.items():
            for variant in variants:
                # Check for exact matches first
                if variant in row_text.split():
                    best_subject = subject
                    best_score = 1.0
                    break
                
                # Then check partial matches
                if variant in row_text:
                    current_score = len(variant) / len(row_text)
                    if current_score > best_score:
                        best_score = current_score
                        best_subject = subject
        
        # Find mark (look for numbers at end of line)
        mark = None
        for item in sorted(row, key=lambda i: i['x'], reverse=True):
            # More robust number detection
            num_match = re.search(r'(\d{2,3})(?:\s*/\s*\d{2,3})?$', item['text'])
            if num_match:
                mark = num_match.group(1)
                break
        
        if best_subject and mark:
            # Handle multiple occurrences (take highest mark)
            if best_subject in subject_marks:
                if int(mark) > int(subject_marks[best_subject]):
                    subject_marks[best_subject] = mark
            else:
                subject_marks[best_subject] = mark
    
    # Print results with formatting
    if subject_marks:
        print("\n📄 Extracted Subject Marks:")
        max_len = max(len(subj) for subj in subject_marks.keys())
        for subj, mark in sorted(subject_marks.items()):
            print(f"{subj.ljust(max_len + 2)}: {mark}")
        
        try:
            total = sum(int(m) for m in subject_marks.values())
            print(f"\n🧮 Total Marks: {total}")
        except:
            print("\n⚠️ Could not calculate total (invalid mark formats)")
    else:
        print("\n❌ No subject marks found in the document")

def show_preprocessing_debug(original_path, processed_path):
    """Enhanced debug visualization with histograms"""
    orig = cv2.imread(original_path)
    proc = cv2.imread(processed_path, cv2.IMREAD_GRAYSCALE)
    
    plt.figure(figsize=(15, 8))
    
    # Original image
    plt.subplot(2, 2, 1)
    plt.imshow(cv2.cvtColor(orig, cv2.COLOR_BGR2RGB))
    plt.title("Original Image")
    plt.axis('off')
    
    # Original histogram
    plt.subplot(2, 2, 2)
    plt.hist(orig.ravel(), 256, [0, 256], color='r')
    plt.title("Original Histogram")
    
    # Processed image
    plt.subplot(2, 2, 3)
    plt.imshow(proc, cmap='gray')
    plt.title("Preprocessed Image")
    plt.axis('off')
    
    # Processed histogram
    plt.subplot(2, 2, 4)
    plt.hist(proc.ravel(), 256, [0, 256], color='b')
    plt.title("Processed Histogram")
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    original_path = 'praveen12.jpeg'  # Replace with your file
    processed_path = preprocess_certificate_image(original_path)
    
    show_preprocessing_debug(original_path, processed_path)
    extract_subject_marks(processed_path)