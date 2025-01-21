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
    from google.api_core import retry
    from google.generativeai import ChatSession
    from google.api_core.exceptions import RetryError
    from google.generativeai.types import RequestOptions, GenerateContentResponse
except ImportError:
    genai = None
    ChatSession = None
    GenerateContentResponse = None

from .images import extract_gs_images_and_genai_upload

if TYPE_CHECKING:
    from google.generativeai.protos import Part
    from google.generativeai import ChatSession
    from google.generativeai.types import RequestOptions, GenerateContentResponse

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

    def __init__(self, config: ConfigManager=None, model_name=None, trace=None, parent_observation_id=None):
        """
        Initializes the GenAIFunctionProcessor with the given configuration.

        Args:
            config (ConfigManager): The configuration manager instance.
            model_name (str): The name of the model
        """
        if not genai:
            raise ImportError("import google.generativeai as genai is required, import via `pip install sunholo[gcp]`")
        
        self.config = config
        self.funcs = self.construct_tools()

        # Add default 'decide_to_go_on' if not provided in construct_tools
        if 'decide_to_go_on' not in self.funcs:
            self.funcs['decide_to_go_on'] = self.decide_to_go_on

        self.model_name = "gemini-1.5-flash"
        if config:
            self.model_name = config.vacConfig("model") if config.vacConfig("llm") == "vertex" else "gemini-1.5-flash"
        
        if model_name:
            log.info(f"Overriding agent model name {self.model_name} with model {model_name}")
            self.model_name = model_name
        
        self.trace = trace
        self.parent_observation_id = parent_observation_id
        
        # agent loops
        self.last_api_requests_and_responses = []
        self._validate_functions()

        self.loop_span = None
        self.token_queue = []
        self.loop_text = ""
        self.loop_content = []
        self.loop_guardrail = 0
        self.big_result = []
        self.usage_metadata = {}
        self.functions_called =[]

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

    def process_funcs(self, full_response, output_parts=True, loop_span=None) -> Union[list['Part'], str]:
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
        if not full_response.candidates or len(full_response.candidates) == 0:
            log.error("No candidates found in the response. The response might have failed.")
            return "No candidates available in the response. Please check your query or try again."

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
                log.info(f"== Executing {function_name} with params {params} (Total Characters: {len(params)})")
                if len(params)>8000:
                    log.warning(f"Total parameters are over 8000 characters - it may not work properly: {params[:10000]}....[{len(params)}]")

                fn_span = loop_span.span(name=function_name, input=params_obj) if loop_span else None

                # Check if the function is in our dictionary of available functions
                if function_name in self.funcs:
                    fn_exec = self.funcs[function_name]
                    try:
                        if not isinstance(fn_exec, genai.protos.FunctionDeclaration):
                            # Execute the function with the provided parameters
                            result = fn_exec(**params_obj)
                            log.info(f"Got result from {function_name}: {result} of type: {type(result)}")
                            #TODO: return images
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
                        result = [error_message] #traceback uses too many tokens
                    clean_result = self.remove_invisible_characters(result)
                    api_requests_and_responses.append(
                        [function_name, params, clean_result]
                    )
                    fn_span.end(output=clean_result) if fn_span else None
                else:
                    msg = f"Function {function_name} is not recognized"
                    log.error(msg)
                    fn_span.end(output=msg) if fn_span else None

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
    
    def remove_invisible_characters(self, string):

        if not isinstance(string, str):
            return string
        
        clean = string.encode('utf-8', errors='replace').decode('unicode_escape')
        log.info(f"Cleaning:\n{string[:100]}\n > to >\n{clean[:100]}")
        
        return clean
    
    def convert_composite_to_native(self, value):
        """
        Recursively converts a proto MapComposite or RepeatedComposite object to native Python types.

        Args:
            value: The proto object, which could be a MapComposite, RepeatedComposite, or a primitive.

        Returns:
            The equivalent Python dictionary, list, or primitive type.
        """
        if isinstance(value, proto.marshal.collections.maps.MapComposite):
            # Convert MapComposite to a dictionary, recursively processing its values
            return {key: self.convert_composite_to_native(val) for key, val in value.items()}
        elif isinstance(value, proto.marshal.collections.repeated.RepeatedComposite):
            # Convert RepeatedComposite to a list, recursively processing its elements
            return [self.convert_composite_to_native(item) for item in value]
        else:
            # If it's a primitive value, return it as is
            return value

    """
        self.loop_span = None
        self.token_queue = None
        self.loop_chat = None
        self.loop_text = None
        self.loop_content = None
        self.loop_guardrail = None
    """

    def _loop_update_content(self):
        if self.loop_text:
            # update content relying on gemini chat history, and the parsed function result objects
            if self.loop_executed_responses:
                self.loop_content = self.loop_executed_responses
            else:
                self.loop_content = [f"[{self.loop_guardrail}] Agent: {self.loop_text}"]
            # if text includes gs:// try to download it
            image_uploads = extract_gs_images_and_genai_upload(self.loop_text)
            if image_uploads:
                for img in image_uploads:
                    log.info(f"Adding {img=}")
                    self.loop_content.append(img)
                    self.loop_content.append(f"{img.name} was created by agent and added")
            log.info(f"[{self.loop_guardrail}] Updated content:\n{self.loop_text}")
            self.big_result.append(self.loop_text)
        else:
            log.warning(f"[{self.loop_guardrail}] No content created this loop")
            self.loop_content = [f"[{self.loop_guardrail}] Agent: ERROR - No response was found for loop [{self.loop_guardrail}]"]

    def _loop_handle_executed_responses(self, response):
        try:
            self.loop_executed_responses = self.process_funcs(response, loop_span=self.loop_span) 
        except Exception as err:
            log.error(f"Error in executions: {str(err)}")
            self.token_queue.append(f"{str(err)} for {response=}")

        log.info(f"[{self.loop_guardrail}] {self.loop_executed_responses=}")

        if self.loop_executed_responses:  
            self.token_queue.append("\n-- Agent Actions:\n")
            fn_exec = self.loop_span.span(name="function_actions", input=self.loop_executed_responses) if self.loop_span else None
            for executed_response in self.loop_executed_responses:
                token = ""
                fn = executed_response.function_response.name
                fn_args = executed_response.function_response.response.get("args")
                fn_result = executed_response.function_response.response["result"]
                fn_log = f"{fn}({fn_args})"
                log.info(fn_log)
                self.functions_called.append(fn_log)
                self.token_queue.append(f"\n-- {fn_log} ...executing...\n") if fn != "decide_to_go_on" else ""
                while self.token_queue:
                    token = self.token_queue.popleft()
                    self.loop_callback.on_llm_new_token(token=token)

                log.info(f"{fn_log} created a result={type(fn_result)=}")
                fn_exec_one = fn_exec.span(name=fn, input=fn_args) if fn_exec else None
                
                fn_result_json = None
                # Convert MapComposite to a standard Python dictionary
                if isinstance(fn_result, proto.marshal.collections.maps.MapComposite):
                    fn_result_json = self.convert_composite_to_native(fn_result)
                elif isinstance(fn_result, proto.marshal.collections.repeated.RepeatedComposite):
                    fn_result = self.convert_composite_to_native(fn_result)
                elif isinstance(fn_result, dict):
                    fn_result_json = fn_result
                elif isinstance(fn_result, str):
                    try:
                        if isinstance(fn_result_json, str):
                            fn_result_json = json.loads(fn_result_json)
                    except json.JSONDecodeError:
                        log.warning(f"{fn_result} was not JSON decoded")
                    except Exception as err:
                        log.warning(f"{fn_result} was not json decoded due to unknown exception: {str(err)} {traceback.format_exc()}")
                else:
                    log.warning(f"Unrecognised type for {fn_log}: {type(fn_result)}")
                
                # should be a string or a dict by now
                log.info(f"Processed {fn_log} to {fn_result_json=} type: {type(fn_result_json)}")
                
                if fn == "decide_to_go_on":
                    log.info(f"{fn_result_json=} {type(fn_result)}")
                    if fn_result_json:
                        token = f"\n{'STOPPING' if not fn_result_json.get('go_on') else 'CONTINUE'}: {fn_result_json.get('chat_summary')}\n"
                    else:
                        log.warning(f"{fn_result_json} did not work for decide_to_go_on")
                        token = f"Error calling decide_to_go_on with {fn_result=}\n"
                else:

                    token = f"--- {fn_log} result --- \n"
                    # if json dict we look for keys to extract
                    if fn_result_json:
                        log.info(f"{fn_result_json} dict parsing")
                        if fn_result_json.get('stdout'):
                            text = fn_result_json.get('stdout')
                            token += self.remove_invisible_characters(text)
                        if fn_result_json.get('stderr'):
                            text = fn_result_json.get('stdout')
                            token += self.remove_invisible_characters(text)
                        # If neither 'stdout' nor 'stderr' is present, dump the entire JSON
                        if 'stdout' not in fn_result_json and 'stderr' not in fn_result_json:
                            log.info(f"No recognised keys ('stdout' or 'stderr') in dict: {fn_result_json=} - dumping it all")
                            token += f"{json.dumps(fn_result_json, indent=2)}\n"  # Added `indent=2` for readability
                    else:
                        # probably a string, just return it
                        log.info(f"{fn_result_json} non-dict (String?) parsing")
                        token += f"{self.remove_invisible_characters(fn_result)}\n--- end ---\n"
                
                self.loop_text += token
                self.token_queue.append(token)
                fn_exec_one.end(output=token) if fn_exec_one else None
            fn_exec.end(output=self.loop_text) if fn_exec else None        

        else:
            token = f"\n[{self.loop_guardrail}] No function executions were performed\n"
            self.token_queue.append(token)
            self.loop_text += token
            
    def _loop_output_text(self, response:GenerateContentResponse):
        if not response:
            return
        
        for chunk in response:
            if not chunk:
                continue

            log.debug(f"[{self.loop_guardrail}] {chunk=}")
            try:
                if hasattr(chunk, 'text') and isinstance(chunk.text, str):
                    token = chunk.text
                    self.token_queue.append(token)
                    self.loop_text += token
                else:
                    log.info("skipping chunk with no text")
                
            except ValueError as err:
                self.token_queue.append(f"{str(err)} for {chunk=}")

    def _loop_metadata(self, response:GenerateContentResponse, gen=None):
        loop_metadata = None
        if response:
            loop_metadata = response.usage_metadata
            if loop_metadata:
                self.usage_metadata = {
                    "prompt_token_count": self.usage_metadata["prompt_token_count"] + (loop_metadata.prompt_token_count or 0),
                    "candidates_token_count": self.usage_metadata["candidates_token_count"] + (loop_metadata.candidates_token_count or 0),
                    "total_token_count": self.usage_metadata["total_token_count"] + (loop_metadata.total_token_count or 0),
                }
                self.token_queue.append((
                    "\n-- Agent response -- " 
                    f"Loop tokens: [{loop_metadata.prompt_token_count}]/[{self.usage_metadata['prompt_token_count']}] "
                    f"Session tokens: [{loop_metadata.total_token_count}]/[{self.usage_metadata['total_token_count']}] \n"
                ))
            gen.end(output=response.to_dict()) if gen else None
        else:
            gen.end(output="No response received") if gen else None
        
        return loop_metadata

    def _loop_call_agent(self, chat:ChatSession):
        response=None
        gen=None
        try:
            self.token_queue.append("\n= Calling Agent =\n")
            loop_content = self.loop_content
            gen = self.loop_span.generation(
                name=f"loop_{self.loop_guardrail}",
                model=self.model_name,
                input = {'content': self.loop_content},
            ) if self.loop_span else None

            log.info(f"{loop_content=}")
            response: GenerateContentResponse = chat.send_message(loop_content, request_options=RequestOptions(
                                    retry=retry.Retry(
                                        initial=1, 
                                        multiplier=2, 
                                        maximum=10, 
                                        timeout=60
                                    )
                                    ))
        except RetryError as err:
            msg = f"Retry error - lets try again if its occured less than twice: {str(err)}"
            log.warning(msg)
            self.token_queue.append(msg)
            self.loop_text += msg
            
        except Exception as e:
            msg = f"Error sending {loop_content} to model: {str(e)}"
            if "finish_reason: 10" in str(e):
                    msg = (f"I encounted an error on the previous step when sending this data: {json.dumps(loop_content)}"
                            " -- Can you examine what was sent and identify why? If possible correct it so we can answer the original user question.")
            log.error(msg + f"{traceback.format_exc()}")
            self.token_queue.append(msg)
            self.loop_text += msg
        
        return response, gen

    def run_agent_loop(self, chat:ChatSession, content:list, callback=None, guardrail_max=10, loop_return=3): # type: ignore
        """
        Runs the agent loop, sending messages to the orchestrator, processing responses, and executing functions.

        Args:
            chat: The chat object for interaction with the orchestrator.
            content: The initial content to send to the agent.
            callback: The callback object for handling intermediate responses. If not supplied will use self.IOCallback()
            guardrail_max (int): The maximum number of iterations for the loop.
            loop_return (int): The number of last loop iterations to return. Default 3 will return last 3 iterations. If loop_return > guardrail_max then all iterations are returned.

        Returns:
            tuple: (big_text, usage_metadata) from the loop execution.
        """
        if not callback:
            callback = self.IOCallback()
        self.big_result = []
        self.usage_metadata = {
            "prompt_token_count": 0,
            "candidates_token_count": 0,
            "total_token_count": 0
        }
        
        self.functions_called =[]

        span = self.trace.span(
            name=f"GenAIFunctionProcesser_{self.__class__.__name__}",
            parent_observation_id=self.parent_observation_id,
            input = {'content': content},
        ) if self.trace else None

        self.loop_span = None
        # Initialize token queue to ensure sequential processing
        self.token_queue = deque()
        self.loop_text = ""
        self.loop_content = content
        self.loop_guardrail = 0
        self.loop_executed_responses = []
        self.loop_callback = callback

        while self.loop_guardrail < guardrail_max:
            self.token_queue.append(f"\n----Loop [{self.loop_guardrail}] Start------\nFunctions: {list(self.funcs.keys())}\n")

            content_parse = ""
            for i, chunk in enumerate(content):
                content_parse += f"\n - {i}) {chunk}"
            content_parse += f"\n== End input content for loop [{self.loop_guardrail}] =="

            log.info(f"== Start input content for loop [{self.loop_guardrail}]\n ## Content: {content_parse}")
            
            # resets for this loop
            self.loop_text = ""  
            response = None
            self.loop_executed_responses = []

            self.loop_span = span.span(
                name=f"loop_{self.loop_guardrail}",
                model=self.model_name,
                input = {'content': self.loop_content},
            ) if span else None

            response, gen = self._loop_call_agent(chat)

            loop_metadata = self._loop_metadata(response, gen)

            self._loop_output_text(response)

            self._loop_handle_executed_responses(response)

            self._loop_update_content()

            self.token_queue.append(f"\n----Loop [{self.loop_guardrail}] End------\n{self.usage_metadata}\n----------------------")
            self.loop_span.end(output=self.loop_content, metadata=loop_metadata) if self.loop_span else None

            go_on_check = self.check_function_result("decide_to_go_on", {"go_on": False})
            if go_on_check:
                log.info("Breaking agent loop")
                break
            
            while self.token_queue:
                token = self.token_queue.popleft()
                self.loop_callback.on_llm_new_token(token=token)
            
            self.loop_guardrail += 1
            if self.loop_guardrail > guardrail_max:
                log.warning(f"Guardrail kicked in, more than {guardrail_max} loops")
                break
        
        while self.token_queue:
            token = self.token_queue.popleft()
            self.loop_callback.on_llm_new_token(token=token)
        
        self.usage_metadata["functions_called"] = self.functions_called

        big_text = "\n".join(self.big_result[-loop_return:])
        span.end(output=big_text, metadata=self.sage_metadata) if span else None

        return big_text, self.usage_metadata

    class IOCallback:
        """
        This is a default callback that will print to console any tokens it recieves.
        """
        def on_llm_new_token(self, token:str):
            print(token)
        def on_llm_end(self, response):
            print(f"\nFull response: \n{response}")

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
        return {"go_on": go_on, "chat_summary": chat_summary}
    