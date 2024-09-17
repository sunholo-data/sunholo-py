import traceback

from ..custom_logging import log
from ..utils import ConfigManager
from .safety import genai_safety

from typing import TYPE_CHECKING, Union

import json
from collections import deque

try:
    import google.generativeai as genai
    import proto
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

        # Add default 'decide_to_go_on' if not provided in construct_tools
        if 'decide_to_go_on' not in self.funcs:
            self.funcs['decide_to_go_on'] = self.decide_to_go_on

        self.model_name = config.vacConfig("model") if config.vacConfig("llm") == "vertex" else "gemini-1.5-flash"
        self.last_api_requests_and_responses = []
        self._validate_functions()

    def construct_tools(self) -> dict:
        """
        Constructs a dictionary of tools (functions) specific to the application.

        This method should be overridden in subclasses to provide the specific
        function implementations required for the application.
        
        Note: All functions need arguments to avoid errors.

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
                # Try to decode the result if it's a string
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError:
                        log.warning(f"Failed to decode JSON result for function {function_name}: {result}")
                        continue  # Skip this result if decoding fails

                normalized_target_value = {k: v for k, v in target_value.items()} if isinstance(target_value, dict) else target_value
                log.info(f"{normalized_target_value=} {result=}") 

                if isinstance(result, dict) and isinstance(normalized_target_value, dict):
                    for key, expected_value in normalized_target_value.items():
                        if key in result and result[key] == expected_value:
                            log.info(f"The key '{key}' has the expected value in both dictionaries.")
                            return True
                    return False
                elif result == normalized_target_value:
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
                
                # Handle empty parameters
                if fn.args is None or not fn.args:
                    params_obj = {}
                else:
                    params_obj = {key: val for key, val in fn.args.items()}

                params = ', '.join(f'{key}={val}' for key, val in params_obj.items())
                log.info(f"Executing {function_name} with params {params}")

                # Check if the function is in our dictionary of available functions
                if function_name in self.funcs:
                    fn_exec = self.funcs[function_name]
                    try:
                        if not isinstance(fn_exec, genai.protos.FunctionDeclaration):
                            # Execute the function with the provided parameters
                            result = fn_exec(**params_obj)
                            log.info(f"Got result from {function_name}: {result} of type: {type(result)}")
                            if not isinstance(result, str):
                                log.warning(f"Tool functions should return strings: {function_name} returned type: {type(result)}")
                        else:
                            fn_result = type(fn).to_dict(fn)
                            result = fn_result.get("result")
                            if not result:
                                log.warning("No result found for {function_name}")
                            log.info(f"No execution of {function_name} as a FunctionDeclatation object, just returning args {result}")
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

    def run_agent_loop(self, chat, content, callback, guardrail_max=10, loop_return=3):
        """
        Runs the agent loop, sending messages to the orchestrator, processing responses, and executing functions.

        Args:
            chat: The chat object for interaction with the orchestrator.
            content: The initial content to send to the agent.
            callback: The callback object for handling intermediate responses.
            guardrail_max (int): The maximum number of iterations for the loop.
            loop_return (int): The number of last loop iterations to return. Default 3 will return last 3 iterations. If loop_return > guardrail_max then all iterations are returned.

        Returns:
            tuple: (big_text, usage_metadata) from the loop execution.
        """
        guardrail = 0
        big_result = []
        usage_metadata = {
            "prompt_token_count": 0,
            "candidates_token_count": 0,
            "total_token_count": 0
        }
        functions_called =[]
        function_results = []
        # Initialize token queue to ensure sequential processing
        token_queue = deque()

        while guardrail < guardrail_max:

            token_queue.append(f"\n----Loop [{guardrail}] Start------\nFunctions: {list(self.funcs.keys())}\n")

            content_parse = ""
            for i, chunk in enumerate(content):
                content_parse += f"\n - {i}) {chunk}"
            content_parse += f"\n== End input content for loop [{guardrail}] =="

            log.info(f"== Start input content for loop [{guardrail}]\n ## Content: {content_parse}")
            this_text = ""  # reset for this loop
            response = []

            try:
                token_queue.append("\n= Calling Agent =\n")
                response = chat.send_message(content, stream=True)
                
            except Exception as e:
                msg = f"Error sending {content} to model: {str(e)} - {traceback.format_exc()}"
                log.info(msg)
                token_queue.append(msg)
                break

            loop_metadata = response.usage_metadata
            if loop_metadata:
                usage_metadata = {
                    "prompt_token_count": usage_metadata["prompt_token_count"] + (loop_metadata.prompt_token_count or 0),
                    "candidates_token_count": usage_metadata["candidates_token_count"] + (loop_metadata.candidates_token_count or 0),
                    "total_token_count": usage_metadata["total_token_count"] + (loop_metadata.total_token_count or 0),
                }
                token_queue.append((
                    "\n-- Agent response -- " 
                    f"Loop tokens: [{loop_metadata.prompt_token_count}]/[{usage_metadata['prompt_token_count']}] "
                    f"Session tokens: [{loop_metadata.total_token_count}]/[{usage_metadata['total_token_count']}] \n"
                ))
            loop_metadata = None

            for chunk in response:
                if not chunk:
                    continue

                log.debug(f"[{guardrail}] {chunk=}")
                try:
                    if hasattr(chunk, 'text') and isinstance(chunk.text, str):
                        token = chunk.text
                        token_queue.append(token)
                        this_text += token
                    else:
                        log.info("skipping chunk with no text")
                    
                except ValueError as err:
                    token_queue.append(f"{str(err)} for {chunk=}")
            
            executed_responses = self.process_funcs(response) 
            log.info(f"[{guardrail}] {executed_responses=}")

            if executed_responses:  
                token_queue.append("\n-- Agent Actions:\n")
                for executed_response in executed_responses:
                    token = ""
                    fn = executed_response.function_response.name
                    fn_args = executed_response.function_response.response.get("args")
                    fn_result = executed_response.function_response.response["result"]
                    fn_log = f"{fn}({fn_args})"
                    log.info(fn_log)
                    functions_called.append(fn_log)
                    function_results.append(fn_result)
                    token_queue.append(f"\n-- {fn_log} ...executing...\n") if fn != "decide_to_go_on" else ""
                    while token_queue:
                        token = token_queue.popleft()
                        callback.on_llm_new_token(token=token)

                    try:
                        # Convert MapComposite to a standard Python dictionary
                        if isinstance(fn_result, proto.marshal.collections.maps.MapComposite):
                            fn_result = dict(fn_result)
                        fn_result_json = json.loads(fn_result)
                        if not isinstance(fn_result_json, dict):
                            log.warning(f"{fn_result} was loaded but is not a dictionary")
                            fn_result_json = None
                    except json.JSONDecodeError:
                        log.warning(f"{fn_result} was not JSON decoded")
                        fn_result_json = None
                    except Exception as err:
                        log.warning(f"{fn_result} was not json decoded due to unknown exception: {str(err)}")
                        fn_result_json = None

                    if fn == "decide_to_go_on":
                        log.info(f"{fn_result_json} {fn_result=} {type(fn_result)}")
                        go_on_args = fn_result_json
                        if go_on_args:
                            token = f"\n{'STOPPING' if not go_on_args.get('go_on') else 'CONTINUE'}: {go_on_args.get('chat_summary')}\n"
                        else:
                            log.warning(f"{fn_result_json} did not work for decide_to_go_on")
                            token = f"Error calling decide_to_go_on with {fn_result_json}\n"
                    else:
                        token = f"--- {fn}() result --- \n"
                        if fn_result_json:
                            if fn_result_json.get('stdout'):
                                text = fn_result_json.get('stdout').encode('utf-8').decode('unicode_escape')
                                token += text
                            if fn_result_json.get('stderr'):
                                text = fn_result_json.get('stdout').encode('utf-8').decode('unicode_escape')
                                token += text
                            if not fn_result_json.get('stdout') and fn_result_json.get('stderr'):
                                token += f"{fn_result}\n"
                        else:
                            token += f"{fn_result}\n--- end ---\n"
                    
                    this_text += token
                    token_queue.append(token)
            else:
                token = "\nNo function executions were found\n"
                token_queue.append(token)
                this_text += token

            if this_text:
                content.append(f"Agent: {this_text}")    
                log.info(f"[{guardrail}] Updated content:\n{this_text}")
                big_result.append(this_text)
            else:
                log.warning(f"[{guardrail}] No content created this loop")
                content.append(f"Agent: No response was found for loop [{guardrail}]")

            token_queue.append(f"\n----Loop [{guardrail}] End------\n{usage_metadata}\n----------------------")

            go_on_check = self.check_function_result("decide_to_go_on", {"go_on": False})
            if go_on_check:
                log.info("Breaking agent loop")
                break
            
            while token_queue:
                token = token_queue.popleft()
                callback.on_llm_new_token(token=token)
            
            guardrail += 1
            if guardrail > guardrail_max:
                log.warning(f"Guardrail kicked in, more than {guardrail_max} loops")
                break
        
        while token_queue:
            token = token_queue.popleft()
            callback.on_llm_new_token(token=token)
        
        usage_metadata["functions_called"] = functions_called

        big_text = "\n".join(big_result[-loop_return:])

        return big_text, usage_metadata

    @staticmethod
    def decide_to_go_on(go_on: bool, chat_summary: str) -> dict:
        """
        Examine the chat history.  If the answer to the user's question has been answered, then go_on=False.
        If the chat history indicates the answer is still being looked for, then go_on=True.
        If there is no chat history, then go_on=True.
        If there is an error that can't be corrected or solved by you, then go_on=False.
        If there is an error but you think you can solve it by correcting your function arguments (such as an incorrect source), then go_on=True
        If you want to ask the user a question or for some more feedback, then go_on=False.  
        Avoid asking the user if you suspect you can solve it yourself with the functions at your disposal - you get top marks if you solve it yourself without help.
        When calling, please also add a chat summary of why you think the function should  be called to end.
        
        Args:
            go_on: boolean Whether to continue searching for an answer
            chat_summary: string A brief explanation on why go_on is TRUE or FALSE
        
        Returns:
            boolean: True to carry on, False to continue
        """
        return json.dumps({"go_on": go_on, "chat_summary": chat_summary})