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


import base64
import json

def process_pubsub(data):

    log.debug(f'process_pubsub: {data}')
    message_data = base64.b64decode(data['message']['data']).decode('utf-8')
    messageId = data['message'].get('messageId')
    publishTime = data['message'].get('publishTime')

    log.debug(f"This Function was triggered by messageId {messageId} published at {publishTime}")
    # DANGER: Will trigger this dunction recursivly
    #log.info(f"bot_help.process_pubsub message data: {message_data}")

    try:
        message_data = json.loads(message_data)
    except:
        log.debug("Its not a json")

    if message_data:
        return message_data
    
    log.info(f"message_data was empty")
    return ''