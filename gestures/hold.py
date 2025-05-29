from .base import Gesture
import time
import logging

class HoldGesture(Gesture):
    def __init__(self, config):
        super().__init__(config)
        self.required_fingers = config.get('fingers', 1)
        self.required_duration = config.get('duration', 0.5)
        self.current_fingers = 0
        self.last_event_time = 0

    def process_event(self, event_type: int, event_code: int, event_value: int) -> bool:
        current_time = time.time()
        
        # Track number of active fingers
        if event_code == 57:  # ABS_MT_TRACKING_ID
            self.log_event(event_type, event_code, event_value)
            if event_value >= 0:  # Finger down
                self.current_fingers += 1
                logging.debug(f"{self.name} - Finger down: total_fingers={self.current_fingers}")
                if self.current_fingers == 1:
                    self.start_time = current_time
                    self.last_event_time = current_time
                    logging.debug(f"{self.name} - Started timing at {self.start_time}")
            else:  # Finger up
                self.current_fingers -= 1
                logging.debug(f"{self.name} - Finger up: total_fingers={self.current_fingers}")
                if self.current_fingers == 0:
                    hold_time = current_time - self.start_time
                    logging.debug(f"{self.name} - All fingers lifted after {hold_time:.2f}s")
                    self.reset()
                    return False

        # Check hold duration on every event when fingers are down
        if self.current_fingers > 0:
            hold_time = current_time - self.start_time
            time_since_last_event = current_time - self.last_event_time
            
            # Log if it's been more than 100ms since last event
            if time_since_last_event >= 0.1:
                logging.debug(f"{self.name} - Current hold: duration={hold_time:.2f}s, fingers={self.current_fingers}, time_since_last_event={time_since_last_event:.2f}s")
            
            self.last_event_time = current_time

            # Check if hold duration is met
            if (self.current_fingers == self.required_fingers and 
                not self.is_active and 
                hold_time >= self.required_duration):
                logging.info(f"{self.name} - ❤️ - Hold duration met: {hold_time:.2f}s")
                self.log_detection(duration=f"{hold_time:.2f}s", fingers=self.current_fingers)
                self.is_active = True
                return True

        return False

    def reset(self):
        super().reset()
        self.current_fingers = 0
        self.last_event_time = 0 