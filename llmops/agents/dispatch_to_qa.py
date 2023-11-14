#   Copyright [2023] [Sunholo ApS]
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
import logging
import requests
import aiohttp

from .route import route_endpoint

def send_to_qa(user_input, vector_name, chat_history, message_author=None, stream=False):

    # {'stream': '', 'invoke': ''}
    endpoints = route_endpoint(vector_name)

    if stream:
        qna_endpoint = endpoints["stream"]
    else:
        qna_endpoint = endpoints["invoke"]

    qna_data = {
        'user_input': user_input,
        'chat_history': chat_history,
        'message_author': message_author
    }

    try:
        logging.info(f"Sending to {qna_endpoint} this data: {qna_data}")
        qna_response = requests.post(qna_endpoint, json=qna_data, stream=stream)
        qna_response.raise_for_status()

        if stream:
            # If streaming, return a generator that yields response content chunks
            def content_generator():
                for chunk in qna_response.iter_content(chunk_size=8192):
                    yield chunk
            return content_generator()
        else:
            # Otherwise, return the JSON response directly
            return qna_response.json()

    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        error_message = f"There was an error processing your request. Please try again later. {str(err)}"
        if stream:
            return iter([error_message])
        else:
            return {"answer": error_message}

    except Exception as err:
        logging.error(f"Other error occurred: {str(err)}")
        error_message = f"Something went wrong. Please try again later. {str(err)}"
        if stream:
            return iter([error_message])
        else:
            return {"answer": error_message}

async def send_to_qa_async(user_input, vector_name, chat_history):

    # {'stream': '', 'invoke': ''}
    endpoints = route_endpoint(vector_name)

    qna_endpoint = endpoints['invoke']
    qna_data = {
        'user_input': user_input,
        'chat_history': chat_history,
    }
    logging.info(f"Sending to {qna_endpoint} this data: {qna_data}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(qna_endpoint, json=qna_data) as resp:
            qna_response = await resp.json()

    logging.info(f"Got back QA response: {qna_response}")
    return qna_response
