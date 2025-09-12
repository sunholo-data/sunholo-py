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
Utilities for parsing Server-Sent Events (SSE) responses from MCP servers.
"""

import json
from typing import Any, Dict, Optional


def parse_sse_response(text: str) -> Dict[str, Any]:
    """
    Parse SSE-formatted response from MCP server.
    
    FastMCP returns responses in SSE format when using HTTP transport,
    even with stateless_http=True. This function extracts the JSON data
    from the SSE format.
    
    Args:
        text: Raw response text from MCP server
        
    Returns:
        Parsed JSON data from the SSE response
        
    Raises:
        ValueError: If the response cannot be parsed
        
    Example:
        >>> response_text = 'event: message\\ndata: {"jsonrpc": "2.0", "id": 1, "result": {...}}'
        >>> data = parse_sse_response(response_text)
        >>> print(data['result'])
    """
    # Check if it's SSE format
    if text.startswith('event:') or text.startswith('data:'):
        # Parse SSE format - extract JSON from data: line
        lines = text.split('\n')
        
        # Find the data line
        data_line = None
        for line in lines:
            if line.startswith('data:'):
                data_line = line
                break
        
        if data_line:
            # Remove 'data:' prefix and parse JSON
            json_str = data_line[5:].strip()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse JSON from SSE data: {e}")
        else:
            raise ValueError("No data line found in SSE response")
    else:
        # Try parsing as regular JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Response is not valid JSON or SSE format: {e}")


def is_sse_response(text: str) -> bool:
    """
    Check if a response is in SSE format.
    
    Args:
        text: Response text to check
        
    Returns:
        True if the response appears to be SSE format
    """
    return text.startswith('event:') or text.startswith('data:')


def extract_sse_data(text: str) -> Optional[str]:
    """
    Extract the data portion from an SSE response.
    
    Args:
        text: SSE-formatted response text
        
    Returns:
        The extracted data string, or None if not found
    """
    if not is_sse_response(text):
        return None
    
    lines = text.split('\n')
    for line in lines:
        if line.startswith('data:'):
            return line[5:].strip()
    
    return None