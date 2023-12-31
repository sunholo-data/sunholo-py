import requests
from ..logging import setup_logging

logging = setup_logging()

# Global cache for storing input schemas
langserve_input_schema_cache = {}

def fetch_input_schema(endpoint):
    """ Fetch the input schema from the endpoint, with caching """
    # Check if the schema is already in the cache
    if endpoint in langserve_input_schema_cache:
        return langserve_input_schema_cache[endpoint]

    try:
        response = requests.get(endpoint)
        response.raise_for_status()
        schema = response.json()
        logging.info(f"Fetched schema: {schema}")
        # Cache the fetched schema
        langserve_input_schema_cache[endpoint] = schema
        return schema
    except requests.RequestException as e:
        logging.error(f"Error fetching input schema: {e}")
        return None

def prepare_request_data(user_input, endpoint, **kwargs):
    """ Prepare the request data based on the input schema from the endpoint. 
        Additional data can be passed via kwargs.
    """
    input_schema = fetch_input_schema(endpoint)
    logging.info(f"Found input schema: {input_schema}")
    if input_schema is not None and 'properties' in input_schema:
        key = next(iter(input_schema['properties']))
        input_data = {key: user_input}

        # Merge kwargs into request_data
        input_data.update(kwargs)
        request_data = {"input": input_data}
        return request_data
    else:
        logging.error("Invalid or no input schema available.")
        return None

# Example usage
#endpoint = "http://example.com/api/endpoint"
#user_input = "What is the weather today?"
#additional_data = {"location": "New York", "date": "2024-01-06"}
#request_data = prepare_request_data(user_input, endpoint, **additional_data)

#if request_data is not None:
#    print("Request data:", request_data)
#    # Further code to use request_data as needed
