# scripts/sort_to_subject.py
import os
import shutil
from PIL import Image
import easyocr
from transformers import pipeline

IN_DIR = "incoming"
OUT_DIR = "worksheets"

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'], gpu=False)

# Hugging Face classifier (if you're still using it)
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
subjects = ["math", "english", "science", "history", "other"]

def detect_subject(text):
    result = classifier(text, subjects)
    return result['labels'][0]

def process_image(file_path):
    # Run EasyOCR on image and join all detected text lines
    results = reader.readtext(file_path, detail=0)
    text = " ".join(results).strip()

    if not text:
        print(f"⚠️ Skipping {file_path} (no text found)")
        subject = "other"
    else:
        subject = detect_subject(text)

    dest_dir = os.path.join(OUT_DIR, subject)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, os.path.basename(file_path))
    shutil.move(file_path, dest_path)
    print(f"→ Moved {file_path} → {dest_path}")

def main():
    for filename in os.listdir(IN_DIR):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            process_image(os.path.join(IN_DIR, filename))

if __name__ == "__main__":
    main()
