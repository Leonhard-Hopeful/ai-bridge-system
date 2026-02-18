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
from app.services.expert_service import stream_expert_response
from app.utils.doc_gen import create_docx, create_pdf

app = FastAPI(title="AI-Powered Learning Bridge")

# --- MIDDLEWARE ---
# Necessary for the Vue frontend to communicate with this FastAPI backend
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
    
    # Initialize session variables immediately to prevent UnboundLocalError
    # during unexpected disconnections
    session_id = "initialization"
    
    try:
        while True:
            # Receive message from Vue frontend
            raw_data = await websocket.receive_text()
            payload = json.loads(raw_data)
            
            user_message = payload.get("message")
            session_id = payload.get("session_id", "anonymous")
            topic = payload.get("topic", "General")
            community = payload.get("community", "Cameroon")

            # Stream response from Groq LLM
            async for text_chunk in stream_tutor_response(
                user_message, topic, community, session_id
            ):
                await websocket.send_text(json.dumps({
                    "type": "content",
                    "payload": text_chunk
                }))
                # Smooth pacing prevents the UI from flickering 
                # during high-speed text generation
                await asyncio.sleep(0.02)

            # Signal that the AI has finished its current turn
            await websocket.send_text(json.dumps({"type": "done"}))

    except WebSocketDisconnect:
        # Handles Code 1001 (browser refresh) or 1000 (tab close)
        print(f"INFO: Bridge Session {session_id} disconnected.")
    except Exception as e:
        # Log unexpected server-side errors
        print(f"ERROR: WebSocket crash in session {session_id}: {str(e)}")
        try:
            # Attempt to notify frontend if the connection is still alive
            await websocket.send_text(json.dumps({
                "type": "error", 
                "payload": "The learning bridge encountered a temporary glitch."
            }))
        except:
            pass

# --- UPDATED OCR & REFINEMENT ENDPOINT ---
@app.post("/digitize-notes")
async def digitize_notes(
    file: UploadFile = File(...),
    output_format: str = Form("json")
):
    # 1. VALIDATION: Check file extension
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload a PNG or JPEG image."
        )

    # 2. VALIDATION: Enforce a 5MB limit for efficiency in low-bandwidth areas
    MAX_SIZE = 5 * 1024 * 1024 
    file_bytes = await file.read()
    
    if len(file_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File is too large. Keep images under 5MB for faster processing."
        )

    try:
        # A. Raw OCR Extraction using the engine service
        raw_text = await process_handwriting(file_bytes)
        
        if not raw_text:
            raise ValueError("OCR engine could not detect any text in the image.")

        # B. AI Refinement (handles Cameroon-specific terms and context)
        refined_text = await refine_ocr_text(raw_text)
        
        # 3. EXPORT HANDLING: Convert text to requested document format
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

        # Default JSON response for instant preview in the app
        return {
            "filename": file.filename,
            "raw_text": raw_text,
            "digitized_text": refined_text,
            "status": "success",
            "word_count": len(refined_text.split())
        }

    except Exception as e:
        print(f"Digitization Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OCR Refinement failed: {str(e)}"
        )

# --- DOWNLOAD ENDPOINT ---
@app.post("/download-notes")
async def download_notes(req: DownloadRequest):
    """Allows users to download their previous chat history or notes as docs."""
    try:
        if req.format == "pdf":
            path = create_pdf(req.text)
            return FileResponse(path, media_type="application/pdf", filename="Bridge_Notes.pdf")
        else:
            path = create_docx(req.text)
            return FileResponse(
                path, 
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                filename="Bridge_Notes.docx"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- EXPERT AGENT ENDPOINT ---
@app.websocket("/ws/expert")
async def expert_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw_data = await websocket.receive_text()
            payload = json.loads(raw_data)
            
            user_message = payload.get("message")
            subject = payload.get("subject")

            # Validate input
            if not user_message:
                continue

            # Stream chunks from your RAG service
            async for text_chunk in stream_expert_response(user_message, subject):
                # We send as "content" type for the frontend to append
                await websocket.send_text(json.dumps({
                    "type": "content",
                    "payload": text_chunk
                }))
            
            # Critical: Signal the frontend that the stream is finished
            await websocket.send_text(json.dumps({"type": "done"}))
            
    except WebSocketDisconnect:
        print(f"Expert session disconnected for subject: {subject}")
    except Exception as e:
        print(f"Server Error: {e}")
        await websocket.send_text(json.dumps({
            "type": "content", 
            "payload": "\n\n**Error:** The bridge connection was interrupted."
        }))