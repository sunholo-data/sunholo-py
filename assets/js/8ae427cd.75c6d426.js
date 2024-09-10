"use strict";(self.webpackChunkdocs=self.webpackChunkdocs||[]).push([[4673],{1182:(n,e,s)=>{s.r(e),s.d(e,{assets:()=>l,contentTitle:()=>r,default:()=>u,frontMatter:()=>i,metadata:()=>c,toc:()=>a});var o=s(4848),t=s(8453);const i={},r="process_funcs_cls.py",c={id:"sunholo/genai/process_funcs_cls",title:"process_funcs_cls.py",description:"Source: sunholo/genai/processfuncscls.py",source:"@site/docs/sunholo/genai/process_funcs_cls.md",sourceDirName:"sunholo/genai",slug:"/sunholo/genai/process_funcs_cls",permalink:"/docs/sunholo/genai/process_funcs_cls",draft:!1,unlisted:!1,editUrl:"https://github.com/sunholo-data/sunholo-py/tree/main/docs/docs/sunholo/genai/process_funcs_cls.md",tags:[],version:"current",frontMatter:{},sidebar:"tutorialSidebar",previous:{title:"init.py",permalink:"/docs/sunholo/genai/init"},next:{title:"safety.py",permalink:"/docs/sunholo/genai/safety"}},l={},a=[{value:"Classes",id:"classes",level:2},{value:"GenAIFunctionProcessor",id:"genaifunctionprocessor",level:3}];function h(n){const e={a:"a",br:"br",code:"code",em:"em",h1:"h1",h2:"h2",h3:"h3",li:"li",p:"p",pre:"pre",strong:"strong",ul:"ul",...(0,t.R)(),...n.components};return(0,o.jsxs)(o.Fragment,{children:[(0,o.jsx)(e.h1,{id:"process_funcs_clspy",children:"process_funcs_cls.py"}),"\n",(0,o.jsxs)(e.p,{children:[(0,o.jsx)(e.em,{children:"Source"}),": ",(0,o.jsx)(e.a,{href:"https://github.com/sunholo-data/sunholo-py/blob/main/sunholo/genai/process_funcs_cls.py",children:"sunholo/genai/process_funcs_cls.py"})]}),"\n",(0,o.jsx)(e.h2,{id:"classes",children:"Classes"}),"\n",(0,o.jsx)(e.h3,{id:"genaifunctionprocessor",children:"GenAIFunctionProcessor"}),"\n",(0,o.jsx)(e.p,{children:"A generic class for processing function calls from google.generativeai function calling models."}),"\n",(0,o.jsxs)(e.p,{children:["This class provides a framework for handling multiple function calls in responses\nfrom generative AI systems. Users of this class should subclass it and provide\ntheir own implementation of the ",(0,o.jsx)(e.code,{children:"construct_tools"})," method, which returns a dictionary\nof function names mapped to their implementations."]}),"\n",(0,o.jsx)(e.p,{children:"Attributes:\nconfig (ConfigManager): Configuration manager instance. Reach values via self.config within your own construct_tools() method\nfuncs (dict): A dictionary of function names mapped to their implementations."}),"\n",(0,o.jsx)(e.p,{children:"Example usage:"}),"\n",(0,o.jsx)(e.pre,{children:(0,o.jsx)(e.code,{className:"language-python",children:'class AlloyDBFunctionProcessor(GenAIFunctionProcessor):\n    def construct_tools(self) -> dict:\n        pass\n\nconfig = ConfigManager()\nalloydb_processor = AlloyDBFunctionProcessor(config)\n\nresults = alloydb_processor.process_funcs(full_response)\n\nalloydb_model = alloydb_processor.get_model(\n    model_name="gemini-1.5-pro",\n    system_instruction="You are a helpful AlloyDB agent that helps users search and extract documents from the database."\n)\n'})}),"\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsxs)(e.li,{children:[(0,o.jsx)(e.strong,{children:"init"}),"(self, config: sunholo.utils.config_class.ConfigManager)","\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsx)(e.li,{children:"Initializes the GenAIFunctionProcessor with the given configuration."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,o.jsx)(e.p,{children:"Args:\nconfig (ConfigManager): The configuration manager instance."}),"\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsxs)(e.li,{children:["_validate_functions(self)","\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsxs)(e.li,{children:["Validates that all functions in the ",(0,o.jsx)(e.code,{children:"funcs"})," dictionary have docstrings."]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,o.jsxs)(e.p,{children:["This method checks each function in the ",(0,o.jsx)(e.code,{children:"funcs"})," dictionary to ensure it has\na docstring. If a function is missing a docstring, an error is logged, and\na ",(0,o.jsx)(e.code,{children:"ValueError"})," is raised."]}),"\n",(0,o.jsx)(e.p,{children:"Raises:\nValueError: If any function is missing a docstring."}),"\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsxs)(e.li,{children:["check_function_result(self, function_name, target_value, api_requests_and_responses=[])","\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsx)(e.li,{children:"Checks if a specific function result in the api_requests_and_responses contains a certain value."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,o.jsxs)(e.p,{children:["Args:\nfunction_name (str): The name of the function to check.\ntarget_value: The value to look for in the function result.\napi_requests_and_responses (list, optional): List of function call results to check.\nIf not provided, the method will use ",(0,o.jsx)(e.code,{children:"self.last_api_requests_and_responses"}),"."]}),"\n",(0,o.jsx)(e.p,{children:"Returns:\nbool: True if the target_value is found in the specified function's result, otherwise False."}),"\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsxs)(e.li,{children:["construct_tools(self) -> dict","\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsx)(e.li,{children:"Constructs a dictionary of tools (functions) specific to the application."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,o.jsx)(e.p,{children:"This method should be overridden in subclasses to provide the specific\nfunction implementations required for the application."}),"\n",(0,o.jsx)(e.p,{children:"Note: All functions need arguments to avoid errors."}),"\n",(0,o.jsx)(e.p,{children:"Returns:\ndict: A dictionary where keys are function names and values are function objects"}),"\n",(0,o.jsx)(e.p,{children:"Raises:\nNotImplementedError: If the method is not overridden in a subclass."}),"\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsxs)(e.li,{children:["decide_to_go_on(go_on: bool, chat_summary: str) -> dict","\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsxs)(e.li,{children:["Examine the chat history.  If the answer to the user's question has been answered, then go_on=False.\nIf the chat history indicates the answer is still being looked for, then go_on=True.\nIf there is no chat history, then go_on=True.\nIf there is an error that can't be corrected or solved by you, then go_on=False.\nIf there is an error but you think you can solve it by correcting your function arguments (such as an incorrect source), then go_on=True\nIf you want to ask the user a question or for some more feedback, then go_on=False.",(0,o.jsx)(e.br,{}),"\n","Avoid asking the user if you suspect you can solve it yourself with the functions at your disposal - you get top marks if you solve it yourself without help.\nWhen calling, please also add a chat summary of why you think the function should  be called to end."]}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,o.jsx)(e.p,{children:"Args:\ngo_on: boolean Whether to continue searching for an answer\nchat_summary: string A brief explanation on why go_on is TRUE or FALSE"}),"\n",(0,o.jsx)(e.p,{children:"Returns:\nboolean: True to carry on, False to continue"}),"\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsxs)(e.li,{children:["get_model(self, system_instruction: str, generation_config=None, model_name: str = None, tool_config: str = 'auto')","\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsx)(e.li,{children:"Constructs and returns the generative AI model configured with the tools."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,o.jsxs)(e.p,{children:["This method creates a generative AI model using the tools defined in the\n",(0,o.jsx)(e.code,{children:"funcs"})," dictionary and the provided configuration options."]}),"\n",(0,o.jsx)(e.p,{children:"Args:\nmodel_name (str): The name of the model to use.\nsystem_instruction (str): Instructions for the AI system.\ngeneration_config (dict, optional): Configuration for generation, such as temperature.\ntool_config (str, optional): Configuration for tool behaviour: 'auto' it decides, 'none' no tools, 'any' always use tools"}),"\n",(0,o.jsx)(e.p,{children:"Returns:\nGenerativeModel: An instance of the GenerativeModel configured with the provided tools."}),"\n",(0,o.jsx)(e.p,{children:"Example usage:"}),"\n",(0,o.jsx)(e.pre,{children:(0,o.jsx)(e.code,{className:"language-python",children:'alloydb_model = alloydb_processor.get_model(\n    model_name="gemini-1.5-pro",\n    system_instruction="You are a helpful AlloyDB agent that helps users search and extract documents from the database."\n)\n'})}),"\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsxs)(e.li,{children:["\n",(0,o.jsx)(e.p,{children:"parse_as_parts(self, api_requests_and_responses=[])"}),"\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsx)(e.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,o.jsxs)(e.li,{children:["\n",(0,o.jsx)(e.p,{children:"parse_as_string(self, api_requests_and_responses=[])"}),"\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsx)(e.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n",(0,o.jsxs)(e.li,{children:["\n",(0,o.jsx)(e.p,{children:"process_funcs(self, full_response, output_parts=True) -> Union[list['Part'], str]"}),"\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsx)(e.li,{children:"Processes the functions based on the full_response from the generative model."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,o.jsxs)(e.p,{children:["This method iterates through each part of the response, extracts function\ncalls and their parameters, and executes the corresponding functions defined\nin the ",(0,o.jsx)(e.code,{children:"funcs"})," dictionary."]}),"\n",(0,o.jsx)(e.p,{children:"Args:\nfull_response: The response object containing function calls.\noutput_parts (bool): Indicates whether to return structured parts or plain strings."}),"\n",(0,o.jsx)(e.p,{children:"Returns:\nlist[Part] | str: A list of Part objects or a formatted string with the results."}),"\n",(0,o.jsx)(e.p,{children:"Example usage:"}),"\n",(0,o.jsx)(e.pre,{children:(0,o.jsx)(e.code,{className:"language-python",children:"results = alloydb_processor.process_funcs(full_response)\n"})}),"\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsxs)(e.li,{children:["run_agent_loop(self, chat, content, callback, guardrail_max=10)","\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsx)(e.li,{children:"Runs the agent loop, sending messages to the orchestrator, processing responses, and executing functions."}),"\n"]}),"\n"]}),"\n"]}),"\n",(0,o.jsx)(e.p,{children:"Args:\nchat: The chat object for interaction with the orchestrator.\ncontent: The initial content to send to the agent.\ncallback: The callback object for handling intermediate responses.\nguardrail_max (int): The maximum number of iterations for the loop."}),"\n",(0,o.jsx)(e.p,{children:"Returns:\ntuple: (big_text, usage_metadata) from the loop execution."}),"\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsxs)(e.li,{children:["tool_config_setting(self, mode: str)","\n",(0,o.jsxs)(e.ul,{children:["\n",(0,o.jsx)(e.li,{children:"No docstring available."}),"\n"]}),"\n"]}),"\n"]})]})}function u(n={}){const{wrapper:e}={...(0,t.R)(),...n.components};return e?(0,o.jsx)(e,{...n,children:(0,o.jsx)(h,{...n})}):h(n)}},8453:(n,e,s)=>{s.d(e,{R:()=>r,x:()=>c});var o=s(6540);const t={},i=o.createContext(t);function r(n){const e=o.useContext(i);return o.useMemo((function(){return"function"==typeof n?n(e):{...e,...n}}),[e,n])}function c(n){let e;return e=n.disableParentContext?"function"==typeof n.components?n.components(t):n.components||t:r(n.components),o.createElement(i.Provider,{value:e},n.children)}}}]);