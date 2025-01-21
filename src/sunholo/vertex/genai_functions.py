try:
    import google.generativeai as genai
except ImportError:
    genai = None

from .init import init_genai
from .safety import genai_safety
from ..custom_logging import log
import json
from .type_dict_to_json import describe_typed_dict, openapi_to_typed_dict, is_typed_dict

def genai_structured_output(
        openapi_spec, 
        system_prompt: str = "", 
        model_name: str = "models/gemini-1.5-pro",
        **kwargs):
    """
    Generate AI function output with the specified configuration.
    
    Parameters:
    - output_schema: The schema for the response output.
    - system_prompt: Optional system prompt to guide the generation.
    - model_name: The name of the model to use (default is 'models/gemini-1.5-flash').
    - output_schema_json: The JSON schema with descriptions.
    - **kwargs: Additional keyword arguments to customize the generation config.
    
    Returns:
    - model: The configured generative model.
    """
    
    init_genai()

    # Generate the JSON schema with descriptions
    output_schema, descriptions = openapi_to_typed_dict(openapi_spec, 'Input')

    # Convert TypedDict to JSON schema if necessary
    if is_typed_dict(output_schema):
        output_schema_json = describe_typed_dict(output_schema, descriptions)

    # Base generation configuration
    generation_config = {
        "response_mime_type": "application/json",
        #"response_schema": output_schema, # didn't work yet as couldn't deal with Optional values
        "temperature": 0.5
    }
    
    # Merge additional kwargs into generation_config
    generation_config.update(kwargs)

    if output_schema_json:
        system_prompt = f"{system_prompt}\n##OUTPUT JSON SCHEMA:\n{json.dumps(output_schema_json, indent=2)}\n"

    model = genai.GenerativeModel(
        model_name=model_name,
        safety_settings=genai_safety(),
        generation_config=generation_config,
        system_instruction=system_prompt,
        tool_config={'function_calling_config': 'ANY'} # pro models only
    )
    
    return model