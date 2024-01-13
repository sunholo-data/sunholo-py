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
import os
import datetime
from flask import Flask
from ...utils import fetch_config
from ...logging import setup_logging

logging = setup_logging()

def create_app(name):
    # Initialize Flask app
    app = Flask(name)
    app.config['TRAP_HTTP_EXCEPTIONS'] = True

    # Setup a global variable to store the last modification time
    app.last_mod_time = None
    app.last_check_time = datetime.datetime.now()

    @app.before_request
    def before_request():
        # Use 'app' context to store last_mod_time and last_check_time
        logging.info("Checking configuration")

        # Check if it's been more than 5 minutes since the last check
        current_time = datetime.datetime.now()
        time_diff = current_time - app.last_check_time
        if time_diff.seconds < 300:
            logging.debug("Less than 5 minutes since last check. Skipping this check.")
            return
        
        app.last_check_time = current_time

        # The name of your bucket and the file you want to check
        bucket_name = os.environ.get('GCS_BUCKET')
        if bucket_name:
            bucket_name = bucket_name.replace('gs://', '')
        else:
            raise EnvironmentError("GCS_BUCKET environment variable not set")
        
        blob_name = 'config/config_llm.yaml'
        # Fetch the current modification time from Cloud Storage
        current_mod_time = fetch_config(bucket_name, blob_name)
        
        if current_mod_time:
            # Compare the modification times
            if app.last_mod_time is None or app.last_mod_time < current_mod_time:
                app.last_mod_time = current_mod_time
                logging.info("Configuration file updated, reloaded the new configuration.")
            else:
                logging.info("Configuration file not modified.")    
    return app
