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
import json, os
import requests
from ..logging import setup_logging

logging = setup_logging()

def generate_discord_output(bot_output):
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

def discord_webhook(message_data):
    webhook_url = os.getenv('DISCORD_URL', None)  # replace with your webhook url
    if webhook_url is None:
        return None
    
    logging.info(f'webhook url: {webhook_url}')

    # If the message_data is not a dict, wrap it in a dict.
    if not isinstance(message_data, dict):
        message_data = {'content': message_data}
    else:
        # if it is a dict, turn it into a string
        message_data = {'content': json.dumps(message_data)}
        #TODO parse out message_data into other discord webhook objects like embed
        # https://birdie0.github.io/discord-webhooks-guide/discord_webhook.html
    
    data = message_data

    logging.info(f'Sending discord this data: {data}')
    response = requests.post(webhook_url, json=data,
                            headers={'Content-Type': 'application/json'})
    logging.debug(f'Sent data to discord: {response}')
    
    return response