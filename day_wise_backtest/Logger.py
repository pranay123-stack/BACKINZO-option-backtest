import datetime
import logging
import colorlog
import os

def setup_logger(caller_file):
    # Ensure the log directory exists
      # Get the directory where the logger_setup.py script is located
    base_directory = os.path.dirname(os.path.abspath(__file__))
    # Create the log directory path
    log_directory = os.path.join(base_directory, 'log')
    
    # Ensure the log directory exists
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    # Extract the module name from the caller file name
    module_name = os.path.splitext(os.path.basename(caller_file))[0]

    # Configure logger
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    # Create console handler with color
    console_handler = colorlog.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create file handler with a unique file name based on the current timestamp and module name
    log_filename = os.path.join(log_directory, f'{module_name}_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
