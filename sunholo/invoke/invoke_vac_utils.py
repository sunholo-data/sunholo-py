import json
import requests

from pathlib import Path

from ..logging import log
from ..agents import send_to_qa
from ..qna.parsers import parse_output
from ..streaming import generate_proxy_stream

def invoke_vac_qa(vac_input: dict, vac_name: str, chat_history=[], stream=False):
    """
    This lets VACs call other VAC Q&A endpoints within their code
    """

    if 'user_input' not in vac_input:
        raise ValueError('vac_input must contain at least "user_input" key - got {vac_input}')

    user_id = vac_input.get('user_id')
    session_id = vac_input.get('session_id')
    image_uri = vac_input.get('image_url') or vac_input.get('image_uri')

    if not stream:
        log.info(f'Batch invoke_vac_qa with {vac_input=}')
        vac_response = send_to_qa(
            vac_input["user_input"],
            vector_name=vac_name,
            chat_history=chat_history,
            message_author=user_id,
            #TODO: populate these
            image_url=image_uri,
            source_filters=None,
            search_kwargs=None,
            private_docs=None,
            whole_document=False,
            source_filters_and_or=False,
            # system kwargs
            configurable={
                "vector_name": vac_name,
            },
            user_id=user_id,
            session_id=session_id, 
            message_source="sunholo.invoke_vac_qa.invoke")
        
        # ensures {'answer': answer}
        answer = parse_output(vac_response)
        chat_history.append({"name": "Human", "content": vac_input})
        chat_history.append({"name": "AI", "content": answer})
        answer["chat_history"] = chat_history
        
        return answer
    
    log.info(f"Streaming invoke_vac_qa with {vac_input=}")
    def stream_response():
        generate = generate_proxy_stream(
                send_to_qa,
                vac_input["user_input"],
                vector_name=vac_name,
                chat_history=chat_history,
                generate_f_output=lambda x: x,  # Replace with actual processing function
                stream_wait_time=0.5,
                stream_timeout=120,
                message_author=user_id,
                #TODO: populate these
                image_url=image_uri,
                source_filters=None,
                search_kwargs=None,
                private_docs=None,
                whole_document=False,
                source_filters_and_or=False,
                # system kwargs
                configurable={
                    "vector_name": vac_name,
                },
                user_id=user_id,
                session_id=session_id, 
                message_source="sunholo.invoke_vac_qa.stream"
        )
        for part in generate():
            yield part

    answer = ""

    for token in stream_response():
        if isinstance(token, bytes):
            token = token.decode('utf-8')
            yield token
        if isinstance(token, dict):
            # ?
            pass
        elif isinstance(token, str):
            answer += token

    if answer:
        chat_history.append({"name": "Human", "content": vac_input})
        chat_history.append({"name": "AI", "content": answer})

    return chat_history

def invoke_vac(service_url, data, vector_name=None, metadata=None, is_file=False):
    """
    This lets a VAC be invoked by directly calling its URL, used for file uploads
    """
    try:
        if is_file:
            log.info("Uploading file...")
            # Handle file upload
            if not isinstance(data, Path) or not data.is_file():
                raise ValueError("For file uploads, 'data' must be a Path object pointing to a valid file.")
            
            files = {
                'file': (data.name, open(data, 'rb')),
            }
            form_data = {
                'vector_name': vector_name,
                'metadata': json.dumps(metadata) if metadata else '',
            }

            response = requests.post(service_url, files=files, data=form_data)
        else:
            log.info("Uploading JSON...")
            try:
                if isinstance(data, dict):
                    json_data = data
                else:
                    json_data = json.loads(data)
            except json.JSONDecodeError as err:
                log.error(f"[bold red]ERROR: invalid JSON: {str(err)} [/bold red]")
                raise err
            except Exception as err:
                log.error(f"[bold red]ERROR: could not parse JSON: {str(err)} [/bold red]")
                raise err

            log.debug(f"Sending data: {data} or json_data: {json.dumps(json_data)}")
            # Handle JSON data
            headers = {"Content-Type": "application/json"}
            response = requests.post(service_url, headers=headers, data=json.dumps(json_data))

        response.raise_for_status()

        the_data = response.json()
        log.info(the_data)

        return the_data
    
    except requests.exceptions.RequestException as e:
        log.error(f"[bold red]ERROR: Failed to invoke VAC: {e}[/bold red]")
        raise e
    except Exception as e:
        log.error(f"[bold red]ERROR: An unexpected error occurred: {e}[/bold red]")
        raise e
