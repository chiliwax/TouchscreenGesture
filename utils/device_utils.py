import evdev
import logging
from typing import List, Optional

def list_devices(verbose: bool = False) -> List[evdev.InputDevice]:
    """List all available input devices
    
    Args:
        verbose (bool): Whether to enable verbose logging
        
    Returns:
        List[evdev.InputDevice]: List of found input devices
    """
    if verbose:
        logging.info("Listing devices...")
    else:
        print("Listing devices...")
        
    devices = []
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
            devices.append(dev)
            if verbose:
                logging.info(f"Device: {dev.path}, {dev.name}, {dev.phys}")
                logging.debug(f"Device capabilities: {dev.capabilities()}")
            else:
                print(f"Device: {dev.path}, {dev.name}, {dev.phys}")
        except Exception as e:
            if verbose:
                logging.debug(f"Failed to open device {path}: {e}")
            continue
            
    return devices

def find_device_by_name(name: str, verbose: bool = False) -> Optional[evdev.InputDevice]:
    """Find input device by name pattern
    
    Args:
        name (str): Name pattern to search for
        verbose (bool): Whether to enable verbose logging
        
    Returns:
        Optional[evdev.InputDevice]: Found device or None
    """
    for device in evdev.list_devices():
        try:
            dev = evdev.InputDevice(device)
            if name.lower() in dev.name.lower():
                if verbose:
                    logging.info(f"Found device: {dev.name}")
                    logging.debug(f"Device capabilities: {dev.capabilities()}")
                return dev
        except Exception as e:
            if verbose:
                logging.debug(f"Failed to open device {device}: {e}")
            continue
    return None

def find_device_by_id(event_id: int, verbose: bool = False) -> Optional[evdev.InputDevice]:
    """Find input device by event ID
    
    Args:
        event_id (int): Event ID to search for
        verbose (bool): Whether to enable verbose logging
        
    Returns:
        Optional[evdev.InputDevice]: Found device or None
    """
    try:
        dev = evdev.InputDevice(f"/dev/input/event{event_id}")
        if verbose:
            logging.info(f"Found device: {dev.name}")
            logging.debug(f"Device capabilities: {dev.capabilities()}")
        return dev
    except Exception as e:
        if verbose:
            logging.error(f"Could not find device with event ID: {event_id}")
            logging.debug(f"Error details: {e}")
        return None 