# # app/services/ocr_engine.py
# import easyocr
# import numpy as np
# from PIL import Image
# import io

# # Initialize the reader globally so it doesn't reload for every request
# # This saves time and memory
# reader = easyocr.Reader(['en'], gpu=False) # gpu=False since we installed the CPU version

# async def process_handwriting(file_bytes: bytes):
#     try:
#         # 1. Open the image from the uploaded bytes
#         image = Image.open(io.BytesIO(file_bytes))
        
#         # 2. Convert to a format EasyOCR understands (numpy array)
#         image_np = np.array(image)

#         # 3. Read the text
#         # paragraph=True helps group lines together into readable sentences
#         results = reader.readtext(image_np, detail=0, paragraph=True)
        
#         return " ".join(results)
#     except Exception as e:
#         return f"OCR Error: {str(e)}"
# app/services/ocr_engine.py
import easyocr
import numpy as np
from PIL import Image
import io
import os
import requests
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Initialize local fallback reader
reader = easyocr.Reader(['en'], gpu=False)

# Hugging Face Config
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
# We use Nougat-small for better document/note structure, or TrOCR for handwriting
HF_API_URL = "https://api-inference.huggingface.co/models/facebook/nougat-small"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

async def process_handwriting(file_bytes: bytes):
    """
    Tries Cloud OCR first, falls back to local EasyOCR if Cloud fails.
    """
    # --- TRY CLOUD OCR (Hugging Face) ---
    if HF_TOKEN:
        try:
            # We use a thread to keep the request from blocking the async loop
            response = await asyncio.to_thread(
                requests.post, HF_API_URL, headers=headers, data=file_bytes, timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                # Handle different return formats from different HF models
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "")
                elif isinstance(result, dict):
                    return result.get("generated_text", "")
        except Exception as e:
            print(f"Cloud OCR failed, switching to fallback: {e}")

    # --- FALLBACK: LOCAL EASYOCR ---
    try:
        image = Image.open(io.BytesIO(file_bytes))
        image_np = np.array(image)
        results = reader.readtext(image_np, detail=0, paragraph=True)
        return " ".join(results)
    except Exception as e:
        return f"All OCR methods failed: {str(e)}"