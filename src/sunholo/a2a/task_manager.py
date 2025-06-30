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
A2A Task Management for VAC interactions.
Handles the lifecycle of A2A tasks and their state transitions.
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator
from enum import Enum
import json
from ..custom_logging import log


class TaskState(Enum):
    """A2A Task states as defined in the protocol."""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"
    UNKNOWN = "unknown"


class A2ATask:
    """Represents an A2A task with its state and data."""
    
    def __init__(self, task_id: str, skill_name: str, input_data: Dict[str, Any], 
                 client_metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize an A2A task.
        
        Args:
            task_id: Unique task identifier
            skill_name: Name of the skill being invoked
            input_data: Input parameters for the task
            client_metadata: Optional metadata from the client
        """
        self.task_id = task_id
        self.skill_name = skill_name
        self.input_data = input_data
        self.client_metadata = client_metadata or {}
        
        self.state = TaskState.SUBMITTED
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.completed_at: Optional[datetime] = None
        
        self.messages: List[Dict[str, Any]] = []
        self.artifacts: List[Dict[str, Any]] = []
        self.error: Optional[Dict[str, Any]] = None
        self.progress: float = 0.0
        
        # For streaming tasks
        self.stream_queue: Optional[asyncio.Queue] = None
        self.is_streaming = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary format for A2A responses."""
        return {
            "taskId": self.task_id,
            "state": self.state.value,
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
            "messages": self.messages,
            "artifacts": self.artifacts,
            "error": self.error,
            "progress": self.progress,
            "metadata": {
                "skillName": self.skill_name,
                "isStreaming": self.is_streaming,
                "clientMetadata": self.client_metadata
            }
        }
    
    def add_message(self, role: str, content: str, message_type: str = "text"):
        """Add a message to the task."""
        message = {
            "role": role,
            "parts": [{
                "type": message_type,
                "text": content
            }],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.messages.append(message)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_artifact(self, name: str, content: Any, artifact_type: str = "text"):
        """Add an artifact to the task."""
        artifact = {
            "name": name,
            "type": artifact_type,
            "content": content,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        self.artifacts.append(artifact)
        self.updated_at = datetime.now(timezone.utc)
    
    def update_state(self, new_state: TaskState, error_message: str = None):
        """Update the task state."""
        self.state = new_state
        self.updated_at = datetime.now(timezone.utc)
        
        if new_state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED]:
            self.completed_at = self.updated_at
        
        if new_state == TaskState.FAILED and error_message:
            self.error = {
                "message": error_message,
                "timestamp": self.updated_at.isoformat()
            }
    
    def update_progress(self, progress: float):
        """Update task progress (0.0 to 1.0)."""
        self.progress = max(0.0, min(1.0, progress))
        self.updated_at = datetime.now(timezone.utc)


class A2ATaskManager:
    """Manages A2A tasks and their lifecycle."""
    
    def __init__(self, stream_interpreter: Callable, vac_interpreter: Optional[Callable] = None):
        """
        Initialize the task manager.
        
        Args:
            stream_interpreter: Function for streaming VAC interactions
            vac_interpreter: Function for static VAC interactions
        """
        self.stream_interpreter = stream_interpreter
        self.vac_interpreter = vac_interpreter
        self.tasks: Dict[str, A2ATask] = {}
        self.task_subscribers: Dict[str, List[asyncio.Queue]] = {}
    
    async def create_task(self, skill_name: str, input_data: Dict[str, Any], 
                         client_metadata: Optional[Dict[str, Any]] = None) -> A2ATask:
        """
        Create a new A2A task.
        
        Args:
            skill_name: Name of the skill to invoke
            input_data: Input parameters for the task
            client_metadata: Optional client metadata
            
        Returns:
            Created A2ATask instance
        """
        task_id = str(uuid.uuid4())
        task = A2ATask(task_id, skill_name, input_data, client_metadata)
        
        self.tasks[task_id] = task
        self.task_subscribers[task_id] = []
        
        log.info(f"Created A2A task {task_id} for skill {skill_name}")
        
        # Start processing the task
        asyncio.create_task(self._process_task(task))
        
        return task
    
    async def get_task(self, task_id: str) -> Optional[A2ATask]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if task was canceled, False if not found or already completed
        """
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED]:
            return False
        
        task.update_state(TaskState.CANCELED)
        await self._notify_subscribers(task_id, task.to_dict())
        
        log.info(f"Canceled A2A task {task_id}")
        return True
    
    async def subscribe_to_task(self, task_id: str):
        """
        Subscribe to task updates via async generator.
        
        Args:
            task_id: ID of the task to subscribe to
            
        Yields:
            Task update dictionaries
        """
        if task_id not in self.tasks:
            return  # Early return for async generator
        
        queue = asyncio.Queue()
        self.task_subscribers[task_id].append(queue)
        
        # Send current state immediately
        current_task = self.tasks[task_id]
        await queue.put(current_task.to_dict())
        
        try:
            while True:
                update = await queue.get()
                if update is None:  # End signal
                    break
                yield update
        finally:
            # Clean up subscription
            if queue in self.task_subscribers.get(task_id, []):
                self.task_subscribers[task_id].remove(queue)
    
    async def _process_task(self, task: A2ATask):
        """
        Process a task by invoking the appropriate VAC functionality.
        
        Args:
            task: The task to process
        """
        try:
            task.update_state(TaskState.WORKING)
            await self._notify_subscribers(task.task_id, task.to_dict())
            
            # Parse skill name to extract VAC name and operation
            vac_name, operation = self._parse_skill_name(task.skill_name)
            
            if operation == "query":
                await self._process_query_task(task, vac_name)
            elif operation == "stream":
                await self._process_stream_task(task, vac_name)
            elif operation == "memory_search":
                await self._process_memory_search_task(task, vac_name)
            else:
                raise ValueError(f"Unknown operation: {operation}")
                
        except Exception as e:
            log.error(f"Error processing task {task.task_id}: {e}")
            task.update_state(TaskState.FAILED, str(e))
            await self._notify_subscribers(task.task_id, task.to_dict())
    
    async def _process_query_task(self, task: A2ATask, vac_name: str):
        """Process a static query task."""
        if not self.vac_interpreter:
            raise ValueError("VAC interpreter not available for query tasks")
        
        query = task.input_data.get("query", "")
        chat_history = task.input_data.get("chat_history", [])
        context = task.input_data.get("context", {})
        
        task.add_message("user", query)
        task.update_progress(0.3)
        await self._notify_subscribers(task.task_id, task.to_dict())
        
        # Convert A2A chat history to VAC format
        vac_chat_history = self._convert_chat_history(chat_history)
        
        # Execute VAC query
        if asyncio.iscoroutinefunction(self.vac_interpreter):
            result = await self.vac_interpreter(
                question=query,
                vector_name=vac_name,
                chat_history=vac_chat_history,
                **context
            )
        else:
            # Run sync function in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.vac_interpreter(
                    question=query,
                    vector_name=vac_name,
                    chat_history=vac_chat_history,
                    **context
                )
            )
        
        # Process result
        if isinstance(result, dict):
            answer = result.get("answer", str(result))
            source_docs = result.get("source_documents", [])
        else:
            answer = str(result)
            source_docs = []
        
        task.add_message("agent", answer)
        task.add_artifact("response", {
            "answer": answer,
            "source_documents": source_docs,
            "metadata": result if isinstance(result, dict) else {}
        }, "json")
        
        task.update_progress(1.0)
        task.update_state(TaskState.COMPLETED)
        await self._notify_subscribers(task.task_id, task.to_dict())
    
    async def _process_stream_task(self, task: A2ATask, vac_name: str):
        """Process a streaming task."""
        query = task.input_data.get("query", "")
        chat_history = task.input_data.get("chat_history", [])
        stream_settings = task.input_data.get("stream_settings", {})
        
        task.add_message("user", query)
        task.is_streaming = True
        task.update_progress(0.1)
        await self._notify_subscribers(task.task_id, task.to_dict())
        
        # Convert chat history
        vac_chat_history = self._convert_chat_history(chat_history)
        
        try:
            # Import streaming function
            from ..streaming import start_streaming_chat_async
            
            # Start streaming
            full_response = ""
            async for chunk in start_streaming_chat_async(
                question=query,
                vector_name=vac_name,
                qna_func_async=self.stream_interpreter,
                chat_history=vac_chat_history,
                wait_time=stream_settings.get("wait_time", 7),
                timeout=stream_settings.get("timeout", 120)
            ):
                if isinstance(chunk, dict) and 'answer' in chunk:
                    full_response = chunk['answer']
                    task.update_progress(0.9)
                elif isinstance(chunk, str):
                    full_response += chunk
                    task.update_progress(min(0.8, task.progress + 0.1))
                
                # Send intermediate updates
                await self._notify_subscribers(task.task_id, task.to_dict())
            
            # Final response
            task.add_message("agent", full_response)
            task.add_artifact("streaming_response", {
                "final_answer": full_response,
                "stream_completed": True
            }, "json")
            
            task.update_progress(1.0)
            task.update_state(TaskState.COMPLETED)
            
        except Exception as e:
            task.update_state(TaskState.FAILED, f"Streaming error: {str(e)}")
        
        await self._notify_subscribers(task.task_id, task.to_dict())
    
    async def _process_memory_search_task(self, task: A2ATask, vac_name: str):
        """Process a memory search task."""
        # This is a placeholder for memory search functionality
        # In a real implementation, this would interface with the VAC's vector store
        
        search_query = task.input_data.get("search_query", "")
        limit = task.input_data.get("limit", 10)
        similarity_threshold = task.input_data.get("similarity_threshold", 0.7)
        
        task.add_message("agent", f"Searching memory for: {search_query}")
        task.update_progress(0.5)
        await self._notify_subscribers(task.task_id, task.to_dict())
        
        # TODO: Implement actual memory search
        # For now, return a placeholder response
        results = [{
            "content": f"Memory search result for '{search_query}' (placeholder)",
            "score": 0.8,
            "metadata": {"vac_name": vac_name, "query": search_query}
        }]
        
        task.add_artifact("search_results", {
            "results": results,
            "total_results": len(results),
            "query": search_query,
            "limit": limit,
            "similarity_threshold": similarity_threshold
        }, "json")
        
        task.update_progress(1.0)
        task.update_state(TaskState.COMPLETED)
        await self._notify_subscribers(task.task_id, task.to_dict())
    
    def _parse_skill_name(self, skill_name: str) -> tuple[str, str]:
        """
        Parse skill name to extract VAC name and operation.
        
        Expected format: "vac_{operation}_{vac_name}"
        
        Args:
            skill_name: The skill name to parse
            
        Returns:
            Tuple of (vac_name, operation)
        """
        parts = skill_name.split("_")
        if len(parts) < 3 or parts[0] != "vac":
            raise ValueError(f"Invalid skill name format: {skill_name}")
        
        operation = parts[1]  # query, stream, memory
        vac_name = "_".join(parts[2:])  # Handle VAC names with underscores
        
        return vac_name, operation
    
    def _convert_chat_history(self, a2a_history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Convert A2A chat history format to VAC format.
        
        Args:
            a2a_history: A2A format chat history
            
        Returns:
            VAC format chat history
        """
        vac_history = []
        
        for msg in a2a_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            if role == "user":
                vac_history.append({"human": content})
            elif role == "assistant":
                vac_history.append({"ai": content})
        
        return vac_history
    
    async def _notify_subscribers(self, task_id: str, task_data: Dict[str, Any]):
        """Notify all subscribers of a task update."""
        if task_id in self.task_subscribers:
            for queue in self.task_subscribers[task_id]:
                try:
                    await queue.put(task_data)
                except Exception as e:
                    log.warning(f"Failed to notify subscriber for task {task_id}: {e}")
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """
        Clean up completed tasks older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours for completed tasks
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if (task.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED] and
                task.completed_at and task.completed_at < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            if task_id in self.task_subscribers:
                del self.task_subscribers[task_id]
        
        if tasks_to_remove:
            log.info(f"Cleaned up {len(tasks_to_remove)} completed tasks")