import os
import pytesseract
from PIL import Image

# Setup tesseract path if needed, on Windows it's usually:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Let's see if tesseract is installed
try:
    image_path = r'C:\Users\docto\.gemini\antigravity\brain\cdb2a7fc-422f-4c1f-901b-6f5409cea063\.tempmediaStorage\media_cdb2a7fc-422f-4c1f-901b-6f5409cea063_1777576112213.png'
    # Wait, the artifacts list says:
    # [ARTIFACT: media__1777576112213]
    # Path: file:///C:/Users/docto/.gemini/antigravity/brain/cdb2a7fc-422f-4c1f-901b-6f5409cea063/media__1777576112213.png
    
    img_path = r'C:\Users\docto\.gemini\antigravity\brain\cdb2a7fc-422f-4c1f-901b-6f5409cea063\media__1777576112213.png'
    if not os.path.exists(img_path):
        print(f"File not found: {img_path}")
        # Try the tempmediaStorage one
        img_path = r'C:\Users\docto\.gemini\antigravity\brain\cdb2a7fc-422f-4c1f-901b-6f5409cea063\.tempmediaStorage\media_cdb2a7fc-422f-4c1f-901b-6f5409cea063_1777576112213.png'
        
    print(f"Trying to read {img_path}")
    text = pytesseract.image_to_string(Image.open(img_path))
    print("Extracted Text:")
    print(text)
except Exception as e:
    print(f"Error: {e}")
