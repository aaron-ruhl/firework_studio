import random
from PyQt6.QtGui import QColor

class FiringHandles:
    def __init__(self, firing_time, color, display_number, pattern="circle", number_firings=1):
        self.firing_time = firing_time
        self.handle_color = color
        self.pattern = pattern
        self.number_firings = number_firings
        self.display_number = display_number

        # Choose a random explosion color from a set of vibrant colors
        color_choices = [
            (0.0, 0.5, 1.0),   # blue
            (0.0, 1.0, 0.0),   # green
            (1.0, 0.0, 0.0),   # red
            (1.0, 1.0, 0.0),   # yellow
            (1.0, 0.5, 0.0),   # orange
            (0.5, 0.0, 1.0),   # purple
            (1.0, 0.0, 1.0),   # magenta
            (0.0, 1.0, 1.0),   # cyan
        ]
        chosen = random.choice(color_choices)
        self.explosion_color = QColor.fromRgbF(*chosen)

    @classmethod
    def from_list(cls, values):
        return cls(*values)

    def to_list(self):
        # Ensure all values are JSON-serializable Python types
        firing_time = float(self.firing_time)
        
        # Convert color to tuple of ints
        if hasattr(self.handle_color, 'red'):
            # It's a QColor
            handle_color = (int(self.handle_color.red()), int(self.handle_color.green()), int(self.handle_color.blue()))
        elif isinstance(self.handle_color, (tuple, list)) and len(self.handle_color) >= 3:
            handle_color = (int(self.handle_color[0]), int(self.handle_color[1]), int(self.handle_color[2]))
        else:
            handle_color = (255, 255, 255)  # Default white
            
        display_number = int(self.display_number)
        pattern = str(self.pattern)
        number_firings = int(self.number_firings)
        
        return [
            firing_time,
            handle_color,
            display_number,
            pattern,
            number_firings
        ]