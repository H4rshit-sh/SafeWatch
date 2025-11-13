import os
from transformers import pipeline, AutoTokenizer, CLIPProcessor, CLIPModel
from PyPDF2 import PdfReader
import docx
from PIL import Image
import torch
import warnings
warnings.filterwarnings("ignore", "Possibly corrupt EXIF data.")

text_morderator = pipeline( model="facebook/bart-large-mnli")
image_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
image_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")


tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-mnli")

VIOLATION_LABELS = [
    "violence",
    "Fight",
    "gore",
    "blood",
    "weapon",
    "nudity",
    "sexual",
    "hate speech",
    "hate symbol",
    "threat",
    "insult",
    "self-harm",
    "suicide",
    "drug use",      
    "promoting illegal acts", 
    "severe insult",
    "disturbing content"
]
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
    threshold = 0.6
    threshold_img = 0.99
    if ext in [".pdf",".txt",".docx"]:
        text = extract_text(file_path)
        if text.strip():
            chunks = chunk_text(text, tokenizer)
            
            try:
                for chunk in chunks:
                    result = text_morderator(
                        chunk,
                        candidate_labels=VIOLATION_LABELS,
                        multi_label=True
                    )
                    for i, label in enumerate(result['labels']):
                        if result['scores'][i] > threshold:
                            violations.add(label)
            except Exception as e:
                print(f"Error scanning text: {e}")
    
    elif ext in [".jpg",".jpeg",".png",".gif",".bmp"]:
        try:
            image = Image.open(file_path).convert("RGB")

            inputs = image_processor(
                text=VIOLATION_LABELS, 
                images=image, 
                return_tensors="pt", 
                padding=True
            )

            with torch.no_grad(): # Disable gradient calculations for inference
                outputs = image_model(**inputs)
            
            logits_per_image = outputs.logits_per_image # Raw similarity scores
            probs = logits_per_image.softmax(dim=1).cpu().squeeze() # Apply sigmoid, move to CPU, make 1D
            if probs.dim() == 0: #Handle case for single label result
                if probs.item() > threshold:
                     violations.add(VIOLATION_LABELS[0])
            else:
                for i, label in enumerate(VIOLATION_LABELS):
                    score = probs[i].item()
                    if score > threshold:
                        violations.add(label) 
        except Exception as e:
            print(f"Could not open image {file_path}: {e}")

    elif ext in [".mp4",".mov",".mkv",".avi"]:
        #TODO
        pass
    
    if violations:
        return{"status": "Danger","violations": list(violations)}
    else :
        return{"status": "safe","violations": []}
