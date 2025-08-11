from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QRect, Qt, QPoint
from PyQt6.QtGui import QPainter, QColor

import sounddevice as sd
import random

class FiringHandles:
    def __init__(self, firing_time, color, display_number, pattern="circle", number_firings=1):
        self.firing_time = firing_time
        self.firing_color = color
        self.pattern = pattern
        self.number_firings = number_firings
        self.display_number = display_number

    @property
    def display_number(self):
        return self._display_number

    @display_number.setter
    def display_number(self, value):
        self._display_number = value

    @property
    def firing_time(self):
        return self._firing_time

    @firing_time.setter
    def firing_time(self, value):
        self._firing_time = value

    @property
    def firing_color(self):
        return self._firing_color

    @firing_color.setter
    def firing_color(self, value):
        self._firing_color = value

    @property
    def pattern(self):
        return self._pattern

    @pattern.setter
    def pattern(self, value):
        self._pattern = value

    @property
    def number_firings(self):
        return self._number_firings

    @number_firings.setter
    def number_firings(self, value):
        self._number_firings = value

'''THIS IS THE BAR CLASS FOR ALONG THE BOTTOM TWO PLOTS'''
class FireworkPreviewWidget(QWidget):
    def __init__(self, waveform_selection_tool=None, main_window=None):
        super().__init__()
        self.setMinimumHeight(200)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.audio_data = None
        self.sr = None
        self.segment_times = None
        self.fired_times = set()
        self.firework_times = []
        self.delay = 1.8  # 1.8 seconds
        self.fireworks = []

        self.current_time = 0
        self.playhead_time = 0
        self.duration = 0
        self.resume = False
        self.audio_thread = None
        self.selected_firing = None
        self.selected_region = tuple()
        self.waveform_selection_tool = waveform_selection_tool
        self.main_window = main_window
        self.preview_timer = None

    def set_show_data(self, audio_data, sr, segment_times, firework_times, duration):
        self.audio_data = audio_data
        self.sr = sr
        self.segment_times = segment_times
        self.firework_times = firework_times
        self.duration = duration
        self.update()

    def reset_fireworks(self):
        """Reset all fireworks."""
        self.fireworks = []
        self.update()

    def reset_selected_region(self):
        """Reset the selected region to the whole duration."""
        if self.duration:
            self.selected_region = (0, self.duration)
        else:
            self.selected_region = tuple()
        self.set_show_data(self.audio_data, self.sr, self.segment_times, self.firework_times, self.duration)
        self.update()
        
    # Ensure negative times are not allowed in selected_region
    def set_selected_region(self, region):
        """Called by WaveformSelectionTool when a region is selected."""
        if region and len(region) == 2:
            start, end = region
            if start < 0:
                start = 0
            if end > self.duration:
                end = self.duration
            # Never move playhead when zooming/panning
            self.selected_region = (start, end)
        else:
            self.selected_region = region
        self.update()
   
    def add_time(self):
        # Only add a firework when explicitly called, not automatically by playhead
        if self.audio_data is None or self.sr is None:
            return
        if self.firework_times is None:
            self.firework_times = []
        elif not isinstance(self.firework_times, list):
            self.firework_times = list(self.firework_times)

        '''THIS IS WHERE HANDLES ARE CREATED '''
        firing_time = self.current_time
        # do not allow placing at very start
        if firing_time < self.delay:
            return
        color = QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

        self.firework_times.append(firing_time)
        self.firework_times.sort()
        display_number = self.firework_times.index(firing_time) + 1

        # create the handle for displaying on preview_widget
        # Store the  firing_time in the handle for consistency
        handle = FiringHandles(firing_time, color, number_firings=5, pattern="circle", display_number=display_number)
        self.fireworks.append(handle)
        self.fireworks.sort(key=lambda handle: handle.firing_time)
        self.update()

    def advance_preview(self):
            if self.audio_data is None or self.sr is None or self.duration is None:
                return
            # Advance by 16 ms (assuming timer interval is 16 ms)
            self.current_time += 0.016
            # Always clamp current_time to [0, duration]
            if self.current_time > self.duration:
                self.current_time = self.duration
            if self.current_time < 0:
                self.current_time = 0

            # MODIFIED: Only stop at the end of the full duration, not the zoomed region
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

    def remove_selected_firing(self):
        if hasattr(self, 'selected_firing') and self.selected_firing is not None:
            idx = self.selected_firing
            if self.firework_times is not None and 0 <= idx < len(self.firework_times):
                if not isinstance(self.firework_times, list):
                    self.firework_times = list(self.firework_times)
                del self.firework_times[idx]
                if self.fireworks is not None and len(self.fireworks) > idx:
                    del self.fireworks[idx]
            self.selected_firing = None
            self.update()
        return self.firework_times
    
    def start_preview(self):
        if self.audio_data is not None and self.sr is not None:
            sd.stop()
            import threading
            # Always clamp current_time to [0, duration]
            if self.current_time < 0:
                self.current_time = 0

            def play_audio():
                if self.audio_data is not None and self.current_time is not None and self.sr is not None:
                    # If a region is selected, play only that region from the correct offset
                    if self.selected_region and len(self.selected_region) == 2:
                        start, end = self.selected_region
                        # Clamp current_time to region
                        play_start = min(self.current_time, end)
                        start_idx = int(play_start * self.sr)
                        # MODIFIED: play to end of audio, not just to end of region
                        end_idx = int(self.duration * self.sr)
                        sd.play(self.audio_data[start_idx:end_idx], self.sr, blocking=False)
                    else:
                        play_start = max(0, min(self.current_time, self.duration if self.duration else 0))
                        start_idx = int((play_start) * self.sr)
                        sd.play(self.audio_data[start_idx:], self.sr, blocking=False)

            if self.audio_thread is not None and self.audio_thread.is_alive():
                self.audio_thread.join(timeout=1)
            self.audio_thread = threading.Thread(target=play_audio, daemon=True)
            self.audio_thread.start()
        if self.preview_timer:
            self.preview_timer.stop()
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.advance_preview)
        self.preview_timer.start(16)

    def toggle_play_pause(self):
        if self.preview_timer and self.preview_timer.isActive():
            try:
                # Just stop playback and timer, do not update current_time
                sd.stop(ignore_errors=True)
                self.preview_timer.stop()
            except Exception:
                pass
        else:
            # Resume from current_time
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

        grad = QColor(25, 28, 40)
        painter.fillRect(self.rect(), grad)
        # --- ZOOM LOGIC ---
        # If a region is selected, zoom in on that region
        if self.selected_region and len(self.selected_region) == 2 and self.duration:
            zoom_start, zoom_end = self.selected_region
            zoom_duration = max(zoom_end - zoom_start, 1e-9)
            draw_start = zoom_start
            draw_end = zoom_end
            def format_time(t):
                mins = int(t // 60)
                secs = int(t % 60)
                ms = int((t - int(t)) * 1000)
                return f"{mins:02d}:{secs:02d}:{ms:03d}"
            # Draw arrow and time if playhead is outside region
            gap = 1.41  # add a small gap to improve functionality
            if self.playhead_time < draw_start - gap or self.playhead_time > draw_end + gap:
                # Lower the arrow so it's not blocked by the preview timeline
                label = format_time(self.playhead_time)
                # Save current font
                orig_font = painter.font()
                label_font = painter.font()
                label_font.setBold(True)
                label_font.setPointSizeF(label_font.pointSizeF() * 1.1)
                painter.setFont(label_font)
                label_width = painter.fontMetrics().horizontalAdvance(label) + 12
                label_height = painter.fontMetrics().height() + 6
                # Place arrow at the same vertical position as the playhead timer label
                arrow_y = timeline_y - 48 + 12 + label_height // 2

                if self.playhead_time < draw_start:
                    # Draw left arrow
                    arrow_x = 10
                    points = [
                        QPoint(arrow_x + 8, arrow_y - 18),
                        QPoint(arrow_x + 8, arrow_y + 18),
                        QPoint(arrow_x, arrow_y)
                    ]
                    painter.setBrush(QColor(0, 255, 120, 180))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawPolygon(*points)
                    # Draw label to right of arrow
                    painter.setBrush(QColor(25, 28, 40, 230))
                    painter.drawRoundedRect(arrow_x + 16, arrow_y - label_height // 2, label_width, label_height, 7, 7)
                    painter.setPen(QColor(0, 255, 120))
                    painter.drawText(arrow_x + 16, arrow_y - label_height // 2, label_width, label_height, Qt.AlignmentFlag.AlignCenter, label)
                else:
                    # Draw right arrow
                    arrow_x = self.width() - 10
                    points = [
                        QPoint(arrow_x - 8, arrow_y - 18),
                        QPoint(arrow_x - 8, arrow_y + 18),
                        QPoint(arrow_x, arrow_y)
                    ]
                    painter.setBrush(QColor(0, 255, 120, 180))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawPolygon(*points)
                    # Draw label to left of arrow
                    painter.setBrush(QColor(25, 28, 40, 230))
                    painter.drawRoundedRect(arrow_x - 16 - label_width, arrow_y - label_height // 2, label_width, label_height, 7, 7)
                    painter.setPen(QColor(0, 255, 120))
                    painter.drawText(arrow_x - 16 - label_width, arrow_y - label_height // 2, label_width, label_height, Qt.AlignmentFlag.AlignCenter, label)
                # Restore original font so tick labels are not affected
                painter.setFont(orig_font)
        else:
            draw_start = 0
            draw_end = self.duration
            zoom_duration = self.duration if self.duration else 1

        bar_rect = QRect(left_margin, timeline_y - 8, usable_w, 16)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(50, 55, 70, 220))
        painter.drawRoundedRect(bar_rect, 8, 8)

        # Draw tighter, more professional ticks and labels
        painter.setPen(QColor(150, 150, 170))
        # Choose a reasonable pixel spacing for ticks (e.g., every ~60px)
        min_tick_px = 60
        tick_area = usable_w
        approx_ticks = max(2, tick_area // min_tick_px)
        # Compute a "nice" step (1, 2, 5, 10, 15, 30, 60, etc. seconds)
        def nice_step(span, target_ticks):
            raw = span / target_ticks
            for step in [1, 2, 5, 10, 15, 30, 60, 120, 300, 600, 900, 1800, 3600]:
                if raw <= step:
                    return step
            return 3600
        span = draw_end - draw_start
        step = nice_step(span, approx_ticks)
        first_tick = ((draw_start // step) + 1) * step if draw_start % step != 0 else draw_start
        t = first_tick
        label_font = painter.font()
        label_font.setPointSizeF(label_font.pointSizeF() * 0.9)
        painter.setFont(label_font)
        while t < draw_end + 1e-6:
            x = left_margin + int((t - draw_start) / zoom_duration * usable_w)
            painter.drawLine(x, timeline_y + 10, x, timeline_y + 18)
            if self.duration:
                minutes = int(t // 60)
                seconds = int(t % 60)
                label = f"{minutes}:{seconds:02d}"
                painter.setPen(QColor(200, 200, 220))
                painter.drawText(x - 12, timeline_y + 22, 24, 14, Qt.AlignmentFlag.AlignCenter, label)
                painter.setPen(QColor(150, 150, 170))
            t += step

        # Draw fireworks (handles)
        self.firing_handles = []
        # Add enough space for a self.delay amount of delay at the start
        handle_radius = 12
        if self.fireworks is not None and self.duration:
            for idx, fw in enumerate(self.fireworks):
                # Only draw if within visible region
                if draw_start <= fw.firing_time <= draw_end:
                    x = left_margin + ((fw.firing_time - draw_start) / zoom_duration) * usable_w
                    is_selected = hasattr(self, 'selected_firing') and self.selected_firing == idx
                    painter.setBrush(QColor(0, 0, 0, 120))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(int(round(x)) - handle_radius, timeline_y - handle_radius + 3, 2 * handle_radius, 2 * handle_radius)
                    painter.setBrush(fw.firing_color)
                    painter.setPen(QColor(255, 255, 0) if is_selected else QColor(220, 220, 220, 180))
                    r = int(handle_radius * (1.3 if is_selected else 1))
                    painter.drawEllipse(int(round(x)) - r, timeline_y - r, 2 * r, 2 * r)
                    painter.setPen(QColor(40, 40, 40, 180))
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    
                    # Draw firing number from FiringHandles.display_number
                    painter.setPen(QColor(255, 255, 255))
                    number_font = painter.font()
                    number_font.setBold(True)
                    number_font.setPointSizeF(label_font.pointSizeF() * 1.1)
                    painter.setFont(number_font)
                    painter.drawText(
                        int(round(x)) - handle_radius,
                        timeline_y - handle_radius + 3,
                        2 * handle_radius,
                        2 * handle_radius,
                        Qt.AlignmentFlag.AlignCenter,
                        str(fw.display_number)
                    )
                    # Store handle rect for hit-testing
                    self.firing_handles.append((QRect(int(round(x)) - handle_radius, timeline_y - handle_radius + 3, 2 * handle_radius, 2 * handle_radius), idx))
                painter.setFont(label_font)  # Restore font

        # --- PLAYHEAD DRAWING (always draw, even if outside zoom) ---
        self.playhead_time = min(max(self.current_time, 0), self.duration)
        playhead_x = left_margin + ((self.playhead_time - draw_start) / zoom_duration) * usable_w
        # Clamp playhead_x to valid integer range to avoid OverflowError
        playhead_x = max(-2_147_483_648, min(playhead_x, 2_147_483_647))
        # Allow playhead to be drawn outside the zoomed region (fade if out of bounds)
        fade = False
        if self.playhead_time < draw_start or self.playhead_time > draw_end:
            fade = True
        painter.setPen(Qt.PenStyle.NoPen)
        if fade:
            painter.setBrush(QColor(0, 0, 0, 40))
        else:
            painter.setBrush(QColor(0, 0, 0, 100))
        painter.drawRect(int(round(playhead_x)) - 2, timeline_y - 44, 4, 88)
        if fade:
            painter.setPen(QColor(0, 255, 120, 80))
        else:
            painter.setPen(QColor(0, 255, 120))
        painter.drawLine(int(round(playhead_x)), timeline_y - 40, int(round(playhead_x)), timeline_y + 40)
        if fade:
            painter.setBrush(QColor(0, 255, 120, 80))
        else:
            painter.setBrush(QColor(0, 255, 120))
        points = [
            (int(round(playhead_x)) - 8, timeline_y - 48),
            (int(round(playhead_x)) + 8, timeline_y - 48),
            (int(round(playhead_x)), timeline_y - 36)
        ]
        painter.drawPolygon(*[QPoint(*pt) for pt in points])

        # --- PROFESSIONAL TIME LABEL (mm:ss:ms) ---
        minutes = int(self.playhead_time // 60)
        seconds = int(self.playhead_time % 60)
        milliseconds = int((self.playhead_time - int(self.playhead_time)) * 1000)
        time_label = f"{minutes:02d}:{seconds:02d}:{milliseconds:03d}"

        label_font = painter.font()
        label_font.setBold(True)
        label_font.setPointSizeF(label_font.pointSizeF() * 1.15)
        painter.setFont(label_font)
        # Draw the label just below the triangle
        label_width = painter.fontMetrics().horizontalAdvance(time_label) + 12
        label_height = painter.fontMetrics().height() + 4
        label_x = int(round(playhead_x)) - label_width // 2
        label_y = timeline_y - 48 + 12  # 12px below the triangle tip
        # Draw background for readability
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(25, 28, 40, 230))
        painter.drawRoundedRect(label_x, label_y, label_width, label_height, 7, 7)
        # Draw the text
        painter.setPen(QColor(0, 255, 120) if not fade else QColor(0, 255, 120, 120))
        painter.drawText(label_x, label_y, label_width, label_height, Qt.AlignmentFlag.AlignCenter, time_label)

        painter.setPen(QColor(80, 80, 100, 180))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRect(left_margin, top_margin, usable_w, usable_h), 12, 12)
        painter.setClipping(False)
        

    def mousePressEvent(self, event):
        w = self.width()
        left_margin = 40
        right_margin = 40
        top_margin = 30
        bottom_margin = 40
        usable_w = w - left_margin - right_margin
        h = self.height()
        usable_h = h - top_margin - bottom_margin
        timeline_y = top_margin + usable_h // 2
        self.head_move = True

        # --- ZOOM LOGIC ---
        if self.selected_region and len(self.selected_region) == 2 and self.duration:
            draw_start, draw_end = self.selected_region
            zoom_duration = max(draw_end - draw_start, 1e-6)
        else:
            draw_start = 0
            draw_end = self.duration
            zoom_duration = self.duration if self.duration else 1

        # Playhead
        playhead_time = min(max(self.current_time, 0), self.duration)
        playhead_x = left_margin + usable_w * (playhead_time - draw_start) / zoom_duration if self.duration else 0
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

    def mouseMoveEvent(self, event):
        # Region selection never interferes with playback: only handle timeline/firework/playhead
        w = self.width()
        left_margin = 40
        right_margin = 40
        top_margin = 30
        bottom_margin = 40
        usable_w = w - left_margin - right_margin
        h = self.height()
        usable_h = h - top_margin - bottom_margin
        timeline_y = top_margin + usable_h // 2

        # --- ZOOM LOGIC ---
        if self.selected_region and len(self.selected_region) == 2 and self.duration:
            draw_start, draw_end = self.selected_region
            zoom_duration = max(draw_end - draw_start, 1e-6)
        else:
            draw_start = 0
            draw_end = self.duration
            zoom_duration = self.duration if self.duration else 1
        
        if hasattr(self, 'dragging_firing') and self.dragging_firing and self.selected_firing is not None:
            x = event.position().x() - getattr(self, 'drag_offset', 0)
            x = max(left_margin, min(x, w - right_margin))
            new_time = (x - left_margin) / usable_w * zoom_duration + draw_start
            new_time = max(draw_start, min(new_time, draw_end))
            if self.firework_times is not None:
                idx = self.selected_firing
                # Guard: never allow firework firing to be outside [0, duration]
                new_time = max(0, min(new_time, self.duration))
                self.firework_times[idx] = new_time
            self.update()
            return

        if hasattr(self, 'dragging_playhead') and self.dragging_playhead:
            x = event.position().x()
            x = max(left_margin, min(x, w - right_margin))
            new_time = (x - left_margin) / usable_w * zoom_duration + draw_start
            # Always clamp playhead to [0, duration]
            new_time = max(0, min(new_time, self.duration))
            if event.buttons() & Qt.MouseButton.LeftButton:
                self.current_time = new_time
            self.update()
            return

        if hasattr(self, 'firing_handles'):
            for rect, idx in self.firing_handles:
                if rect.contains(event.position().toPoint()):
                    self.setCursor(Qt.CursorShape.OpenHandCursor)
                    return
        playhead_time = min(max(self.current_time, 0), self.duration)
        playhead_x = left_margin + usable_w * (playhead_time - draw_start) / zoom_duration if self.duration else 0
        playhead_rect = QRect(int(playhead_x) - 8, timeline_y - 40, 16, 80)
        if playhead_rect.contains(event.position().toPoint()):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            return

        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        # Region selection never interferes with playback: only handle timeline/firework/playhead
        if hasattr(self, 'dragging_firing') and self.dragging_firing:
            self.dragging_firing = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
            return

        if hasattr(self, 'dragging_playhead') and self.dragging_playhead:
            w = self.width()
            left_margin = 40
            right_margin = 40
            usable_w = w - left_margin - right_margin

            if self.selected_region and len(self.selected_region) == 2 and self.duration:
                draw_start, draw_end = self.selected_region
                zoom_duration = max(draw_end - draw_start, 1e-6)
            else:
                draw_start = 0
                draw_end = self.duration
                zoom_duration = self.duration if self.duration else 1

            x = event.position().x()
            x = max(left_margin, min(x, w - right_margin))
            new_time = (x - left_margin) / usable_w * zoom_duration + draw_start
            # Always clamp playhead to [0, duration]
            new_time = max(0, min(new_time, self.duration))
            self.current_time = new_time
            self.dragging_playhead = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
            # If playback was active, pause it and update play/pause button state
            if self.preview_timer and self.preview_timer.isActive():
                try:
                    if sd.get_stream() is not None:
                        sd.stop(ignore_errors=True)
                except RuntimeError:
                    pass
                self.preview_timer.stop()
                return
            # Otherwise, just update current_time and state; playback will resume from here when play is pressed
            return

