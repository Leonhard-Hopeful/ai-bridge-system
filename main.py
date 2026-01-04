# main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.models.schemas import StreamPacket
from app.services.groq_client import get_ai_bridging_stream
import json

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