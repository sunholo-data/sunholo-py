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

    def structured_log(self, log_text=None, log_struct=None, logger_name=None, severity="INFO"):
        """
        Writes log entries to the specified logger as either text or structured data.

        Args:
            log_text (str, optional): The log message as a text string. Defaults to None.
            log_struct (dict, optional): The log message as a dictionary for structured log. Defaults to None.
            logger_name (str, optional): The name of the logger to which to write the log entries. e.g. 
        logName="run.googleapis.com%2Fstderr"
            severity (str, optional): The severity level of the log entry. Defaults to "INFO".
        """

        from .utils.version import sunholo_version

        log_text = f"[{sunholo_version()}] {log_text}"

        if not logger_name and not self.logger_name:
            raise ValueError("Must provide a logger name e.g. 'run.googleapis.com%2Fstderr'")
        
        from .utils.gcp import is_running_on_gcp, is_gcp_logged_in
        if not is_running_on_gcp() and not is_gcp_logged_in():
            log.basicConfig(level=log.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            if log_text:
                log.info(f"[{severity}][{logger_name or self.logger_name}][{self.version}] - {log_text}")
            elif log_struct:
                log.info(f"[{severity}][{logger_name or self.logger_name}][{self.version}] - {str(log_struct)}")

        logger = self.client.logger(logger_name or self.logger_name)

        caller_info = self._get_caller_info()

        if log_text:
            if isinstance(log_struct, dict):
                logger.log_struct(log_struct, severity=severity, source_location=caller_info)
            elif isinstance(log_struct, str):
                logger.log_text(log_text, severity=severity, source_location=caller_info)
            else:
                try:
                    turn_to_text = str(log_text)
                    logger.log_text(turn_to_text, severity=severity, source_location=caller_info)
                except Exception as err:
                    print(f"Could not log this: {log_text=} - {str(err)}")

        elif log_struct:
            if not isinstance(log_struct, dict):
                raise ValueError("log_struct must be a dictionary.")
            logger.log_struct(log_struct, severity=severity, source_location=caller_info)

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
        return logger
    
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
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log = logging.getLogger(logger_name)

        return log
    




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