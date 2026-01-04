# app/models/schemas.py
from pydantic import BaseModel
from typing import Optional

class BridgeRequest(BaseModel):
    topic: str
    community: str = "General"

class BridgeResponse(BaseModel):
    topic: str
    community: str
    ai_guidance: str

# This schema will be used for our WebSocket JSON packets
class StreamPacket(BaseModel):
    type: str  # e.g., "content", "status", or "error"
    payload: str
    metadata: Optional[dict] = None