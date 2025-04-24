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
# https://cloud.google.com/python/docs/reference/logging/latest/google.cloud.logging_v2.client.Client

try:
    from google.cloud.logging import Client
except ImportError:
    Client = None

from .utils.version import sunholo_version
import logging
import inspect
import os
import json
from functools import wraps

class GoogleCloudLogging:
    
    _instances = {}  # Dictionary to hold instances keyed by a tuple of (project_id, logger_name)

    

    def __new__(cls, project_id=None, log_level=logging.INFO, logger_name=None):
        key = (project_id, logger_name)
        if key not in cls._instances:
            cls._instances[key] = super(GoogleCloudLogging, cls).__new__(cls)
        return cls._instances[key]

    def __init__(self, project_id=None, log_level=logging.INFO, logger_name=None):
        if not hasattr(self, 'initialized'):  # Avoid re-initialization
            from .utils.gcp_project import get_gcp_project # circular import if outside
            from .utils.gcp import is_gcp_logged_in

            self.project_id = project_id or get_gcp_project()
            self.client = Client(project=self.project_id) if is_gcp_logged_in() else None
            self.logger_name = logger_name
            self.log_level = log_level
            self.initialized = True  # Mark as initialized
            self.version = sunholo_version()
        print(f"Initialized logging object for logger_name: {logger_name}")


    def setup_logging(self, log_level=logging.INFO, logger_name=None):
        if log_level:
            self.log_level = log_level
        if logger_name:
            self.logger_name = logger_name

        try:
            caller_info = self._get_caller_info()
            from .utils.gcp import is_running_on_gcp, is_gcp_logged_in
            if not is_running_on_gcp() and not is_gcp_logged_in():
                import logging
                logging.basicConfig(level=self.log_level, format='%(asctime)s - %(levelname)s - %(message)s')
                logging.info(f"Standard logging: {caller_info['file']}")
                return logging
            
            print(f"Cloud logging for {caller_info['file']}")
            self.client.setup_logging(log_level=self.log_level)

            return self  # Return the instance itself on success
        except Exception as e:
            # If there's an exception, use standard Python logging as a fallback
            import logging
            logging.basicConfig(level=self.log_level, format='%(asctime)s - %(levelname)s - %(message)s')
            logging.warning(f"Failed to set up Google Cloud log. Using standard log. Error: {e}")
            return logging

    def _get_caller_info(self):
        """
        Internal method to get caller's filename, line number, and function name.
        """
        frame = inspect.currentframe()
        caller_frame = frame.f_back.f_back.f_back if frame is not None else None  # Three levels up in the stack
        if caller_frame:
            return {
                    'file': caller_frame.f_code.co_filename,
                    'line': str(caller_frame.f_lineno),  
                    'function': caller_frame.f_code.co_name
                }
        return None

    def update_trace_id(self, trace_id):
        """
        Updates the trace ID to be included in all logs.
        
        Args:
            trace_id (str): The trace ID to add to all logs.
        """
        self.trace_id = trace_id

    def _append_trace_id(self, log_text):
        """
        Appends trace ID to log text if available.
        
        Args:
            log_text (str): The log message.
        
        Returns:
            str: Log message with trace ID prefixed if available.
        """
        if hasattr(self, 'trace_id') and self.trace_id:
            return f"{self.logger_name}-{self.trace_id} {log_text}"
        return log_text

    def _add_trace_to_struct(self, log_struct):
        """
        Adds trace ID to structured log data if available.
        
        Args:
            log_struct (dict): The structured log data.
        
        Returns:
            dict: Log structure with trace ID added if available.
        """
        if not isinstance(log_struct, dict):
            return log_struct
            
        if hasattr(self, 'trace_id') and self.trace_id:
            return {**log_struct, "trace_id": self.trace_id}
        return log_struct

    def structured_log(self, log_text=None, log_struct=None, logger_name=None, severity="INFO"):
        """
        Writes log entries to the specified logger as either text or structured data.
        
        Args:
            log_text (str, optional): The log message as a text string. Defaults to None.
            log_struct (dict, optional): The log message as a dictionary for structured log. Defaults to None.
            logger_name (str, optional): The name of the logger to which to write the log entries.
                e.g. logName="run.googleapis.com%2Fstderr"
            severity (str, optional): The severity level of the log entry. Defaults to "INFO".
        """
        from .utils.version import sunholo_version
        
        # Add version to log_text if it exists
        if log_text is not None:
            log_text = f"[{sunholo_version()}] {log_text}"
            log_text = self._append_trace_id(log_text)
        
        # Always create or update log_struct with trace_id if available
        if not log_struct:
            log_struct = {}
        
        # Make sure log_struct is a dictionary
        if not isinstance(log_struct, dict):
            log_struct = {"original_non_dict_value": str(log_struct)}
        
        # Add trace ID to log_struct
        if hasattr(self, 'trace_id') and self.trace_id:
            log_struct["trace_id"] = self.trace_id
        
        # Add version to log_struct
        log_struct["version"] = sunholo_version()
        
        if not logger_name and not self.logger_name:
            raise ValueError("Must provide a logger name e.g. 'run.googleapis.com%2Fstderr'")
        
        from .utils.gcp import is_running_on_gcp, is_gcp_logged_in
        if not is_running_on_gcp() and not is_gcp_logged_in():
            import logging as log
            log.basicConfig(level=log.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            if log_text:
                log.info(f"[{severity}][{logger_name or self.logger_name}][{self.version}] - {log_text} - {log_struct}")
            else:
                log.info(f"[{severity}][{logger_name or self.logger_name}][{self.version}] - {str(log_struct)}")
            return
        
        logger = self.client.logger(logger_name or self.logger_name)
        caller_info = self._get_caller_info()
        
        # Always log struct, and include message if provided
        if log_text:
            log_struct["message"] = log_text
        
        try:
            logger.log_struct(log_struct, severity=severity, source_location=caller_info)
        except Exception as err:
            print(f"Failed to log struct: {err}")
            # Fallback to text logging
            fallback_message = log_text if log_text else str(log_struct)
            try:
                logger.log_text(fallback_message, severity=severity, source_location=caller_info)
            except Exception as text_err:
                print(f"Even fallback text logging failed: {text_err}")

    def log(self, message, *args, **kwargs):
        """
        Some weird bug keeps calling this method - do not use normally

        A catch-all method to handle unexpected .log() calls on this class.
        Routes the call to the appropriate logging method based on severity level.
        """
        severity = kwargs.get('severity', 'INFO')
        # Remove severity from kwargs if it exists to avoid passing it twice
        if 'severity' in kwargs:
            del kwargs['severity']
        
        # Determine if this is a structured log or simple message
        if isinstance(message, dict):
            # Assume this is a structured log
            return self.structured_log(log_struct=message, severity=severity)
        else:
            # Assume this is a text log
            return self.structured_log(log_text=message, severity=severity)

    def debug(self, log_text=None, log_struct=None):

        """
        Writes a debug log entry.
        
        Args:
            log_text (str, optional): The debug log message as a text string. Defaults to None.
            log_struct (dict, optional): The debug log message as structured data. Defaults to None.
            logger_name (str, optional): The name of the logger to which to write the debug log entry.
        """
        self.structured_log(log_text=log_text, log_struct=log_struct, severity="DEBUG")


    def info(self, log_text=None, log_struct=None):
        """
        Writes an info log entry.
        
        Args:
            log_text (str, optional): The info log message as a text string. Defaults to None.
            log_struct (dict, optional): The info log message as structured data. Defaults to None.
            logger_name (str, optional): The name of the logger to which to write the info log entry.
        """
        self.structured_log(log_text=log_text, log_struct=log_struct, severity="INFO")

    def warning(self, log_text=None, log_struct=None):
        """
        Writes a warning log entry.
        
        Args:
            log_text (str, optional): The warning log message as a text string. Defaults to None.
            log_struct (dict, optional): The warning log message as structured data. Defaults to None.
            logger_name (str, optional): The name of the logger to which to write the warning log entry.
        """
        self.structured_log(log_text=log_text, log_struct=log_struct, severity="WARNING")

    def error(self, log_text=None, log_struct=None):
        """
        Writes an error log entry.
        
        Args:
            log_text (str, optional): The error log message as a text string. Defaults to None.
            log_struct (dict, optional): The error log message as structured data. Defaults to None.
            logger_name (str, optional): The name of the logger to which to write the error log entry.
        """
        self.structured_log(log_text=log_text, log_struct=log_struct, severity="ERROR")
    
    def exception(self, log_text=None, log_struct=None):
        """
        Writes an exception log entry.
        
        Args:
            log_text (str, optional): The error log message as a text string. Defaults to None.
            log_struct (dict, optional): The error log message as structured data. Defaults to None.
            logger_name (str, optional): The name of the logger to which to write the error log entry.
        """
        self.structured_log(log_text=log_text, log_struct=log_struct, severity="CRITICAL")

class StandardLoggerWrapper:
    """
    A wrapper for standard Python logger that mimics the interface of GoogleCloudLogging.
    """
    def __init__(self, logger):
        self.logger = logger
        self.trace_id = None
        self.version = None

    def _format_message(self, log_text=None, log_struct=None, severity=None):
        """Format message to include structured data as JSON"""
        parts = []
        
        # Add severity if provided
        if severity:
            parts.append(f"[{severity}]")
            
        # Add trace ID if available
        if self.trace_id:
            parts.append(f"[trace_id:{self.trace_id}]")
            
        # Add version if available
        if self.version:
            parts.append(f"[version:{self.version}]")
            
        # Add the log text if provided
        if log_text:
            parts.append(log_text)
            
        # Add structured data as JSON if provided
        if log_struct:
            if self.trace_id and isinstance(log_struct, dict):
                log_struct["trace_id"] = self.trace_id
            if self.version and isinstance(log_struct, dict):
                log_struct["version"] = self.version
            parts.append(f"STRUCT: {json.dumps(log_struct, default=str)}")
            
        return " ".join(parts)

    def update_trace_id(self, trace_id):
        """Set trace ID to be included in all logs."""
        self.trace_id = trace_id
        
    def set_version(self, version):
        """Set version to be included in all logs."""
        self.version = version
        
    def structured_log(self, log_text=None, log_struct=None, logger_name=None, severity="INFO"):
        """
        Emulates Google Cloud's structured_log method using standard logging.
        """
        message = self._format_message(log_text, log_struct, severity)
        
        if severity == "DEBUG":
            self.logger.debug(message)
        elif severity == "INFO":
            self.logger.info(message)
        elif severity == "WARNING":
            self.logger.warning(message)
        elif severity == "ERROR":
            self.logger.error(message)
        elif severity == "CRITICAL":
            self.logger.critical(message)
        else:
            self.logger.info(message)  # Default to info
            
    def debug(self, log_text=None, log_struct=None):
        self.structured_log(log_text=log_text, log_struct=log_struct, severity="DEBUG")
        
    def info(self, log_text=None, log_struct=None):
        self.structured_log(log_text=log_text, log_struct=log_struct, severity="INFO")
        
    def warning(self, log_text=None, log_struct=None):
        self.structured_log(log_text=log_text, log_struct=log_struct, severity="WARNING")
        
    def error(self, log_text=None, log_struct=None):
        self.structured_log(log_text=log_text, log_struct=log_struct, severity="ERROR")
        
    def exception(self, log_text=None, log_struct=None):
        self.structured_log(log_text=log_text, log_struct=log_struct, severity="CRITICAL")
        
    # Forward any other standard logging methods to the underlying logger
    def __getattr__(self, name):
        return getattr(self.logger, name)
    
def is_logging_setup(logger=None):
    logger = logger or logging.getLogger()  # If no logger is specified, use the root logger
    return bool(logger.handlers)

def setup_logging(logger_name=None, log_level=logging.INFO, project_id=None):
    """
    Sets up Google Cloud Logging with the provided log level and project ID. If no project ID
    is provided, it attempts to retrieve the project ID from the metadata server.

    Parameters:
    logger_name (str): The name of the log to send to. If not provided, set to run.googleapis.com%2Fstderr
    log_level: The logging level to capture. Uses Python's logging module levels.
               Default is log.INFO.
    project_id: A string representing the Google Cloud project ID. If None, the project ID
                will be retrieved from the metadata server.

    Example:
        # Set up Google Cloud Logging for the script with default INFO level
        setup_logging()

        # Now you can use Python's logging module as usual
        import logging
        log.info('This is an info message that will be sent to Google Cloud log.')

        # Basic structured logging
        log.info(log_struct={"action": "user_login", "user_id": "12345"})

        # Structured logging with trace ID
        log.update_trace_id("abc-123")
        log.info(log_struct={"action": "process_started", "file_count": 42})
        # This will include trace_id: "abc-123" in the logged structure

        # Logging with both text and structure
        log.info(
            log_text="Processing completed successfully", 
            log_struct={"duration_ms": 1234, "items_processed": 100}
        )

        # Logging error with structured context
        try:
            # Some operation
            process_data()
        except Exception as e:
            log.error(
                log_text=f"Error processing data: {str(e)}",
                log_struct={
                    "error_type": type(e).__name__,
                    "file_name": "example.csv",
                    "line_number": 42
                }
            )

        # More complex structured logging
        log.info(log_struct={
            "request": {
                "method": "POST",
                "path": "/api/data",
                "user_agent": "Mozilla/5.0...",
                "ip": "192.168.1.1"
            },
            "response": {
                "status_code": 200,
                "processing_time_ms": 345,
                "bytes_sent": 1024
            },
            "metadata": {
                "version": "1.2.3",
                "environment": "production"
            }
        })
        
    Note:
        This function requires that the 'google-cloud-logging' library is installed and
        that the application is authenticated with Google Cloud. This can be done by setting
        the GOOGLE_APPLICATION_CREDENTIALS environment variable to the path of your service
        account key file, or by running this code in an environment where default
        application credentials are already set, such as Google Cloud Compute Engine,
        Google Kubernetes Engine, Google App Engine, etc.
    """

    logger = logging.getLogger(logger_name)
    if is_logging_setup(logger):
        # Check if it's already our wrapper
        if hasattr(logger, 'structured_log'):
            return logger
        else:
            # Wrap the existing logger
            wrapper = StandardLoggerWrapper(logger)
            wrapper.set_version(sunholo_version())
            return wrapper
    
    if logger_name is None:
        logger_name = "sunholo"

    if not Client and os.environ.get('GOOGLE_CLOUD_LOGGING') == "1":
        print("Found GOOGLE_CLOUD_LOGGING=1 but no GCP Client available, install via `pip install sunholo[gcp]` and/or authenticate")

    if Client and os.environ.get('GOOGLE_CLOUD_LOGGING') == "1":
        if project_id is None:
            from .utils.gcp_project import get_gcp_project
            project_id = get_gcp_project()
        # Instantiate the GoogleCloudLogging class
        gc_logger = GoogleCloudLogging(project_id, log_level=log_level, logger_name=logger_name)
        # Setup logging and return the logger instance
        return gc_logger.setup_logging()
    else:
        if not logging.getLogger().hasHandlers():
            logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log = logging.getLogger(logger_name)
        
        # Wrap the standard logger to support log_struct parameter
        wrapper = StandardLoggerWrapper(log)
        wrapper.set_version(sunholo_version())
        return wrapper
    
# for debugging
def safe_log_struct(log, severity, message, struct):
    try:
        if severity == "INFO":
            log.info(log_text=message, log_struct=struct)
        elif severity == "ERROR":
            log.error(log_text=message, log_struct=struct)
        # Add other severity levels as needed
    except Exception as e:
        print(f"Logging error: {e}")
        print(f"Failed to log structure: {struct}")
        # Fallback to simple text logging
        if severity == "INFO":
            log.info(f"{message} (struct logging failed)")
        elif severity == "ERROR":
            log.error(f"{message} (struct logging failed)")

def log_folder_location(folder_name):
    # Get the current working directory
    current_working_directory = os.getcwd()
    
    # Construct the absolute path to the folder
    folder_path = os.path.join(current_working_directory, folder_name)
    
    # Check if the folder exists
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        logging.info(f"The folder '{folder_name}' is located at: {folder_path}")
    else:
        logging.warning(f"The folder '{folder_name}' does not exist in the current working directory: {current_working_directory}")

# lazy eval
_logger = None
def get_logger():
    global _logger
    if _logger is None:
        _logger = setup_logging("sunholo")
    return _logger

log = get_logger()

"""
# Basic structured logging
log.info(log_struct={"action": "user_login", "user_id": "12345"})

# Structured logging with trace ID
log.update_trace_id("abc-123")
log.info(log_struct={"action": "process_started", "file_count": 42})
# This will include trace_id: "abc-123" in the logged structure

# Logging with both text and structure
log.info(
    log_text="Processing completed successfully", 
    log_struct={"duration_ms": 1234, "items_processed": 100}
)

# Logging error with structured context
try:
    # Some operation
    process_data()
except Exception as e:
    log.error(
        log_text=f"Error processing data: {str(e)}",
        log_struct={
            "error_type": type(e).__name__,
            "file_name": "example.csv",
            "line_number": 42
        }
    )

# More complex structured logging
log.info(log_struct={
    "request": {
        "method": "POST",
        "path": "/api/data",
        "user_agent": "Mozilla/5.0...",
        "ip": "192.168.1.1"
    },
    "response": {
        "status_code": 200,
        "processing_time_ms": 345,
        "bytes_sent": 1024
    },
    "metadata": {
        "version": "1.2.3",
        "environment": "production"
    }
})
"""