from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QRect, Qt
from PyQt6.QtGui import QPainter, QColor
import librosa
import sounddevice as sd
import random

'''THIS IS THE BAR CLASS FOR ALONG THE BOTTOM TWO PLOTS'''
class FireworkPreviewWidget(QWidget):
    def set_zoom_region(self, start_time, end_time):
        """
        Set the visible region (in seconds) for the timeline.
        Only firework firings and segments within this region will be shown.
        """
        self.zoom_start = start_time
        self.zoom_end = end_time
        self.update()

    def clear_zoom(self):
        """
        Reset to show the full duration.
        """
        self.zoom_start = None
        self.zoom_end = None
        self.update()
    
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(200)
        self.setMouseTracking(True)  # Enable mouse tracking for interactivity
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)  # Enable hover events
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)  # Ensure widget receives mouse events
        self.audio_data = None
        self.sr = None
        self.segment_times = None
        self.firework_firing = None
        self.preview_timer = None
        self.current_time = 0
        self.duration = 0
        self.resume=False
        self.firework_colors = []
        self.audio_thread = None

    def set_show_data(self, audio_data, sr, segment_times, firework_firing, duration):
        self.audio_data = audio_data
        self.sr = sr
        self.segment_times = segment_times
        self.firework_firing = firework_firing
        self.duration = duration
        self.update()
        
    def start_preview(self):
        if self.audio_data is not None and self.sr is not None:
            sd.stop()
            # Start playback from current_time, not from 0
            import threading
            def play_audio():
                if self.audio_data is not None and self.current_time is not None and self.sr is not None:
                    sd.play(self.audio_data[int(self.current_time * self.sr):], self.sr, blocking=False)
            if self.audio_thread is not None and self.audio_thread.is_alive():
                # Wait for previous thread to finish
                self.audio_thread.join(timeout=1)
            self.audio_thread = threading.Thread(target=play_audio, daemon=True)
            self.audio_thread.start()
        # Only reset current_time if starting from the beginning
        if not self.resume:
            self.current_time = 0
        self.resume = False
        if self.preview_timer:
            self.preview_timer.stop()
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.advance_preview)
        self.preview_timer.start(50)  # 20 FPS

    def toggle_play_pause(self):
        if self.preview_timer and self.preview_timer.isActive():
            self.preview_timer.stop()
            try:
                if sd.get_stream() is not None:
                    sd.stop(ignore_errors=True)
            except RuntimeError:
                pass
            self.resume = True
        else:
            self.start_preview()

    def stop_preview(self):
        if self.audio_data is None or self.sr is None:
            return
        if self.preview_timer and self.preview_timer.isActive():
            self.preview_timer.stop()
        self.current_time = 0
        try:
            if sd.get_stream() is not None:
                sd.stop(ignore_errors=True)
        except RuntimeError:
            pass
        if self.audio_thread is not None and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1)
            self.audio_thread = None
        self.update()
        if self.audio_data is None or self.sr is None:
            return
        if self.preview_timer and self.preview_timer.isActive():
            self.preview_timer.stop()
        self.current_time = 0
        try:
            if sd.get_stream() is not None:
                sd.stop(ignore_errors=True)
        except RuntimeError:
            pass
        self.update()

    def add_time(self, seconds):
        if self.audio_data is None or self.sr is None:
            return
        if self.firework_firing is None:
            self.firework_firing = []
        elif not isinstance(self.firework_firing, list):
            self.firework_firing = list(self.firework_firing)
        self.firework_firing.append(self.current_time)
        # Add a new color for the new firing, keep existing colors
        if not hasattr(self, 'firework_colors') or len(self.firework_colors) != len(self.firework_firing) - 1:
            self.firework_colors = [
                QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                for _ in self.firework_firing[:-1]
            ]
        self.firework_colors.append(
            QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        )
    def advance_preview(self):
        if self.audio_data is None or self.sr is None or self.duration == 0:
            return
        self.current_time += 0.05  # 50 ms per timer tick
        if self.current_time >= self.duration:
            self.current_time = self.duration
            if self.preview_timer:
                self.preview_timer.stop()
            try:
                if sd.get_stream() is not None:
                    sd.stop(ignore_errors=True)
            except RuntimeError:
                pass
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(30, 30, 40))

        w, h = self.width(), self.height()
        left_margin = 0
        right_margin = 0
        usable_w = w - left_margin - right_margin
        usable_h = 150
        timeline_y = usable_h // 2
        painter.setPen(QColor(200, 200, 200))
        painter.drawLine(left_margin, timeline_y, w - right_margin, timeline_y)
        painter.setWindow(QRect(0, 0, w, usable_h))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw segments
        if self.segment_times is not None and self.duration:
            for t in self.segment_times:
                x = left_margin + usable_w * t / self.duration
                painter.setPen(QColor(255, 165, 0))
                painter.drawLine(int(x), timeline_y - 100, int(x), timeline_y + 100)

        # Draw firework firings as handles (highlight one if selected)
        self.firing_handles = []  # Store handle rects for hit-testing
        handle_radius = 10
        if self.firework_firing is not None and self.duration:
            if not hasattr(self, 'firework_colors') or len(self.firework_colors) != len(self.firework_firing):
                self.firework_colors = [
                    QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                    for _ in self.firework_firing
                ]
            for idx, ft in enumerate(self.firework_firing):
                x = left_margin + usable_w * ft / self.duration
                color = self.firework_colors[idx]
                is_selected = hasattr(self, 'selected_firing') and self.selected_firing == idx
                painter.setBrush(color)
                painter.setPen(QColor(255, 255, 0) if is_selected else color)
                r = int(handle_radius * (1.5 if is_selected else 1))
                painter.drawEllipse(int(x) - r, timeline_y - r, 2 * r, 2 * r)
                self.firing_handles.append((QRect(int(x) - r, timeline_y - r, 2 * r, 2 * r), idx))

        # Draw playhead
        if self.duration and self.duration > 0:
            playhead_x = left_margin + usable_w * self.current_time / self.duration
            painter.setPen(QColor(0, 255, 0))
            painter.drawLine(int(playhead_x), timeline_y - 40, int(playhead_x), timeline_y + 40)

    def mousePressEvent(self, event):
        # Only highlight the firing handle if clicked
        if not hasattr(self, 'firing_handles'):
            return
        self.selected_firing = None
        self.dragging_firing = False
        for rect, idx in self.firing_handles:
            if rect.contains(event.position().toPoint()):
                self.selected_firing = idx
                self.dragging_firing = True
                self.drag_offset = event.position().x() - rect.center().x()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.update()
                return
        self.update()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'dragging_firing') and self.dragging_firing and self.selected_firing is not None:
            # Move the selected firing handle
            w = self.width()
            left_margin = 0
            right_margin = 0
            usable_w = w - left_margin - right_margin
            x = event.position().x() - getattr(self, 'drag_offset', 0)
            # Clamp x to timeline
            x = max(left_margin, min(x, w - right_margin))
            # Convert x back to time
            new_time = (x - left_margin) / usable_w * self.duration
            # Clamp to [0, duration]
            new_time = max(0, min(new_time, self.duration))
            # Allow overlap with neighbors
            if self.firework_firing is not None:
                idx = self.selected_firing
                self.firework_firing[idx] = new_time
            self.update()
        else:
            # Change cursor if hovering over a handle
            if hasattr(self, 'firing_handles'):
                for rect, idx in self.firing_handles:
                    if rect.contains(event.position().toPoint()):
                        self.setCursor(Qt.CursorShape.OpenHandCursor)
                        return
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'dragging_firing') and self.dragging_firing:
            self.dragging_firing = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()

    
    def remove_selected_firing(self):
        if hasattr(self, 'selected_firing') and self.selected_firing is not None:
            idx = self.selected_firing
            if self.firework_firing is not None and 0 <= idx < len(self.firework_firing):
                # Ensure firework_firing is a list before deletion
                if not isinstance(self.firework_firing, list):
                    self.firework_firing = list(self.firework_firing)
                del self.firework_firing[idx]
                if hasattr(self, 'firework_colors') and len(self.firework_colors) > idx:
                    del self.firework_colors[idx]
            self.selected_firing = None
            self.update()
