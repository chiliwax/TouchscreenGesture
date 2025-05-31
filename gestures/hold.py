from .base import Gesture
import time
import logging
import threading

class HoldGesture(Gesture):
    def __init__(self, config):
        super().__init__(config)
        self.required_fingers = config.get('fingers', 1)
        self.required_duration = config.get('duration', 0.5)
        self.movement_tolerance = config.get('movement_tolerance', 20)  # pixels
        self.current_fingers = 0
        self.hold_timer = None
        self.hold_timer_lock = threading.Lock()
        self.gesture_triggered = False
        self.initial_position = None
        self.current_position = None
        self.waiting_for_initial_position = False
        logging.debug(f"{self.name} - Action configured: {self.action}")
        logging.debug(f"{self.name} - Movement tolerance: {self.movement_tolerance}px")

    def calculate_movement_distance(self):
        """Calculate the distance moved from initial touch position"""
        if not self.initial_position or not self.current_position:
            return 0
        
        dx = self.current_position['x'] - self.initial_position['x']
        dy = self.current_position['y'] - self.initial_position['y']
        distance = (dx ** 2 + dy ** 2) ** 0.5
        return distance

    def start_hold_timer(self):
        with self.hold_timer_lock:
            if self.hold_timer is None:
                self.hold_timer = threading.Timer(self.required_duration, self.check_hold_duration)
                self.hold_timer.start()
                logging.debug(f"{self.name} - Started hold timer for {self.required_duration}s")

    def stop_hold_timer(self):
        with self.hold_timer_lock:
            if self.hold_timer is not None:
                self.hold_timer.cancel()
                self.hold_timer = None
                logging.debug(f"{self.name} - Stopped hold timer")

    def check_hold_duration(self):
        with self.hold_timer_lock:
            if (self.current_fingers == self.required_fingers and 
                not self.is_active and not self.gesture_triggered):
                
                # Check if movement exceeds tolerance
                movement_distance = self.calculate_movement_distance()
                if movement_distance > self.movement_tolerance:
                    logging.debug(f"{self.name} - Hold cancelled: movement {movement_distance:.1f}px > {self.movement_tolerance}px tolerance")
                    self.stop_hold_timer()
                    return False
                
                hold_time = time.time() - self.start_time
                if hold_time >= self.required_duration:
                    logging.info(f"{self.name} - ❤️ - Hold duration met: {hold_time:.2f}s (movement: {movement_distance:.1f}px)")
                    self.log_detection(duration=f"{hold_time:.2f}s", fingers=self.current_fingers, movement=f"{movement_distance:.1f}px")
                    self.is_active = True
                    self.gesture_triggered = True
                    logging.debug(f"{self.name} - Gesture active, will trigger action: {self.action}")
                    # Trigger the gesture immediately via callback
                    self.trigger_gesture()
                    return True
        return False

    def process_event(self, event_type: int, event_code: int, event_value: int) -> bool:
        # Track position updates
        if event_type == 3:  # EV_ABS
            if event_code == 53:  # ABS_MT_POSITION_X
                if self.current_position is None:
                    self.current_position = {'x': event_value, 'y': 0}
                else:
                    self.current_position['x'] = event_value
                
                # Set initial position if we're waiting for it
                if self.waiting_for_initial_position and self.current_position['y'] != 0:
                    self.initial_position = self.current_position.copy()
                    self.waiting_for_initial_position = False
                    logging.debug(f"{self.name} - Initial position set: {self.initial_position}")
                
                # Check movement during hold period
                if self.hold_timer and self.initial_position:
                    movement_distance = self.calculate_movement_distance()
                    if movement_distance > self.movement_tolerance:
                        logging.debug(f"{self.name} - Hold cancelled during movement: {movement_distance:.1f}px > {self.movement_tolerance}px")
                        self.stop_hold_timer()
                        return False
                        
            elif event_code == 54:  # ABS_MT_POSITION_Y
                if self.current_position is None:
                    self.current_position = {'x': 0, 'y': event_value}
                else:
                    self.current_position['y'] = event_value
                
                # Set initial position if we're waiting for it
                if self.waiting_for_initial_position and self.current_position['x'] != 0:
                    self.initial_position = self.current_position.copy()
                    self.waiting_for_initial_position = False
                    logging.debug(f"{self.name} - Initial position set: {self.initial_position}")
                
                # Check movement during hold period
                if self.hold_timer and self.initial_position:
                    movement_distance = self.calculate_movement_distance()
                    if movement_distance > self.movement_tolerance:
                        logging.debug(f"{self.name} - Hold cancelled during movement: {movement_distance:.1f}px > {self.movement_tolerance}px")
                        self.stop_hold_timer()
                        return False
        
        # Track number of active fingers
        if event_code == 57:  # ABS_MT_TRACKING_ID
            self.log_event(event_type, event_code, event_value)
            if event_value >= 0:  # Finger down
                self.current_fingers += 1
                logging.debug(f"{self.name} - Finger down: total_fingers={self.current_fingers}")
                if self.current_fingers == 1:
                    self.start_time = time.time()
                    # Mark that we're waiting for the first position update
                    self.waiting_for_initial_position = True
                    self.initial_position = None
                    logging.debug(f"{self.name} - Waiting for initial position...")
                    self.start_hold_timer()
            else:  # Finger up
                self.current_fingers -= 1
                logging.debug(f"{self.name} - Finger up: total_fingers={self.current_fingers}")
                if self.current_fingers == 0:
                    hold_time = time.time() - self.start_time
                    movement_distance = self.calculate_movement_distance()
                    logging.debug(f"{self.name} - All fingers lifted after {hold_time:.2f}s (movement: {movement_distance:.1f}px)")
                    self.stop_hold_timer()
                    self.reset()
                    return False

        # No longer need to check is_active here since we use callbacks
        return False

    def reset(self):
        super().reset()
        self.current_fingers = 0
        self.gesture_triggered = False
        self.initial_position = None
        self.current_position = None
        self.waiting_for_initial_position = False
        self.stop_hold_timer() 