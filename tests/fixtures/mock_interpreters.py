#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import asyncio
import time
from typing import List, Optional, Any


async def mock_async_stream_interpreter(
    question: str,
    vector_name: str,
    chat_history: Optional[List] = None,
    callback: Any = None,
    **kwargs
) -> dict:
    """
    Mock async interpreter that simulates streaming with callbacks.
    
    This mimics a real LLM that streams tokens via callbacks.
    """
    tokens = ["Hello", " ", "from", " ", "async", " ", "interpreter", "!", " ", 
              "You", " ", "asked", ":", " ", f'"{question}"']
    
    # Simulate streaming tokens via callback
    for token in tokens:
        if callback:
            if hasattr(callback, 'async_on_llm_new_token'):
                await callback.async_on_llm_new_token(token)
            elif hasattr(callback, 'on_llm_new_token'):
                callback.on_llm_new_token(token)
        await asyncio.sleep(0.05)  # Simulate processing delay
    
    # Final response
    full_answer = "".join(tokens)
    final_response = {
        "answer": full_answer,
        "source_documents": [
            {
                "page_content": "Mock source content",
                "metadata": {"source": "mock_source.txt", "page": 1}
            }
        ]
    }
    
    if callback:
        if hasattr(callback, 'async_on_llm_end'):
            await callback.async_on_llm_end(final_response)
        elif hasattr(callback, 'on_llm_end'):
            callback.on_llm_end(final_response)
    
    return final_response


def mock_sync_stream_interpreter(
    question: str,
    vector_name: str,
    chat_history: Optional[List] = None,
    callback: Any = None,
    **kwargs
) -> dict:
    """
    Mock sync interpreter that simulates streaming with callbacks.
    
    This mimics a real LLM that streams tokens via callbacks.
    """
    tokens = ["Hello", " ", "from", " ", "sync", " ", "interpreter", "!", " ",
              "You", " ", "asked", ":", " ", f'"{question}"']
    
    # Simulate streaming tokens via callback
    for token in tokens:
        if callback and hasattr(callback, 'on_llm_new_token'):
            callback.on_llm_new_token(token)
        time.sleep(0.05)  # Simulate processing delay
    
    # Final response
    full_answer = "".join(tokens)
    final_response = {
        "answer": full_answer,
        "source_documents": [
            {
                "page_content": "Mock sync source content",
                "metadata": {"source": "mock_sync_source.txt", "page": 1}
            }
        ]
    }
    
    if callback and hasattr(callback, 'on_llm_end'):
        callback.on_llm_end(final_response)
    
    return final_response


async def mock_async_vac_interpreter(
    question: str,
    vector_name: str,
    chat_history: Optional[List] = None,
    **kwargs
) -> dict:
    """
    Mock async VAC interpreter for non-streaming responses.
    """
    await asyncio.sleep(0.1)  # Simulate processing
    
    return {
        "answer": f"Async VAC response to: {question}",
        "source_documents": [
            {
                "page_content": "Mock VAC source",
                "metadata": {"source": "vac_source.txt"}
            }
        ]
    }


def mock_sync_vac_interpreter(
    question: str,
    vector_name: str,
    chat_history: Optional[List] = None,
    **kwargs
) -> dict:
    """
    Mock sync VAC interpreter for non-streaming responses.
    """
    time.sleep(0.1)  # Simulate processing
    
    return {
        "answer": f"Sync VAC response to: {question}",
        "source_documents": [
            {
                "page_content": "Mock sync VAC source",
                "metadata": {"source": "sync_vac_source.txt"}
            }
        ]
    }


async def mock_async_stream_with_heartbeat(
    question: str,
    vector_name: str,
    chat_history: Optional[List] = None,
    callback: Any = None,
    **kwargs
) -> dict:
    """
    Mock async interpreter that includes heartbeat tokens.
    """
    tokens = ["Starting", " ", "response", "..."]
    
    for i, token in enumerate(tokens):
        if callback:
            if hasattr(callback, 'async_on_llm_new_token'):
                await callback.async_on_llm_new_token(token)
        
        # Send heartbeat every 2 tokens
        if i % 2 == 0 and callback:
            heartbeat = f"[[HEARTBEAT]]Processing token {i}[[/HEARTBEAT]]"
            if hasattr(callback, 'async_on_llm_new_token'):
                await callback.async_on_llm_new_token(heartbeat)
        
        await asyncio.sleep(0.1)
    
    final_response = {
        "answer": "".join(tokens),
        "source_documents": []
    }
    
    if callback and hasattr(callback, 'async_on_llm_end'):
        await callback.async_on_llm_end(final_response)
    
    return final_response


async def mock_async_stream_with_error(
    question: str,
    vector_name: str,
    chat_history: Optional[List] = None,
    callback: Any = None,
    **kwargs
) -> dict:
    """
    Mock async interpreter that raises an error mid-stream.
    """
    tokens = ["Starting", " ", "to", " ", "process"]
    
    for token in tokens[:3]:  # Stream first 3 tokens
        if callback and hasattr(callback, 'async_on_llm_new_token'):
            await callback.async_on_llm_new_token(token)
        await asyncio.sleep(0.05)
    
    # Simulate an error
    raise ValueError("Mock error during streaming")


def mock_sync_stream_with_timeout(
    question: str,
    vector_name: str,
    chat_history: Optional[List] = None,
    callback: Any = None,
    **kwargs
) -> dict:
    """
    Mock sync interpreter that simulates a timeout by taking too long.
    """
    tokens = ["This", " ", "will", " ", "timeout"]
    
    for i, token in enumerate(tokens):
        if callback and hasattr(callback, 'on_llm_new_token'):
            callback.on_llm_new_token(token)
        
        # Simulate long delay on 3rd token
        if i == 2:
            time.sleep(5)  # This should trigger timeout if timeout < 5
        else:
            time.sleep(0.1)
    
    return {"answer": "".join(tokens), "source_documents": []}