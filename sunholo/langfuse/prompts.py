from ..logging import log
from ..utils import ConfigManager

# Load the YAML file
def load_prompt_from_yaml(key, prefix="sunholo", load_from_file=False):
    """
    Returns a string you can use with Langfuse PromptTemplate.from_template() 

    Will first try to load from the Langfuse prompt library, if unavailable will look in promptConfig type file.

    Langfuse prompts have {{ two braces }}, Langchain prompts have { one brace }.

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

        return langfuse_prompt.get_langchain_prompt()
    
    except Exception as err:
        log.warning(f"Could not find langfuse template: {langfuse_template} - {str(err)} - attempting to load from promptConfig")

    return config.promptConfig(key)