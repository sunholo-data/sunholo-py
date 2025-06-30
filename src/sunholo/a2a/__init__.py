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

"""A2A (Agent-to-Agent) protocol integration for Sunholo."""

try:
    from .agent_card import AgentCardGenerator
    from .task_manager import A2ATaskManager
    from .vac_a2a_agent import VACA2AAgent
except (ImportError, SyntaxError) as e:
    # Handle missing dependencies or syntax errors gracefully
    AgentCardGenerator = None
    VACA2AAgent = None
    A2ATaskManager = None

__all__ = ['AgentCardGenerator', 'VACA2AAgent', 'A2ATaskManager']