"""
Cliente para comunicación con Langflow.
Reemplaza temporalmente a auphere-agent para el MVP.

Maneja:
- Ejecución de flows con streaming SSE
- Mapeo de eventos Langflow → eventos Auphere
- Session ID para persistencia de historial
"""

import json
import logging
from typing import Dict, Any, AsyncGenerator, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LangflowClient:
    """
    Cliente para comunicación con Langflow.
    
    Langflow expone flows como API endpoints que pueden ejecutarse
    con o sin streaming.
    
    Eventos de Langflow:
        - add_message: Mensaje añadido al chat
        - token: Token de texto generado
        - end: Fin de la respuesta
        
    Eventos que enviamos al frontend (compatibles con el formato actual):
        - status: Estado del procesamiento
        - token: Chunk de texto
        - end: Respuesta final con places y metadata
        - error: Error
    """
    
    def __init__(self):
        self.base_url = settings.langflow_url.rstrip("/")
        self.api_key = settings.langflow_api_key
        self.flow_ids = {
            "recommend": settings.langflow_recommend_flow_id,
            "explore": settings.langflow_recommend_flow_id,  # Alias
            "chitchat": settings.langflow_chitchat_flow_id,
        }
        # Timeout largo para respuestas de LLM
        self.http_client = httpx.AsyncClient(timeout=180)
    
    async def aclose(self) -> None:
        """Cierra el cliente HTTP."""
        await self.http_client.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Headers comunes para las peticiones."""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers
    
    async def send_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía un mensaje a Langflow sin streaming.
        
        Args:
            payload: Dict con:
                - message: Mensaje del usuario
                - user_id: ID del usuario
                - session_id: ID de sesión para historial
                - mode: Modo de chat ("recommend", "chitchat", etc.)
        
        Returns:
            Dict con la respuesta del flow
        """
        mode = payload.get("mode", "recommend")
        flow_id = self.flow_ids.get(mode) or self.flow_ids.get("recommend")
        
        if not flow_id:
            raise ValueError(f"Flow ID no configurado para modo: {mode}")
        
        session_id = payload.get("session_id", "")
        message = payload.get("message", "")
        
        url = f"{self.base_url}/api/v1/run/{flow_id}"
        
        langflow_payload = {
            "input_value": message,
            "output_type": "chat",
            "input_type": "chat",
            "session_id": session_id,
        }
        
        logger.info(f"Sending to Langflow: flow={flow_id}, session={session_id}")
        
        try:
            response = await self.http_client.post(
                url,
                headers=self._get_headers(),
                json=langflow_payload,
            )
            response.raise_for_status()
            data = response.json()
            
            # Extraer respuesta del formato de Langflow
            result = self._extract_response(data)
            result["session_id"] = session_id
            
            return result
            
        except httpx.HTTPStatusError as exc:
            logger.error(f"Langflow HTTP error: {exc.response.status_code} - {exc.response.text}")
            raise
        except Exception as exc:
            logger.error(f"Langflow error: {exc}")
            raise
    
    async def stream_chat_sse(self, payload: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream de chat usando SSE desde Langflow.
        
        Mapea los eventos de Langflow al formato esperado por el frontend de Auphere.
        
        Args:
            payload: Dict con message, user_id, session_id, mode
            
        Yields:
            Strings SSE en formato: "event: {type}\ndata: {json}\n\n"
        """
        mode = payload.get("mode", "recommend")
        flow_id = self.flow_ids.get(mode) or self.flow_ids.get("recommend")
        
        if not flow_id:
            yield self._format_sse_event("error", {"content": f"Flow no configurado para modo: {mode}"})
            return
        
        session_id = payload.get("session_id", "")
        message = payload.get("message", "")
        
        url = f"{self.base_url}/api/v1/run/{flow_id}?stream=true"
        
        langflow_payload = {
            "input_value": message,
            "output_type": "chat",
            "input_type": "chat",
            "session_id": session_id,
        }
        
        logger.info(f"Streaming from Langflow: flow={flow_id}, session={session_id}, mode={mode}")
        
        # Emitir evento de status inicial
        yield self._format_sse_event("status", {"content": "🔍 Procesando tu consulta..."})
        
        try:
            headers = self._get_headers()
            headers["Accept"] = "text/event-stream"
            
            accumulated_text = ""
            places = []
            final_data = None
            
            async with self.http_client.stream(
                "POST",
                url,
                headers=headers,
                json=langflow_payload,
            ) as response:
                response.raise_for_status()
                
                buffer = ""
                current_event_type = "message"
                
                async for chunk in response.aiter_text():
                    buffer += chunk
                    
                    # Procesar eventos SSE completos (separados por \n\n)
                    while "\n\n" in buffer:
                        event_block, buffer = buffer.split("\n\n", 1)
                        
                        # Parsear el bloque de evento
                        event_type = "message"
                        data_str = ""
                        
                        for line in event_block.split("\n"):
                            line = line.strip()
                            if line.startswith("event:"):
                                event_type = line[6:].strip()
                            elif line.startswith("data:"):
                                data_str += line[5:].strip()
                        
                        if not data_str:
                            continue
                        
                        try:
                            event_data = json.loads(data_str)
                            
                            # Langflow envía eventos en formato: {"event": "...", "data": {...}}
                            inner_event = event_data.get("event", event_type)
                            inner_data = event_data.get("data", event_data)
                            
                            logger.debug(f"Langflow event: {inner_event}")
                            
                            # Mapear eventos de Langflow a formato Auphere
                            if inner_event == "token":
                                # Token de texto (streaming del LLM)
                                token_chunk = inner_data.get("chunk", "") if isinstance(inner_data, dict) else str(inner_data)
                                if token_chunk:
                                    accumulated_text += token_chunk
                                    yield self._format_sse_event("token", {"content": token_chunk})
                            
                            elif inner_event == "add_message":
                                # ✅ PRINCIPAL: Mensaje completo del asistente
                                # Este evento contiene la respuesta final
                                sender = inner_data.get("sender", "")
                                
                                # Solo procesar mensajes del asistente (Machine/AI)
                                if sender in ("Machine", "AI", "assistant"):
                                    msg_text = inner_data.get("text", "")
                                    if msg_text:
                                        # Intentar extraer places del texto (marcador oculto)
                                        clean_text, extracted_places = self._extract_places_from_text(msg_text)
                                        if extracted_places:
                                            places = self._normalize_places(extracted_places)
                                        accumulated_text = clean_text
                                        
                                        logger.info(f"Extracted {len(places)} places from add_message text")
                                    
                                    # ✅ STRUCTURED OUTPUT: Buscar places en data del mensaje
                                    # El Structured Output añade campos extraídos en el data
                                    msg_data = inner_data.get("data", {})
                                    if isinstance(msg_data, dict):
                                        # Structured Output puede devolver places directamente
                                        if msg_data.get("places") and not places:
                                            places = self._normalize_places(msg_data.get("places", []))
                                            logger.info(f"Extracted {len(places)} places from Structured Output data")
                                        
                                        # También puede venir como response_text + places
                                        if msg_data.get("response_text") and not accumulated_text:
                                            accumulated_text = msg_data.get("response_text", "")
                            
                            elif inner_event == "end":
                                # Fin de la respuesta
                                final_data = inner_data
                                
                                # Intentar extraer texto y places del evento end si no tenemos
                                if isinstance(inner_data, dict):
                                    result = inner_data.get("result", {})
                                    if isinstance(result, dict):
                                        outputs = result.get("outputs", [])
                                        if outputs and isinstance(outputs, list):
                                            for output in outputs:
                                                inner_outputs = output.get("outputs", [])
                                                for inner_out in inner_outputs:
                                                    results = inner_out.get("results", {})
                                                    
                                                    # ✅ STRUCTURED OUTPUT: Buscar en structured_output
                                                    structured = results.get("structured_output", {})
                                                    if isinstance(structured, dict):
                                                        if structured.get("places") and not places:
                                                            places = self._normalize_places(structured.get("places", []))
                                                            logger.info(f"Extracted {len(places)} places from end.structured_output")
                                                        if structured.get("response_text") and not accumulated_text:
                                                            accumulated_text = structured.get("response_text", "")
                                                    
                                                    # También buscar en data (formato alternativo)
                                                    data_obj = results.get("data", {})
                                                    if isinstance(data_obj, dict):
                                                        if data_obj.get("places") and not places:
                                                            places = self._normalize_places(data_obj.get("places", []))
                                                        if data_obj.get("response_text") and not accumulated_text:
                                                            accumulated_text = data_obj.get("response_text", "")
                                                    
                                                    # Fallback: mensaje tradicional
                                                    message = results.get("message", {})
                                                    if isinstance(message, dict):
                                                        msg_text = message.get("text", "")
                                                        if msg_text and not accumulated_text:
                                                            clean_text, extracted_places = self._extract_places_from_text(msg_text)
                                                            if extracted_places and not places:
                                                                places = self._normalize_places(extracted_places)
                                                            accumulated_text = clean_text
                                                        
                                                        # Buscar places en message.data
                                                        msg_data = message.get("data", {})
                                                        if isinstance(msg_data, dict) and msg_data.get("places") and not places:
                                                            places = self._normalize_places(msg_data.get("places", []))
                            
                            elif inner_event == "error":
                                error_msg = inner_data.get("message", "Error desconocido") if isinstance(inner_data, dict) else str(inner_data)
                                yield self._format_sse_event("error", {"content": error_msg})
                                return
                                    
                        except json.JSONDecodeError as e:
                            logger.debug(f"JSON decode error: {e}, data: {data_str[:100]}")
                            pass
            
            # Emitir evento end con la respuesta completa
            end_content = accumulated_text
            if not end_content and final_data:
                if isinstance(final_data, dict):
                    end_content = final_data.get("text", "") or final_data.get("message", {}).get("text", "")
                else:
                    end_content = str(final_data)
            
            end_data = {
                "content": end_content,
                "places": places,
                "plan": None,  # No soportamos plan en MVP
                "metadata": {
                    "session_id": session_id,
                    "mode": mode,
                    "flow_id": flow_id,
                }
            }
            
            logger.info(f"Sending end event with {len(places)} places")
            yield self._format_sse_event("end", end_data)
            
        except httpx.HTTPStatusError as exc:
            logger.error(f"Langflow HTTP error: {exc.response.status_code}")
            yield self._format_sse_event("error", {
                "content": f"Error del servicio: {exc.response.status_code}"
            })
        except Exception as exc:
            logger.error(f"Langflow streaming error: {exc}")
            yield self._format_sse_event("error", {
                "content": "No pudimos conectar con el asistente. Intenta de nuevo."
            })
    
    def _format_sse_event(self, event_type: str, data: Dict[str, Any]) -> str:
        """Formatea un evento SSE."""
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    
    def _extract_places_from_text(self, text: str) -> tuple[str, list]:
        """
        Extrae los places embebidos en el texto y retorna el texto limpio.
        
        El componente GooglePlacesSearch añade los places en formato:
        <!-- AUPHERE_PLACES:{json}:END_AUPHERE_PLACES -->
        
        Returns:
            tuple: (texto_limpio, lista_de_places)
        """
        import re
        
        places = []
        clean_text = text
        
        # Buscar el marcador de places
        pattern = r'<!-- AUPHERE_PLACES:(.*?):END_AUPHERE_PLACES -->'
        match = re.search(pattern, text, re.DOTALL)
        
        if match:
            try:
                places_json = match.group(1)
                places = json.loads(places_json)
                # Remover el marcador del texto
                clean_text = re.sub(pattern, '', text, flags=re.DOTALL).strip()
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing places JSON from text: {e}")
        
        return clean_text, places
    
    def _normalize_places(self, places: list) -> list:
        """
        Normaliza los places al formato esperado por el frontend.
        
        Frontend espera:
        - id, name, category, rating, reviewCount, address, images[], 
          priceLevel, location{lat,lon,lng}, openNow, website
        """
        if not places or not isinstance(places, list):
            return []
        
        normalized = []
        for place in places:
            if not isinstance(place, dict):
                continue
            
            # Normalizar location
            location = None
            if place.get("location"):
                loc = place["location"]
                if isinstance(loc, dict):
                    lat = loc.get("lat") or loc.get("latitude")
                    lng = loc.get("lng") or loc.get("lon") or loc.get("longitude")
                    if lat and lng:
                        location = {"lat": lat, "lon": lng, "lng": lng}
            elif place.get("latitude") and place.get("longitude"):
                location = {
                    "lat": place["latitude"],
                    "lon": place["longitude"],
                    "lng": place["longitude"],
                }
            
            # Normalizar images
            images = place.get("images", [])
            if not images and place.get("photo_url"):
                images = [place["photo_url"]]
            if not images and place.get("primary_photo_url"):
                images = [place["primary_photo_url"]]
            
            # Asegurar que images es una lista
            if isinstance(images, str):
                images = [images]
            
            # Normalizar category
            category = place.get("category", "other")
            if not category or category == "other":
                # Intentar inferir de type o types
                place_type = place.get("type", "")
                if "bar" in place_type.lower():
                    category = "bar"
                elif "restaurant" in place_type.lower():
                    category = "restaurant"
                elif "cafe" in place_type.lower() or "coffee" in place_type.lower():
                    category = "cafe"
                elif "club" in place_type.lower():
                    category = "club"
            
            normalized_place = {
                "id": place.get("id", place.get("place_id", "")),
                "place_id": place.get("place_id", place.get("id", "")),
                "name": place.get("name", "Sin nombre"),
                "category": category,
                "description": place.get("description", ""),
                "rating": place.get("rating"),
                "reviewCount": place.get("reviewCount", place.get("rating_count", 0)),
                "priceLevel": place.get("priceLevel", place.get("price_level")),
                "address": place.get("address", ""),
                "location": location,
                "openNow": place.get("openNow", place.get("is_open")),
                "images": images,
                "website": place.get("website"),
            }
            
            normalized.append(normalized_place)
        
        return normalized
    
    def _extract_response(self, langflow_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae la respuesta del formato de Langflow.
        
        Langflow devuelve una estructura anidada:
        {
            "outputs": [
                {
                    "outputs": [
                        {
                            "results": {
                                "message": {
                                    "text": "...",
                                    "data": {...}
                                }
                            }
                        }
                    ]
                }
            ]
        }
        """
        try:
            outputs = langflow_response.get("outputs", [])
            if outputs:
                inner_outputs = outputs[0].get("outputs", [])
                if inner_outputs:
                    results = inner_outputs[0].get("results", {})
                    message = results.get("message", {})
                    
                    text = message.get("text", "")
                    data = message.get("data", {})
                    places = data.get("places", [])
                    
                    return {
                        "response": text,
                        "places": places,
                        "plan": None,
                        "metadata": {
                            "source": "langflow",
                        }
                    }
        except Exception as e:
            logger.error(f"Error extracting Langflow response: {e}")
        
        return {
            "response": "",
            "places": [],
            "plan": None,
            "metadata": {}
        }
    
    # =========================================================================
    # Métodos de gestión de chats (para compatibilidad con frontend)
    # Nota: Langflow almacena mensajes internamente por session_id
    # =========================================================================
    
    async def get_user_chats(
        self, 
        user_id: str, 
        limit: int = 50, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Obtiene los chats de un usuario.
        
        Nota: Langflow no tiene concepto de "usuario" directamente,
        usamos session_id que incluye el user_id.
        Para MVP, retornamos lista vacía y el frontend maneja esto localmente.
        """
        # TODO: Implementar tabla auxiliar en backend para trackear chats por usuario
        return {
            "chats": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
        }
    
    async def get_chat(self, chat_id: str) -> Dict[str, Any]:
        """Obtiene un chat específico."""
        # TODO: Implementar con tabla auxiliar
        return {
            "id": chat_id,
            "title": "Chat",
            "created_at": None,
            "updated_at": None,
        }
    
    async def create_chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo chat."""
        import uuid
        chat_id = str(uuid.uuid4())
        return {
            "id": chat_id,
            "title": payload.get("title", "Nuevo chat"),
            "user_id": payload.get("user_id"),
        }
    
    async def update_chat(self, chat_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un chat."""
        return {
            "id": chat_id,
            **payload,
        }
    
    async def delete_chat(self, chat_id: str, user_id: str) -> None:
        """Elimina un chat."""
        # TODO: Implementar limpieza de mensajes en Langflow
        pass
    
    async def get_chat_history(
        self, 
        chat_id: str, 
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Obtiene el historial de mensajes de un chat.
        
        Nota: Langflow almacena mensajes por session_id.
        Podemos consultarlos via API si session_id == chat_id.
        """
        try:
            # Intentar obtener mensajes de Langflow
            url = f"{self.base_url}/api/v1/monitor/messages"
            params = {
                "session_id": chat_id,
                "limit": limit,
            }
            
            response = await self.http_client.get(
                url,
                headers=self._get_headers(),
                params=params,
            )
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                
                # Formatear al formato esperado por frontend
                formatted_messages = []
                for msg in messages:
                    formatted_messages.append({
                        "role": msg.get("sender", "assistant"),
                        "content": msg.get("text", ""),
                        "places": msg.get("data", {}).get("places", []),
                        "timestamp": msg.get("timestamp"),
                    })
                
                return {
                    "chat_id": chat_id,
                    "messages": formatted_messages,
                }
        except Exception as e:
            logger.error(f"Error getting chat history from Langflow: {e}")
        
        return {
            "chat_id": chat_id,
            "messages": [],
        }


# Singleton instance
langflow_client = LangflowClient()


