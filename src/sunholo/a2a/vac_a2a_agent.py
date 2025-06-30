#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
A2A Agent wrapper for VAC functionality.
Implements the Agent-to-Agent protocol for Sunholo VACs.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from ..custom_logging import log
from .agent_card import AgentCardGenerator
from .task_manager import A2ATaskManager, A2ATask

try:
    # Import A2A Python SDK components when available
    from a2a import Agent, Task, Message
    A2A_AVAILABLE = True
except ImportError:
    # Create placeholder classes for development
    Agent = None
    Task = None 
    Message = None
    A2A_AVAILABLE = False


class VACA2AAgent:
    """
    A2A Agent implementation for Sunholo VACs.
    
    This class wraps VAC functionality to be compatible with the 
    Agent-to-Agent protocol, allowing VACs to participate in A2A ecosystems.
    """
    
    def __init__(self, 
                 base_url: str,
                 stream_interpreter: Callable,
                 vac_interpreter: Optional[Callable] = None,
                 vac_names: Optional[List[str]] = None,
                 agent_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the A2A agent.
        
        Args:
            base_url: Base URL where the agent is hosted
            stream_interpreter: Function for streaming VAC interactions
            vac_interpreter: Function for static VAC interactions (optional)
            vac_names: List of VAC names to expose (discovers all if None)
            agent_config: Additional agent configuration
        """
        if not A2A_AVAILABLE:
            log.warning("A2A Python SDK not available. Install with: pip install a2a-python")
        
        self.base_url = base_url.rstrip('/')
        self.stream_interpreter = stream_interpreter
        self.vac_interpreter = vac_interpreter
        self.agent_config = agent_config or {}
        
        # Initialize components
        self.agent_card_generator = AgentCardGenerator(self.base_url)
        self.task_manager = A2ATaskManager(stream_interpreter, vac_interpreter)
        
        # Discover VACs
        self.vac_names = vac_names or self.agent_card_generator._discover_vacs()
        if not self.vac_names:
            log.warning("No VACs discovered. Agent will have no skills.")
        
        # Generate agent card
        self.agent_card = self.agent_card_generator.generate_agent_card(self.vac_names)
        
        log.info(f"Initialized A2A agent with {len(self.vac_names)} VACs: {self.vac_names}")
    
    def get_agent_card(self) -> Dict[str, Any]:
        """
        Get the agent card for A2A discovery.
        
        Returns:
            Agent card dictionary
        """
        return self.agent_card
    
    def get_discovery_endpoints(self) -> Dict[str, str]:
        """
        Get the A2A discovery endpoint paths.
        
        Returns:
            Dictionary mapping endpoint names to their paths
        """
        return self.agent_card_generator.generate_discovery_endpoints()
    
    async def handle_task_send(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle A2A task send request.
        
        Args:
            request_data: JSON-RPC request data
            
        Returns:
            JSON-RPC response data
        """
        try:
            # Extract parameters from JSON-RPC request
            params = request_data.get("params", {})
            skill_name = params.get("skillName")
            input_data = params.get("input", {})
            client_metadata = params.get("clientMetadata", {})
            
            if not skill_name:
                return self._create_error_response(
                    request_data.get("id"),
                    -32602,  # Invalid params
                    "Missing required parameter: skillName"
                )
            
            # Validate skill exists
            available_skills = [skill["name"] for skill in self.agent_card["skills"]]
            if skill_name not in available_skills:
                return self._create_error_response(
                    request_data.get("id"),
                    -32601,  # Method not found
                    f"Unknown skill: {skill_name}. Available skills: {available_skills}"
                )
            
            # Create and start task
            task = await self.task_manager.create_task(skill_name, input_data, client_metadata)
            
            # Return task creation response
            return {
                "jsonrpc": "2.0",
                "result": {
                    "taskId": task.task_id,
                    "state": task.state.value,
                    "createdAt": task.created_at.isoformat(),
                    "estimatedDuration": self._estimate_task_duration(skill_name, input_data)
                },
                "id": request_data.get("id")
            }
            
        except Exception as e:
            log.error(f"Error handling task send: {e}")
            return self._create_error_response(
                request_data.get("id"),
                -32603,  # Internal error
                f"Internal error: {str(e)}"
            )
    
    async def handle_task_send_subscribe(self, request_data: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Handle A2A task send with subscription (SSE).
        
        Args:
            request_data: JSON-RPC request data
            
        Yields:
            Server-sent event data strings
        """
        try:
            # First, send the task
            response = await self.handle_task_send(request_data)
            
            # Send initial response
            yield f"data: {json.dumps(response)}\n\n"
            
            # If task creation failed, stop here
            if "error" in response:
                return
            
            # Get task ID and subscribe to updates
            task_id = response["result"]["taskId"]
            
            # Subscribe to task updates
            async for update in self.task_manager.subscribe_to_task(task_id):
                if update is None:
                    break
                
                # Format as SSE
                sse_data = {
                    "type": "task_update",
                    "taskId": task_id,
                    "data": update
                }
                
                yield f"data: {json.dumps(sse_data)}\n\n"
                
                # Stop if task is complete
                if update.get("state") in ["completed", "failed", "canceled"]:
                    break
            
        except Exception as e:
            log.error(f"Error in task send subscribe: {e}")
            error_event = {
                "type": "error",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    async def handle_task_get(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle A2A task get request.
        
        Args:
            request_data: JSON-RPC request data
            
        Returns:
            JSON-RPC response data
        """
        try:
            params = request_data.get("params", {})
            task_id = params.get("taskId")
            
            if not task_id:
                return self._create_error_response(
                    request_data.get("id"),
                    -32602,  # Invalid params
                    "Missing required parameter: taskId"
                )
            
            task = await self.task_manager.get_task(task_id)
            if not task:
                return self._create_error_response(
                    request_data.get("id"),
                    -32602,  # Invalid params
                    f"Task not found: {task_id}"
                )
            
            return {
                "jsonrpc": "2.0",
                "result": task.to_dict(),
                "id": request_data.get("id")
            }
            
        except Exception as e:
            log.error(f"Error handling task get: {e}")
            return self._create_error_response(
                request_data.get("id"),
                -32603,  # Internal error
                f"Internal error: {str(e)}"
            )
    
    async def handle_task_cancel(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle A2A task cancel request.
        
        Args:
            request_data: JSON-RPC request data
            
        Returns:
            JSON-RPC response data
        """
        try:
            params = request_data.get("params", {})
            task_id = params.get("taskId")
            
            if not task_id:
                return self._create_error_response(
                    request_data.get("id"),
                    -32602,  # Invalid params
                    "Missing required parameter: taskId"
                )
            
            success = await self.task_manager.cancel_task(task_id)
            
            if not success:
                return self._create_error_response(
                    request_data.get("id"),
                    -32602,  # Invalid params
                    f"Cannot cancel task: {task_id} (not found or already completed)"
                )
            
            task = await self.task_manager.get_task(task_id)
            
            return {
                "jsonrpc": "2.0",
                "result": {
                    "taskId": task_id,
                    "state": task.state.value if task else "canceled",
                    "canceledAt": task.updated_at.isoformat() if task else None
                },
                "id": request_data.get("id")
            }
            
        except Exception as e:
            log.error(f"Error handling task cancel: {e}")
            return self._create_error_response(
                request_data.get("id"),
                -32603,  # Internal error
                f"Internal error: {str(e)}"
            )
    
    async def handle_push_notification_set(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle A2A push notification settings.
        
        Args:
            request_data: JSON-RPC request data
            
        Returns:
            JSON-RPC response data
        """
        # For now, this is a placeholder
        # In a full implementation, this would configure push notifications
        
        return {
            "jsonrpc": "2.0",
            "result": {
                "status": "not_implemented",
                "message": "Push notifications not yet implemented"
            },
            "id": request_data.get("id")
        }
    
    def _create_error_response(self, request_id: Any, error_code: int, error_message: str) -> Dict[str, Any]:
        """
        Create a JSON-RPC error response.
        
        Args:
            request_id: The request ID
            error_code: JSON-RPC error code
            error_message: Error message
            
        Returns:
            JSON-RPC error response
        """
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": error_code,
                "message": error_message
            },
            "id": request_id
        }
    
    def _estimate_task_duration(self, skill_name: str, input_data: Dict[str, Any]) -> float:
        """
        Estimate task duration in seconds.
        
        Args:
            skill_name: Name of the skill
            input_data: Input parameters
            
        Returns:
            Estimated duration in seconds
        """
        # Simple heuristic based on skill type
        if "stream" in skill_name:
            return 30.0  # Streaming typically takes longer
        elif "memory_search" in skill_name:
            return 5.0   # Memory searches are usually quick
        else:
            return 15.0  # Default for queries
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent statistics.
        
        Returns:
            Dictionary with agent statistics
        """
        return {
            "agent_name": self.agent_card["name"],
            "vac_count": len(self.vac_names),
            "skill_count": len(self.agent_card["skills"]),
            "active_tasks": len([t for t in self.task_manager.tasks.values() 
                               if t.state.value in ["submitted", "working"]]),
            "total_tasks": len(self.task_manager.tasks),
            "base_url": self.base_url,
            "a2a_available": A2A_AVAILABLE
        }