import requests
from ..logging import setup_logging
from ..auth import get_header

logging = setup_logging()

# Global cache for storing input schemas
langserve_input_schema_cache = {}

def fetch_input_schema(endpoint, vector_name):
    """ Fetch the input schema from the endpoint, with caching """
    # Check if the schema is already in the cache
    if endpoint in langserve_input_schema_cache:
        return langserve_input_schema_cache[endpoint]

    header = get_header(vector_name)

    try:
        response = requests.get(endpoint, headers = header)
        response.raise_for_status()
        schema = response.json()
        logging.info(f"Fetched schema: {schema}")
        # Cache the fetched schema
        langserve_input_schema_cache[endpoint] = schema
        return schema
    except requests.RequestException as e:
        logging.error(f"Error fetching input schema: {e}")
        return None

def prepare_request_data(user_input, endpoint, vector_name, **kwargs):
    """ Prepare the request data based on the input schema from the endpoint. 
        Additional data can be passed via kwargs.
    """
    input_schema = fetch_input_schema(endpoint, vector_name)
    logging.info(f"Found input schema: {input_schema}")
    if input_schema is not None and 'properties' in input_schema:
        key = next(iter(input_schema['properties']))
        input_data = {key: user_input}

        # Merge kwargs into request_data
        input_data.update(kwargs)
        input_data['vector_name'] = vector_name
        request_data = {"input": input_data}
        return request_data
    else:
        logging.error("Invalid or no input schema available.")
        return None

