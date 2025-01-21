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

from ..utils.config import load_config

def generate_webapp_output(bot_output):
    source_documents = []
    if bot_output.get('source_documents', None) is not None:
        source_documents = []
        for doc in bot_output['source_documents']:
            metadata = doc.get("metadata",{})
            filtered_metadata = {}
            if metadata.get("source", None) is not None:
                filtered_metadata["source"] = metadata["source"]
            if metadata.get("type", None) is not None:
                filtered_metadata["type"] = metadata["type"]
            source_doc = {
                'page_content': doc["page_content"],
                'metadata': filtered_metadata
            }
            source_documents.append(source_doc)

    return {
        'result': bot_output.get('answer', "No answer available"),
        'source_documents': source_documents
    }

def to_proper_case(s):
    return ' '.join(word.capitalize() for word in s.replace('_', ' ').replace('-', ' ').split())

def craft_config_description(name, filename="config/llm_config.yaml"):
    configs, filename = load_config(filename)
    description = configs[name].get('description')

    if description is None:
        description = f"Agent vac: {configs[name].get('agent')} LLM: {configs[name].get('llm')}"

    return description