import evdev
from typing import List, Dict, Any, Optional
import yaml
import os
import logging
from gestures.hold import HoldGesture
from gestures.pinch import PinchGesture

class InputListener:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.devices: List[evdev.InputDevice] = []
        self.gestures = []
        self.setup_logging()
        self._setup_gestures()
        self._setup_devices()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get('debug', {})
        if log_config.get('enabled', False):
            logging.basicConfig(
                filename=log_config.get('log_file', '/var/log/touchgesture.log'),
                level=logging.DEBUG,
                format='%(asctime)s - %(levelname)s - %(message)s'
            )

    def _setup_gestures(self):
        """Initialize gesture recognizers based on config"""
        gesture_configs = self.config.get('gestures', {})
        
        if gesture_configs.get('hold', {}).get('enabled', False):
            self.gestures.append(HoldGesture(gesture_configs['hold']))
        
        if gesture_configs.get('pinch', {}).get('enabled', False):
            self.gestures.append(PinchGesture(gesture_configs['pinch']))

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
                    logging.debug(f"Found device: {dev.name}")
            except:
                continue

    def _find_device_by_id(self, event_id: int):
        """Find input device by event ID"""
        try:
            dev = evdev.InputDevice(f"/dev/input/event{event_id}")
            self.devices.append(dev)
            logging.debug(f"Found device: {dev.name}")
        except:
            logging.error(f"Could not find device with event ID: {event_id}")

    def start(self):
        """Start listening for input events"""
        if not self.devices:
            logging.error("No input devices found")
            return

        try:
            # Create a select-based event loop
            from select import select
            while True:
                r, w, x = select(self.devices, [], [])
                for device in r:
                    for event in device.read():
                        self._process_event(event)
        except KeyboardInterrupt:
            logging.info("Stopping input listener")
        finally:
            for device in self.devices:
                device.close()

    def _process_event(self, event):
        """Process an input event through all gesture recognizers"""
        for gesture in self.gestures:
            if gesture.process_event(event.type, event.code, event.value):
                self._trigger_action(gesture.action)
                gesture.reset()

    def _trigger_action(self, action_name: str):
        """Trigger the configured action"""
        action_config = self.config.get('actions', {}).get(action_name)
        if not action_config:
            return

        action_type = action_config.get('type')
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
        subprocess.run(['xdotool', f'mouse{event}', button])

    def _trigger_keyboard_action(self, config: Dict[str, Any]):
        """Trigger a keyboard action using xdotool"""
        import subprocess
        keys = config.get('in', '').split('+')
        subprocess.run(['xdotool', 'key'] + keys)

    def _trigger_command_action(self, config: Dict[str, Any]):
        """Trigger a shell command"""
        import subprocess
        command = config.get('command', '')
        if command:
            subprocess.run(command, shell=True) 