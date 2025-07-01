#!/usr/bin/env python3
"""
MCP stdio-to-HTTP bridge for Sunholo VAC server.
This script translates between stdio (used by Claude Desktop) and HTTP (used by Sunholo).
"""

import sys
import json
import asyncio
import aiohttp
from typing import Optional

from ..custom_logging import setup_logging
log = setup_logging("mcp-bridge")

class MCPStdioHttpBridge:
    def __init__(self, http_url: str):
        self.http_url = http_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def start(self):
        """Start the bridge."""
        self.session = aiohttp.ClientSession()
        
        # Send initialization success to stderr for debugging
        log.info(f"MCP stdio-to-HTTP bridge started, forwarding to: {self.http_url}")
        
        try:
            await self.process_messages()
        finally:
            await self.session.close()
    
    async def process_messages(self):
        """Process messages from stdin and forward to HTTP server."""
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        while True:
            try:
                # Read line from stdin
                line = await reader.readline()
                if not line:
                    break
                
                line = line.decode().strip()
                if not line:
                    continue
                
                # Parse JSON-RPC message
                try:
                    message = json.loads(line)
                    log.debug(f"Received from stdin: {message}")
                except json.JSONDecodeError as e:
                    log.error(f"Invalid JSON: {e}")
                    continue
                
                # Forward to HTTP server
                try:
                    async with self.session.post(
                        self.http_url,
                        json=message,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        result = await response.json()
                        log.debug(f"Received from HTTP: {result}")
                        
                        # Send response back to stdout
                        print(json.dumps(result))
                        sys.stdout.flush()
                        
                except aiohttp.ClientError as e:
                    log.error(f"HTTP error: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32603,
                            "message": f"HTTP error: {str(e)}"
                        },
                        "id": message.get("id")
                    }
                    print(json.dumps(error_response))
                    sys.stdout.flush()
                    
            except Exception as e:
                log.error(f"Bridge error: {e}")
                continue

async def run_bridge(http_url: str):
    """Run the stdio-to-HTTP bridge."""
    bridge = MCPStdioHttpBridge(http_url)
    await bridge.start()