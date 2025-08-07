from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QRect, Qt, QPoint, pyqtSignal 
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
        if self.preview_timer:
            self.preview_timer.stop()
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.advance_preview)
        self.preview_timer.start(50)  # 20 FPS

    def toggle_play_pause(self):
        if self.preview_timer and self.preview_timer.isActive():
            # Pause: stop timer and audio playback
            self.preview_timer.stop()
            try:
                sd.stop(ignore_errors=True)
            except Exception:
                pass
        else:
            # Resume: start playback from current_time
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

    def add_time(self):
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
        return self.firework_firing
    
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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        left_margin = 40
        right_margin = 40
        top_margin = 30
        bottom_margin = 40
        usable_w = w - left_margin - right_margin
        usable_h = h - top_margin - bottom_margin
        timeline_y = top_margin + usable_h // 2

        # Background gradient
        grad = QColor(25, 28, 40)
        painter.fillRect(self.rect(), grad)

        # Draw timeline bar with shadow
        bar_rect = QRect(left_margin, timeline_y - 8, usable_w, 16)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(50, 55, 70, 220))
        painter.drawRoundedRect(bar_rect, 8, 8)

        # Draw ticks and time labels in mm:ss format
        painter.setPen(QColor(120, 120, 140))
        tick_count = 10
        for i in range(tick_count + 1):
            x = left_margin + int(i * usable_w / tick_count)
            painter.drawLine(x, timeline_y + 12, x, timeline_y + 22)
            if self.duration:
                t = self.duration * i / tick_count
                minutes = int(t // 60)
                seconds = int(t % 60)
                label = f"{minutes:02d}:{seconds:02d}"
                painter.setPen(QColor(180, 180, 200))
                painter.drawText(x - 15, timeline_y + 38, 30, 16, Qt.AlignmentFlag.AlignCenter, label)
                painter.setPen(QColor(120, 120, 140))

        # Draw segments
        if self.segment_times is not None and self.duration:
            for t in self.segment_times:
                x = left_margin + usable_w * t / self.duration
                painter.setPen(QColor(255, 180, 60, 180))
                painter.drawLine(int(x), timeline_y - 28, int(x), timeline_y + 28)

        # Draw firework firings as handles (highlight one if selected)
        self.firing_handles = []
        handle_radius = 12
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
                # Draw shadow
                painter.setBrush(QColor(0, 0, 0, 120))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(int(x) - handle_radius, timeline_y - handle_radius + 3, 2 * handle_radius, 2 * handle_radius)
                # Draw handle
                painter.setBrush(color)
                painter.setPen(QColor(255, 255, 0) if is_selected else QColor(220, 220, 220, 180))
                r = int(handle_radius * (1.3 if is_selected else 1))
                painter.drawEllipse(int(x) - r, timeline_y - r, 2 * r, 2 * r)
                # Draw border
                painter.setPen(QColor(40, 40, 40, 180))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(int(x) - r, timeline_y - r, 2 * r, 2 * r)
                # Draw index number
                painter.setPen(QColor(30, 30, 30))
                painter.setFont(painter.font())
                painter.drawText(int(x) - r, timeline_y - r, 2 * r, 2 * r, Qt.AlignmentFlag.AlignCenter, str(idx + 1))
                self.firing_handles.append((QRect(int(x) - r, timeline_y - r, 2 * r, 2 * r), idx))

        # Draw playhead
        if self.duration and self.duration > 0:
            playhead_x = left_margin + usable_w * self.current_time / self.duration
            # Playhead shadow
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 100))
            painter.drawRect(int(playhead_x) - 2, timeline_y - 44, 4, 88)
            # Playhead line
            painter.setPen(QColor(0, 255, 120))
            painter.drawLine(int(playhead_x), timeline_y - 40, int(playhead_x), timeline_y + 40)
            # Playhead triangle
            painter.setBrush(QColor(0, 255, 120))
            points = [
                (int(playhead_x) - 8, timeline_y - 48),
                (int(playhead_x) + 8, timeline_y - 48),
                (int(playhead_x), timeline_y - 36)
            ]
            painter.drawPolygon(*[QPoint(*pt) for pt in points])

        # Draw border
        painter.setPen(QColor(80, 80, 100, 180))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRect(left_margin, top_margin, usable_w, usable_h), 12, 12)

    def mousePressEvent(self, event):
        # Use the same margins and timeline_y as in paintEvent for consistency
        w = self.width()
        left_margin = 40
        right_margin = 40
        top_margin = 30
        bottom_margin = 40
        usable_w = w - left_margin - right_margin
        h = self.height()
        usable_h = h - top_margin - bottom_margin
        timeline_y = top_margin + usable_h // 2
        playhead_x = left_margin + usable_w * self.current_time / self.duration if self.duration else 0
        playhead_rect = QRect(int(playhead_x) - 8, timeline_y - 40, 16, 80)
        if playhead_rect.contains(event.position().toPoint()):
            self.dragging_playhead = True
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            return
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
        w = self.width()
        left_margin = 40
        right_margin = 40
        top_margin = 30
        bottom_margin = 40
        usable_w = w - left_margin - right_margin
        h = self.height()
        usable_h = h - top_margin - bottom_margin
        timeline_y = top_margin + usable_h // 2

        # Handle dragging of firing handles
        if hasattr(self, 'dragging_firing') and self.dragging_firing and self.selected_firing is not None:
            x = event.position().x() - getattr(self, 'drag_offset', 0)
            x = max(left_margin, min(x, w - right_margin))
            new_time = (x - left_margin) / usable_w * self.duration
            new_time = max(0, min(new_time, self.duration))
            if self.firework_firing is not None:
                idx = self.selected_firing
                self.firework_firing[idx] = new_time
            self.update()
            return

        # Handle dragging of playhead
        if hasattr(self, 'dragging_playhead') and self.dragging_playhead:
            self.stop_preview()
            x = event.position().x()
            x = max(left_margin, min(x, w - right_margin))
            new_time = (x - left_margin) / usable_w * self.duration
            new_time = max(0, min(new_time, self.duration))
            self.current_time = new_time
            self.update()
            return

        # Change cursor if hovering over a handle or playhead
        if hasattr(self, 'firing_handles'):
            for rect, idx in self.firing_handles:
                if rect.contains(event.position().toPoint()):
                    self.setCursor(Qt.CursorShape.OpenHandCursor)
                    return
        # Check if hovering over playhead
        playhead_x = left_margin + usable_w * self.current_time / self.duration if self.duration else 0
        playhead_rect = QRect(int(playhead_x) - 8, timeline_y - 40, 16, 80)
        if playhead_rect.contains(event.position().toPoint()):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            return

        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        if hasattr(self, 'dragging_firing') and self.dragging_firing:
            self.dragging_firing = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
            return

        if hasattr(self, 'dragging_playhead') and self.dragging_playhead:
            self.dragging_playhead = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
            return

    
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
        return self.firework_firing
