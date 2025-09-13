#!/usr/bin/env python3
"""
MCP Server for Cloud Run Deployment
Supports both public (OAuth) and private (IAM) authentication modes.
"""

import os
from typing import Dict, Any
from sunholo.agents.fastapi import VACRoutesFastAPI
from sunholo.utils import ConfigManager
from fastapi import Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Determine service mode from environment
SERVICE_MODE = os.getenv("SERVICE_MODE", "private")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://claude.ai").split(",")


async def stream_interpreter(question: str, vector_name: str, chat_history: list, callback=None, **kwargs):
    """
    Main stream interpreter for VAC.
    This should be replaced with your actual implementation.
    """
    try:
        # Get configuration
        config = ConfigManager(vector_name)
        
        # Your actual implementation here
        # This is just a simple example
        response = f"Processing query for {vector_name}: {question}"
        
        # Stream response if callback provided
        if callback:
            for word in response.split():
                if hasattr(callback, 'async_on_llm_new_token'):
                    await callback.async_on_llm_new_token(word + " ")
                elif hasattr(callback, 'on_llm_new_token'):
                    callback.on_llm_new_token(word + " ")
        
        return {
            "answer": response,
            "source_documents": []
        }
    except Exception as e:
        logger.error(f"Error in stream_interpreter: {e}")
        raise


# Create FastAPI app with MCP support
logger.info(f"Starting MCP Server in {SERVICE_MODE} mode")

if SERVICE_MODE == "public":
    # Public service with OAuth protection
    app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(
        title="Sunholo MCP Server (Public)",
        description="MCP Server with OAuth authentication for external access",
        stream_interpreter=stream_interpreter,
        version="1.0.0"
    )
    
    logger.info("OAuth authentication enabled via FastMCP environment variables")
    
else:
    # Private service with IAM protection
    app, vac_routes = VACRoutesFastAPI.create_app_with_mcp(
        title="Sunholo MCP Server (Private)",
        description="MCP Server with Cloud Run IAM authentication for internal access",
        stream_interpreter=stream_interpreter,
        version="1.0.0"
    )
    
    logger.info("Using Cloud Run IAM authentication")


# Add CORS middleware for browser-based access
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {
        "status": "healthy",
        "mode": SERVICE_MODE,
        "auth": "oauth" if SERVICE_MODE == "public" else "iam",
        "mcp_enabled": True
    }


# Metadata endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Sunholo MCP Server",
        "mode": SERVICE_MODE,
        "endpoints": {
            "mcp": "/mcp",
            "vac_streaming": "/vac/streaming/{vector_name}",
            "vac_sse": "/vac/streaming/{vector_name}/sse",
            "health": "/health"
        },
        "authentication": "OAuth 2.0 (Google)" if SERVICE_MODE == "public" else "Cloud Run IAM",
        "documentation": "/docs"
    }


# Custom MCP tools - Add your custom tools here
@vac_routes.add_mcp_tool
async def analyze_document(content: str, analysis_type: str = "summary") -> Dict[str, Any]:
    """
    Analyze a document with specified analysis type.
    
    Args:
        content: The document content to analyze
        analysis_type: Type of analysis (summary, sentiment, entities)
    
    Returns:
        Analysis results
    """
    # Implement your document analysis logic here
    return {
        "content_length": len(content),
        "analysis_type": analysis_type,
        "result": f"Analysis of type '{analysis_type}' completed"
    }


@vac_routes.add_mcp_tool
async def search_knowledge_base(query: str, limit: int = 10) -> list:
    """
    Search the knowledge base for relevant information.
    
    Args:
        query: Search query
        limit: Maximum number of results
    
    Returns:
        List of search results
    """
    # Implement your search logic here
    return [
        {"title": f"Result {i}", "relevance": 1.0 - (i * 0.1)}
        for i in range(min(limit, 5))
    ]


# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "mode": SERVICE_MODE
    }


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unexpected error: {exc}")
    return {
        "error": "Internal server error",
        "status_code": 500,
        "mode": SERVICE_MODE
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"MCP Server started in {SERVICE_MODE} mode")
    logger.info(f"Available MCP tools: {vac_routes.list_mcp_tools()}")
    
    if SERVICE_MODE == "public":
        base_url = os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_BASE_URL", "Not configured")
        logger.info(f"OAuth base URL: {base_url}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("MCP Server shutting down")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)