import json
from ..logging import setup_logging

logging = setup_logging()

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
    logging.info(f'Lines: {lines}')

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
        if line.startswith('event: data'):
            json_str = accumulate_json_lines(lines, i + 1)
            yield from parse_json_data(json_str)
        elif line.startswith('event: metadata'):
            logging.info(f"Found event metadata: {line}")
        elif line.startswith('event: error'):
            logging.error(f"Error in stream line: {line}")
            yield line
        elif line.startswith('event:'):
            logging.info(f"Found langserve non-data event: {line}")



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
                logging.info("No 'content' found - sending full JSON data")
                yield json_data
            else:
                yield content
    except json.JSONDecodeError as err:
        logging.error(f"JSON decoding error: {err} - JSON string was: '{json_str}'")
        yield json_str

def accumulate_json_lines(lines, start_index):
    """
    Accumulate JSON string parts from a list of lines starting at a given index.

    :param lines: The list of lines containing the JSON data.
    :param start_index: The index to start accumulation from.
    :return: The accumulated JSON string.
    """
    json_str_accumulator = ""
    for line in lines[start_index:]:
        if line.startswith('data:'):
            json_str_accumulator += line[len('data:'):].strip()
        else:
            break
    return json_str_accumulator

