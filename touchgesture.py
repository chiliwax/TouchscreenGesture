#!/usr/bin/env python3

import os
import sys
import argparse
import logging
from input.listener import InputListener

def get_config_path():
    """Get the appropriate config file path"""
    # First try user config
    user_config = os.path.expanduser('~/.config/touchgesture/config.yaml')
    if os.path.exists(user_config):
        return user_config
    
    # Then try system config
    system_config = '/etc/touchgesture/default.yaml'
    if os.path.exists(system_config):
        return system_config
    
    # Finally, try local config
    local_config = os.path.join(os.path.dirname(__file__), 'config/default.yaml')
    if os.path.exists(local_config):
        return local_config
    
    raise FileNotFoundError("No configuration file found")

def setup_logging(verbose: bool):
    """Setup logging configuration"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format=log_format,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('/tmp/touchgesture.log')
            ]
        )
        logging.debug("Verbose logging enabled")
    else:
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[logging.StreamHandler()]
        )

def main():
    parser = argparse.ArgumentParser(description='TouchGesture - Touchscreen Gesture Detection')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    try:
        setup_logging(args.verbose)
        config_path = args.config if args.config else get_config_path()
        logging.info(f"Using configuration from: {config_path}")
        
        listener = InputListener(config_path, verbose=args.verbose)
        logging.info("Starting TouchGesture daemon...")
        listener.start()
    except FileNotFoundError as e:
        logging.error(f"Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("\nStopping TouchGesture...")
        sys.exit(0)

if __name__ == '__main__':
    main() 