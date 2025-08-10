class Playhead:
    def __init__(self, duration=0):
        self.current_time = 0
        self.duration = duration

    def set_duration(self, duration):
        self.duration = duration

    def set_time(self, time):
        self.current_time = max(0, min(time, self.duration))

    def advance(self, dt):
        self.current_time = min(self.current_time + dt, self.duration)

    def reset(self):
        self.current_time = 0

    def clamp(self):
        self.current_time = max(0, min(self.current_time, self.duration))
