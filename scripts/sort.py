import os
import shutil
import google.generativeai as genai
from PIL import Image
import pytesseract
import pdfplumber

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-lite")

src_dir = "incoming"
dest_dir = "worksheets"
os.makedirs(dest_dir, exist_ok=True)

def extract_text(path):
    if path.lower().endswith((".jpg", ".png", ".jpeg")):
        image = Image.open(path)
        image = auto_rotate_image(image)  # 👈 rotation fix
        return pytesseract.image_to_string(image)
    elif path.lower().endswith(".pdf"):
        return "[PDF content skipped]"
    else:
        with open(path, "r", errors="ignore") as f:
            return f.read()

def auto_rotate_image(image):
    # Try 0°, 90°, 180°, 270° and pick the one with the most words
    rotations = [0, 90, 180, 270]
    best_text = ""
    best_image = image

    for angle in rotations:
        rotated = image.rotate(angle, expand=True)
        text = pytesseract.image_to_string(rotated)
        if len(text.split()) > len(best_text.split()):
            best_text = text
            best_image = rotated

    return best_image

def get_worksheet_name_and_label(content):
    prompt = f"""
Classify the following worksheet content into one of: Math, English, Biology, Economics, or Other.
Also, try to identify a short title or number (e.g., 9.2) from the content.

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
