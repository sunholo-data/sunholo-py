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
                        # Extract "content" from JSON
                        content = None
                        try:
                            content = json_data.get("content")
                        except AttributeError as err:
                            logging.info(f"No 'content' found - sending full {json_str}")
                            yield json_str
                        if content:
                            yield content
                    except json.JSONDecodeError as err:
                        logging.error(f"Langserve JSON decoding error: {err}")
                        yield line
                        # Optionally append the original line in case of an error
                else:
                    logging.warning("Could not find data:")
        elif line.startswith('event: error'):
            logging.error(f"Error in stream line: {line}")
            yield line
        elif line.startswith('event:'):
            logging.info(f"Found langserve non-data event: {line}")