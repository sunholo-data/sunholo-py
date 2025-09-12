import os
import asyncio
import subprocess
from typing import List, Optional

from fastmcp import FastMCP

# Configure logging
from ..custom_logging import setup_logging
logger = setup_logging("sunholo-mcp")

# Initialize FastMCP server
mcp = FastMCP("sunholo-mcp-server")

@mcp.resource("sunholo://vacs/list")
async def list_vacs() -> str:
    """
    List of available Virtual Agent Computers.
    
    Returns the list of configured VACs in the system.
    """
    try:
        result = subprocess.run(
            ["sunholo", "vac", "list"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to list VACs: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error accessing Sunholo: {str(e)}")

@mcp.tool
async def chat_with_vac(vac_name: str, message: str, headless: bool = True) -> str:
    """
    Chat with a specific Sunholo VAC.
    
    Args:
        vac_name: Name of the VAC to chat with
        message: Message to send to the VAC
        headless: Run in headless mode (default: True)
    
    Returns:
        Response from the VAC
    """
    try:
        cmd = ["sunholo", "vac", "chat", vac_name, message]
        if headless:
            cmd.append("--headless")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error chatting with VAC: {e.stderr}"

@mcp.tool
async def list_configs(
    kind: Optional[str] = None,
    vac: Optional[str] = None,
    validate: bool = False
) -> str:
    """
    List Sunholo configurations.
    
    Args:
        kind: Filter configurations by kind (e.g., 'vacConfig')
        vac: Filter configurations by VAC name
        validate: Validate the configuration files
    
    Returns:
        Configuration listing output
    """
    cmd = ["sunholo", "list-configs"]
    
    if kind:
        cmd.extend(["--kind", kind])
    if vac:
        cmd.extend(["--vac", vac])
    if validate:
        cmd.append("--validate")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@mcp.tool
async def embed_content(
    vac_name: str,
    content: str,
    local_chunks: bool = False
) -> str:
    """
    Embed content in a VAC's vector store.
    
    Args:
        vac_name: Name of the VAC to embed content for
        content: Content to embed
        local_chunks: Whether to process chunks locally
    
    Returns:
        Embedding operation result
    """
    try:
        cmd = ["sunholo", "embed", vac_name, content]
        if local_chunks:
            cmd.append("--local-chunks")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error embedding content: {e.stderr}"

def cli_mcp(args):
    """CLI handler for the MCP server command using FastMCP."""
    try:
        if not os.getenv("VAC_CONFIG_FOLDER"):
            raise ValueError("sunholo configuration folder must be present in config/ or via VAC_CONFIG_FOLDER")
        
        logger.info("Starting Sunholo MCP server with FastMCP...")
        
        # Run the FastMCP server in stdio mode (default for Claude Desktop)
        mcp.run()
        
    except Exception as e:
        logger.error(f"Error running MCP server: {str(e)}")
        raise

def cli_mcp_bridge(args):
    """
    CLI handler for the MCP bridge command.
    FastMCP handles HTTP transport natively, so this can be simplified.
    """
    try:
        http_url = args.url
        
        # Parse port from URL if provided
        import urllib.parse
        parsed = urllib.parse.urlparse(http_url)
        port = parsed.port or 8000
        
        logger.info(f"Starting FastMCP HTTP server on port {port}")
        
        # Run FastMCP in HTTP mode
        mcp.run(transport="http", port=port)
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running MCP server: {str(e)}")
        raise

def setup_mcp_subparser(subparsers):
    """
    Sets up an argparse subparser for the 'mcp' command.
    
    By default will use configurations within the folder specified by 'VAC_CONFIG_FOLDER'
    
    Example command:
    ```bash
    sunholo mcp
    ```
    """
    mcp_parser = subparsers.add_parser('mcp', 
                                      help='MCP (Model Context Protocol) commands')
    
    # Create subcommands for mcp
    mcp_subparsers = mcp_parser.add_subparsers(title='mcp commands',
                                               description='MCP subcommands',
                                               help='MCP subcommands',
                                               dest='mcp_command')
    
    # mcp server command (default)
    server_parser = mcp_subparsers.add_parser('server',
                                             help='Start an Anthropic MCP server that wraps sunholo functionality')
    server_parser.set_defaults(func=cli_mcp)
    
    # mcp bridge command - now simplified with FastMCP
    bridge_parser = mcp_subparsers.add_parser('bridge',
                                             help='Start an HTTP MCP server (FastMCP handles transport)')
    bridge_parser.add_argument('url',
                                  nargs='?',
                                  default='http://127.0.0.1:8000/mcp',
                                  help='HTTP URL for the MCP server (default: http://127.0.0.1:8000/mcp)')
    bridge_parser.set_defaults(func=cli_mcp_bridge)
    
    # Set default behavior when no subcommand is provided
    mcp_parser.set_defaults(func=cli_mcp)