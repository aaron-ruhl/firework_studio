import random
from PyQt6.QtGui import QColor
from PyQt6.QtCore import QRect



class FiringHandles:
    def __init__(self):
        self.firework_firing = []
        self.firework_colors = []
        self.selected_firing = None
        self.firing_handles = []

    def set_firings(self, firings, colors=None):
        self.firework_firing = list(firings) if firings is not None else []
        if colors is not None:
            self.firework_colors = list(colors)
        else:
            self.firework_colors = [
                QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                for _ in self.firework_firing
            ]

    def add_firing(self, firing_time):
        self.firework_firing.append(firing_time)
        self.firework_colors.append(
            QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        )

    def remove_selected_firing(self):
        idx = self.selected_firing
        if idx is not None and 0 <= idx < len(self.firework_firing):
            del self.firework_firing[idx]
            if len(self.firework_colors) > idx:
                del self.firework_colors[idx]
        self.selected_firing = None

    def update_handle_rects(self, draw_start, draw_end, zoom_duration, usable_w, left_margin, timeline_y, handle_radius, duration):
        self.firing_handles = []
        filtered_firings = []
        filtered_colors = []
        filtered_indices = []
        for idx, ft in enumerate(self.firework_firing):
            if draw_start <= ft <= draw_end:
                filtered_firings.append(ft)
                if self.firework_colors and len(self.firework_colors) > idx:
                    filtered_colors.append(self.firework_colors[idx])
                else:
                    filtered_colors.append(QColor(255, 255, 255))
                filtered_indices.append(idx)
        for i, (ft, color, orig_idx) in enumerate(zip(filtered_firings, filtered_colors, filtered_indices)):
            x = left_margin + ((ft - draw_start) / zoom_duration) * usable_w
            self.firing_handles.append((
                QRect(int(round(x)) - handle_radius, timeline_y - handle_radius + 3, 2 * handle_radius, 2 * handle_radius),
                orig_idx
            ))
