import os
import sys
import json
import datetime
import logging
from logging import Logger
import pprint


"""
Modified from: How can I color Python logging output?
https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
"""
class CustomFormatter(logging.Formatter):
    light_green = "\x1b[0;32m"
    light_blue = "\x1b[38;5;117m"
    grey = "\x1b[38;5;250m"
    light_brown = "\x1b[38;5;179m"
    dark_yellow = "\x1b[33;20m"
    red = "\x1b[31m"
    bold_red = "\x1b[1;31m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: light_blue + format + reset,
        logging.INFO: light_green + format + reset,
        logging.WARNING: light_brown + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)
    
    
class LlamediaLogger():
    def __init__(self, bot_name: str=""):
        # Remove all handlers in logging for a clean startup.
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Create the root logger.
        self.root_logger = logging.getLogger(bot_name)
        self.root_logger.propagate = 0
        self.root_logger.setLevel(logging.DEBUG)

        # Create the stdout sub-logger.
        self.stdout_handler = logging.StreamHandler(sys.stdout)
        self.stdout_handler.setFormatter(CustomFormatter())  
        self.root_logger.addHandler(self.stdout_handler)

        # Create the file sub-logger.
        log_dir= os.getenv("LOG_DIR")
        self.bot_log_dir = f'{log_dir}/{bot_name}'
        if not os.path.exists(self.bot_log_dir):
            os.makedirs(self.bot_log_dir)

        curr_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.bot_log_filename = f"{self.bot_log_dir}/log_{curr_timestamp}.txt"

        self.file_handler = logging.FileHandler(self.bot_log_filename)
        file_log_format = f'%(asctime)s - %(name)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)d) '
        file_log_formatter = logging.Formatter(file_log_format, datefmt='%Y-%m-%d %H:%M:%S')
        self.file_handler.setFormatter(file_log_formatter)
        self.root_logger.addHandler(self.file_handler)


    def getLogger(self):
        return self.root_logger
    

    @staticmethod
    def run_demo():
        logger = LlamediaLogger("LoggerDemo").getLogger()
        logger.info(f"LlamediaLogger class initialized.")
        logger.error(f"Demo error message.")
        logger.critical(f"Demo critical message.")
        logger.debug(f"Demo debug message.")
        logger.warn(f"Demo warn message.")