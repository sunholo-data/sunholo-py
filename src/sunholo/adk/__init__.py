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
Google ADK (Agent Development Kit) integration for sunholo.

Provides utilities for building ADK-based agents with:
- Dynamic agent configuration and runtime assembly
- Session management with auth injection
- Event transformation for SSE streaming
- Artifact services for file/image persistence
- MCP tool decorator patterns
- Multi-model support (Azure OpenAI, Gemini, Claude via LiteLLM)

Install with: pip install sunholo[adk]
"""
