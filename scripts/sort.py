import os
import shutil
import google.generativeai as genai
from PIL import Image
import pytesseract
import pdfplumber

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro")

src_dir = "incoming"
dest_dir = "worksheets"
os.makedirs(dest_dir, exist_ok=True)

def extract_text(path):
    if path.lower().endswith((".jpg", ".jpeg", ".png")):
        return pytesseract.image_to_string(Image.open(path))
    elif path.lower().endswith(".pdf"):
        with pdfplumber.open(path) as pdf:
            first_page = pdf.pages[0]
            return first_page.extract_text() or "[PDF content unreadable]"
    else:
        with open(path, "r", errors="ignore") as f:
            return f.read()

def get_worksheet_name_and_label(content):
    prompt = f"""
Classify the following worksheet content into one of: Math, English, Biology, Economics, or Other.
Also, try to identify a short title or number (e.g., 9.2, "Darwin", or "Linear Equations") from the content.

Respond only with the label and worksheet name in this format:
label: <one word label>
name: <short title or number>

Content:
{content[:3000]}
"""
    response = model.generate_content(prompt)
    lines = response.text.strip().splitlines()

    label = "other"
    name = None

    for line in lines:
        if line.lower().startswith("label:"):
            label = line.split(":", 1)[1].strip().lower()
        elif line.lower().startswith("name:"):
            name = line.split(":", 1)[1].strip()

    return label, name

for filename in os.listdir(src_dir):
    fpath = os.path.join(src_dir, filename)
    if not os.path.isfile(fpath):
        continue

    try:
        content = extract_text(fpath)
        label, name = get_worksheet_name_and_label(content)

        if label not in ["math", "english", "biology", "economics"]:
            label = "other"

        out_dir = os.path.join(dest_dir, label)
        os.makedirs(out_dir, exist_ok=True)

        # Construct a safe new filename
        base_name = name or os.path.splitext(filename)[0]
        ext = os.path.splitext(filename)[1]
        clean_name = base_name.replace(" ", "_").replace("/", "_")[:50]
        new_filename = f"{clean_name}{ext}"

        target_path = os.path.join(out_dir, new_filename)
        counter = 1
        while os.path.exists(target_path):
            new_filename = f"{clean_name}_{counter}{ext}"
            target_path = os.path.join(out_dir, new_filename)
            counter += 1

        shutil.move(fpath, target_path)
        print(f"✅ Moved {filename} to worksheets/{label}/{new_filename}")

    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
