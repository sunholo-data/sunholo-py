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
from ..utils import load_config_key, ConfigManager

import os

def pick_llm(vector_name:str=None, config:ConfigManager=None):

    if config is None:
        if vector_name is None:
            raise ValueError("config and vector_name was None")
        config = ConfigManager(vector_name)

    log.debug('Picking llm')
    
    llm_str = config.vacConfig("llm")
    
    if llm_str == 'openai':
        llm_chat = get_llm_chat(config=config)
        llm = get_llm_chat(model="gpt-3.5-turbo-16k", config=config) # TODO: fix it needs llm_chat and not llm
        embeddings = get_embeddings(config=config)

        log.debug("Chose OpenAI")
    elif llm_str == 'vertex':
        llm = get_llm_chat(vector_name) # TODO: fix it needs llm_chat and not llm
        llm_chat = get_llm_chat(vector_name)
        embeddings = get_embeddings(vector_name)
        log.debug("Chose VertexAI text-bison")
    elif llm_str == 'codey':
        llm = get_llm(vector_name)
        llm_chat = get_llm_chat(vector_name)
        embeddings = get_embeddings(vector_name)
        log.debug("Chose VertexAI code-bison")
    elif llm_str == 'model_garden':
        llm = get_llm(vector_name)
        llm_chat = llm
        embeddings = None
        log.debug("Chose VertexAIModelGarden")

    else:
        raise NotImplementedError(f'No llm implemented for {llm_str}')   

    return llm, embeddings, llm_chat

def pick_streaming(vector_name):
    
    llm_str = load_config_key("llm", vector_name, kind="vacConfig")
    
    if llm_str == 'openai' or llm_str == 'gemini' or llm_str == 'vertex':
        return True
    
    return False


def llm_str_to_llm(llm_str, model=None, vector_name=None, config=None):

    if llm_str is None:
        raise NotImplementedError("llm_str was None")
    
    if config is None:
        if vector_name is None:
            raise ValueError("vector_name and config was None")
        config = ConfigManager(vector_name)

    if llm_str == 'openai':
        # Setup for OpenAI LLM
        from langchain_openai import ChatOpenAI
        if model is None:
            model = 'gpt-3.5-turbo'
            log.info(f"No 'model' value in config file - selecting default ChatOpenAI: {model}")
            return ChatOpenAI(model=model, temperature=0, max_tokens=4000)
                
        return ChatOpenAI(model=model, temperature=0, max_tokens=4000)
    
    elif llm_str == 'genai':
        from langchain_google_genai import ChatGoogleGenerativeAI
        if model is None:
            model = "gemini-1.5-pro"
            log.info(f"No 'model' value in config file - selecting default {model}")
        
        return ChatGoogleGenerativeAI(model=model)

    elif llm_str == 'vertex':
        # Setup for Vertex LLM
        
        if model is None:
            model = 'gemini-1.5-pro'
            log.info(f"No 'model' value in config file - selecting default {model}")
        if model.startswith('claude'):
            from langchain_google_vertexai.model_garden import ChatAnthropicVertex
            gcp_config = config.vacConfig("gcp_config")
            return ChatAnthropicVertex(model_name=model, 
                                    project=gcp_config.get('project_id'), 
                                    location=gcp_config.get('location'))
            
        from langchain_google_vertexai import VertexAI
        return VertexAI(model_name = model, temperature=0, max_output_tokens=1024)

    elif llm_str == 'model_garden':
        from ..patches.langchain.vertexai import VertexAIModelGarden
        model_garden_config = config.vacConfig("gcp_config")
        if model_garden_config is None:
            raise ValueError("llm='model_garden' requires a gcp_config entry in config yaml file")
        
        return VertexAIModelGarden(project=model_garden_config['project_id'], 
                                   endpoint_id=model_garden_config['endpoint_id'], 
                                   location=model_garden_config['location'], 
                                   allowed_model_args=["max_tokens"])
    elif llm_str == 'anthropic':
        from langchain_anthropic import ChatAnthropic
        if model is None:
            model = 'claude-3-5-sonnet-20240620'
            log.info(f"No 'model' value in config file - selecting default {model}")

        return ChatAnthropic(model_name = model, temperature=0)
    
    elif llm_str == 'anthropic-vertex':
        from langchain_google_vertexai.model_garden import ChatAnthropicVertex
        if model is None:
            model = "claude-3-5-sonnet@20240620"
            log.info(f"No 'model' value in config file - selecting default {model}")
        gcp_config = config.vacConfig("gcp_config")

        return ChatAnthropicVertex(model_name=model, 
                                   project=gcp_config.get('project_id'), 
                                   location=gcp_config.get('location'))

    if llm_str is None:
        raise NotImplementedError(f'No llm implemented for {llm_str}') 

def get_llm(vector_name=None, model=None, config=None):

    if vector_name:
        config = ConfigManager(vector_name)

    llm_str = config.vacConfig("llm")

    if not model:
        model = config.vacConfig("model")

    log.debug(f"Chose LLM: {llm_str}")
    return llm_str_to_llm(llm_str, model=model, config=config)

def get_llm_chat(vector_name:str=None, model=None, config:ConfigManager=None):

    if config is None:
        if vector_name is None:
            raise ValueError("config and vector_name was None")
        config = ConfigManager(vector_name)

    llm_str = config.vacConfig("llm")
    if not model:
        model = config.vacConfig("model")

    log.debug(f"Chose LLM: {llm_str}")
    # Configure LLMs based on llm_str
    if llm_str == 'openai':
        # Setup for OpenAI LLM
        from langchain_openai import ChatOpenAI
        if model is None:
            model = 'gpt-4'
            log.info(f"No 'model' value in config file - selecting default {model}")
            
        return ChatOpenAI(model=model, temperature=0, max_tokens=4000)

    elif llm_str == 'vertex':
        # Setup for Vertex LLM
        from langchain_community.chat_models import ChatVertexAI
        if model is None:
            model = 'gemini-1.0-pro'
            log.info(f"No 'model' value in config file - selecting default {model}")
        if model.startswith('claude'):
            from langchain_google_vertexai.model_garden import ChatAnthropicVertex
            gcp_config = config.vacConfig("gcp_config")
            return ChatAnthropicVertex(model_name=model, 
                                    project=gcp_config.get('project_id'), 
                                    location=gcp_config.get('location'))
        
        return ChatVertexAI(model_name = model, temperature=0, max_output_tokens=1024)
    
    elif llm_str == 'gemini':
        from langchain_google_genai import ChatGoogleGenerativeAI
        if model is None:
            model="gemini-pro"
            log.info(f"No 'model' value in config file - selecting default {model}")
        
        return ChatGoogleGenerativeAI(model_name = model, temperature=0)

    elif llm_str == 'anthropic':
        from langchain_anthropic import ChatAnthropic
        if model is None:
            model = 'claude-3-opus-20240229'
            log.info(f"No 'model' value in config file - selecting default {model}")

        return ChatAnthropic(model_name = model, temperature=0)
    
    elif llm_str == 'azure':
        from langchain_openai import AzureChatOpenAI
        azure_config = config.vacConfig("azure")
        if not azure_config:
            raise ValueError("Need to configure azure.config if llm='azure'")

        AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
        if not AZURE_OPENAI_API_KEY:
            raise ValueError("AZURE_OPENAI_API_KEY env has not been set")

        # "https://<your-endpoint>.openai.azure.com/"
        AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT") or azure_config.get("azure_openai_endpoint")

        if not AZURE_OPENAI_ENDPOINT:
            raise ValueError("AZURE_OPENAI_API_KEY env or config value azure.azure_openai_endpoint has not been set")
        
        openai_api_version = azure_config.get("openai_api_version", "2024-02-01")

        if model is None:
            model = "gpt-4-turbo-1106-preview"
            log.info(f"No 'model' value (or azure_deployment) in config file - selecting default {model}")

        mo = AzureChatOpenAI(
            temperature=0, 
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            openai_api_version=openai_api_version, 
            azure_deployment=model, # or "gpt-35-turbo-1106"
            openai_api_key=AZURE_OPENAI_API_KEY, 
            openai_api_type="azure",
        )
        log.info(f"OpenAI Azure object: {mo}")

        return mo
    elif llm_str == "ollama":
        from langchain_community.chat_models import ChatOllama
        if model is None:
            model = 'llama3'
            log.info(f"No 'model' value in config file - selecting default {model}")
    
        return ChatOllama(model=model, temprature=0)

    if llm_str is None:
        raise NotImplementedError(f'No llm implemented for {llm_str}')

def get_embeddings(vector_name=None, config:ConfigManager=None):

    if not config:
        if not vector_name:
            raise ValueError(f"config and vector_name was None: {vector_name}")
        config = ConfigManager(vector_name)
    

    llm_str = None
    embed_dict = config.vacConfig("embedder")

    if embed_dict:
        llm_str = embed_dict.get('llm')

    if llm_str is None:
        llm_str = config.vacConfig("llm")
    
    if llm_str is None:
        raise ValueError(f"llm_str was None: {llm_str}")

    return pick_embedding(llm_str, config=config)


#TODO: specify model
def pick_embedding(llm_str: str, vector_name: str=None, config: ConfigManager=None):

    if not config:
        if not vector_name:
            raise ValueError(f"config and vector_name was None {vector_name}")
        config = ConfigManager(vector_name)

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
    
    elif llm_str == 'azure':
        from langchain_openai import AzureOpenAIEmbeddings
        
        azure_config = config.vacConfig("azure")
        if not azure_config:
            raise ValueError("Need to configure azure.config if llm='azure'")

        AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
        if not AZURE_OPENAI_API_KEY:
            raise ValueError("AZURE_OPENAI_API_KEY env has not been set")

        # "https://<your-endpoint>.openai.azure.com/"
        AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT") or azure_config.get("azure_openai_endpoint")

        if not AZURE_OPENAI_ENDPOINT:
            raise ValueError("AZURE_OPENAI_API_KEY env or config value azure.azure_openai_endpoint has not been set")
        
        openai_api_version = azure_config.get("openai_api_version")
        if not openai_api_version:
            raise ValueError("config.azure.openai_api_version has not been set")
        
        model = azure_config.get("embed_model") if azure_config.get("embed_model") else "text-embedding-3-large"

        return AzureOpenAIEmbeddings(azure_endpoint=AZURE_OPENAI_ENDPOINT,
                                     openai_api_key=AZURE_OPENAI_API_KEY, 
                                     model=model)

    if llm_str is None:
        raise NotImplementedError(f'No embeddings implemented for {llm_str}')
