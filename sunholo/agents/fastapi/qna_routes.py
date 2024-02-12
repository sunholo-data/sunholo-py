from fastapi import FastAPI, Request, Response, APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
import json
import traceback
import asyncio

from pydantic import BaseModel
from typing import Optional

from ...agents import extract_chat_history, handle_special_commands
from ...qna.parsers import parse_output
from ...streaming import start_streaming_chat_async
from ...archive import archive_qa
from ...logging import setup_logging

logging = setup_logging()

app = FastAPI()

class VACRequest(BaseModel):
    user_input: str
    chat_history: Optional[list] = None
    stream_wait_time: Optional[int] = 7
    stream_timeout: Optional[int] = 120
    message_author: Optional[str] = None
    image_url: Optional[str] = None



def create_stream_qa_endpoint(stream_interpreter):
    async def stream_qa(vector_name: str, request: VACRequest):
        user_input = request.user_input.strip()
        paired_messages = extract_chat_history(request.chat_history)

        command_response = handle_special_commands(user_input, vector_name, paired_messages)
        if command_response is not None:
            return JSONResponse(content=command_response)

        logging.info(f'Streaming data with stream_wait_time: {request.stream_wait_time} and stream_timeout: {request.stream_timeout}')

        async def generate_response_content():
            async for chunk in start_streaming_chat_async(user_input,
                                                            vector_name=vector_name,
                                                            qna_func=stream_interpreter,
                                                            chat_history=paired_messages,
                                                            wait_time=request.stream_wait_time,
                                                            timeout=request.stream_timeout,
                                                            message_author=request.message_author):
                if isinstance(chunk, dict) and 'answer' in chunk:
                    archive_qa(chunk, vector_name)
                    yield f"###JSON_START###{json.dumps(chunk)}###JSON_END###"
                    break
                else:
                    yield chunk

        return StreamingResponse(generate_response_content(), media_type='text/plain')

    return stream_qa

def create_process_qna_endpoint(qna_interpreter):
    async def process_qna(vector_name: str, request: VACRequest):
        user_input = request.user_input.strip()
        paired_messages = extract_chat_history(request.chat_history)

        command_response = handle_special_commands(user_input, vector_name, paired_messages)
        if command_response is not None:
            return JSONResponse(content=command_response)

        try:

            if asyncio.iscoroutinefunction(qna_interpreter):
                bot_output = await qna_interpreter(user_input, vector_name, chat_history=paired_messages, message_author=request.message_author)
            else:
                bot_output = qna_interpreter(user_input, vector_name, chat_history=paired_messages, message_author=request.message_author)

            bot_output = parse_output(bot_output)
            archive_qa(bot_output, vector_name)
        except Exception as err:
            bot_output = {'answer': f'QNA_ERROR: An error occurred while processing /qna/{vector_name}: {str(err)} traceback: {traceback.format_exc()}'}
        
        logging.info(f'==LLM Q:{user_input} - A:{bot_output["answer"]}')
        
        return JSONResponse(content=bot_output)
    return process_qna

def register_qna_fastapi_routes(app: FastAPI, stream_interpreter, qna_interpreter):
    router = APIRouter()

    # Register your routes on the router
    router.add_api_route('/qna/streaming/{vector_name}', create_stream_qa_endpoint(stream_interpreter), methods=['POST'])
    router.add_api_route('/qna/{vector_name}', create_process_qna_endpoint(qna_interpreter), methods=['POST'])

    # Include the router in the main FastAPI application
    app.include_router(router)

