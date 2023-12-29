# ciab/logging.py
# https://cloud.google.com/python/docs/reference/logging/latest/google.cloud.logging_v2.client.Client

from google.cloud.logging import Client
from .utils.gcp import get_gcp_project
import logging

class GoogleCloudLogging:
    def __init__(self, project_id=None, logger_name=None):
        """
        Initializes the GoogleCloudLogging instance with a specific Google Cloud project ID.
        
        Args:
            project_id (str): The project ID for the Google Cloud project.
        """
        # Instantiates a Google Cloud logging client
        if project_id is None:
            self.project_id = get_gcp_project()
        else:
            self.project_id = project_id

        self.client = Client(project=self.project_id)
        self.logger_name = logger_name

    def setup_logging(self, log_level=logging.INFO, logger_name=None):
        try:
            self.client.setup_logging(log_level=log_level)
            if logger_name:
                self.logger_name = logger_name
            return self  # Return the instance itself on success
        except Exception as e:
            # If there's an exception, use standard Python logging as a fallback
            logging.basicConfig(level=log_level)
            logging.warning(f"Failed to set up Google Cloud Logging. Using standard logging. Error: {e}")
            return logging.getLogger()  # Return the root logger


    def structured_log(self, log_text=None, log_struct=None, logger_name=None, severity="INFO"):
        """
        Writes log entries to the specified logger as either text or structured data.

        Args:
            log_text (str, optional): The log message as a text string. Defaults to None.
            log_struct (dict, optional): The log message as a dictionary for structured logging. Defaults to None.
            logger_name (str, optional): The name of the logger to which to write the log entries. e.g. 
        logName="projects/your-project/logs/run.googleapis.com%2Fstderr"
            severity (str, optional): The severity level of the log entry. Defaults to "INFO".
        """

        if not logger_name and not self.logger_name:
            ValueError("Must provide a logger name e.g. projects/your-project/logs/run.googleapis.com%2Fstderr")

        logger = self.client.logger(logger_name)
        sunholo_logger = self.client.logger(f"projects/{self.project_id}/logs/sunholo")

        if log_text:
            logger.log_text(log_text, severity=severity)
            sunholo_logger.log_text(log_text, severity=severity)

        elif log_struct:
            if not isinstance(log_struct, dict):
                raise ValueError("log_struct must be a dictionary.")
            logger.log_struct(log_struct, severity=severity)
            sunholo_logger.log_struct(log_struct, severity=severity)


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

    def warn(self, log_text=None, log_struct=None):
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

def setup_logging(logger_name=None, log_level=logging.INFO, project_id=None):
    """
    Sets up Google Cloud Logging with the provided log level and project ID. If no project ID
    is provided, it attempts to retrieve the project ID from the metadata server.

    Parameters:
    logger_name (str): The name of the log to send to. If not provided, set to run.googleapis.com%2Fstderr
    log_level: The logging level to capture. Uses Python's logging module levels.
               Default is logging.INFO.
    project_id: A string representing the Google Cloud project ID. If None, the project ID
                will be retrieved from the metadata server.

    Example:
        # Set up Google Cloud Logging for the script with default INFO level
        setup_logging()

        # Now you can use Python's logging module as usual
        import logging
        logging.info('This is an info message that will be sent to Google Cloud Logging.')
        
    Note:
        This function requires that the 'google-cloud-logging' library is installed and
        that the application is authenticated with Google Cloud. This can be done by setting
        the GOOGLE_APPLICATION_CREDENTIALS environment variable to the path of your service
        account key file, or by running this code in an environment where default
        application credentials are already set, such as Google Cloud Compute Engine,
        Google Kubernetes Engine, Google App Engine, etc.
    """

    if project_id is None:
        project_id = get_gcp_project()

    if logger_name is None:
        logger_name = f"projects/{project_id}/logs/run.googleapis.com%2Fstderr"

    # Instantiate the GoogleCloudLogging class
    gc_logger = GoogleCloudLogging(project_id)

    # Setup logging and return the logger instance
    return gc_logger.setup_logging(log_level=log_level, logger_name=logger_name)


