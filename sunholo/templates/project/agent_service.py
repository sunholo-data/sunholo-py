
from sunholo.utils import ConfigManager
from sunholo.vertex import (
    init_genai,
)

from tools.your_agent import get_quarto, quarto_content, QuartoProcessor

from my_log import log

init_genai()

# kwargs supports - image_uri, mime
def vac_stream(question: str, vector_name:str, chat_history=[], callback=None, **kwargs):
    
    config=ConfigManager(vector_name)
    processor = QuartoProcessor(config)

    orchestrator = get_quarto(config, processor)
    if not orchestrator:
        msg = f"No quarto model could be configured for {vector_name}"
        log.error(msg)
        callback.on_llm_end(response=msg)
        return {"answer": msg}

    chat = orchestrator.start_chat()

    guardrail = 0
    guardrail_max = kwargs.get('max_steps', 10)
    big_text = ""
    usage_metadata = None
    functions_called = []
    result=None
    last_responses=None
    while guardrail < guardrail_max:

        content = quarto_content(question, chat_history)
        log.info(f"# Loop [{guardrail}] - {content=}")
        response = chat.send_message(content, stream=True)
        this_text = "" # reset for this loop
        log.debug(f"[{guardrail}] {response}")

        for chunk in response:
            try:
                log.debug(f"[{guardrail}] {chunk=}")
                # Check if 'text' is an attribute of chunk and if it's a string
                if hasattr(chunk, 'text') and isinstance(chunk.text, str):
                    token = chunk.text
                else:
                    function_names = []
                    try:
                        for part in chunk.candidates[0].content.parts:
                            if fn := part.function_call:
                                params = {key: val for key, val in fn.args.items()}
                                func_args = ",".join(f"{key}={value}" for key, value in params.items())
                                log.info(f"Found function call: {fn.name}({func_args})")
                                function_names.append(f"{fn.name}({func_args})")
                                functions_called.append(f"{fn.name}({func_args})")
                    except Exception as err:
                        log.warning(f"{str(err)}")

                    token = ""  # Handle the case where 'text' is not available
                    
                    if processor.last_api_requests_and_responses:
                        if processor.last_api_requests_and_responses != last_responses:
                            last_responses = processor.last_api_requests_and_responses
                        for last_response in last_responses:
                            result=None # reset for this function response
                            if last_response:
                                log.info(f"[{guardrail}] {last_response=}")
                                
                                # Convert the last_response to a string by extracting relevant information
                                function_name = last_response[0]
                                arguments = last_response[1]
                                result = last_response[2]
                                func_args = ",".join(f"{key}={value}" for key, value in arguments.items())

                                if f"{function_name}({func_args})" not in function_names:
                                    log.warning(f"skipping {function_name}({func_args}) as not in execution list")
                                    continue

                                token = f"\n## Loop [{guardrail}] Function call: {function_name}({func_args}):\n"

                                if function_name == "decide_to_go_on":
                                    token += f"# go_on={result}\n"
                                else:
                                    log.info("Adding result for: {function_name}")
                                    token += result

                callback.on_llm_new_token(token=token)
                big_text += token
                this_text += token
                
                if not usage_metadata:
                    chunk_metadata = chunk.usage_metadata
                    usage_metadata = {
                        "prompt_token_count": chunk_metadata.prompt_token_count,
                        "candidates_token_count": chunk_metadata.candidates_token_count,
                        "total_token_count": chunk_metadata.total_token_count,
                    }

            except ValueError as err:
                callback.on_llm_new_token(token=str(err))
        
        # change response to one with executed functions
        response = processor.process_funcs(response)

        if this_text:
            chat_history.append(("<waiting for ai>", this_text))
            log.info(f"[{guardrail}] Updated chat_history: {chat_history}")

        go_on_check = processor.check_function_result("decide_to_go_on", False)
        if go_on_check:
            log.info("Breaking agent loop")
            break
        
        guardrail += 1
        if guardrail > guardrail_max:
            log.warning("Guardrail kicked in, more than 10 loops")
            break

    callback.on_llm_end(response=big_text)
    log.info(f"orchestrator.response: {big_text}")

    metadata = {
        "question:": question,
        "chat_history": chat_history,
        "usage_metadata": usage_metadata,
        "functions_called": functions_called
    }

    return {"answer": big_text or "No answer was given", "metadata": metadata}


def vac(question: str, vector_name: str, chat_history=[], **kwargs):
    # Create a callback that does nothing for streaming if you don't want intermediate outputs
    class NoOpCallback:
        def on_llm_new_token(self, token):
            pass
        def on_llm_end(self, response):
            pass

    # Use the NoOpCallback for non-streaming behavior
    callback = NoOpCallback()

    # Pass all arguments to vac_stream and use the final return
    result = vac_stream(
        question=question, 
        vector_name=vector_name, 
        chat_history=chat_history, 
        callback=callback, 
        **kwargs
    )

    return result


