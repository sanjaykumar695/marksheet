from paddleocr import PaddleOCR
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import json

# Step 1: OCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')

def extract_text_from_image(img_path):
    results = ocr.ocr(img_path, cls=True)
    text_lines = []
    for res in results[0]:
        text_lines.append(res[1][0])  # Extract text
    return "\n".join(text_lines)

# Step 2: LLM for structured parsing
model_name = "meta-llama/Meta-Llama-3-8B-Instruct"  # you need local/hf access
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, device_map="auto")

def parse_marksheet_with_llm(raw_text):
    prompt = f"""
    You are given OCR text extracted from a marksheet. 
    Extract the following in JSON format:
    - student_name
    - class
    - medium
    - subjects: list of {{"subject": ..., "marks": ...}}
    - total
    - percentage

    OCR text:
    {raw_text}
    """

    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_new_tokens=500)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Try extracting JSON from LLM output
    try:
        structured = json.loads(response.split("```json")[-1].split("```")[0])
    except:
        structured = {"raw_output": response}
    return structured

# Step 3: Calculate totals if LLM doesn’t
def compute_results(data):
    if "subjects" in data:
        total = sum(int(s["marks"]) for s in data["subjects"])
        percentage = round(total / (len(data["subjects"])*100) * 100, 2)
        data["total"] = total
        data["percentage"] = percentage
    return data

# Main
if __name__ == "__main__":
    img_path = "sanjay10.jpeg"  # your input
    raw_text = extract_text_from_image(img_path)
    parsed = parse_marksheet_with_llm(raw_text)
    final_data = compute_results(parsed)

    print(json.dumps(final_data, indent=2))
