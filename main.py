# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.models.schemas import StreamPacket
from app.services.groq_client import get_ai_bridging_stream
import json
from fastapi import FastAPI, File, UploadFile
from app.services.ocr_engine import process_handwriting
from fastapi import HTTPException, status
from app.models.schemas import OCRResponse

app = FastAPI(title="AI-Powered Learning Bridge")

@app.websocket("/ws/bridge")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 1. Receive JSON from the user
            data = await websocket.receive_text()
            params = json.loads(data)
            
            topic = params.get("topic")
            community = params.get("community", "General")

            # 2. Send status via Structured JSON
            status_packet = StreamPacket(type="status", payload="Thinking...")
            await websocket.send_json(status_packet.model_dump())

            # 3. Stream AI chunks
            async for chunk in get_ai_bridging_stream(topic, community):
                content_packet = StreamPacket(type="content", payload=chunk)
                await websocket.send_json(content_packet.model_dump())
            
            # 4. Final status
            done_packet = StreamPacket(type="status", payload="Done.")
            await websocket.send_json(done_packet.model_dump())

    except WebSocketDisconnect:
        print("User closed the connection")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()


@app.post("/digitize-notes", response_model=OCRResponse)
async def digitize_notes(file: UploadFile = File(...)):
    # 1. VALIDATION: Check file type
    # We only want to allow images (jpg, png, jpeg)
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload a PNG or JPEG image."
        )

    # 2. VALIDATION: Check file size (e.g., limit to 5MB)
    MAX_SIZE = 5 * 1024 * 1024  # 5 Megabytes
    file_bytes = await file.read() # Read the bytes once
    
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large. Please upload an image smaller than 5MB."
        )

    # 3. Processing (Only if validation passes)
    text = await process_handwriting(file_bytes)
    
    # 4. Return the validated Pydantic model
    return OCRResponse(
        filename=file.filename,
        digitized_text=text,
        status="success",
        word_count=len(text.split())
    )

    # 1. Read the file
    content = await file.read()
    
    # 2. Extract text using our new local service
    text = await process_handwriting(content)
    
    # 3. Return structured JSON
    return {
        "filename": file.filename,
        "digitized_text": text,
        "status": "success",
        "note": "You can now copy this text or save it as a PDF."
    }