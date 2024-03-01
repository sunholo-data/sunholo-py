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
    for i, line in enumerate(lines):
        if line.startswith('event: data'):
            # Next line should contain the JSON
            json_line_index = i + 1
            if json_line_index < len(lines):
                json_line = lines[json_line_index]
                logging.info(f"json_line - {json_line}")
                if json_line.startswith('data:'):
                    json_str = json_line[len('data:'):].strip()
                    try:
                        json_data = json.loads(json_str)
                        if isinstance(json_data, str):
                            # Strip the quotes and yield
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
                else:
                    logging.warning("Could not find 'data:' line after 'event: data'")
        if line.startswith('event: metadata'):
            logging.info(f"Found event metadata: {line}")
        elif line.startswith('event: error'):
            logging.error(f"Error in stream line: {line}")
            yield line
        elif line.startswith('event:'):
            logging.info(f"Found langserve non-data event: {line}")

