# Talk to AlloyDB

This is an example of a VAC that communicates with an AlloyDB database via natural language, by using tools to search and fetch documents.

## Config - config/vac_config.yaml

A vacConfig is first set up in a local `config/` directory.  This determines which database AlloyDB will use.  This is picked up by the `ConfigManager` class.

```yaml
kind: vacConfig
apiVersion: v1
vac:
  demo_alloydb:
    llm: vertex
    model: gemini-1.5-pro
    model_quick: gemini-1.5-flash-001
    agent: vertex-genai
    display_name: Speak to AlloydB
    description: Demo Speak to AlloyDB VAC
    tools:
       alloydb:
          vac: my_alloydb_db # which db to call
    alloydb_config:
      project_id: multivac-demoalloydb
      region: europe-west1
      cluster: multivac-alloydb-cluster
      instance: primary-instance

```

## HTTP Flask App - app.py

A simple Flask app is set up using the `VACRoutes` class to create endpoints such as streaming and OpenAI compatible URLs.

```python
import os

from sunholo.agents import VACRoutes, create_app

from vac_service import vac_stream

app = create_app(__name__)

# Register the Q&A routes with the specific interpreter functions
# creates /vac/<vector_name> and /vac/streaming/<vector_name>
VACRoutes(app, vac_stream, vac)

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)

```

## Creating the VAC logic - vac_service.py

For this example we shall only stream the GenAI results:

```python
from sunholo.utils import ConfigManager
from sunholo.vertex import init_genai

from talk_to_alloydb import get_alloydb_model, process_alloydb_funcs

def vac_stream(question: str, vector_name:str, chat_history=[], callback=None, **kwargs):

    init_genai()
    config=ConfigManager(vector_name)

    orchestrator = get_alloydb_model(config)

    chat = orchestrator.start_chat()

    model = get_alloydb_model(config)

    content = [
      (
        "The user has asked a question which may or may not be answered by the documents in your database."
        f"<question>{question}</question>"
      )
    ]
    response = chat.send_message(content)
    parsed_response = process_alloydb_funcs(response, config, output_parts=True)

    executed_response = chat.send_message(parsed_response, stream=True)

    text = ""

    for chunk in executed_response:
        try:
            # Concatenate the text parts (if multiple parts exist)
            token = chunk.text
        
            callback.on_llm_new_token(token=token)
            text += token
            
        except ValueError as err:
            callback.on_llm_new_token(token=str(err))

    callback.on_llm_end(response=text)

    metadata = {
        "question:": question,
        "chat_history": chat_history,
    }

    return {"answer": text, "metadata": metadata}
```

## Calling AlloyDB via genai tools - talk_to_alloydb.py

This holds the genai function processing, the function definitions created via the inherited class from `GenAIFunctionProcessor` and genai model that will use the function as tools.  

The functions are defined to the model via the docstrings, but they are not executed.  Once the function arguments are returned by the model, the `AlloyDBClient` class is used to actually communicate with AlloyDB and extract the results.

```python
from sunholo.database import AlloyDBClient
from sunholo.utils import ConfigManager
from sunholo.genai import GenAIFunctionProcessor

# Example subclass for AlloyDB
class AlloyDBFunctionProcessor(GenAIFunctionProcessor):
    def construct_tools(self) -> dict:
        tools = self.config.vacConfig("tools")
        alloydb_tool_config = tools.get("alloydb")
        vector_name = alloydb_tool_config.get("vac")
        if not vector_name:
            log.error("could not process_alloydb_funcs due to no config.tools.alloydb.vac found")
            return {"Config error in config.tools.alloydb.vac so no results found": None}

        def list_alloydb_sources(sources: list[str], search_type: str = "OR") -> list[str]:
            """
            List the document source names e.g. sources=['example'] will match ['example1.pdf', 'example2.pdf'] in the AlloyDB docstore.
            Will use %ILIKE% to look for source names that match the string given, so split long strings into individual words for broader searches e.g. ['german','contracts'] will match more than 'german contracts'

            Args:
            sources: list(str) List of sources to fetch from the docstore.  
            search_type: str (optional) The type of search to perform (e.g., 'OR', 'AND')
            
            Returns:
                List of strings showing names of sources in AlloyDB database
            """
            adb = AlloyDBClient(self.config, db=os.environ.get("ALLOYDB_DB"))
            return adb.get_sources_from_docstore(
                sources=sources,
                vector_name=vector_name,
                search_type=search_type,
                just_source_name=True
            )

        def get_alloydb_source_text(source: str) -> dict:
            """
            From the passed source string finds a single file that is an exact match of the name, then fetches the stored text and metadata
            
            Args:
            source: str The exact match name of the source file to fetch.  Will only match one file.
            
            Returns:
                A dictionary of the source text and the metadata, or None if no file exists of this name.
            """
            adb = AlloyDBClient(self.config)
            source_data = adb.get_document_from_docstore(
                source=source,
                vector_name=vector_name
            )
            return source_data

        return {
            "list_alloydb_sources": list_alloydb_sources,
            "get_alloydb_source_text": get_alloydb_source_text,
        }

def process_alloydb_funcs(full_response, config: ConfigManager, output_parts=False):

    alloydb_processor = AlloyDBFunctionProcessor(config)

    return alloydb_processor.process_funcs(full_response)

def get_alloydb_model(config: ConfigManager):

    alloydb_processor = AlloyDBFunctionProcessor(config)
    
    tools = config.vacConfig('tools')

    if tools and tools.get('alloydb'):
        alloydb_model = alloydb_processor.get_model(
            system_instruction=(
                    "You are a helpful AlloyDB agent that helps users search and extract documents from the database. "
                    "Use the list_sources_in_docstore tool to determine what files are available and the get_single_source_text_from_docstore tool to fetch the actual text and metadata"
                )
        )

        if alloydb_model:
            return alloydb_model

    log.error("Error initializing alloydb model")    
    return None
```
