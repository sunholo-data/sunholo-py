from ..custom_logging import log
from ..utils import ConfigManager
import threading
try:
    from langfuse import Langfuse
    langfuse = Langfuse()
except ImportError:
    langfuse = None

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
    # Initialize Langfuse client
    if load_from_file:
        config = ConfigManager(prefix)
        
        return config.promptConfig(key)

    if langfuse is None:
        log.warning("No Langfuse import available - install via sunholo[http]")
    else:
        langfuse_result = [None]
        
        def langfuse_load():
            try:
                template = f"{prefix}-{key}" if prefix else key
                prompt = langfuse.get_prompt(template, cache_ttl_seconds=300)
                langfuse_result[0] = prompt.get_langchain_prompt() if f_string else prompt
            except Exception as err:
                log.warning(f"Langfuse error: {template} - {str(err)}")
                config = ConfigManager(prefix)
                langfuse_result[0] = config.promptConfig(key)

        thread = threading.Thread(target=langfuse_load)
        thread.start()
        thread.join(timeout=1)

        if langfuse_result[0]:
            return langfuse_result[0]

    config = ConfigManager(prefix)
    return config.promptConfig(key)