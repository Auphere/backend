"""
Client utilities to communicate with the auphere-agent microservice.
Handles REST calls to the agent API and SSE streaming to frontend.
"""

from typing import Dict, Any
import logging

import httpx

from app.config import settings
from app.utils.normalizers import normalize_places, normalize_plan

logger = logging.getLogger(__name__)


class GPTBackendClient:
    """Client for communicating with auphere-agent microservice."""
    
    def __init__(self):
        self.base_url = settings.gpt_backend_url.rstrip("/")
        # Increased timeout to 180 seconds to handle slow agent responses
        self.http_client = httpx.AsyncClient(base_url=self.base_url, timeout=180)

    async def send_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a message to the agent and get a response.
        
        Args:
            payload: Dict with keys:
                - message: The user message
                - user_id: User UUID
                - session_id: Session UUID
                - mode: Chat mode ("explore" or "plan")
                
        Returns:
            Dict with agent response including response_text, places, metadata
        """
        # Transform payload to match agent API schema
        agent_payload = {
            "user_id": payload.get("user_id"),
            "session_id": payload.get("session_id"),
            "query": payload.get("message"),  # Agent expects 'query' not 'message'
            "language": payload.get("language", "es"),
            "context": {
                "metadata": {
                    "chat_mode": payload.get("mode", "explore"),  # Pass mode to agent
                }
            }
        }
        
        logger.info(f"Sending message to agent: user_id={agent_payload['user_id']}, session_id={agent_payload['session_id']}")
        
        try:
            response = await self.http_client.post("/agent/query", json=agent_payload)
            response.raise_for_status()
            agent_response = response.json()
            
            # Normalize places using consistent normalizer
            places = normalize_places(agent_response.get("places", []))
            
            # Check if response contains a plan
            plan = None
            if agent_response.get("plan"):
                plan = normalize_plan(agent_response["plan"])
            
            return {
                "response": agent_response.get("response_text", ""),
                "session_id": payload.get("session_id"),
                "places": places,
                "plan": plan,
                "metadata": {
                    "intention": agent_response.get("intention"),
                    "confidence": agent_response.get("confidence"),
                    "model_used": agent_response.get("model_used"),
                    "processing_time_ms": agent_response.get("processing_time_ms"),
                }
            }
        except httpx.HTTPStatusError as exc:
            logger.error(f"Agent HTTP error: {exc.response.status_code} - {exc.response.text}")
            raise
        except Exception as exc:
            logger.error(f"Agent communication error: {exc}")
            raise

    async def stream_chat_sse(self, payload: Dict[str, Any]):
        """
        Handle chat streaming using Server-Sent Events (SSE).
        
        Calls the agent via REST and yields SSE-formatted events.
        
        `payload` must include message, session_id, user_id, and optionally mode.
        
        Yields:
            SSE-formatted strings with events: status, token, end, error
        """
        import asyncio
        
        import json
        
        try:
            # Send status to frontend
            status_data = {"content": "Conectando con el asistente..."}
            yield f"event: status\ndata: {json.dumps(status_data)}\n\n"
            
            # Prepare payload for agent
            agent_payload = {
                "user_id": payload.get("user_id"),
                "session_id": payload.get("session_id"),
                "query": payload.get("message"),
                "language": payload.get("language", "es"),
                "context": {
                    "metadata": {
                        "chat_mode": payload.get("mode", "explore"),
                    }
                }
            }
            
            logger.info(f"Calling agent: user_id={agent_payload['user_id']}, mode={agent_payload['context']['metadata']['chat_mode']}")
            
            status_data = {"content": "Analizando tu consulta..."}
            yield f"event: status\ndata: {json.dumps(status_data)}\n\n"
            
            # Call agent via REST (with 180s timeout)
            response = await self.http_client.post("/agent/query", json=agent_payload)
            response.raise_for_status()
            agent_response = response.json()
            
            response_text = agent_response.get("response_text", "")
            places = normalize_places(agent_response.get("places", []))
            
            # Check if response contains a plan
            plan = None
            if agent_response.get("plan"):
                plan = normalize_plan(agent_response["plan"])
            
            # Stream response text word by word for better UX
            if response_text:
                words = response_text.split()
                chunk_size = 3  # words per chunk
                
                for i in range(0, len(words), chunk_size):
                    chunk = " ".join(words[i:i+chunk_size])
                    if i + chunk_size < len(words):
                        chunk += " "
                    
                    token_data = {"content": chunk}
                    yield f"event: token\ndata: {json.dumps(token_data)}\n\n"
                    
                    # Small delay for streaming effect
                    await asyncio.sleep(0.05)
            
            # Send end message with complete response, places, and plan
            end_data = {
                "content": response_text,
                "places": places,
                "plan": plan,
                "metadata": {
                    "intention": agent_response.get("intention"),
                    "confidence": agent_response.get("confidence"),
                    "model_used": agent_response.get("model_used"),
                    "processing_time_ms": agent_response.get("processing_time_ms"),
                }
            }
            yield f"event: end\ndata: {json.dumps(end_data)}\n\n"
            
        except httpx.HTTPStatusError as exc:
            logger.error(f"Agent HTTP error: {exc.response.status_code}")
            error_data = {"content": f"Error del asistente: {exc.response.status_code}"}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
        except Exception as exc:
            logger.error(f"Agent communication error: {exc}")
            error_data = {"content": "No pudimos conectar con el asistente. Intenta de nuevo."}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"


    async def get_user_chats(self, user_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get all chats for a user from the agent."""
        try:
            response = await self.http_client.get(
                "/chats",
                params={"user_id": user_id, "limit": limit, "offset": offset}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(f"Agent HTTP error getting chats: {exc.response.status_code} - {exc.response.text}")
            raise
        except Exception as exc:
            logger.error(f"Agent communication error getting chats: {exc}")
            raise

    async def get_chat(self, chat_id: str) -> Dict[str, Any]:
        """Get a specific chat by ID from the agent."""
        try:
            response = await self.http_client.get(f"/chats/{chat_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(f"Agent HTTP error getting chat: {exc.response.status_code} - {exc.response.text}")
            raise
        except Exception as exc:
            logger.error(f"Agent communication error getting chat: {exc}")
            raise

    async def create_chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new chat in the agent."""
        try:
            response = await self.http_client.post("/chats", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(f"Agent HTTP error creating chat: {exc.response.status_code} - {exc.response.text}")
            raise
        except Exception as exc:
            logger.error(f"Agent communication error creating chat: {exc}")
            raise

    async def update_chat(self, chat_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update a chat in the agent."""
        try:
            response = await self.http_client.patch(f"/chats/{chat_id}", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(f"Agent HTTP error updating chat: {exc.response.status_code} - {exc.response.text}")
            raise
        except Exception as exc:
            logger.error(f"Agent communication error updating chat: {exc}")
            raise

    async def delete_chat(self, chat_id: str, user_id: str) -> None:
        """Delete a chat in the agent."""
        try:
            response = await self.http_client.delete(
                f"/chats/{chat_id}",
                params={"user_id": user_id}
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(f"Agent HTTP error deleting chat: {exc.response.status_code} - {exc.response.text}")
            raise
        except Exception as exc:
            logger.error(f"Agent communication error deleting chat: {exc}")
            raise

    async def get_chat_history(self, chat_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get full chat history (messages) from the agent."""
        try:
            response = await self.http_client.get(
                f"/chats/{chat_id}/history",
                params={"limit": limit},
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(f"Agent HTTP error getting chat history: {exc.response.status_code} - {exc.response.text}")
            raise
        except Exception as exc:
            logger.error(f"Agent communication error getting chat history: {exc}")
            raise


gpt_backend_client = GPTBackendClient()

