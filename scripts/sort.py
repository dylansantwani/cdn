import os
import shutil
import google.generativeai as genai
from PIL import Image
import pytesseract

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-pro")
src_dir = "incoming"
dest_dir = "worksheets"

os.makedirs(dest_dir, exist_ok=True)

def extract_text(path):
    if path.lower().endswith((".jpg", ".png")):
        return pytesseract.image_to_string(Image.open(path))
    elif path.lower().endswith(".pdf"):
        return "[PDF content skipped]"
    else:
        with open(path, "r", errors="ignore") as f:
            return f.read()

for filename in os.listdir(src_dir):
    fpath = os.path.join(src_dir, filename)
    if not os.path.isfile(fpath):
        continue

    content = extract_text(fpath)
    prompt = f"""
Classify this content into one of: Math, English,Biology,Economics or Other.
Give only the label in lowercase — no explanation.

Content:
{content[:3000]}
"""

    try:
        response = model.generate_content(prompt)
        label = response.text.strip().lower()

        if "math" in label:
            folder = "math"
        elif "english" in label:
            folder = "english"
        else:
            folder = "other"

    except Exception as e:
        print(f"Error classifying {filename}: {e}")
        folder = "other"

    out_dir = os.path.join(dest_dir, folder)
    os.makedirs(out_dir, exist_ok=True)
    shutil.move(fpath, os.path.join(out_dir, filename))
    print(f"Moved {filename} to worksheets/{folder}/")
