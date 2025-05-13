

import logging
import traceback

class ErrorHandler:
    def __init__(self, log_file):
        self.logger = logging.getLogger('ErrorHandler')
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.ERROR)

    def handle_exception(self, e):
        error_message = f"An error occurred: {str(e)}"
        traceback_message = traceback.format_exc()
        self.logger.error(f"{error_message}\n{traceback_message}")
        print(f"Reporting error: {error_message}")
        print("Attempting to recover from error...")
        print(traceback_message)  # This will print the detailed traceback to the console

    def log_error(self, e):
        # Log the error with traceback
        error_message = ''.join(traceback.format_exception(None, e, e.__traceback__))
        self.logger.error(error_message)

    def report_error(self, e):
        # Report the error (e.g., send an email or notification)
        # Placeholder for error reporting logic
        print(f"Reporting error: {e}")

    def recover_from_error(self, e):
        # Recover from the error if possible
        # Placeholder for error recovery logic
        print("Attempting to recover from error...")

    def handle_specific_error(self, e, custom_message):
        # Handle specific types of errors with custom messages
        if isinstance(e, FileNotFoundError):
            print(f"File not found: {custom_message}")
        elif isinstance(e, ValueError):
            print(f"Invalid value: {custom_message}")
        else:
            self.handle_exception(e)

# Example usage:
# try:
#     # Code that may raise an exception
#     raise ValueError("An example error")
# except Exception as e:
#     error_handler = ErrorHandler()
#     error_handler.handle_exception(e)
