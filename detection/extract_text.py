import easyocr

def extract_text_from_image(image):
    reader = easyocr.Reader(['en'])
    results = reader.readtext(image, detail=0)
    return "\n".join(results)
