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
import datetime
import tempfile
import os
import re

from google.cloud import storage

from ..database import delete_row_from_source, return_sources_last24
from ..utils.parsers import contains_url, extract_urls
from ..chunker.publish import publish_text
from ..chunker.gcs import add_file_to_gcs

def handle_special_commands(user_input, vector_name, paired_messages):
    now = datetime.datetime.now()
    hourmin = now.strftime("%H%M%S")
    the_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if user_input.startswith("!savethread"):
        with tempfile.TemporaryDirectory() as temp_dir:
            chat_file_path = os.path.join(temp_dir, f"{hourmin}_chat_history.txt")
            with open(chat_file_path, 'w') as file:
                file.write(f"## Thread history at {the_datetime}\nUser: {user_input}")
                for human_message, ai_message in paired_messages:
                    file.write(f"Human: {human_message}\nAI: {ai_message}\n")
            gs_file = app_to_store(chat_file_path, vector_name, via_bucket_pubsub=True)
            return f"Saved chat history to {gs_file}"

    elif user_input.startswith("!saveurl"):
        if contains_url(user_input):
            urls = extract_urls(user_input)
            branch="main"
            if "branch:" in user_input:
                match = re.search(r'branch:(\w+)', user_input)
                if match:
                    branch = match.group(1)
            for url in urls:
                publish_text(f"{url} branch:{branch}", vector_name)
            return f"URLs sent for processing: {urls} to {vector_name}."
        else:
            return "No URLs were found"

    elif user_input.startswith("!deletesource"):
        source = user_input.replace("!deletesource", "")
        source = source.replace("source:","").strip()
        delete_row_from_source(source, vector_name=vector_name)
        return f"Deleting source: {source}"

    elif user_input.startswith("!sources"):
        rows = return_sources_last24(vector_name)
        if rows is None:
            return "No sources were found"
        else:
            msg = "\n".join([f"{row}" for row in rows])
            return f"*sources:*\n{msg}"


    elif user_input.startswith("!help"):
        return f"""*Commands*
- `!saveurl [https:// url]` - add the contents found at this URL to database. 
- `!help`- see this message
- `!sources` - get sources added in last 24hrs
- `!deletesource [gs:// source]` - delete a source from database
- `!dream` - get last night's dream. Use `!dream 2023-07-30` to get a dream from a specific date. Also works with `!journal` and `!practice`
*Tips*
- See user guide here: https://docs.google.com/document/d/1WMi5X4FVHCihIkZ69gzxkVzr86m4WQj3H75LjSPjOtQ
- Attach files to Discord messages to upload them into database
- If you have access, upload big files (>5MB) to the Google Cloud Storage bucket
- URLs of GoogleDrive work only if shared with **edmonbrain-app@devo-mark-sandbox.iam.gserviceaccount.com** in your own drive
- URLs of GitHub (https://github.com/* branch:main) will git clone and add all repo files. e.g. `!saveurl https://github.com/me/repo branch:master`. 
- For private GitHub repositories, the app has a GitHub PAT that will need access linked to MarkEdmondson1234 account
*Slash Commands*
"""
    
    # check for special text file request via !dream !journal or !practice
    result = get_gcs_text_file(user_input, vector_name)
    if result:
        return result

    # If no special commands were found, return None
    return None

def get_gcs_text_file(user_input, vector_name):
    command = None
    for keyword in ["!dream", "!journal", "!practice"]:
        if user_input.startswith(keyword):
            command = keyword.strip('!')
            break

    if not command:
        return None

    dream_date = datetime.datetime.now() - datetime.timedelta(1)
    if ' ' in user_input:
        _, date_str = user_input.split(' ', 1)
        try:
            dream_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return f"Invalid date format for !{command}. Use YYYY-MM-DD."

    dream_date_str = dream_date.strftime('%Y-%m-%d')

    bucket_name = os.getenv("GCS_BUCKET").replace("gs://","") 
    source_blob_name = f"{vector_name}/{command}/{command}_{dream_date_str}.txt"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(source_blob_name)
    if blob.exists():
        dream_text = blob.download_as_text()
        return dream_text
    else:
        return f"!{command} file does not exist for date {dream_date_str}"
    

def app_to_store(safe_file_name, vector_name, via_bucket_pubsub=False, metadata:dict=None):
    
    gs_file = add_file_to_gcs(safe_file_name, vector_name, metadata=metadata)

    # we send the gs:// to the pubsub ourselves
    if not via_bucket_pubsub:
        publish_text(gs_file, vector_name)

    return gs_file

def handle_files(uploaded_files, temp_dir, vector_name):
    bot_output = []
    if uploaded_files:
        for file in uploaded_files:
            # Save the file temporarily
            safe_filepath = os.path.join(temp_dir, file.filename)
            file.save(safe_filepath)

            app_to_store(safe_filepath, vector_name)
            bot_output.append(f"{file.filename} sent to {vector_name}")

    return bot_output