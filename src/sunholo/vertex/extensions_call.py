from .extensions_class import VertexAIExtensions
from ..utils import ConfigManager
from ..custom_logging import log
import collections.abc
import json

from .genai_functions import genai_structured_output

def dynamic_extension_call(question, config:ConfigManager, project_id:str=None, model_name:str="models/gemini-1.5-pro", **kwargs):

    extensions = config.vacConfig('extensions')
    if not extensions:
        log.warning(f"No extensions founded for vac: {config.vector_name}")

        return None
    
    responses = []
    for tool in extensions:

        call_json = parse_extension_input(question, 
                                          extension_id=tool.get('extension_id'),
                                          extension_display_name=tool.get('extension_display_name'),
                                          config=config,
                                          project_id=project_id,
                                          model_name=model_name,
                                          **kwargs)
        if call_json:
            question = call_json.pop('question')
            extension_output = get_extension_content(question=question,
                                                     config=config,
                                                     project_id=project_id,
                                                     **call_json)
            responses.append(extension_output)
        else:
            log.warning(f"No json found for extension {tool}")
    
    return responses

def parse_extension_input(
        question: str, 
        extension_id: str=None, 
        extension_display_name:str=None, 
        config: ConfigManager=None, 
        project_id:str=None, 
        model_name:str="models/gemini-1.5-pro", 
        **kwargs):
    """
    Takes a question and kwargs and makes an LLM call to extract parameters for an extension call.
    If no parameters are found, returns None
    Once parameters are extracted, makes the call to the extension via get_extenstion_content()

    Example:
    Assuming an OpenAPI configuration file as follows:
    
    """

    extensions = config.vacConfig('extensions')
    ve = VertexAIExtensions(project_id)

    for ext in extensions:
        if extension_id == ext.get("extension_id") or extension_display_name == ext.get("extension_display_name"):
            extension = ve.get_extension(extension_id=extension_id, extension_display_name=extension_display_name)
            break
    
    if not extension:
        raise ValueError(f"No extension found matching {extension_id=} or {extension_display_name=}")
    
    openapi_spec = ve.get_openapi_spec()
    log.info(f"OpenAPI Spec: {openapi_spec}")

    if not openapi_spec:
        raise ValueError(f"No input schema detected for {extension=}")

    model = genai_structured_output(
        openapi_spec, 
        system_prompt="You are an assistant that must only parse your input into the provided json schema output. Do not attempt to answer any questions or do anything else other than extracting data into the output schema", 
        model_name=model_name, 
        **kwargs)

    contents = [
        "The user question may contain information that can be used to populate the output schema",
        "As a minimum the question key should container the user question in 'question', but also examine the content and see if you can fill in the rest of the output schema fields",
        f"User Question to parse: {question}"
    ]

    tokens = model.count_tokens(contents)
    log.info(f"Used [{tokens}] in prompt")

    json_response = model.generate_content(contents)

    log.debug(f"parsed_extension_input returns: {json_response=}")

    try:
        json_object = json.loads(json_response.text)
        log.info(f"Got valid json: {json_object}")

        return json_object
    
    except Exception as err:
        log.error(f"Failed to parse GenAI output to JSON: {json_response=} - {str(err)}")

        return None 


def get_extension_content(question: str, config: ConfigManager, project_id:str=None, **kwargs):
    """
    Fetches content from extensions based on the provided question and configuration.
    
    Args:
        question (str): The question to be processed by the extensions.
        config (ConfigManager): The configuration manager instance.
        **kwargs: Additional parameters to be passed to the extension.

    Returns:
        list: A list of responses from the extensions.

    Example:
        Assuming a YAML configuration file as follows:
        
        ```yaml
        kind: vacConfig
        vac:
            my_vac:
                extensions:
                - extension_id: 8524997435263549440 # or extension_display_name:
                  operation_id: post_extension_invoke_one_generic
                  vac: our_generic
                  operation_params:
                    input:
                      question: ""
                      chat_history: []
                      source_filters: []
                      source_filters_and_or: false
                      search_kwargs:
                        k: 0
                        filter: ""
                        fetch_k: 0
                      private_docs: []
                      whole_document: false
        ```

        The function can be called as:

        ```python
        config = ConfigManager()
        question = "What is the capital of France?"

        responses = get_extension_content(
            question=question,
            config=config,
            input={
                "chat_history": [{"role": "user", "content": "Hello"}],
                "source_filters": ["PPA/"],
                "search_kwargs": {"k": 50, "filter": "source ILIKE '%GermanPolicyforPPA/%'", "fetch_k": 100}
            }
        )
        ```

        In this example, `operation_params` will be updated to:

        ```python
        {
            "input": {
                "question": "What is the capital of France?",
                "chat_history": [{"role": "user", "content": "Hello"}],
                "source_filters": ["PPA/"],
                "source_filters_and_or": false,
                "search_kwargs": {
                    "k": 50,
                    "filter": "source ILIKE '%GermanPolicyforPPA/%'",
                    "fetch_k": 100
                },
                "private_docs": [],
                "whole_document": false
            }
        }
        ```
    """
    extensions = config.vacConfig('extensions')
    responses = []
    for tool in extensions:
        try:
            ve = VertexAIExtensions(project_id)
            
            # Merge operation_params from tool config and **kwargs
            operation_params = tool.get('operation_params', {})
            log.info(f'{operation_params=}')
            operation_params_input = update_nested_params(operation_params, kwargs)

            # Update the question in operation_params if it exists
            operation_params_input = inject_question(question, operation_params)

            response = ve.execute_extension(
                operation_id=tool['operation_id'],
                operation_params=operation_params_input,
                extension_id=tool.get('extension_id'),
                extension_display_name=tool.get('extension_display_name'),
                vac=tool.get('vac')
            )

            # Dynamically get keys for answer and metadata from YAML configuration
            output_config = operation_params.get('output', {})
            answer_key = output_config.get('answer', 'answer')
            metadata_key = output_config.get('metadata', 'metadata')

            # Extract answer and metadata based on the specified keys
            log.info(f'{answer_key} {metadata_key}')

            answer = extract_nested_value(response, answer_key)
            metadata = extract_nested_value(response, metadata_key)

            log.info(f'{answer=} {metadata=}')

            if answer and metadata:
                responses.append(f"{answer}\nMetadata: {metadata}")
            elif answer:
                responses.append(answer)

        except Exception as err:
            log.error(f'Could not find vertex-extension response: {str(err)}')
            answer = None
    
    log.info(f'Vertex extension responses: {responses=}')

    answers = "\n\n".join([resp for resp in responses if resp is not None])

    return answers

def update_nested_params(original, updates):
    """
    Recursively update nested dictionaries with new values.
    
    Args:
        original (dict): The original dictionary to be updated.
        updates (dict): The new values to be merged into the original dictionary.

    Returns:
        dict: The updated dictionary.

    Example:
        ```python
        original = {
            "param1": "value1",
            "nested_param": {
                "sub_param1": "sub_value1"
            }
        }

        updates = {
            "param1": "new_value1",
            "nested_param": {
                "sub_param1": "new_sub_value1"
            }
        }

        updated_params = update_nested_params(original, updates)

        # updated_params will be:
        # {
        #     "param1": "new_value1",
        #     "nested_param": {
        #         "sub_param1": "new_sub_value1"
        #     }
        # }
        ```
    """
    for key, value in updates.items():
        if isinstance(value, collections.abc.Mapping):
            original[key] = update_nested_params(original.get(key, {}), value)
        else:
            original[key] = value
    return original

def inject_question(question, params):
    """
    Recursively injects the question into nested dictionaries where the key is 'question' and the value is empty.

    Args:
        question (str): The question to be injected.
        params (dict): The dictionary where the question should be injected.

    Returns:
        dict: The dictionary with the question injected.

    Example:
        ```python
        params = {
            "input": {
                "question": "",
                "chat_history": [],
                "source_filters": [],
                "search_kwargs": {
                    "k": 0,
                    "filter": "",
                    "fetch_k": 0
                },
                "private_docs": [],
                "whole_document": false
            }
        }

        question = "What is the capital of France?"

        updated_params = inject_question(question, params)

        # updated_params will be:
        # {
        #     "input": {
        #         "question": "What is the capital of France?",
        #         "chat_history": [],
        #         "source_filters": [],
        #         "search_kwargs": {
        #             "k": 0,
        #             "filter": "",
        #             "fetch_k": 0
        #         },
        #         "private_docs": [],
        #         "whole_document": false
        #     }
        # }
        ```
    """
    if isinstance(params, collections.abc.Mapping):
        for key, value in params.items():
            if isinstance(value, collections.abc.Mapping):
                params[key] = inject_question(question, value)
            elif key == 'question' and not value:
                params[key] = question
    return params

def extract_nested_value(data, key):
    """
    Recursively extract a value from nested dictionaries based on the specified key or a dot-separated key path.
    If the key is not dot-separated, it will find the first occurrence of that key in the nested dictionaries.

    Args:
        data (dict): The dictionary to extract the value from.
        key (str): The key or dot-separated key path to extract the value.

    Returns:
        Any: The extracted value, or None if the key or key path is not found.

    Example:
        ```python
        data = {
            "output": {
                "content": "Some content",
                "metadata": {"key1": "value1"}
            }
        }

        value = extract_nested_value(data, "content")
        # value will be "Some content"

        value = extract_nested_value(data, "output.metadata")
        # value will be {"key1": "value1"}
        ```
    """
    def search_key(data, key):
        if isinstance(data, dict):
            if key in data:
                return data[key]
            for k, v in data.items():
                if isinstance(v, dict):
                    result = search_key(v, key)
                    if result is not None:
                        return result
        return None

    if '.' in key:
        keys = key.split('.')
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return None
        return data
    else:
        return search_key(data, key)

if __name__ == "__main__":
    config = ConfigManager("one_ai")
    #get_extension_content("What are PPAs in france like?", config=config)
    parse_extension_input("What are PPAs in france like?", 
                          extension_display_name="Our New Energy Database2",
                          config=config)
    parse_extension_input("What are PPas in france like? Look in files within the PPA/ or /PPA2 folder, returning the whole documents", 
                          extension_display_name="Our New Energy Database2", 
                          config=config, model_name="models/gemini-1.5-pro")
# {'question': 'What are PPas in france like? Look in files within the PPA/ or /PPA2 folder, returning the whole documents', 
# 'chat_history': [], 'source_filters': ['PPA/', '/PPA2'], 
# 'source_filters_and_or': False, 'search_kwargs': {}, 'private_docs': [], 'whole_document': True}
