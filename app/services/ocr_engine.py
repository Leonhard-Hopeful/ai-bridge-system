import easyocr
import numpy as np
from PIL import Image
import io

# Initialize the reader (this will download the model the first time you run it)
# We include 'en' for English; you can add 'fr' for French if needed!
reader = easyocr.Reader(['en'])

async def process_handwriting(file_bytes: bytes):
    """
    Converts image bytes into structured text.
    """
    # 1. Convert bytes to an image that EasyOCR can read
    image = Image.open(io.BytesIO(file_bytes))
    image_np = np.array(image)

    # 2. Perform OCR
    results = reader.readtext(image_np, detail=0) # detail=0 returns just the text
    
    # 3. Join the list of strings into one paragraph
    full_text = " ".join(results)
    
    return full_text