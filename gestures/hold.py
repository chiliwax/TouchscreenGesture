from .base import Gesture
import time
import logging
import threading

class HoldGesture(Gesture):
    def __init__(self, config):
        super().__init__(config)
        self.required_fingers = config.get('fingers', 1)
        self.required_duration = config.get('duration', 0.5)
        self.current_fingers = 0
        self.hold_timer = None
        self.hold_timer_lock = threading.Lock()
        logging.debug(f"{self.name} - Action configured: {self.action}")

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
                not self.is_active):
                hold_time = time.time() - self.start_time
                logging.info(f"{self.name} - ❤️ - Hold duration met: {hold_time:.2f}s")
                self.log_detection(duration=f"{hold_time:.2f}s", fingers=self.current_fingers)
                self.is_active = True
                logging.debug(f"{self.name} - Gesture active, will trigger action: {self.action}")

    def process_event(self, event_type: int, event_code: int, event_value: int) -> bool:
        # Track number of active fingers
        if event_code == 57:  # ABS_MT_TRACKING_ID
            self.log_event(event_type, event_code, event_value)
            if event_value >= 0:  # Finger down
                self.current_fingers += 1
                logging.debug(f"{self.name} - Finger down: total_fingers={self.current_fingers}")
                if self.current_fingers == 1:
                    self.start_time = time.time()
                    self.start_hold_timer()
            else:  # Finger up
                self.current_fingers -= 1
                logging.debug(f"{self.name} - Finger up: total_fingers={self.current_fingers}")
                if self.current_fingers == 0:
                    hold_time = time.time() - self.start_time
                    logging.debug(f"{self.name} - All fingers lifted after {hold_time:.2f}s")
                    self.stop_hold_timer()
                    self.reset()
                    return False

        return self.is_active

    def reset(self):
        super().reset()
        self.current_fingers = 0
        self.stop_hold_timer() 