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
    image = auto_rotate_image(image)
    image = preprocess_image_for_ocr(image)
    return pytesseract.image_to_string(image)
    elif path.lower().endswith(".pdf"):
        try:
            with pdfplumber.open(path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as e:
            print(f"❌ Failed to extract PDF text: {e}")
            return ""
    else:
        with open(path, "r", errors="ignore") as f:
            return f.read()

def auto_rotate_image(image):
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
Classify the following worksheet content into one of: Math, English, Biology, Economics, Spanish or Other.
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
def get_worksheet_answers(content):
    prompt = f"""Format the provided text of a worksheet as a centered, printable 8.5x11 filled out worksheet, styled to resemble a clean, professional worksheet from Google Docs or Microsoft Word, but in HTML format. Answer all questions completely and accurately, but do not modify any of the original question text. The layout should be easy to read and SIMILAR TO THE ORIGINAL, with clear spacing and structure. Differentiate the answers using a distinct color (e.g., red or blue), and ensure each question and its corresponding answer are clearly visible. Include all necessary formatting using inline or embedded CSS (style should be VERY similar to the original). Return only pure, valid HTML—no comments, notes, or explanations. Please note that the content is OCR generated, so there may be some spelling inaccuracies. Fix those in your HTML. The content is:

{content}"""

    response = model.generate_content(prompt)
    return response

def preprocess_image_for_ocr(pil_image):
    # Convert PIL → OpenCV
    image = np.array(pil_image.convert("RGB"))
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Increase contrast and threshold
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Remove noise
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Convert back to PIL
    return Image.fromarray(cleaned)


    
for filename in os.listdir(src_dir):
    fpath = os.path.join(src_dir, filename)
    if not os.path.isfile(fpath):
        continue

    try:
        content = extract_text(fpath)
        label, name = get_worksheet_name_and_label(content)
        answers = get_worksheet_answers(content)


        if label not in ["math", "english", "biology", "economics", "spanish"]:
            label = "other"

        out_dir = os.path.join(dest_dir, label)
        os.makedirs(out_dir, exist_ok=True)

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
        html_filename = os.path.splitext(new_filename)[0] + ".html"
        html_path = os.path.join(out_dir, html_filename)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(answers.text)

        shutil.move(fpath, target_path)
        print(f"✅ Moved {filename} to worksheets/{label}/{new_filename}")

    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
try:
    shutil.rmtree(src_dir)
    print(f"🗑️ Deleted '{src_dir}' folder after processing.")
except Exception as e:
    print(f"⚠️ Could not delete '{src_dir}': {e}")