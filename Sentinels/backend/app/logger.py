import logging
import sys

def setup_logger():
    # Create a custom logger
    logger = logging.getLogger("sentinels")
    
    # Avoid duplicate logs if already configured
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # Create handlers
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(logging.INFO)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    
    return logger

logger = setup_logger()
