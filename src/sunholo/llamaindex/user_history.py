from ..utils import ConfigManager
from ..custom_logging import log
from .llamaindex_class import LlamaIndexVertexCorpusManager

import datetime

def add_user_history_rag(
        user_id:str, 
        config:ConfigManager, 
        question:str, 
        answer:str, 
        metadata:dict={},
        user_history_template:str=None):
    # add user history to its own RAG store

    log.info(f"Adding user history to RAG store: {question} and {answer}")

    manager = LlamaIndexVertexCorpusManager(config)

    corpus = manager.create_corpus(user_id, description=f"Personal user history for {user_id}")

    current_datetime = datetime.datetime.now()

    # Convert to string with desired format
    current_datetime_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

    if user_history_template is None:
        user_history_template="""Question from {user_id} at {the_date}: {the_question}\nAnswer: {the_answer}\nMetadata:{the_metadata}"""

    log.info(f"Found corpus for {user_id}: {corpus}")
    user_history = user_history_template.format(
        user_id=user_id, 
        the_date=current_datetime_str,
        the_question=question, 
        the_answer=answer,
        the_metadata=metadata
        )

    try:
        manager.upload_text(
            text=user_history, 
            corpus_display_name=user_id, 
            description=f"{user_id} chat history for {current_datetime}"
            )
    except Exception as err:
        log.error(f"Could not upload LlamaIndex QNA RAG history: {str(err)}")
    
    return user_history

def get_user_history_chunks(user_id:str, config:ConfigManager, query):

    try:
        manager = LlamaIndexVertexCorpusManager(config)

        manager.create_corpus(user_id)

        response = manager.query_corpus(query, user_id)
        log.info(f"User history got: {response=}")
        user_history_memory = []
        for chunk in response.contexts.contexts:
            user_history_memory.append(chunk.text)
        
        log.info(f"User history chunks: {user_history_memory}")

        return "\n".join(user_history_memory)
    except Exception as err:
        log.error(f"Could not find user history due to error: {str(err)}")

        return f"No user history available due to error: {str(err)}"
