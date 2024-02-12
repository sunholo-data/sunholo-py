import os
import socketio

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from sunholo.logging import setup_logging

logging = setup_logging()

from fastapi.middleware.cors import CORSMiddleware


def create_fastapi_app():
    """Creates and configures a FastAPI app for image-based Q&A with Socket.IO integration.

    Args:
        image_qna_stream_fn: Streaming Q&A function (likely from gemini.genai)
        image_qna_fn: Non-streaming Q&A function (likely from gemini.genai)

    Returns:
        FastAPI: The configured FastAPI app instance.
    """

    # Create Socket.IO server and FastAPI app 
    sio = socketio.AsyncServer(async_mode='asgi')
    app = FastAPI()
    socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
    app.mount("/ws/socket.io/", socket_app)

    # CORS Configuration 
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Handle Socket.IO events, e.g., a connection
    @sio.event
    async def connect(sid, environ):
        logging.info("Socket.IO client connected", sid)

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

    return app 