#   Copyright [2024] [Holosun ApS]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
from ..logging import setup_logging

logging = setup_logging()
import datetime

from langchain.prompts.prompt import PromptTemplate

from ..utils import load_config_key
from .vectorstore import pick_vectorstore

def pick_prompt(vector_name, chat_history=[]):
    """
    This function picks a custom prompt based on the vector_name parameter and an optional chat_history parameter.

    It loads the prompt_str parameter from a configuration file and then configures the prompt based on this parameter. If the prompt_str parameter contains certain predefined strings, the function raises a ValueError.

    The function returns a PromptTemplate object that represents the configured prompt.

    :param vector_name: The name of the vector used to select the prompt.
    :param chat_history: A list of chat history items. Defaults to an empty list.
    :return: A PromptTemplate object that represents the configured prompt.
    :raises ValueError: If the prompt_str parameter contains certain predefined strings.
    """
    logging.debug('Picking prompt')

    prompt_str = load_config_key("prompt", vector_name, filename = "config/llm_config.yaml")

    the_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')
    prompt_str_default = f"""You are Edmonbrain the chat bot created by Mark Edmondson. It is now {the_date}.
Use your memory to answer the question at the end.
Indicate in your reply how sure you are about your answer, for example whether you are certain, taking your best guess, or its very speculative.

If you don't know, just say you don't know - don't make anything up. Avoid generic boilerplate answers.
Consider why the question was asked, and offer follow up questions linked to those reasons.
Any questions about how you work should direct users to issue the `!help` command.
"""
    if prompt_str is not None:
        if "{context}" in prompt_str:
            raise ValueError("prompt must not contain a string '{context}'")
        if "{question}" in prompt_str:
            raise ValueError("prompt must not contain a string '{question}'")
        prompt_str_default = prompt_str_default + "\n" + prompt_str
    
    chat_summary = ""
    original_question = ""
    if len(chat_history) != 0:
        original_question = chat_history[0][0]
        chat_summary = get_chat_history(chat_history, vector_name)
    
    follow_up = "\nIf you can't answer the human's question without more information, ask a follow up question"

    agent_buddy, agent_description = pick_chat_buddy(vector_name)
    if agent_buddy:
        follow_up += f""" either to the human, or to your friend bot.
You bot friend will reply back to you within your chat history.
Ask {agent_buddy} for help with topics: {agent_description}
Ask clarification questions to the human and wait for response if your friend bot can't help.
Don't repeat the question if you can see the answer in the chat history (from any source)  
This means there are three people in this conversation - you, the human and your assistant bot.
Asking questions to your friend bot are only allowed with this format:
€€Question€€ 
(your question here, including all required information needed to answer the question fully)
Can you help, {agent_buddy} , with the above question?
€€End Question€€
"""
    else:
        follow_up += ".\n"

    memory_str = "\n## Your Memory (ignore if not relevant to question)
{context}\n"

    current_conversation = ""
    if chat_summary != "":
        current_conversation =f"## Current Conversation\n{chat_summary}\n"
        current_conversation = current_conversation.replace("{","{{").replace("}","}}") #escape {} characters
   
    buddy_question = ""
    my_q = "## Current Question\n{question}\n"
    if agent_buddy:
        buddy_question = f"""(Including, if needed, your question to {agent_buddy})"""
        my_q = f"## Original Question that started conversation\n{original_question}\n" + my_q

    prompt_template = prompt_str_default + follow_up + memory_str + current_conversation + my_q + buddy_question + "\n## Your response:\n"
    
    logging.debug(f"--Prompt_template: {prompt_template}") 
    QA_PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    return QA_PROMPT
def pick_chat_buddy(vector_name):
    """
    This function picks a chat buddy based on the vector_name parameter.

    It loads the chat_buddy parameter from a configuration file and then configures the chat buddy based on this parameter. If the chat_buddy parameter is not None, the function also loads the buddy_description parameter from the configuration file.

    The function returns a tuple containing the chat buddy and the buddy description.

    :param vector_name: The name of the vector used to select the chat buddy.
    :return: A tuple containing the chat buddy and the buddy description.
    """
    chat_buddy = load_config_key("chat_buddy", vector_name, filename = "config/llm_config.yaml")
    if chat_buddy is not None:
        logging.info(f"Got chat buddy {chat_buddy} for {vector_name}")
        buddy_description = load_config_key("chat_buddy_description", vector_name)
        return chat_buddy, buddy_description
    return None, None
def pick_agent(vector_name):
    """
    This function determines whether an agent should be picked based on the vector_name parameter.

    It loads the agent_str parameter from a configuration file and then checks if it is equal to 'yes'. If it is, the function returns True. Otherwise, it returns False.

    :param vector_name: The name of the vector used to determine whether an agent should be picked.
    :return: A boolean value indicating whether an agent should be picked.
    """
    agent_str = load_config_key("agent", vector_name, filename = "config/llm_config.yaml")
    if agent_str == "yes":
        return True
    
    return False
def pick_shared_vectorstore(vector_name, embeddings):
    """
    This function picks a shared vectorstore based on the vector_name and embeddings parameters.

    It loads the shared_vectorstore parameter from a configuration file and then calls the pick_vectorstore function with this parameter and the embeddings parameter to pick a shared vectorstore.

    The function returns the picked shared vectorstore.

    :param vector_name: The name of the vector used to pick the shared vectorstore.
    :param embeddings: The embeddings used to pick the shared vectorstore.
    :return: The picked shared vectorstore.
    """
    shared_vectorstore = load_config_key("shared_vectorstore", vector_name, filename = "config/llm_config.yaml")
    vectorstore = pick_vectorstore(shared_vectorstore, embeddings)
    return vectorstore
def get_chat_history(inputs, vector_name, last_chars=1000, summary_chars=1500) -> str:
    """
    This function gets the chat history based on the inputs and vector_name parameters, and optional last_chars and summary_chars parameters.

    It prepares the full chat history, gets the last `last_chars` characters of the full chat history, summarizes the chat history, and then concatenates the summary and the last `last_chars` characters of the chat history.

    The function returns the concatenated summary and last `last_chars` characters of the chat history.

    :param inputs: A list of inputs used to get the chat history.
    :param vector_name: The name of the vector used to get the chat history.
    :param last_chars: The number of last characters of the chat history to get. Defaults to 1000.
    :param summary_chars: The number of characters of the summary to get. Defaults to 1500.
    :return: The concatenated summary and last `last_chars` characters of the chat history.
    """
    from langchain.schema import Document
    from ..summarise import summarise_docs

    # Prepare the full chat history
    res = []
    for human, ai in inputs:
        res.append(f"Human:{human}\nAI:{ai}")
    full_history = "\n".join(res)
    
    # Get the last `last_chars` characters of the full chat history
    last_bits = []
    for human, ai in reversed(inputs):
        add_me = f"Human:{human}\nAI:{ai}"
        last_bits.append(add_me)

    recent_history = "\n".join(reversed(last_bits))
    recent_history = recent_history[-last_chars:]
    logging.info(f"Recent chat history: {recent_history}")
    
    # Summarize chat history too
    remaining_history = full_history
    logging.info(f"Remaining chat history: {remaining_history}")
    doc_history = Document(page_content=remaining_history)
    chat_summary = summarise_docs([doc_history], vector_name=vector_name, skip_if_less=last_chars)
    text_sum = ""
    for summ in chat_summary:
        text_sum += summ.page_content + "\n"
    
    logging.info(f"Conversation Summary: {text_sum}")
    
    # Make sure the summary is not longer than `summary_chars` characters
    summary = text_sum[:summary_chars]
    
    # Concatenate the summary and the last `last_chars` characters of the chat history
    return summary + "\n### Recent Chat History\n..." + recent_history