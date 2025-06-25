import logging
import os
import queue

class LogManager:
    """
    Manages logging for the application.
    Logs messages to a file and maintains an in-memory queue for GUI display.
    """
    def __init__(self, log_file_path="organizer_log.txt", level=logging.INFO):
        self.log_file_path = log_file_path
        self.log_queue = queue.Queue() # Queue to pass log messages to GUI
        self._setup_logger(level)

    def _setup_logger(self, level):
        """Sets up the Python logging system."""
        self.logger = logging.getLogger('FileOrganizer')
        self.logger.setLevel(level)

        # Clear existing handlers to prevent duplicate logs if re-initialized
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # File Handler
        try:
            file_handler = logging.FileHandler(self.log_file_path)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not set up file logging to {self.log_file_path}: {e}")

        # Stream Handler (for console output, mainly during development)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        self.logger.addHandler(stream_handler)

        # Custom Handler for GUI queue
        self.queue_handler = QueueHandler(self.log_queue)
        self.queue_handler.setFormatter(logging.Formatter('%(message)s')) # Simple format for GUI
        self.logger.addHandler(self.queue_handler)

    def info(self, message):
        """Logs an informational message."""
        self.logger.info(message)

    def warning(self, message):
        """Logs a warning message."""
        self.logger.warning(message)

    def error(self, message):
        """Logs an error message."""
        self.logger.error(message)

    def debug(self, message):
        """Logs a debug message."""
        self.logger.debug(message)

    def get_queue(self):
        """Returns the queue for GUI to retrieve log messages."""
        return self.log_queue

class QueueHandler(logging.Handler):
    """
    A custom logging handler that puts log records into a queue.
    Used to pass log messages from the logging system to the GUI.
    """
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        """Emits a log record by putting it into the queue."""
        self.log_queue.put(self.format(record))

# Removed: log_manager = None  <-- THIS LINE SHOULD BE DELETED