import os
from ..pubsub import decode_pubsub_message
from langfuse import Langfuse
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

    if 'trace_id' not in message_data:
        raise ValueError('No trace_id found in message data')

    trace_id = message_data.pop('trace_id', None)

    return do_evals(trace_id, eval_funcs, **message_data)


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
 
    # Fetch the latest trace (or modify as needed to fetch a specific trace)
    trace = langfuse.get_trace(id=trace_id)

    if trace.output is None:
        raise ValueError("Trace {trace.name} had no generated output, it was skipped")

    # Run the evaluation functions
    eval_results = []
    for eval_func in eval_funcs:
        eval_result = eval_func(trace)  # Assuming eval_func returns a dict with 'score' and 'reason'
        eval_results.append(eval_result)

        eval_name = eval_func.__name__

        if 'score' and 'reason' not in eval_result:
            raise ValueError(f"Trace {trace.name} using {eval_name=} did not return a dict with 'score' and 'reason': {eval_result=}")
        
        log.info(f"TraceId {trace.id} with name {trace.name} had {eval_name=} with score {eval_result=}")
        
        # Submit the evaluation to Langfuse
        langfuse.score(
            trace_id=trace.id,
            name=eval_name,  # Use the function name as the evaluation name
            value=eval_result["score"],
            comment=eval_result["reason"],
            **kwargs
        )
    
    return {"trace_id": trace.id, "eval_results": eval_results}


