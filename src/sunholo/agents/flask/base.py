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

from ...custom_logging import log
import time

def create_app(name):
    from flask import Flask, request
    
    app = Flask(name)

    app.config['TRAP_HTTP_EXCEPTIONS'] = True
    app.config['PROPAGATE_EXCEPTIONS'] = True
   
    @app.before_request
    def start_timer():
        request.start_time = time.time()

    @app.after_request  
    def log_timing(response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log all VAC requests with different detail levels
            if request.path.startswith('/vac/streaming/'):
                log.info(f"🚀 STREAMING: {duration:.3f}s - {request.path}")
            elif request.path.startswith('/vac/'):
                log.info(f"⚡ VAC: {duration:.3f}s - {request.path}")
            elif duration > 1.0:  # Log any slow requests
                log.warning(f"🐌 SLOW REQUEST: {duration:.3f}s - {request.path}")
            
            # Add response headers with timing info for debugging
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
            
        return response
    
    return app
