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
import logging
from flask import Flask
from ...utils import fetch_config

def create_app(name):
    # Initialize Flask app
    app = Flask(name)
    app.config['TRAP_HTTP_EXCEPTIONS'] = True

    # Setup a global variable to store the last modification time
    app.last_mod_time = None
    app.last_check_time = datetime.datetime.now()
    
    return app
