import requests
from ..logging import log
from ..auth import get_header

# Global cache for storing input schemas
langserve_input_schema_cache = {}

def fetch_input_schema(endpoint, vector_name):
    """
    Fetch the input schema from the Langserve endpoint and vector name, including a caching mechanism
    to avoid redundant network calls. If the schema for a given endpoint is already cached, it retrieves
    it directly from the cache; otherwise, it makes an HTTP GET request to fetch the schema.

    Parameters:
    - endpoint (str): The URL of the endpoint from which the schema needs to be fetched.
    - vector_name (str): The name of the vector that might modify the headers sent with the request.

    Returns:
    dict or None: Returns the fetched schema as a dictionary if the request is successful and the schema is valid. Returns None if there is an error fetching the schema.

    This function also logs the fetching process, providing information about the fetched schema or any errors encountered.

    Examples

    ```python
    endpoint = "http://api.example.com/schema/weather"
    vector_name = "weatherQuery"
    schema = fetch_input_schema(endpoint, vector_name)
    if schema:
        print("Schema fetched successfully:", schema)
    else:
        print("Failed to fetch schema")

    cached_schema = fetch_input_schema(endpoint, vector_name)
    print("Cached Schema:", cached_schema)
    ```

    """
    # Check if the schema is already in the cache
    if endpoint in langserve_input_schema_cache:
        return langserve_input_schema_cache[endpoint]

    header = get_header(vector_name)

    try:
        response = requests.get(endpoint, headers = header)
        response.raise_for_status()
        schema = response.json()
        log.info(f"Fetched schema: {schema}")
        # Cache the fetched schema
        langserve_input_schema_cache[endpoint] = schema
        return schema
    except requests.RequestException as e:
        log.error(f"Error fetching input schema: {e}")
        return None

def prepare_request_data(user_input, endpoint, vector_name, **kwargs):
    """
    Prepare the request data for an API call to a Langserve endpoint based on the input schema from the specified endpoint. 
    The function constructs a request payload incorporating user input, endpoint-specific configurations, 
    and additional parameters passed through keyword arguments (kwargs).

    Parameters:
    - user_input (str): The main user input data to be processed.
    - endpoint (str): The endpoint URL or identifier used to fetch the corresponding input schema.
    - vector_name (str): The name of the vector, indicating the specific processing or analysis vector to be used.
    - `**kwargs`: Arbitrary keyword arguments. Special handling for 'configurable' which, if present, 
                is moved to a separate 'config' dictionary in the output payload.

    The function extracts the input schema based on the provided endpoint and vector name, logs this schema, 
    and constructs the payload under the 'input' key based on this schema. If 'configurable' is present in kwargs, 
    it is placed in a separate 'config' dictionary within the payload, allowing configuration settings to be 
    specified separately from the input data.

    Returns:
    dict: A dictionary structured as `{ "input": {...}, "config": {...} }` if 'configurable' is provided; otherwise, the 'config' key is omitted.

    If the input schema is not found or invalid, an error is logged and None is returned.
    """
    input_schema = fetch_input_schema(endpoint, vector_name)
    log.info(f"Found input schema: {input_schema}")
    if input_schema is not None and 'properties' in input_schema:
        key = next(iter(input_schema['properties']))
        input_data = {key: user_input}

        # Check for the special 'configurable' key in kwargs
        config_data = {}
        if 'configurable' in kwargs:
            config_data['configurable'] = kwargs.pop('configurable')

        # Merge kwargs into request_data
        input_data.update(kwargs)
        input_data['vector_name'] = vector_name
        request_data = {"input": input_data}
        if config_data:
            request_data['config'] = config_data

        return request_data
    else:
        log.error("Invalid or no input schema available.")
        return None

