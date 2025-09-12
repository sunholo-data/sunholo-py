#!/usr/bin/env python3
"""
Demo showing extensible MCP integration with custom tools.

This example demonstrates how to:
1. Create a FastAPI app with MCP server enabled
2. Add custom MCP tools using decorators
3. Add custom MCP tools programmatically
4. Use both built-in VAC tools and custom tools in Claude Desktop/Code

Usage:
    # Run the demo
    python extensible_mcp_demo.py
    
    # Install for Claude Desktop
    fastmcp install claude-desktop extensible_mcp_demo.py --with sunholo[anthropic]
    
    # Install for Claude Code
    fastmcp install claude-code extensible_mcp_demo.py --with sunholo[anthropic]
"""

import asyncio
import os
import sys
import uvicorn
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Add the sunholo package to path if running from examples directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from sunholo.agents.fastapi import VACRoutesFastAPI
    from sunholo.mcp.extensible_mcp_server import mcp_tool, mcp_resource, create_mcp_server
    from sunholo.custom_logging import log
except ImportError as e:
    print(f"Error importing Sunholo modules: {e}")
    print("Make sure sunholo is installed: pip install sunholo[anthropic]")
    sys.exit(1)


# Example 1: Using decorators to register tools globally
@mcp_tool("get_current_time", "Get the current date and time")
async def get_current_time(timezone: str = "UTC") -> str:
    """
    Get the current date and time.
    
    Args:
        timezone: Timezone to display (currently only supports UTC)
    
    Returns:
        Current date and time as a string
    """
    now = datetime.utcnow()
    return f"Current time ({timezone}): {now.strftime('%Y-%m-%d %H:%M:%S')}"


@mcp_tool("calculate", "Perform basic calculations")
async def calculate(expression: str) -> str:
    """
    Perform basic mathematical calculations.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2", "10 * 3")
    
    Returns:
        Result of the calculation
    """
    try:
        # Simple safe evaluation for basic math
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic mathematical operations are allowed"
        
        result = eval(expression)  # Note: In production, use a safer math parser
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"


@mcp_tool("list_files", "List files in a directory")  
async def list_files(directory: str = ".") -> List[str]:
    """
    List files in a specified directory.
    
    Args:
        directory: Directory path to list (default: current directory)
    
    Returns:
        List of files in the directory
    """
    try:
        path = Path(directory)
        if not path.exists():
            return [f"Error: Directory '{directory}' does not exist"]
        
        if not path.is_dir():
            return [f"Error: '{directory}' is not a directory"]
        
        files = [f.name for f in path.iterdir() if f.is_file()]
        return sorted(files)
    except Exception as e:
        return [f"Error listing files: {str(e)}"]


@mcp_resource("system_info", "Get system information")
async def get_system_info(resource_uri: str) -> Dict[str, Any]:
    """
    Get system information.
    
    Args:
        resource_uri: Resource URI (e.g., "system://info")
    
    Returns:
        System information dictionary
    """
    import platform
    
    return {
        "system": platform.system(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "working_directory": os.getcwd(),
        "resource_uri": resource_uri
    }


# Example 2: Custom business logic tools
class WeatherService:
    """Mock weather service for demonstration."""
    
    @staticmethod
    def get_weather(city: str) -> Dict[str, Any]:
        # Mock weather data
        mock_weather = {
            "london": {"temperature": "15°C", "condition": "Cloudy", "humidity": "75%"},
            "paris": {"temperature": "18°C", "condition": "Sunny", "humidity": "60%"},
            "tokyo": {"temperature": "22°C", "condition": "Partly cloudy", "humidity": "70%"},
            "new york": {"temperature": "12°C", "condition": "Rainy", "humidity": "85%"}
        }
        
        return mock_weather.get(city.lower(), {
            "temperature": "Unknown",
            "condition": "Data not available",
            "humidity": "Unknown"
        })


# Example 3: Standalone MCP server for direct Claude Desktop/Code integration
def create_standalone_mcp_server():
    """Create a standalone MCP server for Claude Desktop/Code integration."""
    
    # Create the extensible MCP server
    server = create_mcp_server(
        server_name="sunholo-extensible-demo",
        include_vac_tools=True  # Include built-in VAC tools
    )
    
    # Add custom weather tool programmatically
    @server.add_tool
    async def get_weather(city: str) -> str:
        """
        Get weather information for a city.
        
        Args:
            city: Name of the city
            
        Returns:
            Weather information string
        """
        weather = WeatherService.get_weather(city)
        return f"Weather in {city.title()}: {weather['condition']}, {weather['temperature']}, Humidity: {weather['humidity']}"
    
    # Add a tool for generating Lorem Ipsum text
    @server.add_tool
    async def generate_lorem(words: int = 10) -> str:
        """
        Generate Lorem Ipsum placeholder text.
        
        Args:
            words: Number of words to generate (default: 10)
            
        Returns:
            Lorem Ipsum text
        """
        lorem_words = [
            "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", 
            "elit", "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore",
            "et", "dolore", "magna", "aliqua", "enim", "ad", "minim", "veniam",
            "quis", "nostrud", "exercitation", "ullamco", "laboris", "nisi",
            "aliquip", "ex", "ea", "commodo", "consequat", "duis", "aute", "irure"
        ]
        
        import random
        selected_words = [random.choice(lorem_words) for _ in range(min(words, 100))]
        return " ".join(selected_words).capitalize() + "."
    
    return server


# Example 4: FastAPI integration with custom tools
def create_fastapi_with_custom_tools():
    """Create FastAPI app with custom MCP tools."""
    
    # Create FastAPI routes with MCP enabled
    routes = VACRoutesFastAPI(
        enable_mcp_server=True,
        stream_interpreter=None,  # Use built-in VAC tools instead
        vac_interpreter=None
    )
    
    # Add custom tools using the FastAPI integration methods
    @routes.add_mcp_tool
    async def get_server_stats() -> Dict[str, Any]:
        """Get server statistics and information."""
        return {
            "server_type": "FastAPI with MCP",
            "mcp_tools_available": len(routes.list_mcp_tools()),
            "mcp_resources_available": len(routes.list_mcp_resources()),
            "uptime_seconds": 42  # Mock uptime
        }
    
    @routes.add_mcp_tool("word_count", "Count words in text")
    async def count_words(text: str) -> Dict[str, int]:
        """
        Count words, characters, and lines in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with word, character, and line counts
        """
        lines = text.split('\n')
        words = text.split()
        chars = len(text)
        chars_no_spaces = len(text.replace(' ', ''))
        
        return {
            "words": len(words),
            "characters": chars,
            "characters_no_spaces": chars_no_spaces,
            "lines": len(lines)
        }
    
    # Add weather tool programmatically  
    async def weather_tool(location: str) -> str:
        """Get weather for a location."""
        weather = WeatherService.get_weather(location)
        return f"Weather in {location}: {weather['condition']}, {weather['temperature']}"
    
    routes.add_mcp_tool(weather_tool, "get_weather_info", "Get weather information")
    
    return routes


def main():
    """Main function - can be run as FastAPI server or standalone MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Extensible MCP Demo")
    parser.add_argument("--mode", choices=["fastapi", "mcp"], default="mcp",
                       help="Run as FastAPI server or standalone MCP server")
    parser.add_argument("--port", type=int, default=8000,
                       help="Port for FastAPI server")
    
    args = parser.parse_args()
    
    if args.mode == "fastapi":
        # Run as FastAPI server
        print("Starting FastAPI server with extensible MCP integration...")
        routes = create_fastapi_with_custom_tools()
        
        print(f"Available MCP tools: {routes.list_mcp_tools()}")
        print(f"Available MCP resources: {routes.list_mcp_resources()}")
        print(f"MCP server available at: http://localhost:{args.port}/mcp")
        print("Configure Claude Desktop with remote MCP server URL")
        
        uvicorn.run(routes.app, host="0.0.0.0", port=args.port)
        
    else:
        # Run as standalone MCP server for Claude Desktop/Code
        print("Starting standalone MCP server for Claude Desktop/Code integration...")
        server = create_standalone_mcp_server()
        
        print(f"Available tools: {server.list_registered_tools()}")
        print(f"Available resources: {server.list_registered_resources()}")
        print("\nTo install for Claude Desktop:")
        print("  fastmcp install claude-desktop extensible_mcp_demo.py --with sunholo[anthropic]")
        print("\nTo install for Claude Code:")
        print("  fastmcp install claude-code extensible_mcp_demo.py --with sunholo[anthropic]")
        print("\nStarting MCP server (STDIO mode)...")
        
        # Run the MCP server
        server.run()


if __name__ == "__main__":
    main()