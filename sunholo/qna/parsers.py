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

from sunholo.logging import setup_logging

log = setup_logging()

def document_to_dict(document):
    return {
        "page_content": document.page_content,
        "metadata": document.metadata
    }

def parse_output(bot_output):
    if isinstance(bot_output, dict) and 'source_documents' in bot_output:
        if 'source_documents' in bot_output:
            bot_output['source_documents'] = [document_to_dict(doc) for doc in bot_output['source_documents']]
        if bot_output.get("answer", None) is None or bot_output.get("answer") == "":
            bot_output['answer'] = "(No text was returned)"
        return bot_output
    else:
        log.error(f"Couldn't parse output for {bot_output}")