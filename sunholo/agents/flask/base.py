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
def create_app(name):
    from flask import Flask
    from flask_cors import CORS

    app = Flask(name)

    CORS(app, 
         origins=["https://*.sunholo.com", "http://*.sunholo.com"],  # Allow all subdomains of sunholo.com
         methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # Allow all necessary HTTP methods
         allow_headers=["DNT", "User-Agent", "X-Requested-With", "If-Modified-Since", 
                        "Cache-Control", "Content-Type", "Range", "Authorization", "x-api-key"],  # Add custom headers
         expose_headers=["Content-Length", "Content-Range"],  # Optional: headers that are exposed to clients
         supports_credentials=True, 
         max_age=1728000  # Set max age of preflight request caching (in seconds)
    )

    app.config['TRAP_HTTP_EXCEPTIONS'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True
   
    return app
