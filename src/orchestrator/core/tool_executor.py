"""
ToolExecutor - Exécution des outils appelés par LLM
Dispatche vers les bons services selon tool_name
"""

from typing import Dict, Any
from loguru import logger
import asyncio

from core.service_registry import ServiceRegistry
from core.models import ToolCall, ToolStatus


class ToolExecutor:
    """
    Exécute les outils demandés par le LLM
    Interface unifiée pour tous les services
    """
    
    def __init__(self, service_registry: ServiceRegistry):
        self.service_registry = service_registry
        
        # Mapping outils → services
        self.tool_to_service = {
            "system_executor": "system_executor",
            "llm_knowledge": "llm",
            "email_connector": "connectors",
            "calendar_connector": "connectors",
            "tts": "tts",
            "stt": "stt"
        }
        
        # Mapping actions → endpoints
        self.action_endpoints = {
            # System Executor
            "system_executor.create_file": "/execute",
            "system_executor.delete_file": "/execute",
            "system_executor.list_directory": "/execute",
            "system_executor.open_application": "/execute",
            "system_executor.execute_command": "/execute",
            
            # LLM Knowledge
            "llm_knowledge.learn": "/learn",
            "llm_knowledge.search": "/search",
            "llm_knowledge.forget": "/forget",
            
            # TTS
            "tts.speak": "/synthesize",
            
            # STT
            "stt.transcribe": "/transcribe",
            
            # Connectors (à implémenter)
            "email_connector.read_inbox": "/email/read",
            "email_connector.send_email": "/email/send",
            "calendar_connector.list_events": "/calendar/events",
            "calendar_connector.create_event": "/calendar/create"
        }
    
    async def execute(self, tool_call: ToolCall) -> Dict[str, Any]:
        """
        Exécute un ToolCall
        
        Args:
            tool_call: ToolCall à exécuter
            
        Returns:
            Résultat de l'exécution
        """
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Résoudre service
            service_name = self.tool_to_service.get(tool_call.tool_name)
            
            if not service_name:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_call.tool_name}"
                }
            
            # Résoudre endpoint
            action_key = f"{tool_call.tool_name}.{tool_call.action}"
            endpoint = self.action_endpoints.get(action_key)
            
            if not endpoint:
                return {
                    "success": False,
                    "error": f"Unknown action: {action_key}"
                }
            
            # Préparer payload selon l'outil
            payload = self._prepare_payload(tool_call)
            
            logger.debug(f"Executing {action_key} → {service_name}{endpoint}")
            
            # Appeler le service
            result = await self.service_registry.call_service(
                service_name=service_name,
                endpoint=endpoint,
                method="POST",
                data=payload,
                timeout=30
            )
            
            # Calculer temps exécution
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            tool_call.execution_time_ms = execution_time
            
            logger.success(f"✅ {action_key} completed in {execution_time:.0f}ms")
            
            return {
                "success": result.get("success", True),
                "data": result,
                "execution_time_ms": execution_time
            }
        
        except Exception as e:
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            tool_call.execution_time_ms = execution_time
            
            logger.error(f"❌ {tool_call.tool_name}.{tool_call.action} failed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time_ms": execution_time
            }
    
    def _prepare_payload(self, tool_call: ToolCall) -> Dict[str, Any]:
        """
        Prépare le payload selon l'outil
        Adapte les paramètres au format attendu par chaque service
        """
        
        tool_name = tool_call.tool_name
        action = tool_call.action
        params = tool_call.parameters
        
        # System Executor
        if tool_name == "system_executor":
            return {
                "action": action,
                **params  # path, content, app_name, command, etc.
            }
        
        # LLM Knowledge
        elif tool_name == "llm_knowledge":
            if action == "learn":
                return {"text": params.get("text", "")}
            elif action == "search":
                return {
                    "query": params.get("query", ""),
                    "top_k": params.get("top_k", 3),
                    "min_score": params.get("min_score", 0.5)
                }
            elif action == "forget":
                return {"fact_id": params.get("fact_id")}
        
        # TTS
        elif tool_name == "tts":
            return {
                "text": params.get("text", ""),
                "voice": params.get("voice", "default"),
                "speed": params.get("speed", 1.0)
            }
        
        # STT
        elif tool_name == "stt":
            return {
                "audio_file": params.get("audio_file", ""),
                "language": params.get("language", "fr")
            }
        
        # Email Connector
        elif tool_name == "email_connector":
            if action == "send_email":
                return {
                    "to": params.get("to"),
                    "subject": params.get("subject"),
                    "body": params.get("body"),
                    "cc": params.get("cc"),
                    "attachments": params.get("attachments", [])
                }
            elif action == "read_inbox":
                return {
                    "filter": params.get("filter", "unread"),
                    "limit": params.get("limit", 10)
                }
        
        # Calendar Connector
        elif tool_name == "calendar_connector":
            if action == "create_event":
                return {
                    "title": params.get("title"),
                    "start_time": params.get("start_time"),
                    "end_time": params.get("end_time"),
                    "description": params.get("description"),
                    "attendees": params.get("attendees", [])
                }
            elif action == "list_events":
                return {
                    "start_date": params.get("start_date"),
                    "end_date": params.get("end_date")
                }
        
        # Défaut: retourner params tel quel
        return params


# ==================== EXPORT ====================

__all__ = ['ToolExecutor']
