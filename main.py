import json
import asyncio
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# Import your custom Pydantic models
from app.models.schemas import OCRResponse, DownloadRequest

# Import your updated services
from app.services.ocr_engine import process_handwriting
from app.services.ocr_refiner import refine_ocr_text
from app.services.tutor_service import stream_tutor_response
from app.utils.doc_gen import create_docx, create_pdf

app = FastAPI(title="AI-Powered Learning Bridge")

# --- MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- WEBSOCKET TUTOR ENDPOINT ---
@app.websocket("/ws/bridge")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw_data = await websocket.receive_text()
            payload = json.loads(raw_data)
            
            user_message = payload.get("message")
            session_id = payload.get("session_id")
            topic = payload.get("topic")
            community = payload.get("community")

            async for text_chunk in stream_tutor_response(
                user_message, topic, community, session_id
            ):
                await websocket.send_text(json.dumps({
                    "type": "content",
                    "payload": text_chunk
                }))
                # Smooth pacing for readability
                await asyncio.sleep(0.02)

            await websocket.send_text(json.dumps({"type": "done"}))

    except WebSocketDisconnect:
        print(f"Session {session_id} disconnected.")
    except Exception as e:
        await websocket.send_text(json.dumps({"type": "error", "payload": str(e)}))

# --- UPDATED OCR & REFINEMENT ENDPOINT ---
@app.post("/digitize-notes")
async def digitize_notes(
    file: UploadFile = File(...),
    output_format: str = Form("json")
):
    # 1. VALIDATION: File type
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload a PNG or JPEG image."
        )

    # 2. VALIDATION: File size (5MB limit)
    MAX_SIZE = 5 * 1024 * 1024 
    file_bytes = await file.read()
    
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large. Please upload an image smaller than 5MB."
        )

    # 3. PROCESSING
    try:
        # A. Raw OCR Extraction (Updated to use Cloud-First with Fallback logic)
        # We pass file_bytes which is handled by your service's new Cloud logic
        raw_text = await process_handwriting(file_bytes)
        
        if not raw_text:
            raise ValueError("OCR engine returned empty text.")

        # B. LLM Refinement (Fixing spelling/OCR errors)
        refined_text = await refine_ocr_text(raw_text)
        
        # 4. EXPORT HANDLING
        if output_format == "pdf":
            file_path = create_pdf(refined_text, filename=file.filename)
            return FileResponse(
                file_path, 
                media_type="application/pdf", 
                filename=f"Digitized_{file.filename}.pdf"
            )
        
        elif output_format == "docx":
            file_path = create_docx(refined_text, filename=file.filename)
            return FileResponse(
                file_path, 
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                filename=f"Digitized_{file.filename}.docx"
            )

        # Default: Return JSON Preview
        return {
            "filename": file.filename,
            "raw_text": raw_text,
            "digitized_text": refined_text,
            "status": "success",
            "word_count": len(refined_text.split())
        }

    except Exception as e:
        # Log error for server-side debugging
        print(f"Digitization Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Refinement/OCR failed: {str(e)}"
        )

# --- DOWNLOAD ENDPOINT ---
@app.post("/download-notes")
async def download_notes(req: DownloadRequest):
    if req.format == "pdf":
        path = create_pdf(req.text)
        return FileResponse(path, media_type="application/pdf", filename="Notes.pdf")
    else:
        path = create_docx(req.text)
        return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument", filename="Notes.docx")