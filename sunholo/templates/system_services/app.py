import os
import traceback

# app.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from my_log import log

app = FastAPI()

@app.get("/")
def home():
    """Simple endpoint to indicate that the app is running."""
    return {"message": "Hello, service!"}

@app.post("/system_service/<param>")
async def system_service(request: Request):
    """
    Pubsub message parsed and sent to Langfuse ID server
    """
    data = await request.json()

    try:
        #TODO: add stuff here
        meta = ""
        return {"status": "success", "message": meta}
    except Exception as err:
        log.error(f'EVAL_ERROR: Error when sending {data} to /pubsub_to_langfuse: {str(err)} traceback: {traceback.format_exc()}')
        return JSONResponse(status_code=200, content={"status": "error", "message": f'{str(err)} traceback: {traceback.format_exc()}'})

@app.post("/test_endpoint")
async def test_me(request: Request):
    """
    Endpoint to send trace_ids directly for evals then sent to Langfuse ID server
    """
    data = await request.json()

    try:
        #TODO: do something here
        meta = ""
        return {"status": "success", "message": meta}
    except Exception as err:
        log.error(f'EVAL_ERROR: Error when sending {data} to /direct_evals: {str(err)} traceback: {traceback.format_exc()}')
        return JSONResponse(status_code=500, content={"status": "error", "message": f'{str(err)} traceback: {traceback.format_exc()}'})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)