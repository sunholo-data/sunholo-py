from ..logging import log
from ..utils import load_config_key

# Load the YAML file
def load_prompt_from_yaml(key, prefix="sunholo", file_path=None):
    """
    Returns a string you can use with Langfuse PromptTemplate.from_template() 

    Will first try to load from the Langfuse prompt library, if unavailable will look in promptConfig type file.

    Langfuse prompts have {{ two braces }}, Langchain prompts have { one brace }.

    Example:

    ```python
    from sunholo.langfuse.prompts import load_prompt_from_yaml
    from langchain_core.prompts import PromptTemplate
    
    """
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

    return load_config_key(key, vector_name=prefix, kind="promptConfig")