# app/services/ocr_engine.py
import easyocr
import numpy as np
from PIL import Image
import io

# Initialize the reader globally so it doesn't reload for every request
# This saves time and memory
reader = easyocr.Reader(['en'], gpu=False) # gpu=False since we installed the CPU version

async def process_handwriting(file_bytes: bytes):
    try:
        # 1. Open the image from the uploaded bytes
        image = Image.open(io.BytesIO(file_bytes))
        
        # 2. Convert to a format EasyOCR understands (numpy array)
        image_np = np.array(image)

        # 3. Read the text
        # paragraph=True helps group lines together into readable sentences
        results = reader.readtext(image_np, detail=0, paragraph=True)
        
        return " ".join(results)
    except Exception as e:
        return f"OCR Error: {str(e)}"