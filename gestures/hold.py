from .base import Gesture
import time

class HoldGesture(Gesture):
    def __init__(self, config):
        super().__init__(config)
        self.required_fingers = config.get('fingers', 1)
        self.required_duration = config.get('duration', 0.5)
        self.current_fingers = 0

    def process_event(self, event_type: int, event_code: int, event_value: int) -> bool:
        # Track number of active fingers
        if event_code == 57:  # ABS_MT_TRACKING_ID
            #self.log_event(event_type, event_code, event_value)
            if event_value >= 0:  # Finger down
                self.current_fingers += 1
                if self.current_fingers == 1:
                    self.start_time = time.time()
            else:  # Finger up
                self.current_fingers -= 1
                if self.current_fingers == 0:
                    self.reset()
                    return False

        # Check if hold duration is met
        if (self.current_fingers == self.required_fingers and 
            not self.is_active and 
            time.time() - self.start_time >= self.required_duration):
            hold_time = time.time() - self.start_time
            self.log_detection(duration=f"{hold_time:.2f}s", fingers=self.current_fingers)
            self.is_active = True
            return True

        return False

    def reset(self):
        super().reset()
        self.current_fingers = 0 