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
from ..utils.config import load_config_key, load_config, get_module_filepath

logging = setup_logging()

"""
This function selects a Language Learning Model (LLM) based on the vector_name parameter.

It loads the llm_str parameter from a configuration file and then configures the LLM, embeddings, and llm_chat based on this parameter.

If the llm_str parameter matches one of the predefined strings ('openai', 'vertex', 'codey', 'model_garden'), the function configures the LLM, embeddings, and llm_chat accordingly. If the llm_str parameter does not match any of the predefined strings, the function raises a NotImplementedError.

:param vector_name: The name of the vector used to select the LLM.
:return: A tuple containing the configured LLM, embeddings, and llm_chat.
:raises NotImplementedError: If the llm_str parameter does not match any of the predefined strings.
"""
def pick_llm(vector_name):
    logging.debug('Picking llm')
    
    llm_str = load_config_key("llm", vector_name, filename = "config/llm_config.yaml")
    
    if llm_str == 'openai':
        llm_chat = get_llm_chat(vector_name)
        llm = get_llm_chat(vector_name, model="gpt-3.5-turbo-16k") # TODO: fix it needs llm_chat and not llm
        embeddings = get_embeddings(vector_name)
        logging.debug("Chose OpenAI")
    elif llm_str == 'vertex':
        llm = get_llm_chat(vector_name) # TODO: fix it needs llm_chat and not llm
        llm_chat = get_llm_chat(vector_name)
        embeddings = get_embeddings(vector_name)
        logging.debug("Chose VertexAI text-bison")
    elif llm_str == 'codey':
        llm = get_llm(vector_name)
        llm_chat = get_llm_chat(vector_name)
        embeddings = get_embeddings(vector_name)
        logging.debug("Chose VertexAI code-bison")
"""
This function determines whether streaming should be used based on the llm_str parameter.

It loads the llm_str parameter from a configuration file and then checks if it matches one of the predefined strings ('openai', 'gemini', 'vertex'). If it does, the function returns True, indicating that streaming should be used. Otherwise, it returns False.

:param vector_name: The name of the vector used to select the LLM.
:return: A boolean value indicating whether streaming should be used.
"""
    elif llm_str == 'model_garden':
        llm = get_llm(vector_name)
"""
This function configures a Language Learning Model (LLM) based on the vector_name and model parameters.

It loads the llm_str parameter from a configuration file and then configures the LLM based on this parameter. If the llm_str parameter matches one of the predefined strings ('openai', 'vertex', 'model_garden', 'anthropic'), the function configures the LLM accordingly. If the llm_str parameter does not match any of the predefined strings, the function raises a NotImplementedError.

:param vector_name: The name of the vector used to select the LLM.
:param model: The model to be used for the LLM. If not provided, a default model is selected based on the llm_str parameter.
:param config_file: The configuration file from which to load the llm_str parameter. Defaults to 'config/llm_config.yaml'.
:return: The configured LLM.
:raises NotImplementedError: If the llm_str parameter does not match any of the predefined strings.
"""
def get_llm(vector_name, model=None, config_file="config/llm_config.yaml"):
    llm_str = load_config_key("llm", vector_name, filename=config_file)
    model_lookup_filepath = get_module_filepath("lookup/model_lookup.yaml")
    model_lookup, _ = load_config(model_lookup_filepath)

    if not model:
        model = load_config_key("model", vector_name, filename=config_file)

    logging.debug(f"Chose LLM: {llm_str}")
    # Configure LLMs based on llm_str
    if llm_str == 'openai':
        # Setup for OpenAI LLM
        from langchain_openai import ChatOpenAI
        if model is None:
            model = 'gpt-3.5-turbo'
            logging.info(f"No 'model' value in config file - selecting default ChatOpenAI: {model}")
            return ChatOpenAI(model=model, temperature=0, max_tokens=4000)
                
        return ChatOpenAI(model=model, temperature=0, max_tokens=4000)

    elif llm_str == 'vertex':
        # Setup for Vertex LLM
        from langchain_community.llms import VertexAI
        if model is None:
            model = 'text-unicorn'
            logging.info(f"No 'model' value in config file - selecting default {model}")
            
        return VertexAI(model_name = model, temperature=0, max_output_tokens=1024)

    elif llm_str == 'model_garden':
        from ..patches.langchain.vertexai import VertexAIModelGarden
        model_garden_config = load_config_key("gcp_config", vector_name, filename = config_file)
        if model_garden_config is None:
            raise ValueError("llm='model_garden' requires a gcp_config entry in config yaml file")
        
        return VertexAIModelGarden(project=model_garden_config['project_id'], 
                                   endpoint_id=model_garden_config['endpoint_id'], 
                                   location=model_garden_config['location'], 
"""
This function configures a Language Learning Model (LLM) for chat based on the vector_name and model parameters.

It loads the llm_str parameter from a configuration file and then configures the LLM for chat based on this parameter. If the llm_str parameter matches one of the predefined strings ('openai', 'vertex', 'gemini', 'anthropic'), the function configures the LLM for chat accordingly. If the llm_str parameter does not match any of the predefined strings, the function raises a NotImplementedError.

:param vector_name: The name of the vector used to select the LLM.
:param model: The model to be used for the LLM. If not provided, a default model is selected based on the llm_str parameter.
:param config_file: The configuration file from which to load the llm_str parameter. Defaults to 'config/llm_config.yaml'.
:return: The configured LLM for chat.
:raises NotImplementedError: If the llm_str parameter does not match any of the predefined strings.
"""
def get_llm_chat(vector_name, model=None, config_file="config/llm_config.yaml"):
    llm_str = load_config_key("llm", vector_name, filename=config_file)
    if not model:
        model = load_config_key("model", vector_name, filename=config_file)

    logging.debug(f"Chose LLM: {llm_str}")
    # Configure LLMs based on llm_str
    if llm_str == 'openai':
        # Setup for OpenAI LLM
        from langchain_openai import ChatOpenAI
        if model is None:
            model = 'gpt-4'
            logging.info(f"No 'model' value in config file - selecting default {model}")
            
        return ChatOpenAI(model=model, temperature=0, max_tokens=4000)

    elif llm_str == 'vertex':
        # Setup for Vertex LLM
        from langchain_community.chat_models import ChatVertexAI
        if model is None:
            model = 'gemini-1.0-pro'
            logging.info(f"No 'model' value in config file - selecting default {model}")
            
        return ChatVertexAI(model_name = model, temperature=0, max_output_tokens=1024)
    
    elif llm_str == 'gemini':
        from langchain_google_genai import ChatGoogleGenerativeAI
        if model is None:
            model="gemini-pro"
            logging.info(f"No 'model' value in config file - selecting default {model}")
        
        return ChatGoogleGenerativeAI(model_name = model, temperature=0)

"""
This function selects an embedding based on the vector_name parameter.

It loads the llm_str parameter from a configuration file and then calls the pick_embedding function with this parameter to select an embedding.

:param vector_name: The name of the vector used to select the embedding.
:return: The selected embedding.
"""
def get_embeddings(vector_name):
    llm_str = load_config_key("llm", vector_name, filename="config/llm_config.yaml")

    return pick_embedding(llm_str)

"""
This function selects an embedding based on the llm_str parameter.

If the llm_str parameter matches one of the predefined strings ('openai', 'vertex', 'codey', 'anthropic'), the function selects an embedding accordingly. If the llm_str parameter does not match any of the predefined strings, the function raises a NotImplementedError.

:param llm_str: The string used to select the embedding.
:return: The selected embedding.
:raises NotImplementedError: If the llm_str parameter does not match any of the predefined strings.
"""
def pick_embedding(llm_str: str):
    # get embedding directly from llm_str
    # Configure embeddings based on llm_str
    if llm_str == 'openai':
        # Setup for OpenAI embeddings
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings()
    elif llm_str == 'vertex' or llm_str == 'codey' or llm_str == 'anthropic':
        # Setup for Text-Bison embeddings
        from langchain_community.embeddings import VertexAIEmbeddings
        
        return VertexAIEmbeddings()
    elif llm_str == 'gemini':
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        return GoogleGenerativeAIEmbeddings(model="models/embedding-001") #TODO add embedding type

    if llm_str is None:
        raise NotImplementedError(f'No embeddings implemented for {llm_str}')