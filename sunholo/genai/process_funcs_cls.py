import traceback

from ..custom_logging import log
from ..utils import ConfigManager
from .safety import genai_safety

from typing import TYPE_CHECKING, Union

import json

try:
    import google.generativeai as genai
except ImportError:
    genai = None

if TYPE_CHECKING:
    from google.generativeai.protos import Part

class GenAIFunctionProcessor:
    """
    A generic class for processing function calls from google.generativeai function calling models.

    This class provides a framework for handling multiple function calls in responses
    from generative AI systems. Users of this class should subclass it and provide
    their own implementation of the `construct_tools` method, which returns a dictionary
    of function names mapped to their implementations.

    Attributes:
        config (ConfigManager): Configuration manager instance. Reach values via self.config within your own construct_tools() method
        funcs (dict): A dictionary of function names mapped to their implementations.

    Example usage:

    ```python
    class AlloyDBFunctionProcessor(GenAIFunctionProcessor):
        def construct_tools(self) -> dict:
            pass

    config = ConfigManager()
    alloydb_processor = AlloyDBFunctionProcessor(config)

    results = alloydb_processor.process_funcs(full_response)

    alloydb_model = alloydb_processor.get_model(
        model_name="gemini-1.5-pro",
        system_instruction="You are a helpful AlloyDB agent that helps users search and extract documents from the database."
    )
    ```
    """

    def __init__(self, config: ConfigManager):
        """
        Initializes the GenAIFunctionProcessor with the given configuration.

        Args:
            config (ConfigManager): The configuration manager instance.
        """
        if not genai:
            raise ImportError("import google.generativeai as genai is required, import via `pip install sunholo[gcp]`")
        
        self.config = config
        self.funcs = self.construct_tools()
        self.model_name = config.vacConfig("model") if config.vacConfig("llm") == "vertex" else "gemini-1.5-flash"
        self.last_api_requests_and_responses = []
        self._validate_functions()

    def construct_tools(self) -> dict:
        """
        Constructs a dictionary of tools (functions) specific to the application.

        This method should be overridden in subclasses to provide the specific
        function implementations required for the application.

        Returns:
            dict: A dictionary where keys are function names and values are function objects

        Raises:
            NotImplementedError: If the method is not overridden in a subclass.
        """
        raise NotImplementedError("Subclasses must implement this method to return a dictionary of functions.")

    def _validate_functions(self):
        """
        Validates that all functions in the `funcs` dictionary have docstrings.

        This method checks each function in the `funcs` dictionary to ensure it has
        a docstring. If a function is missing a docstring, an error is logged, and
        a `ValueError` is raised.

        Raises:
            ValueError: If any function is missing a docstring.
        """
        for func_name, func in self.funcs.items():
            if not func.__doc__:
                log.error(f"Function {func_name} is missing a docstring.")
                raise ValueError(f"Function {func_name} must have a docstring to be used as a genai tool.")
    

    def parse_as_parts(self, api_requests_and_responses=[]):
        if not api_requests_and_responses and not self.last_api_requests_and_responses:
            log.info("No api_requests_and_responses found to parse to parts")
            return None

        if api_requests_and_responses:
            self.last_api_requests_and_responses = api_requests_and_responses
        
        from google.generativeai.protos import Part

        work_on = api_requests_and_responses or self.last_api_requests_and_responses
        parts = []
        for part in work_on:
            try:
                parts.append(
                    Part(
                        function_response=genai.protos.FunctionResponse(
                            name=part[0],
                            response={"result": part[2], "args": json.dumps(part[1])}
                        )
                    )
                )
            except Exception as err:
                parts.append(
                    Part(
                        function_response=genai.protos.FunctionResponse(
                            name=part[0],
                            response={"result": f"ERROR: {str(err)}"}
                        )
                    )
                )                

        return parts

    def check_function_result(self, function_name, target_value, api_requests_and_responses=[]):
        """
        Checks if a specific function result in the api_requests_and_responses contains a certain value.

        Args:
            function_name (str): The name of the function to check.
            target_value: The value to look for in the function result.
            api_requests_and_responses (list, optional): List of function call results to check. 
                                                        If not provided, the method will use `self.last_api_requests_and_responses`.

        Returns:
            bool: True if the target_value is found in the specified function's result, otherwise False.
        """
        if not api_requests_and_responses:
            api_requests_and_responses = self.last_api_requests_and_responses

        if not api_requests_and_responses:
            log.info("No api_requests_and_responses found to check.")
            return False

        for part in api_requests_and_responses:
            func_name = part[0]
            result = part[2]

            if func_name == function_name:
                if isinstance(result, list) and target_value in result:
                    log.info(f"Target value '{target_value}' found in the result of function '{function_name}'.")
                    return True
                elif isinstance(result, dict) and isinstance(target_value, dict):
                    for key, expected_value in target_value.items():
                        if key in result:
                            if result[key] == expected_value:
                                log.info(f"The key '{key}' has the same value in both dictionaries.")
                                return True
                    return False
                elif result == target_value:
                    log.info(f"Target value '{target_value}' found in the result of function '{function_name}'.")
                    return True

        log.info(f"Target value '{target_value}' not found in the result of function '{function_name}'.")
        return False
    
    def parse_as_string(self, api_requests_and_responses=[]):
        if not api_requests_and_responses and not self.last_api_requests_and_responses:
            log.info("No api_requests_and_response found to parse to string")
            return None
        
        if api_requests_and_responses:
            self.last_api_requests_and_responses = api_requests_and_responses
        
        work_on = api_requests_and_responses or self.last_api_requests_and_responses
        strings = []
        for part in work_on:
            strings.append(
                f"function tool {part[0]} was called with arguments: {part[1]} and got this result:\n"
                f"<{part[0]}_result>{part[2]}</{part[0]}_result>"
            )

        return strings

    def process_funcs(self, full_response, output_parts=True) -> Union[list['Part'], str]:
        """
        Processes the functions based on the full_response from the generative model.

        This method iterates through each part of the response, extracts function
        calls and their parameters, and executes the corresponding functions defined
        in the `funcs` dictionary.

        Args:
            full_response: The response object containing function calls.
            output_parts (bool): Indicates whether to return structured parts or plain strings.

        Returns:
            list[Part] | str: A list of Part objects or a formatted string with the results.

        Example usage:
        ```python
        results = alloydb_processor.process_funcs(full_response)
        ```
        """
        api_requests_and_responses = []

        if not full_response:
            log.info("No response was found to process")
            return api_requests_and_responses

        # Loop through each part in the response to handle multiple function calls
        #TODO: async
        for part in full_response.candidates[0].content.parts:
            if fn := part.function_call:
                # Extract parameters for the function call
                function_name = fn.name
                params_obj = {key: val for key, val in fn.args.items()}
                params = ', '.join(f'{key}={val}' for key, val in params_obj.items())
                log.info(f"Executing {function_name} with params {params}")

                # Check if the function is in our dictionary of available functions
                if function_name in self.funcs:
                    try:
                        # Execute the function with the provided parameters
                        result = self.funcs[function_name](**params_obj)
                        log.info(f"Got result from {function_name}: {result}")
                    except Exception as err:
                        error_message = f"Error in {function_name}: {str(err)}"
                        traceback_details = traceback.format_exc()
                        log.warning(f"{error_message}\nTraceback: {traceback_details}")
                        result = [f"{error_message}\n{traceback_details}"]

                    api_requests_and_responses.append(
                        [function_name, params, result]
                    )
                else:
                    log.error(f"Function {function_name} is not recognized")

        log.info(f"{api_requests_and_responses=}")
        self.last_api_requests_and_responses = api_requests_and_responses

        if output_parts:
            return self.parse_as_parts()
        
        return self.parse_as_string()
    
    def tool_config_setting(self, mode:str):
        from google.generativeai.types import content_types

        fns = list(self.funcs.keys())

        if fns and mode == "any":
            return content_types.to_tool_config(
                    {"function_calling_config": {"mode": mode, "allowed_function_names": fns}}
                )
        else:
            return content_types.to_tool_config(
                {"function_calling_config": {"mode": mode}}
            )

    def get_model(
            self, 
            system_instruction: str, 
            generation_config=None, 
            model_name: str=None,
            tool_config: str="auto"):
        """
        Constructs and returns the generative AI model configured with the tools.

        This method creates a generative AI model using the tools defined in the
        `funcs` dictionary and the provided configuration options.

        Args:
            model_name (str): The name of the model to use.
            system_instruction (str): Instructions for the AI system.
            generation_config (dict, optional): Configuration for generation, such as temperature.
            tool_config (str, optional): Configuration for tool behaviour: 'auto' it decides, 'none' no tools, 'any' always use tools

        Returns:
            GenerativeModel: An instance of the GenerativeModel configured with the provided tools.

        Example usage:

        ```python
        alloydb_model = alloydb_processor.get_model(
            model_name="gemini-1.5-pro",
            system_instruction="You are a helpful AlloyDB agent that helps users search and extract documents from the database."
        )
        ```
        """
        if generation_config is None:
            generation_config = {
                "temperature": 0.1,
                "max_output_tokens": 8000,
            }

        # Extract the functions from the dictionary to pass into the model
        tools = list(self.funcs.values())

        try:
            model = genai.GenerativeModel(
                model_name=model_name or self.model_name,
                tools=tools,
                tool_config=self.tool_config_setting(tool_config),
                generation_config=generation_config,
                safety_settings=genai_safety(),
                system_instruction=system_instruction,
            )
            return model
        except Exception as err:
            log.error(f"Error initializing model: {str(err)}")
            return None