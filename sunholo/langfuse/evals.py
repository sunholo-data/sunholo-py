import os
import json

from ..pubsub import decode_pubsub_message
from langfuse import Langfuse
import traceback


from ..custom_logging import log

# Example of how eval_funcs might be structured
def eval_length(trace):
    """
    An example of how eval_funcs might be structured.
    Must output a dictionary with 'score' and 'reason' keys.
    """
    # Example evaluation logic
    return {
        "score": len(trace.output),  # Example: length of the output text
        "reason": "Length of the output text"
    }

def pubsub_to_evals(data: dict, eval_funcs: list=[eval_length]) -> dict:
    """
    Process a Pub/Sub message and run evaluations using the provided evaluation functions.

    Args:
        data (dict): The Pub/Sub message data.
        eval_funcs (list): A list of evaluation functions to run. Each function should return a dict with 'score' and 'reason'.
    """
    
    # Decode the message
    message_data, metadata, vector_name = decode_pubsub_message(data)

    try:
        the_json = json.loads(message_data)
    except Exception as e:
        log.error(f"Could not load message {message_data} as JSON - {str(e)}")
        return None, {"metadata": f"Could not load message as JSON - {str(e)}"}

    if 'trace_id' not in the_json:
        raise ValueError(f'No trace_id found in json data {the_json=}')

    trace_id = the_json.pop('trace_id', None)

    return do_evals(trace_id, eval_funcs, **the_json)


def direct_langfuse_evals(data, eval_funcs: list=[eval_length]):
    if 'trace_id' not in data:
        raise ValueError('No trace_id found in data')
    trace_id = data.pop('trace_id', None)

    return do_evals(trace_id, eval_funcs, **data)


def do_evals(trace_id, eval_funcs: list=[eval_length], **kwargs) -> dict:
    # Initialize Langfuse with environment variables
    langfuse = Langfuse(
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        host=os.environ["LANGFUSE_HOST"]
    )
 
    log.info(f"do_evals langfuse with {kwargs=}")
    # Fetch the latest trace (or modify as needed to fetch a specific trace)
    trace = langfuse.get_trace(id=trace_id)

    if trace.output is None:
        raise ValueError("Trace {trace.name} had no generated output, it was skipped")

    # Run the evaluation functions
    # an eval_response can have multiple eval_results
    eval_responses = []
    for eval_func in eval_funcs:
        try:
            eval_response = eval_func(trace, **kwargs)  # Assuming eval_func returns a dict with 'score' and 'reason'
        except Exception as e:
            eval_response = {"score": 0, "reason":f"ERROR: {str(e)} traceback: {traceback.format_exc()}"}
        eval_responses.append(eval_response)

        eval_name = eval_func.__name__

        if isinstance(eval_response, list):
            eval_results = eval_response
        else:
            eval_results = [eval_response]
        
        for eval_result in eval_results:

            if 'score' and 'reason' not in eval_result:
                log.error(f"Trace {trace.name} using {eval_name=} did not return a dict with 'score' and 'reason': {eval_result=}")
                eval_result = {"score": 0, "reason": f"malformed eval_result: {eval_result}"}
            
            log.info(f"TraceId {trace.id} with name {trace.name} had {eval_name=} with score {eval_result=}")
            
            # Submit the evaluation to Langfuse
            langfuse.score(
                trace_id=trace.id,
                name=eval_name,  # Use the function name as the evaluation name
                value=eval_result["score"],
                comment=eval_result["reason"],
                **kwargs
            )
    
    return {"trace_id": trace.id, "eval_results": eval_responses}


