#   Copyright [2023] [Sunholo ApS]
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
import logging

from ..utils.config import load_config_key

logging.basicConfig(level=logging.INFO)

def pick_llm(vector_name):
    logging.debug('Picking llm')
    
    llm_str = load_config_key("llm", vector_name, filename = "config/llm_config.yaml")
    
    if llm_str == 'openai':
        from langchain.embeddings import OpenAIEmbeddings
        #from langchain.llms import OpenAI
        from langchain.chat_models import ChatOpenAI

        #llm = OpenAI(temperature=0)
        llm_chat = ChatOpenAI(model="gpt-4", temperature=0.3, max_tokens=3000)
        llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0, max_tokens=11000)
        embeddings = OpenAIEmbeddings()
        logging.debug("Chose OpenAI")
    elif llm_str == 'vertex':
        from langchain.llms import VertexAI
        from langchain.embeddings import VertexAIEmbeddings
        from langchain.chat_models import ChatVertexAI
        llm = ChatVertexAI(temperature=0, max_output_tokens=1024)
        llm_chat = ChatVertexAI(temperature=0, max_output_tokens=1024)
        embeddings = VertexAIEmbeddings()
        logging.debug("Chose VertexAI text-bison")
    elif llm_str == 'codey':
        from langchain.llms import VertexAI
        from langchain.embeddings import VertexAIEmbeddings
        from langchain.chat_models import ChatVertexAI
        llm = VertexAI(model_name = "code-bison", temperature=0.5, max_output_tokens=2048)
        llm_chat = ChatVertexAI(model_name="codechat-bison", max_output_tokens=2048)
        embeddings = VertexAIEmbeddings()
        logging.debug("Chose VertexAI code-bison")
    elif llm_str == 'model_garden':
        from ..patches.langchain.vertexai import VertexAIModelGarden
        model_garden_config = load_config_key("gcp_config", vector_name, filename = "config/llm_config.yaml")
        if model_garden_config is None:
            raise ValueError("llm='model_garden' requires a gcp_config entry in config yaml file")
        llm = VertexAIModelGarden(project=model_garden_config['project_id'], 
                                  endpoint_id=model_garden_config['endpoint_id'], 
                                  location=model_garden_config['location'], 
                                  allowed_model_args=["max_tokens"])
        llm_chat = llm
        embeddings = None
        logging.debug("Chose VertexAIModelGarden")

    else:
        raise NotImplementedError(f'No llm implemented for {llm_str}')   

    return llm, embeddings, llm_chat

def pick_streaming(vector_name):
    
    llm_str = load_config_key("llm", vector_name, filename = "config/llm_config.yaml")
    
    if llm_str == 'openai':
        return True
    
    return False
 

