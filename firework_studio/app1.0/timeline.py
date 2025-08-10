class Timeline:
    def __init__(self):
        self.selected_region = tuple()
        self.segment_times = None
        self.duration = 0

    def set_duration(self, duration):
        self.duration = duration

    def set_selected_region(self, region):
        if region and len(region) == 2:
            start, end = region
            if start < 0:
                start = 0
            if end > self.duration:
                end = self.duration
            self.selected_region = (start, end)
        else:
            self.selected_region = region

    def reset_selected_region(self):
        if self.duration:
            self.selected_region = (0, self.duration)
        else:
            self.selected_region = tuple()

    def get_draw_region(self):
        if self.selected_region and len(self.selected_region) == 2 and self.duration:
            zoom_start, zoom_end = self.selected_region
            zoom_duration = max(zoom_end - zoom_start, 1e-9)
            return zoom_start, zoom_end, zoom_duration
        else:
            return 0, self.duration, self.duration if self.duration else 1
