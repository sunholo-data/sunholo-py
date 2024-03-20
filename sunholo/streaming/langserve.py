import json
from ..logging import setup_logging

log = setup_logging("langserve_streaming")

# Global accumulation buffer for JSON parts, indexed by run_id
json_accumulation_buffer = {}

async def parse_langserve_token_async(token):
    """
    Asynchronously parses the token to accumulate content from JSON for 'event: data' events,
    handling JSON strings split between two tokens.

    Args:
        token (str or bytes): The token to parse.

    Yields:
        str: An accumulated content from 'event: data'.
    """
    global json_accumulation_buffer
    
    # Decode bytes to string if necessary
    if isinstance(token, bytes):
        token = token.decode('utf-8')

    # Split the token into lines
    lines = token.split('\r\n')
    log.info(f'Lines: {lines}')

    current_run_id = None

    # Check for run_id in the metadata event
    for line in lines:
        if line.startswith('event: metadata'):
            metadata = json.loads(line.split('data:', 1)[1].strip())
            current_run_id = metadata.get('run_id')
            if current_run_id not in json_accumulation_buffer:
                json_accumulation_buffer[current_run_id] = ""
            break

    # Use process_langserve_lines to process each line, passing the current run_id
    async for content in process_langserve_lines_async(lines, current_run_id):
        yield content

async def process_langserve_lines_async(lines, run_id):
    """
    Asynchronously process lines from langserve, parsing JSON data as needed.
    This is an async wrapper for process_langserve_lines to fit into async processing.

    :param lines: The list of lines to process.
    :param run_id: The current run_id to index the accumulation buffer.
    """
    # Assuming process_langserve_lines itself doesn't need to be async,
    # iterate over its output in an async for loop.
    for content in process_langserve_lines(lines, run_id):
        yield content

def parse_langserve_token(token):
    """
    Parses the token to accumulate content from JSON for 'event: data' events,
    handling JSON strings split between two tokens.

    Args:
        token (str or bytes): The token to parse.

    Returns:
        Generator of str: A generator that yields accumulated contents from 'event: data'.
    """
    global json_accumulation_buffer
    
    # Decode bytes to string if necessary
    if isinstance(token, bytes):
        token = token.decode('utf-8')

    # Split the token into lines
    lines = token.split('\r\n')
    log.info(f'Lines: {lines}')

    current_run_id = None

    # Check for run_id in the metadata event
    for line in lines:
        if line.startswith('event: metadata'):
            metadata = json.loads(line.split('data:', 1)[1].strip())
            current_run_id = metadata.get('run_id')
            if current_run_id not in json_accumulation_buffer:
                json_accumulation_buffer[current_run_id] = ""
            break

    # Use process_langserve_lines to process each line, passing the current run_id
    for content in process_langserve_lines(lines, current_run_id):
        yield content

def process_langserve_lines(lines, run_id):
    """
    Process lines from langserve, parsing JSON data as needed.

    :param lines: The list of lines to process.
    :param run_id: The current run_id to index the accumulation buffer.
    """
    for i, line in enumerate(lines):
        log.debug(f'Line {i}: {line}')
        if line.startswith('event: data'):
            json_str = accumulate_json_lines(lines, i + 1, run_id)
            if json_str:
                yield from parse_json_data(json_str)
        elif line.startswith('event: error'):
            log.error(f"Error in stream line: {line}")
            yield line
        elif line.startswith('event:'):
            log.info(f"Found langserve non-data event: {line}")

def accumulate_json_lines(lines, start_index, run_id):
    """
    Accumulate and parse JSON string parts from a list of lines starting
    at a given index, using a run_id-based buffer to handle splits across tokens.

    :param lines: The list of lines containing the JSON data.
    :param start_index: The index to start accumulation from.
    :param run_id: The run_id for the current JSON accumulation.
    :return: The accumulated JSON string if a complete JSON object is formed, 
             or None if accumulation should continue.
    """
    global json_accumulation_buffer
    accumulator = json_accumulation_buffer.get(run_id, "")
    
    for line in lines[start_index:]:
        if line.startswith('data:'):
            the_data = line[len('data:'):].strip()
            accumulator += the_data
        elif accumulator and not line.startswith('event:'):
            accumulator += line.strip()

        # Attempt to parse the accumulated JSON string periodically
        try:
            parsed_json = json.loads(accumulator)
            # If no exception is raised, a complete JSON object has been formed
            json_accumulation_buffer[run_id] = ""  # Reset buffer for this run_id
            return json.dumps(parsed_json)  # Return the complete JSON string
        except json.JSONDecodeError:
            continue  # Continue accumulating if JSON is incomplete

    # Update the buffer with the current accumulation state
    json_accumulation_buffer[run_id] = accumulator
    return None  # Indicate continuation if a complete object has not been formed

def parse_json_data(json_str):
    """
    Attempt to parse a JSON string and yield the appropriate content or error.

    :param json_str: The JSON string to parse.
    """
    try:
        json_data = json.loads(json_str)
        yield json.dumps(json_data)  # Yielding the JSON data for simplicity
    except json.JSONDecodeError as err:
        log.error(f"JSON decoding error: {err} - JSON string was: '{json_str}'")
        yield json_str  # In case of error, yield the raw string for debugging
