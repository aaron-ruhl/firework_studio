
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
        return [
            self.firing_time,
            self.firing_color,
            self.display_number,
            self.pattern,
            self.number_firings
        ]