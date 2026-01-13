import logging
from logging import Logger

def get_logger(name: str) -> Logger:
    """
    Return a configured logger. This keeps logging configuration in one place.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Basic console handler
        ch = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
        ch.setFormatter(fmt)
        logger.addHandler(ch)
        # Default level can be overridden globally by setting root logger
        logger.setLevel(logging.INFO)
    return logger