from preprocess_image import preprocess
from detect_board import detect_board_type
from extract_text import extract_text_from_image
from parse_data import parse_details

def main():
    image_path = input("Enter marksheet image path: ")

    processed_image = preprocess(image_path)
    board_type = detect_board_type(processed_image)
    print(f"Detected Board: {board_type}")

    text_data = extract_text_from_image(processed_image)
    parsed = parse_details(text_data, board_type)

    print("\n--- Marksheet Details ---")
    for k, v in parsed.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
