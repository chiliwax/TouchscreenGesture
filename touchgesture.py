#!/usr/bin/env python3

import os
import sys
import argparse
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

def main():
    parser = argparse.ArgumentParser(description='TouchGesture - Touchscreen Gesture Detection')
    parser.add_argument('--config', help='Path to configuration file')
    args = parser.parse_args()

    try:
        config_path = args.config if args.config else get_config_path()
        listener = InputListener(config_path)
        listener.start()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopping TouchGesture...")
        sys.exit(0)

if __name__ == '__main__':
    main() 