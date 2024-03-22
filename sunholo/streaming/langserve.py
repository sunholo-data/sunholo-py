import json
from ..logging import setup_logging

log = setup_logging("langserve_streaming")

# Global accumulation buffer for JSON parts, indexed by run_id
json_accumulation_buffer = {}
json_accumulation_flag = False

async def parse_langserve_token_async(token):
    """
    Asynchronously parses the token to accumulate content from JSON for 'event: data' events,
    handling JSON strings split between two tokens.

    Args:
        token (str or bytes): The token to parse.

    Yields:
        str: An accumulated content from 'event: data'.
    """
    
    # Decode bytes to string if necessary
    if isinstance(token, bytes):
        token = token.decode('utf-8')

    if json_accumulation_flag:
        parsed_token = token
        # its just one big string needing to be added, with some :pings one the end
        last_closing_bracket_index = token.rfind('}')
        if last_closing_bracket_index != -1:
            # Slice the string to get only the JSON part
            parsed_token = token[:last_closing_bracket_index+1]

        lines = [parsed_token]
    else:
        # Split the token into lines
        lines = token.split('\r\n')
    log.info(f'Lines: {lines}')

    # Check for run_id in the metadata event
    current_run_id = set_metadata_value(lines)

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

def set_metadata_value(lines):
    global json_accumulation_buffer
    current_run_id = None
    for line in lines:
        if line.startswith('event: metadata'):
            # Find the next line which starts with "data:", assuming it's immediately after the event line
            data_line_index = lines.index(line) + 1
            if data_line_index < len(lines):
                data_line = lines[data_line_index]
                if data_line.startswith('data:'):
                    try:
                        metadata = json.loads(data_line[len('data:'):].strip())
                        current_run_id = metadata.get('run_id')
                    except json.JSONDecodeError as e:
                        log.error(f"Error decoding metadata JSON: {e}")
            break  # Break after processing the first metadata event
    
    return current_run_id


def parse_langserve_token(token):
    """
    Parses the token to accumulate content from JSON for 'event: data' events,
    handling JSON strings split between two tokens.

    Args:
        token (str or bytes): The token to parse.

    Returns:
        Generator of str: A generator that yields accumulated contents from 'event: data'.
    """
    
    # Decode bytes to string if necessary
    if isinstance(token, bytes):
        token = token.decode('utf-8')

    if json_accumulation_flag:
        parsed_token = token
        # its just one big string needing to be added, with some :pings one the end
        last_closing_bracket_index = token.rfind('}')
        if last_closing_bracket_index != -1:
            # Slice the string to get only the JSON part
            parsed_token = token[:last_closing_bracket_index+1]

        lines = [parsed_token]
    else:
        # Split the token into lines
        lines = token.split('\r\n')
    log.info(f'Lines: {lines}')

    # Check for run_id in the metadata event
    current_run_id = set_metadata_value(lines)

    # Use process_langserve_lines to process each line, passing the current run_id
    for content in process_langserve_lines(lines, current_run_id):
        yield content

def process_langserve_lines(lines, run_id):
    """
    Process lines from langserve, parsing JSON data as needed.

    :param lines: The list of lines to process.
    :param run_id: The current run_id to index the accumulation buffer.
    """
    global json_accumulation_flag

    for i, line in enumerate(lines):
        #log.debug(f'Line {i}: {line}')
        if json_accumulation_flag:
            log.info('Accumulation flag active for line:\n{line}')
            json_data = accumulate_json_lines(lines, i, run_id)
            if json_data:
                log.info(f'Got accumulated json_str to parse: {json_data}')
                yield from parse_json_data(json_data)            
        if line.startswith('event: data'):
            #log.debug(f'Sending {i} {line} to accumulator')
            json_data = accumulate_json_lines(lines, i + 1, run_id)
            if json_data:
                #log.info(f'Got json_str to parse: {json_data}')
                yield from parse_json_data(json_data)
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
    global json_accumulation_flag
    accumulator = ""

    if run_id:
        log.info(f"Got run_id: {run_id}")

    if json_accumulation_flag:
        accumulator = json_accumulation_buffer

    if accumulator:
        log.info(f"Using old accumulator for {run_id}")
    
    for line in lines[start_index:]:
        if line.startswith('data:'):
            #log.debug(f'stripping line: {line}')
            the_data = line[len('data:'):].strip()
            #log.debug(f'line_data: {the_data}')
            accumulator += the_data
        elif accumulator and not line.startswith('event:'):
            no_pings = line.split(': ping')[0].strip()
            log.info(f'Adding old accumulator line: {no_pings}')
            accumulator += no_pings

        #log.debug(f'accumulator: {accumulator}')
        # Attempt to parse the accumulated JSON string periodically
        try:
            parsed_json = json.loads(accumulator)
            # If no exception is raised, a complete JSON object has been formed
            json_accumulation_buffer = ""  # Reset buffer for this run_id
            json_accumulation_flag = False
            accumulator = ""
            return parsed_json  # Return the complete JSON string
        except json.JSONDecodeError:
            log.warning(f'Did not parse json for {accumulator}')
            continue  # Continue accumulating if JSON is incomplete

    # Update the buffer with the current accumulation state
    json_accumulation_buffer = accumulator
    json_accumulation_flag = True
    log.info(f'Did not finish accumulator run_id {run_id} - waiting for next token')
    return None  # Indicate continuation if a complete object has not been formed

def parse_json_data(json_data: dict):
    """
    Attempt to parse a JSON string and yield the appropriate content or error.

    :param json_data: The dict string to parse.

    yields: 
        str if within content key
        dict if no content key
        str if error in decoding json

    """
    try:
        content = json_data.get('content')
        if content:
            #log.debug(f'Yield content: {content}')
            yield content
        else:
            log.debug(f'No content found, yielding all json data dict: {json_data}')
            yield json_data # Yielding all JSON data
    except json.JSONDecodeError as err:
        log.error(f"JSON decoding error: {err} - JSON string was: '{json_data}'")
        yield "Parsing JSON error - check logs"  # In case of error, yield the raw string for debugging
