
class FiringHandles:
    def __init__(self, firing_time, color, display_number, pattern="circle", number_firings=1):
        self.firing_time = firing_time
        self.firing_color = color
        self.pattern = pattern
        self.number_firings = number_firings
        self.display_number = display_number

    @classmethod
    def from_list(cls, values):
        return cls(*values)

    def to_list(self):
        # Ensure all values are JSON-serializable Python types
        firing_time = float(self.firing_time)
        
        # Convert color to tuple of ints
        if hasattr(self.firing_color, 'red'):
            # It's a QColor
            firing_color = (int(self.firing_color.red()), int(self.firing_color.green()), int(self.firing_color.blue()))
        elif isinstance(self.firing_color, (tuple, list)) and len(self.firing_color) >= 3:
            firing_color = (int(self.firing_color[0]), int(self.firing_color[1]), int(self.firing_color[2]))
        else:
            firing_color = (255, 255, 255)  # Default white
            
        display_number = int(self.display_number)
        pattern = str(self.pattern)
        number_firings = int(self.number_firings)
        
        return [
            firing_time,
            firing_color,
            display_number,
            pattern,
            number_firings
        ]