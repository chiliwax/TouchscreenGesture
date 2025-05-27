import evdev
from typing import List, Dict, Any, Optional
import yaml
import os
import logging
from gestures.hold import HoldGesture
from gestures.pinch import PinchGesture

class InputListener:
    def __init__(self, config_path: str, verbose: bool = False):
        self.config = self._load_config(config_path)
        self.devices: List[evdev.InputDevice] = []
        self.gestures = []
        self.verbose = verbose
        self.setup_logging()
        self._setup_gestures()
        self._setup_devices()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if self.verbose:
                logging.debug(f"Loaded configuration: {config}")
            return config

    def setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get('debug', {})
        if self.verbose or log_config.get('enabled', False):
            log_file = log_config.get('log_file', '/var/log/touchgesture.log')
            logging.basicConfig(
                filename=log_file,
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )
            logging.debug("Debug logging enabled")

    def _setup_gestures(self):
        """Initialize gesture recognizers based on config"""
        gesture_configs = self.config.get('gestures', {})
        
        if gesture_configs.get('hold', {}).get('enabled', False):
            self.gestures.append(HoldGesture(gesture_configs['hold']))
            logging.debug("Hold gesture enabled")
        
        if gesture_configs.get('pinch', {}).get('enabled', False):
            self.gestures.append(PinchGesture(gesture_configs['pinch']))
            logging.debug("Pinch gesture enabled")

    def _setup_devices(self):
        """Find and setup input devices based on config"""
        device_configs = self.config.get('devices', [])
        
        for device_config in device_configs:
            if 'name' in device_config:
                self._find_device_by_name(device_config['name'])
            elif 'event_id' in device_config:
                self._find_device_by_id(device_config['event_id'])

    def _find_device_by_name(self, name: str):
        """Find input device by name pattern"""
        for device in evdev.list_devices():
            try:
                dev = evdev.InputDevice(device)
                if name.lower() in dev.name.lower():
                    self.devices.append(dev)
                    logging.info(f"Found device: {dev.name}")
                    if self.verbose:
                        logging.debug(f"Device capabilities: {dev.capabilities()}")
            except Exception as e:
                if self.verbose:
                    logging.debug(f"Failed to open device {device}: {e}")
                continue

    def _find_device_by_id(self, event_id: int):
        """Find input device by event ID"""
        try:
            dev = evdev.InputDevice(f"/dev/input/event{event_id}")
            self.devices.append(dev)
            logging.info(f"Found device: {dev.name}")
            if self.verbose:
                logging.debug(f"Device capabilities: {dev.capabilities()}")
        except Exception as e:
            logging.error(f"Could not find device with event ID: {event_id}")
            if self.verbose:
                logging.debug(f"Error details: {e}")

    def start(self):
        """Start listening for input events"""
        if not self.devices:
            logging.error("No input devices found")
            return

        try:
            # Create a select-based event loop
            from select import select
            logging.info("Starting event loop...")
            while True:
                r, w, x = select(self.devices, [], [])
                for device in r:
                    for event in device.read():
                        if self.verbose:
                            logging.debug(f"Event: type={event.type}, code={event.code}, value={event.value}")
                        self._process_event(event)
        except KeyboardInterrupt:
            logging.info("Stopping input listener")
        finally:
            for device in self.devices:
                device.close()
                logging.debug(f"Closed device: {device.name}")

    def _process_event(self, event):
        """Process an input event through all gesture recognizers"""
        for gesture in self.gestures:
            if gesture.process_event(event.type, event.code, event.value):
                if self.verbose:
                    logging.debug(f"Gesture recognized: {gesture.__class__.__name__}")
                self._trigger_action(gesture.action)
                gesture.reset()

    def _trigger_action(self, action_name: str):
        """Trigger the configured action"""
        action_config = self.config.get('actions', {}).get(action_name)
        if not action_config:
            if self.verbose:
                logging.debug(f"No action configuration found for: {action_name}")
            return

        action_type = action_config.get('type')
        if self.verbose:
            logging.debug(f"Triggering action: {action_name} (type: {action_type})")

        if action_type == 'mouse':
            self._trigger_mouse_action(action_config)
        elif action_type == 'keyboard':
            self._trigger_keyboard_action(action_config)
        elif action_type == 'command':
            self._trigger_command_action(action_config)

    def _trigger_mouse_action(self, config: Dict[str, Any]):
        """Trigger a mouse action using xdotool"""
        import subprocess
        button = config.get('button', 'left')
        event = config.get('event', 'click')
        cmd = ['xdotool', f'mouse{event}', button]
        if self.verbose:
            logging.debug(f"Executing mouse command: {' '.join(cmd)}")
        subprocess.run(cmd)

    def _trigger_keyboard_action(self, config: Dict[str, Any]):
        """Trigger a keyboard action using xdotool"""
        import subprocess
        keys = config.get('in', '').split('+')
        cmd = ['xdotool', 'key'] + keys
        if self.verbose:
            logging.debug(f"Executing keyboard command: {' '.join(cmd)}")
        subprocess.run(cmd)

    def _trigger_command_action(self, config: Dict[str, Any]):
        """Trigger a shell command"""
        import subprocess
        command = config.get('command', '')
        if command:
            if self.verbose:
                logging.debug(f"Executing shell command: {command}")
            subprocess.run(command, shell=True) 