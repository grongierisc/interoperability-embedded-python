import traceback
import iris
import logging
from typing import Optional, Tuple

class LogManager:
    """Manages logging integration between Python's logging module and IRIS."""

    @staticmethod
    def get_logger(class_name: str, to_console: bool = False) -> logging.Logger:
        """Get a logger instance configured for IRIS integration.
        
        Args:
            class_name: Name of the class logging the message
            method_name: Optional name of the method logging the message
            to_console: If True, log to the console instead of IRIS
            
        Returns:
            Logger instance configured for IRIS integration
        """
        logger = logging.Logger(f"{class_name}")
        
        # Only add handler if none exists
        if not logger.handlers:
            handler = IRISLogHandler(to_console=to_console)
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            # Set the log level to the lowest level to ensure all messages are sent to IRIS
            logger.setLevel(logging.DEBUG)
        
        return logger

class IRISLogHandler(logging.Handler):
    """Custom logging handler that routes Python logs to IRIS logging system."""

    def __init__(self, to_console: bool = False):
        """Initialize the IRIS logging handler."""
        super().__init__()
        self.to_console = to_console

        # Map Python logging levels to IRIS logging methods
        self.level_map = {
            logging.DEBUG: iris.cls("Ens.Util.Log").LogTrace,
            logging.INFO: iris.cls("Ens.Util.Log").LogInfo,
            logging.WARNING: iris.cls("Ens.Util.Log").LogWarning,
            logging.ERROR: iris.cls("Ens.Util.Log").LogError,
            logging.CRITICAL: iris.cls("Ens.Util.Log").LogAlert,
        }
        # Map Python logging levels to IRIS logging Console level
        self.level_map_console = {
            logging.DEBUG: -1,
            logging.INFO: 0,
            logging.WARNING: 1,
            logging.ERROR: 2,
            logging.CRITICAL: 3,
        }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record into a string.
        
        Args:
            record: The logging record to format
            
        Returns:
            Formatted log message
        """
        return record.getMessage()

    def emit(self, record: logging.LogRecord) -> None:
        """Route the log record to appropriate IRIS logging method.
        
        Args:
            record: The logging record to emit
        """
        class_name = record.class_name if hasattr(record, "class_name") else record.name
        method_name = record.method_name if hasattr(record, "method_name") else record.funcName
        if self.to_console or (hasattr(record, "to_console") and record.to_console):
            iris.cls("%SYS.System").WriteToConsoleLog(self.format(record),
                0,self.level_map_console.get(record.levelno, 0),class_name+"."+method_name)
        else:
            log_func = self.level_map.get(record.levelno, iris.cls("Ens.Util.Log").LogInfo)
            log_func(class_name, method_name, self.format(record))
