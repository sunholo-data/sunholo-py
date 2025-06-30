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
Agent Card generation for A2A protocol.
Generates agent.json discovery documents for VACs.
"""

from typing import Dict, List, Any, Optional
import os
from ..utils import ConfigManager
from ..custom_logging import log
from ..utils.version import sunholo_version


class AgentCardGenerator:
    """Generates A2A Agent Cards for VAC discovery."""
    
    def __init__(self, base_url: str, config_manager: Optional[ConfigManager] = None):
        """
        Initialize the Agent Card generator.
        
        Args:
            base_url: The base URL where the A2A agent is hosted
            config_manager: Optional ConfigManager for global configs
        """
        self.base_url = base_url.rstrip('/')
        self.config_manager = config_manager or ConfigManager('global', validate=False)
        
    def generate_agent_card(self, vac_names: List[str] = None) -> Dict[str, Any]:
        """
        Generate the Agent Card JSON for A2A discovery.
        
        Args:
            vac_names: List of VAC names to include. If None, discovers all configured VACs.
            
        Returns:
            Dict containing the Agent Card JSON structure
        """
        if vac_names is None:
            vac_names = self._discover_vacs()
            
        skills = []
        agent_name = "Sunholo VAC Agent"
        agent_description = "Multi-VAC agent providing access to Sunholo Virtual Agent Computers"
        
        # Generate skills for each VAC
        for vac_name in vac_names:
            try:
                vac_config = ConfigManager(vac_name, validate=False)
                vac_skills = self._generate_vac_skills(vac_name, vac_config)
                skills.extend(vac_skills)
                
                # Use first VAC display name as primary agent name if available
                if len(skills) == len(vac_skills):  # First VAC
                    display_name = vac_config.vacConfig('display_name')
                    if display_name:
                        agent_name = f"{display_name} Agent"
                        
            except Exception as e:
                log.warning(f"Failed to process VAC {vac_name}: {e}")
                continue
        
        # If we have multiple VACs, use a generic name
        if len(vac_names) > 1:
            agent_name = "Sunholo Multi-VAC Agent"
            agent_description = f"Agent providing access to {len(vac_names)} Sunholo VACs: {', '.join(vac_names)}"
        
        agent_card = {
            "name": agent_name,
            "description": agent_description,
            "url": self.base_url,
            "version": sunholo_version(),
            "capabilities": [
                "task_management",
                "streaming",
                "conversation",
                "document_retrieval"
            ],
            "skills": skills,
            "metadata": {
                "framework": "sunholo",
                "protocol_version": "a2a-v1",
                "supported_formats": ["text", "json"],
                "max_context_length": self._get_max_context_length(vac_names),
                "languages": ["en"],  # TODO: Make configurable
                "created_at": self._get_current_timestamp()
            }
        }
        
        return agent_card
    
    def _discover_vacs(self) -> List[str]:
        """
        Discover all configured VACs from the configuration.
        
        Returns:
            List of VAC names found in the configuration
        """
        try:
            vac_configs = self.config_manager.configs_by_kind.get('vacConfig', {})
            if 'vac' in vac_configs:
                return list(vac_configs['vac'].keys())
            return []
        except Exception as e:
            log.error(f"Failed to discover VACs: {e}")
            return []
    
    def _generate_vac_skills(self, vac_name: str, vac_config: ConfigManager) -> List[Dict[str, Any]]:
        """
        Generate A2A skills for a specific VAC.
        
        Args:
            vac_name: Name of the VAC
            vac_config: ConfigManager instance for the VAC
            
        Returns:
            List of skill definitions for this VAC
        """
        skills = []
        
        # Get VAC metadata
        display_name = vac_config.vacConfig('display_name') or vac_name
        model = vac_config.vacConfig('model') or 'unknown'
        agent_type = vac_config.vacConfig('agent') or 'unknown'
        memory_config = vac_config.vacConfig('memory') or []
        
        # Skill 1: VAC Query (static response)
        query_skill = {
            "name": f"vac_query_{vac_name}",
            "description": f"Send a query to {display_name} and get a complete response using {model}",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question or instruction to send to the VAC"
                    },
                    "chat_history": {
                        "type": "array",
                        "description": "Previous conversation history",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string", "enum": ["user", "assistant"]},
                                "content": {"type": "string"}
                            }
                        },
                        "default": []
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context or parameters",
                        "default": {}
                    }
                },
                "required": ["query"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                    "source_documents": {"type": "array"},
                    "metadata": {"type": "object"}
                }
            },
            "metadata": {
                "vac_name": vac_name,
                "model": model,
                "agent_type": agent_type,
                "memory_enabled": len(memory_config) > 0,
                "response_type": "complete"
            }
        }
        skills.append(query_skill)
        
        # Skill 2: VAC Stream (streaming response)
        stream_skill = {
            "name": f"vac_stream_{vac_name}",
            "description": f"Start a streaming conversation with {display_name} using {model}",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The question or instruction to send to the VAC"
                    },
                    "chat_history": {
                        "type": "array",
                        "description": "Previous conversation history",
                        "items": {
                            "type": "object",
                            "properties": {
                                "role": {"type": "string", "enum": ["user", "assistant"]},
                                "content": {"type": "string"}
                            }
                        },
                        "default": []
                    },
                    "stream_settings": {
                        "type": "object",
                        "properties": {
                            "wait_time": {"type": "number", "default": 7},
                            "timeout": {"type": "number", "default": 120}
                        },
                        "default": {}
                    }
                },
                "required": ["query"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "stream_url": {"type": "string"},
                    "task_id": {"type": "string"},
                    "estimated_duration": {"type": "number"}
                }
            },
            "metadata": {
                "vac_name": vac_name,
                "model": model,
                "agent_type": agent_type,
                "memory_enabled": len(memory_config) > 0,
                "response_type": "streaming",
                "supports_sse": True
            }
        }
        skills.append(stream_skill)
        
        # Skill 3: Memory Search (if VAC has memory configured)
        if memory_config:
            memory_skill = {
                "name": f"vac_memory_search_{vac_name}",
                "description": f"Search through {display_name}'s knowledge base and memory",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "search_query": {
                            "type": "string",
                            "description": "The search query for the knowledge base"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        },
                        "similarity_threshold": {
                            "type": "number",
                            "description": "Minimum similarity score for results",
                            "default": 0.7,
                            "minimum": 0.0,
                            "maximum": 1.0
                        }
                    },
                    "required": ["search_query"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "results": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "content": {"type": "string"},
                                    "score": {"type": "number"},
                                    "metadata": {"type": "object"}
                                }
                            }
                        },
                        "total_results": {"type": "integer"}
                    }
                }
            }
            skills.append(memory_skill)
        
        return skills
    
    def _get_max_context_length(self, vac_names: List[str]) -> int:
        """
        Determine the maximum context length based on configured models.
        
        Args:
            vac_names: List of VAC names to check
            
        Returns:
            Maximum context length in tokens
        """
        max_length = 8192  # Default
        
        for vac_name in vac_names:
            try:
                vac_config = ConfigManager(vac_name, validate=False)
                model = vac_config.vacConfig('model')
                
                # Map known models to context lengths
                if model:
                    if 'gemini-1.5' in model:
                        max_length = max(max_length, 2000000)  # Gemini 1.5 Pro
                    elif 'gpt-4' in model:
                        max_length = max(max_length, 128000)   # GPT-4 Turbo
                    elif 'claude-3' in model:
                        max_length = max(max_length, 200000)   # Claude 3
                    elif 'gemini' in model:
                        max_length = max(max_length, 32768)    # Other Gemini models
                        
            except Exception as e:
                log.debug(f"Could not determine context length for {vac_name}: {e}")
                continue
                
        return max_length
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def generate_discovery_endpoints(self) -> Dict[str, str]:
        """
        Generate the A2A discovery endpoint paths.
        
        Returns:
            Dictionary mapping endpoint names to their paths
        """
        return {
            "agent_card": "/.well-known/agent.json",
            "task_send": "/a2a/tasks/send",
            "task_send_subscribe": "/a2a/tasks/sendSubscribe",
            "task_get": "/a2a/tasks/get",
            "task_cancel": "/a2a/tasks/cancel",
            "task_notification": "/a2a/tasks/pushNotification/set"
        }