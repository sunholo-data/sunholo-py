# A2A Agent for VACs

This guide explains how to expose your Sunholo VAC (Virtual Agent Computer) functionality as an A2A (Agent-to-Agent) protocol agent, enabling your VACs to participate in multi-agent ecosystems and be discovered by other A2A-compatible systems.

## Overview

The A2A agent functionality transforms your Flask-based VAC application into an A2A protocol agent, making your VACs discoverable and interactable via the standardized Agent-to-Agent protocol. This enables seamless integration with other AI agents and multi-agent workflows while maintaining compatibility with existing VAC endpoints.

## What is A2A?

The Agent-to-Agent (A2A) protocol is an open standard initiated by Google Cloud that enables AI agents to communicate and collaborate across different platforms and frameworks. Key features include:

- **Agent Discovery**: Automatic capability discovery via Agent Cards
- **Task Management**: Standardized task lifecycle with states like "submitted", "working", "completed"
- **Streaming Support**: Real-time updates via Server-Sent Events (SSE)
- **JSON-RPC 2.0**: Standard communication protocol
- **Multi-Platform**: Works across clouds, platforms, and organizational boundaries

## Enabling A2A Agent

To enable A2A agent functionality in your VAC, set the `enable_a2a_agent` parameter when initializing `VACRoutes`:

```python
from flask import Flask
from sunholo.agents.flask import VACRoutes

app = Flask(__name__)

vac_routes = VACRoutes(
    app,
    stream_interpreter=your_stream_interpreter,
    vac_interpreter=your_vac_interpreter,  # Optional
    enable_a2a_agent=True,  # Enable A2A agent endpoints
    a2a_vac_names=["vac1", "vac2"]  # Optional: specify which VACs to expose
)
```

This will create the following A2A endpoints:
- `/.well-known/agent.json` - Agent Card discovery
- `/a2a/tasks/send` - Create and execute tasks
- `/a2a/tasks/sendSubscribe` - Create tasks with SSE streaming
- `/a2a/tasks/get` - Get task status
- `/a2a/tasks/cancel` - Cancel running tasks
- `/a2a/tasks/pushNotification/set` - Push notification settings

## Agent Card Discovery

The Agent Card at `/.well-known/agent.json` provides automatic discovery of your VAC's capabilities:

```json
{
  "name": "Sunholo VAC Agent",
  "description": "Multi-VAC agent providing access to Sunholo Virtual Agent Computers",
  "url": "https://your-app.run.app",
  "version": "1.0.0",
  "capabilities": [
    "task_management",
    "streaming", 
    "conversation",
    "document_retrieval"
  ],
  "skills": [
    {
      "name": "vac_query_my_vac",
      "description": "Send a query to My VAC and get a complete response using gemini-1.5-flash",
      "input_schema": {
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "The question or instruction to send to the VAC"
          },
          "chat_history": {
            "type": "array",
            "description": "Previous conversation history"
          }
        },
        "required": ["query"]
      }
    }
  ]
}
```

## Available A2A Skills

The A2A agent automatically generates skills based on your VAC configurations:

### 1. VAC Query (vac_query_&#123;vac_name&#125;)
Static queries that return complete responses.

**Parameters:**
- `query` (string, required): The question or instruction
- `chat_history` (array, optional): Previous conversation history
- `context` (object, optional): Additional context parameters

**Response:**
- Complete answer with source documents and metadata

### 2. VAC Stream (vac_stream_&#123;vac_name&#125;)
Streaming conversations with real-time updates.

**Parameters:**
- `query` (string, required): The question or instruction
- `chat_history` (array, optional): Previous conversation history
- `stream_settings` (object, optional): Streaming configuration

**Response:**
- Task ID for tracking streaming progress
- Real-time updates via SSE

### 3. VAC Memory Search (vac_memory_search_&#123;vac_name&#125;)
Search through the VAC's knowledge base (if memory is configured).

**Parameters:**
- `search_query` (string, required): The search query
- `limit` (integer, optional): Maximum results (default: 10)
- `similarity_threshold` (number, optional): Minimum similarity score (default: 0.7)

**Response:**
- Array of search results with scores and metadata

## Complete Example

```python
#!/usr/bin/env python3
from flask import Flask
from sunholo.agents.flask import VACRoutes

# Your VAC interpreter functions
def my_stream_interpreter(question, vector_name, chat_history, **kwargs):
    """Streaming interpreter for real-time responses."""
    yield f"Processing query for VAC '{vector_name}': {question}\n"
    yield "Analyzing context...\n"
    yield {"answer": f"Final answer: {question}"}

def my_vac_interpreter(question, vector_name, chat_history, **kwargs):
    """Static interpreter for complete responses."""
    return {
        "answer": f"Response from {vector_name}: {question}",
        "source_documents": []
    }

# Create Flask app
app = Flask(__name__)

# Initialize with A2A agent enabled
vac_routes = VACRoutes(
    app,
    stream_interpreter=my_stream_interpreter,
    vac_interpreter=my_vac_interpreter,
    enable_a2a_agent=True,
    a2a_vac_names=["support_bot", "research_assistant"]
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

## Task Management

A2A uses a task-based interaction model with the following lifecycle:

1. **Task Creation**: Client sends task to `/a2a/tasks/send`
2. **Processing**: Task moves through states (submitted → working → completed)
3. **Updates**: Real-time updates via `/a2a/tasks/sendSubscribe` (SSE)
4. **Completion**: Final result with artifacts and metadata

### Task States
- `submitted`: Task created and queued
- `working`: Task is being processed
- `input-required`: Task needs additional input (rare)
- `completed`: Task finished successfully
- `failed`: Task encountered an error
- `canceled`: Task was canceled by request

### Example Task Request

```bash
curl -X POST http://localhost:8080/a2a/tasks/send \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tasks/send",
    "params": {
      "skillName": "vac_query_support_bot",
      "input": {
        "query": "How do I reset my password?",
        "chat_history": []
      },
      "clientMetadata": {
        "source": "customer_portal"
      }
    },
    "id": "1"
  }'
```

### Streaming with SSE

For real-time updates, use the SSE endpoint:

```javascript
const eventSource = new EventSource('/a2a/tasks/sendSubscribe', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    jsonrpc: "2.0",
    method: "tasks/sendSubscribe", 
    params: {
      skillName: "vac_stream_research_assistant",
      input: {
        query: "Explain quantum computing",
        stream_settings: {
          wait_time: 5,
          timeout: 180
        }
      }
    },
    id: "2"
  })
});

eventSource.onmessage = function(event) {
  const update = JSON.parse(event.data);
  if (update.type === 'task_update') {
    console.log('Task progress:', update.data.progress);
    if (update.data.state === 'completed') {
      console.log('Final result:', update.data.artifacts);
      eventSource.close();
    }
  }
};
```

## Deploying to Google Cloud Run

The A2A agent is designed to work seamlessly with Google Cloud Run:

1. **Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install A2A support
RUN pip install a2a-python

# Copy application
COPY . .

# Run the app
CMD ["python", "app.py"]
```

2. **Build and deploy:**
```bash
# Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT/vac-a2a-agent

# Deploy to Cloud Run
gcloud run deploy vac-a2a-agent \
  --image gcr.io/YOUR_PROJECT/vac-a2a-agent \
  --port 8080 \
  --no-allow-unauthenticated \
  --region us-central1
```

3. **Authentication**: Cloud Run's IAM handles authentication automatically. A2A clients need the Cloud Run Invoker role.

## A2A Client Integration

Other A2A agents can discover and interact with your VACs:

```python
# Example A2A client code
import requests

# Discover agent capabilities
agent_card = requests.get('https://your-app.run.app/.well-known/agent.json').json()
print(f"Available skills: {[skill['name'] for skill in agent_card['skills']]}")

# Send a task
response = requests.post('https://your-app.run.app/a2a/tasks/send', json={
  "jsonrpc": "2.0",
  "method": "tasks/send", 
  "params": {
    "skillName": "vac_query_support_bot",
    "input": {
      "query": "What are your business hours?"
    }
  },
  "id": "client_123"
}, headers={'Authorization': 'Bearer YOUR_TOKEN'})

task_result = response.json()
```

## Integration with Existing Endpoints

The A2A agent coexists with your existing VAC endpoints:

- **Direct VAC**: `/vac/<vector_name>` and `/vac/streaming/<vector_name>`
- **MCP Server**: `/mcp` (if enabled)
- **A2A Agent**: `/.well-known/agent.json` and `/a2a/*`

All endpoints share the same interpreter functions, ensuring consistent behavior across protocols.

## Configuration and Customization

### VAC Selection
```python
# Expose specific VACs
vac_routes = VACRoutes(
    app,
    stream_interpreter=my_interpreter,
    enable_a2a_agent=True,
    a2a_vac_names=["customer_support", "technical_docs"]  # Only these VACs
)

# Auto-discover all VACs (default)
vac_routes = VACRoutes(
    app,
    stream_interpreter=my_interpreter,
    enable_a2a_agent=True
    # a2a_vac_names=None discovers all configured VACs
)
```

### Agent Metadata
The agent card automatically uses metadata from your VAC configurations:
- `display_name`: Becomes the skill description
- `model`: Included in skill metadata  
- `memory`: Determines if memory search skills are available
- `agent`: Included in capability descriptions

## Troubleshooting

### A2A agent not enabled error
Ensure you have:
1. Set `enable_a2a_agent=True` in VACRoutes
2. Installed the A2A dependencies: `pip install a2a-python`

### Empty skills list
Check that:
1. Your VACs are properly configured in `vac_config.yaml`
2. The `a2a_vac_names` parameter includes valid VAC names
3. VAC discovery is working: Check logs for configuration errors

### Task execution failures
Verify that:
1. Your `stream_interpreter` and `vac_interpreter` functions work correctly
2. VAC names in skill requests match configured VACs
3. Input parameters match the expected schema

### SSE streaming issues  
Ensure:
1. Client properly handles `text/event-stream` content type
2. Connection timeouts are configured appropriately
3. Task cancellation works if connections are dropped

## Relationship with MCP

A2A complements the Model Context Protocol (MCP):
- **MCP**: Tool-focused protocol for extending agent capabilities  
- **A2A**: Agent-focused protocol for agent-to-agent communication

You can enable both protocols simultaneously:

```python
vac_routes = VACRoutes(
    app,
    stream_interpreter=my_interpreter,
    enable_mcp_server=True,   # MCP tools
    enable_a2a_agent=True     # A2A agent communication
)
```

This creates a multi-protocol agent platform that can:
- Serve as MCP tools for other agents
- Participate in A2A agent ecosystems  
- Provide direct VAC access via HTTP

## See Also

- [Creating a VAC](creating_a_vac.md)
- [MCP Server for VACs](mcp_server.md)
- [Flask App Development](flask_app.md)  
- [A2A Protocol Specification](https://www.a2aprotocol.net/docs/specification)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)