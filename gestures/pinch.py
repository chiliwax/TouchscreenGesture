from .base import Gesture
import math

class PinchGesture(Gesture):
    def __init__(self, config):
        super().__init__(config)
        self.initial_distance = 0
        self.current_distance = 0
        self.threshold = config.get('threshold', 50)  # Minimum distance change to trigger pinch

    def calculate_distance(self, point1: dict, point2: dict) -> float:
        """Calculate distance between two touch points"""
        distance = math.sqrt(
            (point1['x'] - point2['x']) ** 2 +
            (point1['y'] - point2['y']) ** 2
        )
        return distance

    def process_event(self, event_type: int, event_code: int, event_value: int) -> bool:
        # Update touch point coordinates
        if event_type == 3:  # EV_ABS
            if event_code == 53:  # ABS_MT_POSITION_X
                self.update_touch_point(0, event_value, self.get_touch_point(0)['y'], 0)
            elif event_code == 54:  # ABS_MT_POSITION_Y
                self.update_touch_point(0, self.get_touch_point(0)['x'], event_value, 0)
            elif event_code == 57:  # ABS_MT_TRACKING_ID
                self.log_event(event_type, event_code, event_value)
                if event_value >= 0:
                    if not self.is_active:
                        self.initial_distance = 0
                        self.current_distance = 0
                else:
                    self.reset()
                    return False

        # Calculate distance between touch points
        active_points = [p for p in self.touch_points if p['tracking_id'] >= 0]
        if len(active_points) == 2:
            self.current_distance = self.calculate_distance(active_points[0], active_points[1])
            if self.initial_distance == 0:
                self.initial_distance = self.current_distance
            else:
                distance_change = abs(self.current_distance - self.initial_distance)
                if distance_change > self.threshold:
                    self.log_detection(distance_change=f"{distance_change:.2f}", threshold=self.threshold)
                    self.is_active = True
                    # Trigger the gesture immediately via callback
                    self.trigger_gesture()
                    return True

        return False

    def reset(self):
        super().reset()
        self.initial_distance = 0
        self.current_distance = 0 