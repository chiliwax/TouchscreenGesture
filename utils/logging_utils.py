import logging
from systemd.journal import JournalHandler
import os
from typing import Optional

def setup_logging(verbose: bool = False, log_file: Optional[str] = None, log_level: int = logging.INFO):
    """Centralized logging setup function
    
    Args:
        verbose (bool): Whether to enable verbose logging
        log_file (str, optional): Path to log file. If None, logs to stdout only
        log_level (int): Logging level to use
    """
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler()]
    handlers.append(JournalHandler())
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    if verbose:
        log_level = logging.DEBUG
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers
    )
    
    if verbose:
        logging.debug("Verbose logging enabled") 