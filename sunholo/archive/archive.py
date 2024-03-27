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
from ..pubsub import PubSubManager
from ..logging import log



import datetime


def archive_qa(bot_output, vector_name):
    try:
        pubsub_manager = PubSubManager(vector_name, pubsub_topic="qna-to-pubsub-bq-archive")
        the_data = {"bot_output": bot_output,
                    "vector_name": vector_name,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        
        pubsub_manager.publish_message(the_data)
    except Exception as e:
        log.warning(f"Could not publish message for {vector_name} to qna-to-pubsub-bq-archive - {str(e)}")