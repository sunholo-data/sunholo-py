try:
    import socketio
except ImportError:
    socketio = None

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import HTMLResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
except ImportError:
    FastAPI = None

from ...logging import log

def create_fastapi_app(origins = ["*"],
                       origin_regex = r"https://(.*\.)?sunholo\.com"):
    """Creates and configures a FastAPI app for GenAI with Socket.IO integration.

    Args:
        image_qna_stream_fn: Streaming Q&A function (likely from gemini.genai)
        image_qna_fn: Non-streaming Q&A function (likely from gemini.genai)

    Returns:
        FastAPI: The configured FastAPI app instance.
    """

    if not socketio:
        raise ImportError("socketio is not available, please install via `pip install fastapi-socketio`")


    if not FastAPI:
        raise ImportError("FastAPI is not available, please install via `pip install fastapi`")

    # Create Socket.IO server and FastAPI app     
    sio = socketio.AsyncServer(async_mode='asgi')
    app = FastAPI()
    socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
    app.mount("/ws/socket.io/", socket_app)

    # CORS Configuration 
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Handle Socket.IO events, e.g., a connection
    @sio.event
    async def connect(sid, environ):
        log.info("Socket.IO client connected", sid)

    # Homepage Route
    @app.get("/", response_class=HTMLResponse)
    async def homepage(request: Request):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Multivac Service Homepage</title>
        </head>
        <body>
            <h1>Welcome to Multivac</h1>
            <p>This is a debug homepage to confirm the service is up and running.</p>
        </body>
        </html>
        """
    
    @app.get("/docs")
    async def get_documentation():
        """Endpoint to serve Swagger UI for API documentation"""
        return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


    @app.get("/redoc")
    async def get_documentation():
        """Endpoint to serve ReDoc for API documentation"""
        return get_redoc_html(openapi_url="/openapi.json", title="redoc")


    return app 