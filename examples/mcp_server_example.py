#!/usr/bin/env python3
"""
Example of how to use the Sunholo VAC MCP Server functionality.

This example shows how to enable MCP server mode in your Flask app
to expose VAC functionality via the MCP protocol.
"""

from flask import Flask
from sunholo.agents.flask import VACRoutes

# Your custom interpreter functions
def my_stream_interpreter(question, vector_name, chat_history, **kwargs):
    """
    Example streaming interpreter that yields responses.
    Replace this with your actual VAC logic.
    """
    # Simulate streaming response
    yield f"Processing query for VAC '{vector_name}': {question}\n"
    yield "Here is my streaming response...\n"
    yield {"answer": f"Final answer to: {question}"}

def my_vac_interpreter(question, vector_name, chat_history, **kwargs):
    """
    Example non-streaming interpreter.
    Replace this with your actual VAC logic.
    """
    return {
        "answer": f"Static response from {vector_name}: {question}",
        "source_documents": []
    }

# Create Flask app
app = Flask(__name__)

# Initialize VAC routes with MCP server enabled
vac_routes = VACRoutes(
    app,
    stream_interpreter=my_stream_interpreter,
    vac_interpreter=my_vac_interpreter,
    enable_mcp_server=True  # This enables the MCP server endpoint at /mcp
)

if __name__ == "__main__":
    print("Starting Flask app with MCP server enabled...")
    print("MCP endpoint available at: http://localhost:8080/mcp")
    print("\nTo deploy to Cloud Run:")
    print("1. Create a Dockerfile for this app")
    print("2. Build and push to Container Registry")
    print("3. Deploy with: gcloud run deploy --image IMAGE_URL --port 8080 --no-allow-unauthenticated")
    print("\nTo test locally with an MCP client:")
    print("- Use the MCP SDK to connect to http://localhost:8080/mcp")
    print("- Available tools: vac_stream, vac_query")
    
    app.run(host="0.0.0.0", port=8080, debug=True)