import os
from transformers import pipeline, AutoTokenizer
from PyPDF2 import PdfReader
import docx
from PIL import Image

toxic_model = pipeline("text-classification", model="unitary/toxic-bert")
violence_model = pipeline("text-classification", model="KoalaAI/Text-Moderation")
sexual_model = pipeline("text-classification", model="Vrandan/Comment-Moderation")

image_morderator=pipeline("image-classification",model="falconsai/nsfw_image_detection")

tokenizer = AutoTokenizer.from_pretrained("unitary/toxic-bert")

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    try:
        if ext == ".txt":
            with open(file_path, "r",errors="ignore") as f:
                text = f.read()
        
        if ext == ".pdf":
            pdf = PdfReader(file_path)
            text = ""
            for page in pdf.pages:
                text += page.extract_text()

        if ext == ".docx":
            doc= docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"

    except Exception as e:
        print(f"Could not extract text from {file_path}: {e}")
    return text

def chunk_text(text, tokenizer, max_tokens=512):
    """
    Encode text with tokenizer, truncate each chunk to max_tokens,
    and decode back to text to avoid pipeline token overflow.
    """
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + 200]  # approx safe number of words
        chunk_text = " ".join(chunk_words)
        # Encode & truncate to MAX_TOKENS
        encoded = tokenizer(chunk_text, truncation=True, max_length=512, return_tensors="pt")
        decoded = tokenizer.decode(encoded["input_ids"][0], skip_special_tokens=True)
        chunks.append(decoded)
        i += 200
    return chunks

def scan_files(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    violations=set()

    if ext in [".pdf",".txt",".docx"]:
        text = extract_text(file_path)
        if text.strip():
            chunks = chunk_text(text, tokenizer)
            label_to_category = {
                "S": "Sexual",
                "H": "Hate",
                "V": "Violence",
                "HR": "Harassment",
                "SH": "Self-Harm",
                "S3": "Sexual/Minors",
                "H2": "Hate/Threat",
                "V2": "Violence/Graphic",
                "OK": "Safe Content"
            }
            try:
                for chunk in chunks:
                    for res in toxic_model(chunk):
                        if res['label'].lower() != "neutral" and res['score'] > 0.7:
                            violations.add(res['label'])
                    for res in violence_model(chunk):
                        if res['label'].lower() != "ok" and res['score'] > 0.3:
                            violations.add(label_to_category[res['label']])
                    
                    for res in sexual_model(chunk):
                        if res['label'].lower() != "ok" and res['score'] > 0.3:
                            violations.add(label_to_category[res['label']])
            except Exception as e:
                print(f"Error scanning text: {e}")
    
    elif ext in [".jpg",".jpeg",".png",".gif",".bmp"]:
        try:
            image = Image.open(file_path)
            result = image_morderator(image)
            flagged = [r for r in result if r['label'].lower() != "normal" and r['score'] > 0.65]
            if flagged:
                for r in flagged:
                    violations.add(r['label'])
        except Exception as e:
            print(f"Could not open image {file_path}: {e}")

    elif ext in [".mp4",".mov",".mkv",".avi"]:
        #TODO
        pass
    
    if violations:
        return{"status": "Danger","voilations": list(violations)}
    else :
        return{"status": "safe","voilations": []}
    
if __name__ == "__main__":
    result = scan_files("slim shady.txt")
    print(result)