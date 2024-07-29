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
from ..custom_logging import log



from ..components import get_llm
from ..chunker.splitter import chunk_doc_to_docs

from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatVertexAI
from langchain.chat_models import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.llms import OpenAI
from langchain.llms import VertexAI
from langchain.chains.summarize import load_summarize_chain
from langchain.schema import Document

prompt_template = """Write a summary for below, including key concepts, people and distinct information but do not add anything that is not in the original text:

"{text}"

SUMMARY:"""
MAP_PROMPT = PromptTemplate(template=prompt_template, input_variables=["text"])


import time
import random

def summarise_docs(docs, vector_name, skip_if_less=10000):
    llm  = get_llm(vector_name)
  
    if isinstance(llm, ChatOpenAI) or isinstance(llm, OpenAI):
        llm = ChatOpenAI(model="gpt-3.5-turbo-16k")
        llm.max_tokens = 2000
        max_content_length = 11000
    elif isinstance(llm, ChatVertexAI) or isinstance(llm, VertexAI):
        llm.max_output_tokens=1024
        max_content_length=1024
    elif isinstance(llm, ChatGoogleGenerativeAI):
        llm.max_output_tokens = 2000
        max_content_length = 28000
    else:
        raise ValueError("Unsupported llm type: %s" % llm)

    chain = load_summarize_chain(llm, chain_type="map_reduce", verbose=True,
                                 map_prompt=MAP_PROMPT,
                                 combine_prompt=MAP_PROMPT)

    summaries = []
    for doc in docs:
        log.info(f"summarise: doc {doc}")
        if len(doc.page_content) < skip_if_less:
            log.info(f"Skipping summarisation as below {skip_if_less} characters")
            continue
        elif len(doc.page_content) > max_content_length:
            log.warning(f"Trimming content to {max_content_length} characters")
            doc.page_content = doc.page_content[:max_content_length]

        metadata = doc.metadata
        chunks = chunk_doc_to_docs([doc], vector_name=vector_name)

        # Initial delay
        delay = 1.0  # 1 second, for example
        max_delay = 300.0  # Maximum delay, adjust as needed

        for attempt in range(2):  # Attempt to summarize 2 times
            try:
                summary = chain.run(chunks)
                break  # If the summary was successful, break the loop
            except Exception as e:
                log.error(f"Error while summarizing on attempt {attempt+1}: {e}")
                print(f"Failure, waiting {delay} seconds before retrying...")
                time.sleep(delay)  # Wait for the delay period
                delay = min(delay * 2 + random.uniform(0, 1), max_delay)  # Exponential backoff with jitter
        else:
            log.error(f"Failed to summarize after 5 attempts")
            continue  # If we've failed after 5 attempts, move on to the next document

        
        metadata["type"] = "summary"
        summary = Document(page_content=summary, metadata=metadata)
        log.info(f"Summary: {summary}")
        summaries.append(summary)
        
    return summaries
