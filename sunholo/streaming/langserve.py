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

    for i, line in enumerate(lines):
        if line.startswith('event: data'):
            # Next line should contain the JSON
            json_line_index = i + 1
            if json_line_index < len(lines):
                json_line = lines[json_line_index]
                logging.info(f'JSON line found: {json_line}')
                if json_line.startswith('data:'):
                    json_str = json_line[len('data:'):].strip()
                    logging.info(f'json_str: {json_str}')
                    try:
                        json_data = json.loads(json_str)
                        # Extract "content" from JSON
                        content = json_data.get("content")
                        if content:
                            logging.info(f'JSON content found: {content}')
                            yield content  # Append content to the accumulator
                    except json.JSONDecodeError as e:
                        logging.error(f"Langserve JSON decoding error: {e}")
                        yield line
                        # Optionally append the original line in case of an error
                else:
                    logging.warning("Could not find data:")
        elif line.startswith('event:'):
            logging.info(f"Found langserve non-data event: {line}")
        else:
            logging.warning(f"Unexpected langserve line: {line}")
            yield line


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

    for i, line in enumerate(lines):
        if line.startswith('event: data'):
            # Next line should contain the JSON
            json_line_index = i + 1
            if json_line_index < len(lines):
                json_line = lines[json_line_index]
                if json_line.startswith('data:'):
                    json_str = json_line[len('data:'):].strip()
                    try:
                        json_data = json.loads(json_str)
                        # Extract "content" from JSON
                        content = json_data.get("content")
                        if content:
                            yield content  # Append content to the accumulator
                    except json.JSONDecodeError as e:
                        logging.error(f"Langserve JSON decoding error: {e}")
                        yield line
                        # Optionally append the original line in case of an error
                else:
                    logging.warning("Could not find data:")
        elif line.startswith('event:'):
            logging.info(f"Found langserve non-data event: {line}")

