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
from ..logging import log


import datetime

from langchain.prompts.prompt import PromptTemplate

from ..utils import load_config_key
from .vectorstore import pick_vectorstore


def pick_prompt(vector_name, chat_history=[]):
    """Pick a custom prompt"""
    log.debug('Picking prompt')

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

    memory_str = "\n## Your Memory (ignore if not relevant to question)\n{context}\n"

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
    
    log.debug(f"--Prompt_template: {prompt_template}") 
    QA_PROMPT = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )

    return QA_PROMPT

def pick_chat_buddy(vector_name):
    chat_buddy = load_config_key("chat_buddy", vector_name, filename = "config/llm_config.yaml")
    if chat_buddy is not None:
        log.info(f"Got chat buddy {chat_buddy} for {vector_name}")
        buddy_description = load_config_key("chat_buddy_description", vector_name)
        return chat_buddy, buddy_description
    return None, None


def pick_agent(vector_name):
    agent_str = load_config_key("agent", vector_name, filename = "config/llm_config.yaml")
    if agent_str == "yes":
        return True
    
    return False

def pick_shared_vectorstore(vector_name, embeddings):
    shared_vectorstore = load_config_key("shared_vectorstore", vector_name, filename = "config/llm_config.yaml")
    vectorstore = pick_vectorstore(shared_vectorstore, embeddings)
    return vectorstore


def get_chat_history(inputs, vector_name, last_chars=1000, summary_chars=1500) -> str:
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
    log.info(f"Recent chat history: {recent_history}")
    
    # Summarize chat history too
    remaining_history = full_history
    log.info(f"Remaining chat history: {remaining_history}")
    doc_history = Document(page_content=remaining_history)
    chat_summary = summarise_docs([doc_history], vector_name=vector_name, skip_if_less=last_chars)
    text_sum = ""
    for summ in chat_summary:
        text_sum += summ.page_content + "\n"
    
    log.info(f"Conversation Summary: {text_sum}")
    
    # Make sure the summary is not longer than `summary_chars` characters
    summary = text_sum[:summary_chars]
    
    # Concatenate the summary and the last `last_chars` characters of the chat history
    return summary + "\n### Recent Chat History\n..." + recent_history
