from abc import ABC, abstractmethod
from typing import Dict, Any, List
import time

class Gesture(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.action = config.get('action')
        self.touch_points: List[Dict[str, float]] = []
        self.start_time = 0
        self.is_active = False

    @abstractmethod
    def process_event(self, event_type: int, event_code: int, event_value: int) -> bool:
        """
        Process an input event and return True if the gesture is recognized
        """
        pass

    def reset(self):
        """Reset the gesture state"""
        self.touch_points = []
        self.start_time = 0
        self.is_active = False

    def get_touch_point(self, slot: int) -> Dict[str, float]:
        """Get or create a touch point for the given slot"""
        while len(self.touch_points) <= slot:
            self.touch_points.append({'x': 0, 'y': 0, 'tracking_id': -1})
        return self.touch_points[slot]

    def update_touch_point(self, slot: int, x: float, y: float, tracking_id: int):
        """Update touch point coordinates and tracking ID"""
        point = self.get_touch_point(slot)
        point['x'] = x
        point['y'] = y
        point['tracking_id'] = tracking_id

    def remove_touch_point(self, tracking_id: int):
        """Remove a touch point by its tracking ID"""
        for point in self.touch_points:
            if point['tracking_id'] == tracking_id:
                point['tracking_id'] = -1
                break 