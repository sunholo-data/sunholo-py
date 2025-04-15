from .custom_logging import setup_logging, GoogleCloudLogging

class TracedGoogleCloudLogging(GoogleCloudLogging):
    """Extends GoogleCloudLogging with trace ID functionality."""
    
    def __init__(self, project_id=None, log_level=None, logger_name=None, trace_id=None):
        super().__init__(project_id, log_level, logger_name)
        self.trace_id = trace_id
        
    def update_trace_id(self, trace_id):
        """Update the trace ID to be included in all logs."""
        self.trace_id = trace_id
        
    def _get_trace_prefix(self):
        """Get the trace prefix if a trace ID is set."""
        return f"aitana-{self.trace_id} " if self.trace_id else ""
        
    def structured_log(self, log_text=None, log_struct=None, logger_name=None, severity="INFO"):
        """Override to add trace ID to logs."""
        if log_text and self.trace_id:
            log_text = f"{self._get_trace_prefix()}{log_text}"
            
        if log_struct and self.trace_id:
            if isinstance(log_struct, dict):
                log_struct = {**log_struct, "trace_id": self.trace_id}
                
        # Call the parent method with the modified parameters
        super().structured_log(log_text, log_struct, logger_name, severity)
        
def setup_traced_logging(logger_name=None, log_level=None, project_id=None, trace_id=None):
    """Sets up traced logging that includes a trace ID in all logs."""
    # First get the base logger from the original setup_logging
    base_logger = setup_logging(logger_name, log_level, project_id)
    
    # If it's a GoogleCloudLogging instance, wrap it with our traced version
    if isinstance(base_logger, GoogleCloudLogging):
        traced_logger = TracedGoogleCloudLogging(
            project_id=base_logger.project_id,
            log_level=base_logger.log_level,
            logger_name=base_logger.logger_name,
            trace_id=trace_id
        )
        traced_logger.client = base_logger.client  # Reuse the client
        return traced_logger
    
    # For standard Python logging, we can add a filter
    import logging
    class TraceFilter(logging.Filter):
        def __init__(self, trace_id=None):
            super().__init__()
            self.trace_id = trace_id
            
        def update_trace_id(self, trace_id):
            self.trace_id = trace_id
            
        def filter(self, record):
            if self.trace_id:
                prefix = f"aitana-{self.trace_id} "
                if not record.msg.startswith(prefix):
                    record.msg = f"{prefix}{record.msg}"
            return True
    
    # Add the trace filter to the logger
    trace_filter = TraceFilter(trace_id)
    base_logger.addFilter(trace_filter)
    
    # Add the update method to the standard logger
    base_logger.update_trace_id = trace_filter.update_trace_id
    
    return base_logger