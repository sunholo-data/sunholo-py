from ..custom_logging import log
from ..utils import ConfigManager

# Load the YAML file
def load_prompt_from_yaml(key, prefix="sunholo", load_from_file=False, f_string=True):
    """
    Returns a string you can use with prompts.

    Will first try to load from the Langfuse prompt library, if unavailable will look in promptConfig type file.

    If f_string is True will be in a Langchain style prompt e.g. { one brace }
    If f_string is False will be Langfuse style prompt e.g. {{ two braces }}

    Example:

    ```python
    from sunholo.langfuse.prompts import load_prompt_from_yaml
    from langchain_core.prompts import PromptTemplate
    
    """
    config = ConfigManager(prefix)
    if load_from_file:
        
        return config.promptConfig(key)


    from langfuse import Langfuse

    # Initialize Langfuse client
    langfuse = Langfuse()

    try:
        if prefix is None:
            langfuse_template = key
        else:
            langfuse_template = f"{prefix}-{key}"
            
        langfuse_prompt = langfuse.get_prompt(langfuse_template, cache_ttl_seconds=300)

        if f_string:
            return langfuse_prompt.get_langchain_prompt()
        
        return langfuse_prompt
    
    except Exception as err:
        log.warning(f"Could not find langfuse template: {langfuse_template} - {str(err)} - attempting to load from promptConfig")

    return config.promptConfig(key)