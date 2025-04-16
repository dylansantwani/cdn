# scripts/sort_to_subject.py
import os
import shutil
from PIL import Image
import pytesseract
from transformers import pipeline

IN_DIR = "incoming"
OUT_DIR = "worksheets"

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
subjects = ["math", "english", "science", "history", "other"]

def detect_subject(text):
    result = classifier(text, subjects)
    return result['labels'][0]  # top prediction

def process_image(file_path):
    text = pytesseract.image_to_string(Image.open(file_path))
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
