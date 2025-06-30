#!/usr/bin/env python3
"""
Example of how to use the Sunholo VAC A2A Agent functionality.

This example shows how to enable A2A agent mode in your Flask app
to expose VAC functionality via the Agent-to-Agent protocol.
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
    yield "Analyzing context and generating response...\n"
    yield {"answer": f"A2A streaming response to: {question}"}

def my_vac_interpreter(question, vector_name, chat_history, **kwargs):
    """
    Example non-streaming interpreter.
    Replace this with your actual VAC logic.
    """
    return {
        "answer": f"A2A static response from {vector_name}: {question}",
        "source_documents": []
    }

# Create Flask app
app = Flask(__name__)

# Initialize VAC routes with A2A agent enabled
vac_routes = VACRoutes(
    app,
    stream_interpreter=my_stream_interpreter,
    vac_interpreter=my_vac_interpreter,
    enable_a2a_agent=True,  # This enables the A2A agent endpoints
    a2a_vac_names=["example_vac", "demo_vac"]  # Optional: specify VAC names
)

if __name__ == "__main__":
    print("Starting Flask app with A2A agent enabled...")
    print("A2A Agent Card available at: http://localhost:8080/.well-known/agent.json")
    print("A2A Task endpoints:")
    print("  - POST /a2a/tasks/send")
    print("  - POST /a2a/tasks/sendSubscribe (SSE)")
    print("  - POST /a2a/tasks/get")
    print("  - POST /a2a/tasks/cancel")
    print("\nTo deploy to Cloud Run:")
    print("1. Create a Dockerfile for this app")
    print("2. Build and push to Container Registry")
    print("3. Deploy with: gcloud run deploy --image IMAGE_URL --port 8080 --no-allow-unauthenticated")
    print("\nTo test with an A2A client:")
    print("1. GET http://localhost:8080/.well-known/agent.json to discover capabilities")
    print("2. POST to /a2a/tasks/send with JSON-RPC request")
    print("3. Available skills: vac_query_*, vac_stream_*, vac_memory_search_*")
    print("\nExample A2A task request:")
    print("""
    {
      "jsonrpc": "2.0",
      "method": "tasks/send",
      "params": {
        "skillName": "vac_query_example_vac",
        "input": {
          "query": "What is the weather today?",
          "chat_history": []
        }
      },
      "id": "1"
    }
    """)
    
    app.run(host="0.0.0.0", port=8080, debug=True)