from ..custom_logging import log
from ..utils import ConfigManager

# Load the YAML file
def load_prompt_from_yaml(key, prefix="sunholo", load_from_file=False, f_string=True):
    """
    Returns a string you can use with prompts.

    If load_from_file=False, by default it will try to load from Langfuse, if fails (which is laggy so not ideal) then load from file.

    Prompts on Langfuse should be specified with a name with {prefix}-{key} e.g. "sunholo-hello"
    
    Prompts in files will use yaml:

    ```yaml
    kind: promptConfig
    apiVersion: v1
    prompts:
    sunholo:
        hello: |
            Say hello to {name} 
    ```

    And load via utils.ConfigManager:

    ```python
    # equivalent to load_prompt_from_yaml("hello", load_from_file=True)
    config = ConfigManager("sunholo")
    config.promptConfig("hello")
    ```

    If f_string is True will be in a Langchain style prompt e.g. { one brace }
    If f_string is False will be Langfuse style prompt e.g. {{ two braces }} - see https://langfuse.com/docs/prompts/get-started

    Example:

    ```python
    from sunholo.langfuse.prompts import load_prompt_from_yaml
    # f_string
    hello_template = load_prompt_from_yaml("hello")
    hello_template.format(name="Bob")

    #langfuse style
    hello_template = load_prompt_from_yaml("hello", f_string=False)
    hello_template.compile(name="Bob")

    # if prompt not available on langfuse, will attempt to load from local promptConfig file
    hello_template = load_prompt_from_yaml("hello", load_from_file=True)

    ```

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