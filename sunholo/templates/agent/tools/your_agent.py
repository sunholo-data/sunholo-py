from sunholo.genai import GenAIFunctionProcessor
from sunholo.utils import ConfigManager

from my_log import log


class QuartoProcessor(GenAIFunctionProcessor):
    def construct_tools(self) -> dict:
        tools = self.config.vacConfig("tools")
        quarto_config = tools.get("quarto")
        
        def decide_to_go_on(go_on: bool):
            """
            Examine the chat history.  If the answer to the user's question has been answered, then go_on=False.
            If the chat history indicates the answer is still being looked for, then go_on=True.
            If there is no chat history, then go_on=True.
            If there is an error that can't be corrected or solved by you, then go_on=False.
            If there is an error but you think you can solve it by correcting your function arguments (such as an incorrect source), then go_on=True
            If you want to ask the user a question or for some more feedback, then go_on=False.
            
            Args:
                go_on: boolean Whether to continue searching or fetching from the AlloyDB database
            
            Returns:
                boolean: True to carry on, False to continue
            """
            return go_on

        def quarto_render() -> dict:
            """
            ...
            
            Args:
            
            
            Returns:
                
            """
            pass

        return {
            "quarto_render": quarto_render,
            "decide_to_go_on": decide_to_go_on
        }

def quarto_content(question: str, chat_history=[]) -> str:
    prompt_config = ConfigManager("quarto")
    alloydb_template = prompt_config.promptConfig("quarto_template")
    
    conversation_text = ""
    for human, ai in chat_history:
        conversation_text += f"Human: {human}\nAI: {ai}\n"

    return alloydb_template.format(the_question=question, chat_history=conversation_text[-10000:])


def get_quarto(config:ConfigManager, processor:QuartoProcessor):

    tools = config.vacConfig('tools')

    if tools and tools.get('quarto'):
        model_name = None
        if config.vacConfig('llm') != "vertex":
            model_name = 'gemini-1.5-flash'
        alloydb_model = processor.get_model(
            system_instruction=(
                    "You are a helpful Quarto agent that helps users create and render Quarto documents. "
                    "When you think the answer has been given to the satisfaction of the user, or you think no answer is possible, or you need user confirmation or input, you MUST use the decide_to_go_on(go_on=False) function"
                    "When you want to ask the question to the user, mark the go_on=False in the function"
                ),
            model_name=model_name
        )

        if alloydb_model:
            return alloydb_model

    log.error("Error initializing quarto model")    
    return None