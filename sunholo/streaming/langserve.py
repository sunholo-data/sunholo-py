import json
from ..logging import setup_logging

log = setup_logging("langserve_streaming")

def parse_langserve_token(token):
    """
    Parses the token to accumulate content from JSON for 'event: data' events.

    Args:
        token (str or bytes): The token to parse.

    Returns:
        str: A string of accumulated contents from 'event: data'.
    """
    # Decode bytes to string if necessary
    if isinstance(token, bytes):
        token = token.decode('utf-8')

    # Split the token into lines
    lines = token.split('\r\n')
    log.info(f'Lines: {lines}')

    if len(lines) == 1:
        yield token

    # Use process_langserve_lines to process each line
    for content in process_langserve_lines(lines):
        yield content

async def parse_langserve_token_async(token):
    """
    Parses the token to accumulate content from JSON for 'event: data' events.

    Args:
        token (str or bytes): The token to parse.

    Returns:
        str: A string of accumulated contents from 'event: data'.
    """
    # Decode bytes to string if necessary
    if isinstance(token, bytes):
        token = token.decode('utf-8')

    # Split the token into lines
    lines = token.split('\r\n')

    if len(lines) == 1:
        yield token

    # Use process_langserve_lines to process each line
    for content in process_langserve_lines(lines):
        yield content

def process_langserve_lines(lines):
    """
    Process lines from langserve, parsing JSON data as needed.

    :param lines: The list of lines to process.
    """
    for i, line in enumerate(lines):
        log.debug(f'Line {i}: {line}')
        if line.startswith('event: data'):
            json_str = accumulate_json_lines(lines, i + 1)
            if json_str:
                yield from parse_json_data(json_str)
        elif line.startswith('event: metadata'):
            log.info(f"Found event metadata: {line}")
        elif line.startswith('event: error'):
            log.error(f"Error in stream line: {line}")
            yield line
        elif line.startswith('event:'):
            log.info(f"Found langserve non-data event: {line}")



def parse_json_data(json_str):
    """
    Attempt to parse a JSON string and yield the appropriate content or error.

    :param json_str: The JSON string to parse.
    """
    try:
        json_data = json.loads(json_str)
        if isinstance(json_data, str):
            yield json_data.strip('"')
        else:
            content = json_data.get("content")
            if content is None:
                log.info("No 'content' found - sending full JSON data")
                yield json_data
            else:
                yield content
    except json.JSONDecodeError as err:
        log.error(f"JSON decoding error: {err} - JSON string was: '{json_str}'")
        yield json_str

def accumulate_json_lines(lines, start_index):
    """
    Attempt to accumulate and parse JSON string parts from a list of lines starting
    at a given index, supporting JSON data that spans across lines and across multiple
    'event: data' sections, ignoring 'event: metadata' lines during accumulation.

    This approach attempts to parse the accumulating JSON string periodically to
    determine if a complete JSON object has been formed, allowing for more prompt
    handling of simple JSON objects.

    :param lines: The list of lines containing the JSON data.
    :param start_index: The index to start accumulation from.
    :return: The accumulated JSON string if a complete JSON object is formed, 
             or None if accumulation should continue.
    """
    json_str_accumulator = ""
    for line in lines[start_index:]:
        if line.startswith('data: {"content"'):
            json_str = None
            the_data = line[len('data:'):].strip()
            try:
                json_str = json.loads(the_data)
            except json.JSONDecodeError:
                log.debug('Got data: content but not: {line}')
            if json_str:
                content = json_str.get('content')
                if content:
                    return line
        elif line.startswith('data:'):
            the_data = line[len('data:'):].strip()
            json_str_accumulator += the_data
        elif json_str_accumulator and not line.startswith('event:'):
            json_str_accumulator += line.strip()
        elif line.startswith('event: metadata'):
            continue
        elif line.startswith('event:') and not line.startswith('event: data'):
            break

        log.info(f'json_accumulator: {json_str_accumulator}')
        # Attempt to parse the accumulated JSON string periodically
        try:
            json.loads(json_str_accumulator)
            # If no exception is raised, a complete JSON object has been formed
            return json_str_accumulator
        except json.JSONDecodeError:
            # If an exception is raised, continue accumulating
            continue

    # Return the accumulated string if it's potentially a complete JSON object,
    # or None if the loop exited for other reasons (e.g., encountering a new event)
    return json_str_accumulator if json_str_accumulator else None

