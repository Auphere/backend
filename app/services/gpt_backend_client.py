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

    async def aclose(self) -> None:
        """Close underlying HTTP client (for app shutdown)."""
        await self.http_client.aclose()

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
        
        Connects to agent's streaming endpoint and forwards events to frontend.
        
        `payload` must include message, session_id, user_id, and optionally mode.
        
        Yields:
            SSE-formatted strings with events: status, thought, action, observation, token, end, error
        """
        import asyncio
        import json
        
        try:
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
            
            logger.info(f"Streaming from agent: user_id={agent_payload['user_id']}, mode={agent_payload['context']['metadata']['chat_mode']}")
            
            # Stream from agent's streaming endpoint using the shared AsyncClient
            async with self.http_client.stream(
                "POST",
                "/agent/query/stream",
                json=agent_payload,
            ) as response:
                    response.raise_for_status()
                    
                    # Forward SSE events from agent to frontend
                    current_event = None
                    
                    async for line in response.aiter_lines():
                        if not line:
                            yield "\n"
                            continue
                        
                        # Track event type
                        if line.startswith("event:"):
                            current_event = line.split(":", 1)[1].strip()
                            yield f"{line}\n"
                            continue
                        
                        # Process data lines
                        if line.startswith("data:"):
                            # Check if this is an 'end' event with places/plan to normalize
                            if current_event == "end":
                                try:
                                    data_json = line[5:].strip()  # Remove "data:" prefix
                                    data = json.loads(data_json)
                                    
                                    # Normalize places
                                    if data.get("places"):
                                        logger.info(f"Before normalize: {len(data['places'])} places")
                                        normalized_places = normalize_places(data["places"])
                                        logger.info(f"After normalize: {len(normalized_places)} places")
                                        data["places"] = normalized_places
                                    
                                    # Normalize plan
                                    if data.get("plan"):
                                        data["plan"] = normalize_plan(data["plan"])
                                    
                                    # Re-emit normalized data
                                    logger.info(f"Sending end event with {len(data.get('places', []))} places")
                                    yield f"data: {json.dumps(data)}\n"
                                except Exception as e:
                                    logger.error(f"Error normalizing end event: {e}")
                                    yield f"{line}\n"
                            else:
                                # Forward other data as-is
                                yield f"{line}\n"
                            
                            # Reset event after processing data
                            current_event = None
                            continue
                        
                        # Forward other lines as-is
                        yield f"{line}\n"
            
        except httpx.HTTPStatusError as exc:
            logger.error(f"Agent HTTP error: {exc.response.status_code}")
            error_data = {"content": f"Error del asistente: {exc.response.status_code}"}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
        except Exception as exc:
            logger.error(f"Agent communication error: {exc}")
            error_data = {"content": "No pudimos conectar con el asistente. Intenta de nuevo."}
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"

    async def edit_plan(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 6: Ask the agent to compute an edited/replanned plan based on a ground-truth plan.

        Expects:
        - user_id
        - plan_id
        - plan (current plan payload)
        - edit (operation/instruction/stop_number/constraints)
        """
        try:
            response = await self.http_client.post("/agent/plan/edit", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Agent plan-edit HTTP error: {exc.response.status_code} - {exc.response.text}"
            )
            raise
        except Exception as exc:
            logger.error(f"Agent plan-edit communication error: {exc}")
            raise

    async def upsert_plan_vector(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Index/update a plan in the agent's vector DB (Qdrant). Best-effort."""
        response = await self.http_client.post("/agent/vectors/plans/upsert", json=payload)
        response.raise_for_status()
        return response.json()


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

