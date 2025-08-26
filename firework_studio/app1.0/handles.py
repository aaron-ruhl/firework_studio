import random
from PyQt6.QtGui import QColor

class FiringHandles:
    def __init__(self, firing_time, color, display_number, pattern="circle", number_firings=1, pattern_list=None, explosion_color_list=None):
        self.firing_time = firing_time
        self.handle_color = color
        self.pattern = pattern
        self.number_firings = number_firings
        self.display_number = display_number
        # If pattern_list is provided, use it; otherwise create from pattern
        if pattern_list is not None:
            self.pattern_list = pattern_list
        else:
            self.pattern_list = [pattern]*number_firings

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
        
        # If explosion_color_list is provided, use it; otherwise create from random colors
        if explosion_color_list is not None:
            self.explosion_color_list = explosion_color_list
            # Set explosion_color to the first color for backward compatibility
            if explosion_color_list:
                self.explosion_color = explosion_color_list[0] if isinstance(explosion_color_list[0], QColor) else QColor(*explosion_color_list[0])
            else:
                chosen = random.choice(color_choices)
                self.explosion_color = QColor.fromRgbF(*chosen)
        else:
            # Create explosion_color_list with random colors for each shot
            self.explosion_color_list = []
            for _ in range(number_firings):
                chosen = random.choice(color_choices)
                qcolor = QColor.fromRgbF(*chosen)
                self.explosion_color_list.append(qcolor)
            # Set explosion_color to the first color for backward compatibility
            self.explosion_color = self.explosion_color_list[0] if self.explosion_color_list else QColor.fromRgbF(*random.choice(color_choices))

    def update_pattern_list_size(self):
        """Update pattern_list and explosion_color_list to match number_firings, preserving existing patterns/colors where possible"""
        current_length = len(self.pattern_list)
        if self.number_firings > current_length:
            # Add more patterns, using the last pattern or default pattern
            last_pattern = self.pattern_list[-1] if self.pattern_list else self.pattern
            self.pattern_list.extend([last_pattern] * (self.number_firings - current_length))
        elif self.number_firings < current_length:
            # Trim the list
            self.pattern_list = self.pattern_list[:self.number_firings]
        
        # Update explosion_color_list similarly
        current_color_length = len(self.explosion_color_list) if hasattr(self, 'explosion_color_list') and self.explosion_color_list else 0
        if not hasattr(self, 'explosion_color_list') or not self.explosion_color_list:
            # Initialize explosion_color_list if it doesn't exist
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
            self.explosion_color_list = []
            for _ in range(self.number_firings):
                chosen = random.choice(color_choices)
                qcolor = QColor.fromRgbF(*chosen)
                self.explosion_color_list.append(qcolor)
        elif self.number_firings > current_color_length:
            # Add more colors, using the last color or a random color
            if self.explosion_color_list:
                last_color = self.explosion_color_list[-1]
            else:
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
                last_color = QColor.fromRgbF(*chosen)
            self.explosion_color_list.extend([QColor(last_color)] * (self.number_firings - current_color_length))
        elif self.number_firings < current_color_length:
            # Trim the color list
            self.explosion_color_list = self.explosion_color_list[:self.number_firings]
        
        # Update the main explosion_color for backward compatibility
        if self.explosion_color_list:
            self.explosion_color = self.explosion_color_list[0]

    @classmethod
    def from_list(cls, values):
        # Handle multiple formats: old format (5 values), medium format (6 values with pattern_list), new format (7 values with explosion_color_list)
        if len(values) >= 7:
            firing_time, color, display_number, pattern, number_firings, pattern_list, explosion_color_list = values[:7]
            # Convert explosion_color_list back to QColor objects if needed
            if explosion_color_list and isinstance(explosion_color_list[0], (tuple, list)):
                explosion_color_list = [QColor(*c) if len(c) >= 3 else QColor(255, 255, 255) for c in explosion_color_list]
            return cls(firing_time, color, display_number, pattern, number_firings, pattern_list, explosion_color_list)
        elif len(values) >= 6:
            firing_time, color, display_number, pattern, number_firings, pattern_list = values[:6]
            return cls(firing_time, color, display_number, pattern, number_firings, pattern_list)
        else:
            # Old format, create pattern_list from pattern
            firing_time, color, display_number, pattern, number_firings = values[:5]
            return cls(firing_time, color, display_number, pattern, number_firings)

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
        pattern_list = [str(p) for p in self.pattern_list]  # Ensure all patterns are strings
        
        # Convert explosion_color_list to tuples for serialization
        explosion_color_list = []
        if hasattr(self, 'explosion_color_list') and self.explosion_color_list:
            for color in self.explosion_color_list:
                if hasattr(color, 'red'):
                    # It's a QColor
                    explosion_color_list.append((int(color.red()), int(color.green()), int(color.blue())))
                elif isinstance(color, (tuple, list)) and len(color) >= 3:
                    explosion_color_list.append((int(color[0]), int(color[1]), int(color[2])))
                else:
                    explosion_color_list.append((255, 255, 255))  # Default white
        
        return [
            firing_time,
            handle_color,
            display_number,
            pattern,
            number_firings,
            pattern_list,
            explosion_color_list
        ]