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
        self.finger_positions = {}  # Dictionary to track each finger's position
        self.current_slot = 0  # Current touch slot being updated
        logging.debug(f"{self.name} - Action configured: {self.action}")
        logging.debug(f"{self.name} - Movement tolerance: {self.movement_tolerance}px")

    def calculate_max_movement_distance(self):
        """Calculate the maximum movement distance of any finger"""
        max_distance = 0
        for finger_id, finger_data in self.finger_positions.items():
            if 'initial' in finger_data and 'current' in finger_data:
                initial = finger_data['initial']
                current = finger_data['current']
                dx = current['x'] - initial['x']
                dy = current['y'] - initial['y']
                distance = (dx ** 2 + dy ** 2) ** 0.5
                max_distance = max(max_distance, distance)
        return max_distance

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
                movement_distance = self.calculate_max_movement_distance()
                if movement_distance > self.movement_tolerance:
                    logging.debug(f"{self.name} - Hold cancelled: max movement {movement_distance:.1f}px > {self.movement_tolerance}px tolerance")
                    self.stop_hold_timer()
                    return False
                
                hold_time = time.time() - self.start_time
                if hold_time >= self.required_duration:
                    logging.info(f"{self.name} - ❤️ - Hold duration met: {hold_time:.2f}s (max movement: {movement_distance:.1f}px, fingers: {self.current_fingers})")
                    self.log_detection(duration=f"{hold_time:.2f}s", fingers=self.current_fingers, movement=f"{movement_distance:.1f}px")
                    self.is_active = True
                    self.gesture_triggered = True
                    logging.debug(f"{self.name} - Gesture active, will trigger action: {self.action}")
                    # Trigger the gesture immediately via callback
                    self.trigger_gesture()
                    return True
        return False

    def process_event(self, event_type: int, event_code: int, event_value: int) -> bool:
        # Track touch slots
        if event_type == 3:  # EV_ABS
            if event_code == 47:  # ABS_MT_SLOT
                self.current_slot = event_value
                logging.debug(f"{self.name} - Switched to slot {self.current_slot}")
            elif event_code == 53:  # ABS_MT_POSITION_X
                # Update current position for the active slot
                if self.current_slot not in self.finger_positions:
                    self.finger_positions[self.current_slot] = {}
                
                if 'current' not in self.finger_positions[self.current_slot]:
                    self.finger_positions[self.current_slot]['current'] = {'x': event_value, 'y': 0}
                else:
                    self.finger_positions[self.current_slot]['current']['x'] = event_value
                    
                logging.debug(f"{self.name} - Slot {self.current_slot} position X: {event_value}")
                
            elif event_code == 54:  # ABS_MT_POSITION_Y
                # Update current position for the active slot
                if self.current_slot not in self.finger_positions:
                    self.finger_positions[self.current_slot] = {}
                
                if 'current' not in self.finger_positions[self.current_slot]:
                    self.finger_positions[self.current_slot]['current'] = {'x': 0, 'y': event_value}
                else:
                    self.finger_positions[self.current_slot]['current']['y'] = event_value
                    
                logging.debug(f"{self.name} - Slot {self.current_slot} position Y: {event_value}")
        
        # Track number of active fingers
        if event_code == 57:  # ABS_MT_TRACKING_ID
            self.log_event(event_type, event_code, event_value)
            if event_value >= 0:  # Finger down
                self.current_fingers += 1
                logging.debug(f"{self.name} - Finger down: total_fingers={self.current_fingers}")
                
                # Set initial position for this finger
                if (self.current_slot in self.finger_positions and 
                    'current' in self.finger_positions[self.current_slot]):
                    self.finger_positions[self.current_slot]['initial'] = self.finger_positions[self.current_slot]['current'].copy()
                    logging.debug(f"{self.name} - Initial position for slot {self.current_slot}: {self.finger_positions[self.current_slot]['initial']}")
                
                # Start timer when we have the required number of fingers
                if self.current_fingers == self.required_fingers:
                    self.start_time = time.time()
                    logging.debug(f"{self.name} - Required fingers reached, starting hold timer...")
                    self.start_hold_timer()
                elif self.current_fingers > self.required_fingers:
                    # Too many fingers, cancel hold
                    logging.debug(f"{self.name} - Too many fingers ({self.current_fingers} > {self.required_fingers}), cancelling hold")
                    self.stop_hold_timer()
                    
            else:  # Finger up
                self.current_fingers -= 1
                logging.debug(f"{self.name} - Finger up: total_fingers={self.current_fingers}")
                
                # Remove finger position data
                if self.current_slot in self.finger_positions:
                    del self.finger_positions[self.current_slot]
                    logging.debug(f"{self.name} - Removed position data for slot {self.current_slot}")
                
                if self.current_fingers == 0:
                    hold_time = time.time() - self.start_time
                    movement_distance = self.calculate_max_movement_distance()
                    logging.debug(f"{self.name} - All fingers lifted after {hold_time:.2f}s (max movement: {movement_distance:.1f}px)")
                    self.stop_hold_timer()
                    self.reset()
                    return False
                elif self.current_fingers < self.required_fingers:
                    # Not enough fingers anymore, cancel hold
                    logging.debug(f"{self.name} - Not enough fingers ({self.current_fingers} < {self.required_fingers}), cancelling hold")
                    self.stop_hold_timer()

        # Check movement during hold period
        if self.hold_timer and len(self.finger_positions) >= self.required_fingers:
            movement_distance = self.calculate_max_movement_distance()
            if movement_distance > self.movement_tolerance:
                logging.debug(f"{self.name} - Hold cancelled during movement: {movement_distance:.1f}px > {self.movement_tolerance}px")
                self.stop_hold_timer()
                return False

        return False

    def reset(self):
        super().reset()
        self.current_fingers = 0
        self.gesture_triggered = False
        self.finger_positions = {}
        self.current_slot = 0
        self.stop_hold_timer() 