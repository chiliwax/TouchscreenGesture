import evdev
from typing import List, Dict, Any, Optional
import yaml
import os
import logging
from gestures.hold import HoldGesture
from gestures.pinch import PinchGesture
from utils.logging_utils import setup_logging
from utils.device_utils import find_device_by_name, find_device_by_id

class InputListener:
    def __init__(self, config_path: str, verbose: bool = False):
        self.verbose = verbose
        self.config = self._load_config(config_path)
        self.devices: List[evdev.InputDevice] = []
        self.gestures = []
        self.total_active_fingers = 0
        self.device_grabbed = False
        self.grab_timeout_timer = None
        self._setup_logging()
        self._setup_gestures()
        self._setup_devices()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if self.verbose:
                logging.debug(f"Loaded configuration: {config}")
            return config

    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get('debug', {})
        log_file = log_config.get('log_file', '/var/log/touchgesture.log')
        setup_logging(self.verbose, log_file)

    def _setup_gestures(self):
        """Initialize gesture recognizers based on config"""
        gesture_configs = self.config.get('gestures', {})
        
        if gesture_configs.get('hold', {}).get('enabled', False):
            hold_gesture = HoldGesture(gesture_configs['hold'])
            hold_gesture.set_gesture_callback(self._on_gesture_detected)
            self.gestures.append(hold_gesture)
            logging.debug("Hold gesture enabled")
        
        if gesture_configs.get('pinch', {}).get('enabled', False):
            pinch_gesture = PinchGesture(gesture_configs['pinch'])
            pinch_gesture.set_gesture_callback(self._on_gesture_detected)
            self.gestures.append(pinch_gesture)
            logging.debug("Pinch gesture enabled")

    def _setup_devices(self):
        """Find and setup input devices based on config"""
        device_configs = self.config.get('devices', [])
        
        for device_config in device_configs:
            if 'name' in device_config:
                device = find_device_by_name(device_config['name'], self.verbose)
                if device:
                    self.devices.append(device)
            elif 'event_id' in device_config:
                device = find_device_by_id(device_config['event_id'], self.verbose)
                if device:
                    self.devices.append(device)

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
            # Clean up
            self._cancel_ungrab_timer()
            self._ungrab_devices()
            for device in self.devices:
                device.close()
                logging.debug(f"Closed device: {device.name}")

    def _grab_devices(self):
        """Grab all input devices to prevent system interference"""
        if not self.device_grabbed:
            try:
                for device in self.devices:
                    device.grab()
                self.device_grabbed = True
                if self.verbose:
                    logging.debug("Grabbed input devices to prevent interference")
                
                # Safety ungrab after 5 seconds to prevent permanent grab
                self._schedule_safety_ungrab()
            except Exception as e:
                logging.warning(f"Failed to grab devices: {e}")

    def _ungrab_devices(self):
        """Release device grab"""
        if self.device_grabbed:
            try:
                for device in self.devices:
                    device.ungrab()
                self.device_grabbed = False
                if self.verbose:
                    logging.debug("Released device grab")
            except Exception as e:
                logging.warning(f"Failed to ungrab devices: {e}")

    def _cancel_ungrab_timer(self):
        """Cancel any pending ungrab timer"""
        if self.grab_timeout_timer:
            self.grab_timeout_timer.cancel()
            self.grab_timeout_timer = None

    def _schedule_ungrab(self, delay=0.1):
        """Schedule device ungrab after a short delay"""
        import threading
        self._cancel_ungrab_timer()
        self.grab_timeout_timer = threading.Timer(delay, self._ungrab_devices)
        self.grab_timeout_timer.start()
        if self.verbose:
            logging.debug(f"Scheduled device ungrab in {delay}s")

    def _update_finger_count(self, event):
        """Track total active fingers across all devices"""
        if event.code == 57:  # ABS_MT_TRACKING_ID
            old_count = self.total_active_fingers
            if event.value >= 0:  # Finger down
                self.total_active_fingers += 1
            else:  # Finger up
                self.total_active_fingers = max(0, self.total_active_fingers - 1)
            
            if self.verbose and old_count != self.total_active_fingers:
                logging.debug(f"Total active fingers: {old_count} → {self.total_active_fingers}")
            
            # Schedule ungrab if no fingers remain and devices are grabbed
            # (but only if there's no pending action ungrab)
            if (self.total_active_fingers == 0 and self.device_grabbed and 
                self.grab_timeout_timer is None):
                self._schedule_ungrab()

    def _process_event(self, event):
        """Process an input event through all gesture recognizers"""
        # Update finger count tracking
        self._update_finger_count(event)
        
        for gesture in self.gestures:
            if self.verbose:
                logging.debug(f"Processing event for {gesture.__class__.__name__}")
            if gesture.process_event(event.type, event.code, event.value):
                if self.verbose:
                    logging.debug(f"Gesture recognized: {gesture.__class__.__name__}")
                    logging.debug(f"Action to trigger: {gesture.action}")
                self._trigger_action(gesture.action)
                gesture.reset()

    def _trigger_action(self, action_name: str):
        """Trigger the configured action"""
        if self.verbose:
            logging.debug(f"Looking up action: {action_name}")
        action_config = self.config.get('actions', {}).get(action_name)
        if not action_config:
            if self.verbose:
                logging.debug(f"No action configuration found for: {action_name}")
            return

        action_type = action_config.get('type')
        if self.verbose:
            logging.debug(f"Triggering action: {action_name} (type: {action_type})")
            logging.debug(f"Action config: {action_config}")

        if action_type == 'mouse':
            self._trigger_mouse_action(action_config)
        elif action_type == 'keyboard':
            self._trigger_keyboard_action(action_config)
        elif action_type == 'command':
            self._trigger_command_action(action_config)
        else:
            if self.verbose:
                logging.debug(f"Unknown action type: {action_type}")

    def _trigger_mouse_action(self, config: Dict[str, Any]):
        """Trigger a mouse action using xdotool"""
        import subprocess
        button = config.get('button', 'left')
        event = config.get('event', 'click')
        cmd = ['xdotool', f'mouse{event}', button]
        if self.verbose:
            logging.debug(f"Executing mouse command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            if self.verbose:
                logging.debug("Mouse command executed successfully")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to execute mouse command: {e}")
        except Exception as e:
            logging.error(f"Unexpected error executing mouse command: {e}")

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

    def _on_gesture_detected(self, action_name: str):
        """Handle gesture detection callback"""
        if self.verbose:
            logging.debug(f"Gesture callback received for action: {action_name}")
        
        # Grab devices to prevent interference
        self._grab_devices()
        
        try:
            # Trigger the action
            self._trigger_action(action_name)
        except Exception as e:
            logging.error(f"Error executing action {action_name}: {e}")
        finally:
            # Always schedule ungrab after action, regardless of finger count
            self._schedule_ungrab_after_action()

    def _schedule_ungrab_after_action(self):
        """Schedule device ungrab after action"""
        import threading
        self._cancel_ungrab_timer()
        # Use a shorter delay for post-action ungrab to ensure responsiveness
        self.grab_timeout_timer = threading.Timer(0.05, self._ungrab_devices)
        self.grab_timeout_timer.start()
        if self.verbose:
            logging.debug("Scheduled device ungrab after action in 0.05s")

    def _schedule_safety_ungrab(self):
        """Schedule a safety ungrab after 5 seconds to prevent permanent device grab"""
        import threading
        def safety_ungrab():
            if self.device_grabbed:
                logging.warning("Safety ungrab triggered - devices were grabbed for too long")
                self._ungrab_devices()
        
        safety_timer = threading.Timer(5.0, safety_ungrab)
        safety_timer.daemon = True  # Don't prevent program exit
        safety_timer.start() 