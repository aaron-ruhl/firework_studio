from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QRect, Qt, QPoint, pyqtSignal 
from PyQt6.QtGui import QPainter, QColor
import librosa
import sounddevice as sd
import random
from matplotlib.widgets import SpanSelector

class WaveformSelectionTool:
    # Add a waveform panning/selection tool using matplotlib's SpanSelector
    def __init__(self, canvas, main_window=None):
        self.canvas = canvas
        self.ax = self.canvas.figure.axes[0]
        self.span = SpanSelector(
            self.ax,
            self.on_select,
            "horizontal",
            useblit=True,
            props=dict(alpha=0.3, facecolor="cyan"),
            interactive=True,
            drag_from_anywhere=True
        )
        self.selected_region = None
        self.main_window = main_window

    def on_select(self, xmin, xmax):
        self.selected_region = (xmin, xmax)
        # Update status bar and filter segments/firings if main_window is provided
        if self.main_window and hasattr(self.main_window, "status_bar"):
            def format_time(t):
                mins = int(t // 60)
                secs = int(t % 60)
                ms = int((t - int(t)) * 1000)
                return f"{mins:02d}:{secs:02d}:{ms:03d}"
            start = format_time(xmin)
            end = format_time(xmax)
            self.main_window.status_bar.showMessage(
                f"Selected region: {start} - {end}"
            )
            # Only update the selected region for visual feedback, do not filter or add firings
            self.main_window.preview_widget.set_selected_region((xmin, xmax))
            self.main_window.preview_widget.update()

    def clear_selection(self):
        self.selected_region = None
        self.span.visible = False
        self.canvas.draw_idle()

'''THIS IS THE BAR CLASS FOR ALONG THE BOTTOM TWO PLOTS'''
class FireworkPreviewWidget(QWidget):
    def __init__(self, waveform_selection_tool=None):
        super().__init__()
        self.setMinimumHeight(200)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.audio_data = None
        self.sr = None
        self.segment_times = None
        self.firework_firing = None
        self.preview_timer = None
        self.current_time = 0
        self.duration = 0
        self.resume = False
        self.firework_colors = []  # Always a list, never None
        self.audio_thread = None
        self.selected_firing = None
        self.selected_region = tuple()
        self.waveform_selection_tool = waveform_selection_tool
        self.delay = 1.5  # 1.5 seconds (milliseconds)

    def set_show_data(self, audio_data, sr, segment_times, firework_firing, duration):
        self.audio_data = audio_data
        self.sr = sr
        self.segment_times = segment_times
        self.firework_firing = firework_firing
        self.duration = duration
        self.update()

    def set_fireworks_colors(self, colors):
        self.firework_colors = colors

    def reset_selected_region(self):
        """Reset the selected region to the whole duration."""
        if self.duration:
            self.selected_region = (0, self.duration)
        else:
            self.selected_region = tuple()
        self.update()

    def set_selected_region(self, region):
        """Called by WaveformSelectionTool when a region is selected."""
        self.selected_region = region
        self.update()

    def start_preview(self):
        if self.audio_data is not None and self.sr is not None:
            sd.stop()
            import threading

            def play_audio():
                if self.audio_data is not None and self.current_time is not None and self.sr is not None:
                    # If a region is selected, play only that region
                    if self.selected_region and len(self.selected_region) == 2:
                        start, end = self.selected_region
                        # Clamp current_time to region
                        play_start = max(start, min(self.current_time, end))
                        start_idx = int(play_start * self.sr)
                        end_idx = int(end * self.sr)
                        sd.play(self.audio_data[start_idx:end_idx], self.sr, blocking=False)
                    else:
                        play_start = max(0, min(self.current_time, self.duration if self.duration else 0))
                        start_idx = int(play_start * self.sr)
                        sd.play(self.audio_data[start_idx:], self.sr, blocking=False)

            if self.audio_thread is not None and self.audio_thread.is_alive():
                self.audio_thread.join(timeout=1)
            self.audio_thread = threading.Thread(target=play_audio, daemon=True)
            self.audio_thread.start()
        if self.preview_timer:
            self.preview_timer.stop()
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.advance_preview)
        self.preview_timer.start(50)

    def toggle_play_pause(self):
        if self.preview_timer and self.preview_timer.isActive():
            self.preview_timer.stop()
            try:
                sd.stop(ignore_errors=True)
            except Exception:
                pass
        else:
            # Do not reset current_time; just resume from where it left off
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

    def add_time(self):
        if self.audio_data is None or self.sr is None:
            return
        if self.firework_firing is None:
            self.firework_firing = []
        elif not isinstance(self.firework_firing, list):
            self.firework_firing = list(self.firework_firing)
        if not hasattr(self, 'firework_colors') or len(self.firework_colors) != len(self.firework_firing) - 1:
            self.firework_colors = [
                QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                for _ in self.firework_firing[:-1]
            ]
        # Prevent adding a firing if it would be before the start of the show (after applying delay)
        firing_time = self.current_time - self.delay
        if firing_time < 0:
            # Optionally, you could show a warning or just do nothing
            return 
        self.firework_colors.append(
            QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        )
        self.firework_firing.append(self.current_time-self.delay)
        return self.firework_firing

    def advance_preview(self):
        if self.audio_data is None or self.sr is None or self.duration == 0:
            return
        # If a region is selected, only advance within that region
        if self.selected_region and len(self.selected_region) == 2:
            region_start, region_end = self.selected_region
            self.current_time += 0.05
            if self.current_time > region_end:
                self.current_time = region_end
                if self.preview_timer:
                    self.preview_timer.stop()
                try:
                    if sd.get_stream() is not None:
                        sd.stop(ignore_errors=True)
                except RuntimeError:
                    pass
        else:
            self.current_time += 0.05
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

        grad = QColor(25, 28, 40)
        painter.fillRect(self.rect(), grad)

        # --- ZOOM LOGIC ---
        # If a region is selected, zoom in on that region
        if self.selected_region and len(self.selected_region) == 2 and self.duration:
            zoom_start, zoom_end = self.selected_region
            zoom_duration = max(zoom_end - zoom_start, 1e-6)
            draw_start = zoom_start
            draw_end = zoom_end
        else:
            draw_start = 0
            draw_end = self.duration
            zoom_duration = self.duration if self.duration else 1

        bar_rect = QRect(left_margin, timeline_y - 8, usable_w, 16)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(50, 55, 70, 220))
        painter.drawRoundedRect(bar_rect, 8, 8)

        painter.setPen(QColor(120, 120, 140))
        tick_count = 10
        for i in range(tick_count + 1):
            # Map ticks to zoomed region
            t = draw_start + (draw_end - draw_start) * i / tick_count
            x = left_margin + int((t - draw_start) / zoom_duration * usable_w)
            painter.drawLine(x, timeline_y + 12, x, timeline_y + 22)
            if self.duration:
                minutes = int(t // 60)
                seconds = int(t % 60)
                label = f"{minutes:02d}:{seconds:02d}"
                painter.setPen(QColor(180, 180, 200))
                painter.drawText(x - 15, timeline_y + 38, 30, 16, Qt.AlignmentFlag.AlignCenter, label)
                painter.setPen(QColor(120, 120, 140))
        # Only draw fireworks within zoomed region
        self.firing_handles = []
        handle_radius = 12
        if self.firework_firing is not None and self.duration:
            # Ensure firework_colors is always a list
            if self.firework_colors is None:
                self.firework_colors = []
            # Filter firings and colors to only those in the zoomed region
            filtered_firings = []
            filtered_colors = []
            filtered_indices = []
            for idx, ft in enumerate(self.firework_firing):
                if draw_start <= ft <= draw_end:
                    filtered_firings.append(ft)
                    # Make sure firework_colors is in sync
                    if self.firework_colors and len(self.firework_colors) > idx:
                        filtered_colors.append(self.firework_colors[idx])
                    else:
                        filtered_colors.append(QColor(255, 255, 255))
                    filtered_indices.append(idx)
            # Draw only filtered firings
            for i, (ft, color, orig_idx) in enumerate(zip(filtered_firings, filtered_colors, filtered_indices)):
                x = left_margin + usable_w * (ft - draw_start) / zoom_duration
                is_selected = hasattr(self, 'selected_firing') and self.selected_firing == orig_idx
                painter.setBrush(QColor(0, 0, 0, 120))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(int(x) - handle_radius, timeline_y - handle_radius + 3, 2 * handle_radius, 2 * handle_radius)
                painter.setBrush(color)
                painter.setPen(QColor(255, 255, 0) if is_selected else QColor(220, 220, 220, 180))
                r = int(handle_radius * (1.3 if is_selected else 1))
                painter.drawEllipse(int(x) - r, timeline_y - r, 2 * r, 2 * r)
                painter.setPen(QColor(40, 40, 40, 180))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(int(x) - r, timeline_y - r, 2 * r, 2 * r)
                painter.setPen(QColor(30, 30, 30))
                painter.setFont(painter.font())
                painter.drawText(int(x) - r, timeline_y - r, 2 * r, 2 * r, Qt.AlignmentFlag.AlignCenter, str(orig_idx + 1))
                self.firing_handles.append((QRect(int(x) - r, timeline_y - r, 2 * r, 2 * r), orig_idx))

        # Draw playhead
        if self.duration and self.duration > 0:
            # Clamp playhead to zoomed region
            playhead_time = min(max(self.current_time, draw_start), draw_end)
            playhead_x = left_margin + usable_w * (playhead_time - draw_start) / zoom_duration
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 100))
            painter.drawRect(int(playhead_x) - 2, timeline_y - 44, 4, 88)
            painter.setPen(QColor(0, 255, 120))
            painter.drawLine(int(playhead_x), timeline_y - 40, int(playhead_x), timeline_y + 40)
            painter.setBrush(QColor(0, 255, 120))
            points = [
                (int(playhead_x) - 8, timeline_y - 48),
                (int(playhead_x) + 8, timeline_y - 48),
                (int(playhead_x), timeline_y - 36)
            ]
            painter.drawPolygon(*[QPoint(*pt) for pt in points])

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

        # --- ZOOM LOGIC ---
        if self.selected_region and len(self.selected_region) == 2 and self.duration:
            draw_start, draw_end = self.selected_region
            zoom_duration = max(draw_end - draw_start, 1e-6)
        else:
            draw_start = 0
            draw_end = self.duration
            zoom_duration = self.duration if self.duration else 1

        # Playhead
        playhead_time = min(max(self.current_time, draw_start), draw_end)
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
            if self.firework_firing is not None:
                idx = self.selected_firing
                self.firework_firing[idx] = new_time
            self.update()
            return

        if hasattr(self, 'dragging_playhead') and self.dragging_playhead:
            self.stop_preview()
            x = event.position().x()
            x = max(left_margin, min(x, w - right_margin))
            new_time = (x - left_margin) / usable_w * zoom_duration + draw_start
            new_time = max(draw_start, min(new_time, draw_end))
            self.current_time = new_time
            self.update()
            return

        if hasattr(self, 'firing_handles'):
            for rect, idx in self.firing_handles:
                if rect.contains(event.position().toPoint()):
                    self.setCursor(Qt.CursorShape.OpenHandCursor)
                    return
        playhead_time = min(max(self.current_time, draw_start), draw_end)
        playhead_x = left_margin + usable_w * (playhead_time - draw_start) / zoom_duration if self.duration else 0
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

        # If using a waveform selection tool, update selected region on mouse release
        if self.waveform_selection_tool and self.waveform_selection_tool.selected_region:
            self.set_selected_region(self.waveform_selection_tool.selected_region)
            self.update()

    def remove_selected_firing(self):
        if hasattr(self, 'selected_firing') and self.selected_firing is not None:
            idx = self.selected_firing
            if self.firework_firing is not None and 0 <= idx < len(self.firework_firing):
                if not isinstance(self.firework_firing, list):
                    self.firework_firing = list(self.firework_firing)
                del self.firework_firing[idx]
                if hasattr(self, 'firework_colors') and len(self.firework_colors) > idx:
                    del self.firework_colors[idx]
            self.selected_firing = None
            self.update()
        return self.firework_firing
