import json
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.dependencies import get_current_user, verify_user_token
from app.services.gpt_backend_client import gpt_backend_client

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    mode: Optional[str] = "explore"  # "explore" or "plan"


@router.post("/message")
async def chat_message(
    payload: ChatMessage,
    current_user: dict = Depends(get_current_user),
):
    try:
        body = payload.dict()
        body["session_id"] = body.get("session_id") or str(uuid.uuid4())
        body["user_id"] = current_user["id"]
        body["mode"] = body.get("mode", "explore")
        response = await gpt_backend_client.send_message(body)
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/stream")
async def chat_stream(
    payload: ChatMessage,
    current_user: dict = Depends(get_current_user),
):
    """
    Stream chat responses using Server-Sent Events (SSE).
    
    Returns a streaming response with events:
    - status: Status updates during processing
    - token: Streamed text chunks
    - end: Final response with complete data
    - error: Error message if something fails
    """
    try:
        data = payload.dict()
        data["session_id"] = data.get("session_id") or str(uuid.uuid4())
        data["user_id"] = current_user["id"]
        data.setdefault("mode", "explore")
        
        # Return SSE stream
        return StreamingResponse(
            gpt_backend_client.stream_chat_sse(data),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# Chat management endpoints (proxy to agent)
@router.get("/list")
async def get_user_chats(
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    """Get all chats for the current user."""
    try:
        response = await gpt_backend_client.get_user_chats(
            user_id=current_user["id"],
            limit=limit,
            offset=offset
        )
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/info/{chat_id}")
async def get_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a specific chat by ID."""
    try:
        response = await gpt_backend_client.get_chat(chat_id)
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/create")
async def create_chat(
    payload: dict,
    current_user: dict = Depends(get_current_user),
):
    """Create a new chat."""
    try:
        payload["user_id"] = current_user["id"]
        response = await gpt_backend_client.create_chat(payload)
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/{chat_id}")
async def update_chat(
    chat_id: str,
    payload: dict,
    current_user: dict = Depends(get_current_user),
):
    """Update a chat (e.g., rename title)."""
    try:
        response = await gpt_backend_client.update_chat(chat_id, payload)
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a chat."""
    try:
        await gpt_backend_client.delete_chat(chat_id, current_user["id"])
        return {"status": "deleted"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/{chat_id}/history")
async def get_chat_history(
    chat_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """Get full chat history (messages) for a chat."""
    try:
        response = await gpt_backend_client.get_chat_history(chat_id, limit=limit)
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

