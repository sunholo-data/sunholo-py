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
import re
import hashlib

def contains_url(message_data):
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    if url_pattern.search(message_data):
        return True
    else:
        return False

def extract_urls(text):
    url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    urls = url_pattern.findall(text)
    return urls

def compute_sha1_from_file(file_path):
    with open(file_path, "rb") as file:
        bytes = file.read() 
        readable_hash = hashlib.sha1(bytes).hexdigest()
    return readable_hash

def compute_sha1_from_content(content):
    readable_hash = hashlib.sha1(content).hexdigest()
    return readable_hash


def remove_whitespace(page_content: str):
    return page_content.replace("\n", " ").replace("\r", " ").replace("\t", " ").replace("  ", " ")