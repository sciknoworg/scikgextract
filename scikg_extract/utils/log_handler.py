import os
import logging
import datetime
from typing import Optional, List
from logging import FileHandler
from logging.handlers import RotatingFileHandler

class LogHandler:
    """A utility class for handling logging configuration."""

    # Default configuration
    LOG_DIR = "logs"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    @staticmethod
    def setup_logging(name: str, log_dir: Optional[str] = None, log_file: Optional[str] = None, console_level: int = logging.INFO, file_level: int = logging.DEBUG, rotating: bool = True, max_bytes: int = 10*1024*1024, backup_count: int = 10, propogate: bool = True) -> logging.Logger:
        """
        Set up logging with console and optional file handlers.

        Args:
            name (str): Name of the logger.
            log_dir (Optional[str]): Directory to save log files. Defaults to 'logs'.
            log_file (Optional[str]): Log file name. If None, file logging is disabled.
            console_level (int): Logging level for console output.
            file_level (int): Logging level for file output.
            rotating (bool): Whether to use rotating file handler.
            max_bytes (int): Maximum size of log file before rotation.
            backup_count (int): Number of backup files to keep.
            propogate (bool): Whether to propagate logs to ancestor loggers.

        Returns:
            logging.Logger: Configured logger instance.
        """

        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)  # Capture all levels; handlers will filter
        logger.propagate = propogate

        # Clear existing handlers
        if logger.hasHandlers(): logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(fmt=LogHandler.LOG_FORMAT, datefmt=LogHandler.DATE_FORMAT)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        if log_file:

            # Ensure log directory
            log_dir = log_dir or LogHandler.LOG_DIR
            os.makedirs(log_dir, exist_ok=True)

            # Append timestamp to log file name
            timestamp = datetime.datetime.now().strftime("%Y%m%d")
            log_file = f"{os.path.splitext(log_file)[0]}_{timestamp}.log"

            # Full log file path
            log_filepath = os.path.join(log_dir, log_file)

            # Choose handler type
            if rotating:
                file_handler = RotatingFileHandler(
                    log_filepath,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
            else:
                file_handler = FileHandler(log_filepath, mode='a', encoding='utf-8')

            file_handler.setLevel(file_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Return the configured logger
        return logger
    
    @staticmethod
    def setup_module_logging(module_name: str, console_level: int = logging.INFO, file_level: int = logging.DEBUG) -> logging.Logger:
        """
        Set up logging for a specific module.

        Args:
            module_name (str): Name of the module.
            console_level (int): Logging level for console output.
            file_level (int): Logging level for file output.
        Returns:
            logging.Logger: Configured logger instance for the module.
        """

        # Build log dir with module name
        log_dir = os.path.join(LogHandler.LOG_DIR, module_name)

        # Build log file name
        log_file = f"{module_name}.log"

        # Return the configured logger
        return LogHandler.setup_logging(
            name=module_name,
            log_dir=log_dir,
            log_file=log_file,
            console_level=console_level,
            file_level=file_level
        )

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Get a logger by name.
        Args:
            name (str): Name of the logger.
        Returns:
            logging.Logger: Logger instance.
        """
        return logging.getLogger(name)