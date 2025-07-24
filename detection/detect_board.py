import easyocr

def detect_board_type(image):
    reader = easyocr.Reader(['en'])
    results = reader.readtext(image, detail=0)
    content = " ".join(results).lower()

    if "cbse" in content:
        return "CBSE"
    elif "government of tamil nadu" in content or "dge" in content:
        return "State"
    elif "icse" in content or "council for the indian school certificate" in content:
        return "ICSE"
    else:
        return "Unknown"
