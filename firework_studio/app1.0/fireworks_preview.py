from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QRect, Qt, QPoint, pyqtSignal 
from PyQt6.QtGui import QPainter, QColor

'''THIS IS THE BAR CLASS FOR ALONG THE BOTTOM TWO PLOTS'''
import random
import sounddevice as sd

from playhead import Playhead
from handles import FiringHandles
from timeline import Timeline

class FireworkPreviewWidget(QWidget):
    def __init__(self, waveform_selection_tool=None, main_window=None):
        super().__init__()
        self.setMinimumHeight(200)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.audio_data = None
        self.sr = None
        self.preview_timer = None
        self.resume = False
        self.audio_thread = None
        self.waveform_selection_tool = waveform_selection_tool
        self.delay = 1.8  # 1.8 seconds
        self.fired_times = set()
        self.main_window = main_window

        self.playhead = Playhead()
        self.firing_handles = FiringHandles()
        self.timeline = Timeline()

    def set_show_data(self, audio_data, sr, segment_times, firework_firing, duration):
        self.audio_data = audio_data
        self.sr = sr
        self.timeline.segment_times = segment_times
        self.firing_handles.set_firings(firework_firing)
        self.timeline.set_duration(duration)
        self.playhead.set_duration(duration)
        self.update()

    def set_fireworks_colors(self, colors):
        self.firing_handles.firework_colors = colors
        self.update()

    def reset_selected_region(self):
        self.timeline.reset_selected_region()
        self.set_show_data(self.audio_data, self.sr, self.timeline.segment_times, self.firing_handles.firework_firing, self.timeline.duration)
        self.update()

    def start_preview(self):
        if self.audio_data is not None and self.sr is not None:
            sd.stop()
            import threading

            # Clamp current_time to region start if outside when resuming playback
            if self.timeline.selected_region and len(self.timeline.selected_region) == 2:
                start, end = self.timeline.selected_region
                if self.playhead.current_time < start or self.playhead.current_time > end:
                    self.playhead.current_time = start

            # Always clamp current_time to [0, duration]
            self.playhead.clamp()

            def play_audio():
                if self.audio_data is not None and self.playhead.current_time is not None and self.sr is not None:
                    # If a region is selected, play only that region from the correct offset
                    if self.timeline.selected_region and len(self.timeline.selected_region) == 2:
                        start, end = self.timeline.selected_region
                        play_start = max(start, min(self.playhead.current_time, end))
                        start_idx = int(play_start * self.sr)
                        end_idx = int(self.timeline.duration * self.sr)
                        sd.play(self.audio_data[start_idx:end_idx], self.sr, blocking=False)
                    else:
                        play_start = max(0, min(self.playhead.current_time, self.timeline.duration if self.timeline.duration else 0))
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

    def advance_preview(self):
        if self.audio_data is None or self.sr is None or self.timeline.duration is None:
            return
        self.playhead.advance(0.016)
        self.playhead.clamp()
        if self.playhead.current_time >= self.timeline.duration:
            self.playhead.current_time = self.timeline.duration
            if self.preview_timer:
                self.preview_timer.stop()
            try:
                if sd.get_stream() is not None:
                    sd.stop(ignore_errors=True)
            except RuntimeError:
                pass
        self.update()

    def toggle_play_pause(self):
        if self.preview_timer and self.preview_timer.isActive():
            try:
                sd.stop(ignore_errors=True)
                self.preview_timer.stop()
            except Exception:
                pass
        else:
            self.start_preview()

    def stop_preview(self):
        if self.audio_data is None or self.sr is None:
            return
        if self.preview_timer and self.preview_timer.isActive():
            self.preview_timer.stop()
        self.playhead.reset()
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
        if self.firing_handles.firework_firing is None:
            self.firing_handles.firework_firing = []
        elif not isinstance(self.firing_handles.firework_firing, list):
            self.firing_handles.firework_firing = list(self.firing_handles.firework_firing)
        firing_time = self.playhead.current_time - self.delay
        if firing_time < 0:
            return
        if not hasattr(self.firing_handles, 'firework_colors') or len(self.firing_handles.firework_colors) != len(self.firing_handles.firework_firing):
            self.firing_handles.firework_colors = [
                QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                for _ in self.firing_handles.firework_firing
            ]
        self.firing_handles.add_firing(firing_time)
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

        draw_start, draw_end, zoom_duration = self.timeline.get_draw_region()

        bar_rect = QRect(left_margin, timeline_y - 8, usable_w, 16)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(50, 55, 70, 220))
        painter.drawRoundedRect(bar_rect, 8, 8)

        painter.setPen(QColor(150, 150, 170))
        min_tick_px = 60
        tick_area = usable_w
        approx_ticks = max(2, tick_area // min_tick_px)
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
            if self.timeline.duration:
                minutes = int(t // 60)
                seconds = int(t % 60)
                label = f"{minutes}:{seconds:02d}"
                painter.setPen(QColor(200, 200, 220))
                painter.drawText(x - 12, timeline_y + 22, 24, 14, Qt.AlignmentFlag.AlignCenter, label)
                painter.setPen(QColor(150, 150, 170))
            t += step

        # Draw fireworks (handles)
        handle_radius = 12
        self.firing_handles.update_handle_rects(draw_start, draw_end, zoom_duration, usable_w, left_margin, timeline_y, handle_radius, self.timeline.duration)
        for i, (rect, orig_idx) in enumerate(self.firing_handles.firing_handles):
            ft = self.firing_handles.firework_firing[orig_idx]
            color = self.firing_handles.firework_colors[orig_idx] if len(self.firing_handles.firework_colors) > orig_idx else QColor(255, 255, 255)
            x = rect.center().x()
            is_selected = self.firing_handles.selected_firing == orig_idx
            painter.setBrush(QColor(0, 0, 0, 120))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect)
            painter.setBrush(color)
            painter.setPen(QColor(255, 255, 0) if is_selected else QColor(220, 220, 220, 180))
            r = int(handle_radius * (1.3 if is_selected else 1))
            painter.drawEllipse(x - r, timeline_y - r, 2 * r, 2 * r)
            painter.setPen(QColor(40, 40, 40, 180))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QColor(255, 255, 255))
            number_font = painter.font()
            number_font.setBold(True)
            number_font.setPointSizeF(label_font.pointSizeF() * 1.1)
            painter.setFont(number_font)
            painter.drawText(
                rect,
                Qt.AlignmentFlag.AlignCenter,
                str(orig_idx + 1)
            )
        painter.setFont(label_font)

        # --- PLAYHEAD DRAWING (always draw, even if outside zoom) ---
        playhead_time = min(max(self.playhead.current_time, 0), self.timeline.duration)
        playhead_x = left_margin + ((playhead_time - draw_start) / zoom_duration) * usable_w
        playhead_x = max(-2_147_483_648, min(playhead_x, 2_147_483_647))
        fade = False
        if playhead_time < draw_start or playhead_time > draw_end:
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

        draw_start, draw_end, zoom_duration = self.timeline.get_draw_region()

        playhead_time = min(max(self.playhead.current_time, 0), self.timeline.duration)
        playhead_x = left_margin + usable_w * (playhead_time - draw_start) / zoom_duration if self.timeline.duration else 0
        playhead_rect = QRect(int(playhead_x) - 8, timeline_y - 40, 16, 80)
        if playhead_rect.contains(event.position().toPoint()):
            self.dragging_playhead = True
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            return
        if not hasattr(self.firing_handles, 'firing_handles'):
            return
        self.firing_handles.selected_firing = None
        self.dragging_firing = False
        for rect, idx in self.firing_handles.firing_handles:
            if rect.contains(event.position().toPoint()):
                self.firing_handles.selected_firing = idx
                self.dragging_firing = True
                self.drag_offset = event.position().x() - rect.center().x()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.update()
                return

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

        draw_start, draw_end, zoom_duration = self.timeline.get_draw_region()

        if hasattr(self, 'dragging_firing') and self.dragging_firing and self.firing_handles.selected_firing is not None:
            x = event.position().x() - getattr(self, 'drag_offset', 0)
            x = max(left_margin, min(x, w - right_margin))
            new_time = (x - left_margin) / usable_w * zoom_duration + draw_start
            new_time = max(draw_start, min(new_time, draw_end))
            if self.firing_handles.firework_firing is not None:
                idx = self.firing_handles.selected_firing
                new_time = max(0, min(new_time, self.timeline.duration))
                self.firing_handles.firework_firing[idx] = new_time
            self.update()
            return

        if hasattr(self, 'dragging_playhead') and self.dragging_playhead:
            x = event.position().x()
            x = max(left_margin, min(x, w - right_margin))
            new_time = (x - left_margin) / usable_w * zoom_duration + draw_start
            new_time = max(0, min(new_time, self.timeline.duration))
            if event.buttons() & Qt.MouseButton.LeftButton:
                self.playhead.current_time = new_time
            self.update()
            return

        if hasattr(self.firing_handles, 'firing_handles'):
            for rect, idx in self.firing_handles.firing_handles:
                if rect.contains(event.position().toPoint()):
                    self.setCursor(Qt.CursorShape.OpenHandCursor)
                    return
        playhead_time = min(max(self.playhead.current_time, 0), self.timeline.duration)
        playhead_x = left_margin + usable_w * (playhead_time - draw_start) / zoom_duration if self.timeline.duration else 0
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
            w = self.width()
            left_margin = 40
            right_margin = 40
            usable_w = w - left_margin - right_margin

            draw_start, draw_end, zoom_duration = self.timeline.get_draw_region()

            x = event.position().x()
            x = max(left_margin, min(x, w - right_margin))
            new_time = (x - left_margin) / usable_w * zoom_duration + draw_start
            new_time = max(0, min(new_time, self.timeline.duration))
            self.playhead.current_time = new_time
            self.dragging_playhead = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
            if self.preview_timer and self.preview_timer.isActive():
                try:
                    if sd.get_stream() is not None:
                        sd.stop(ignore_errors=True)
                except RuntimeError:
                    pass
                self.preview_timer.stop()
                if self.main_window and hasattr(self.main_window, "play_pause_btn"):
                    self.main_window.play_pause_btn.setText("Play")
                    self.main_window.play_pause_btn.setChecked(False)
                return
            return

    def set_selected_region(self, region):
        self.timeline.set_selected_region(region)
        self.update()

    def remove_selected_firing(self):
        self.firing_handles.remove_selected_firing()
        self.update()
        return self.firing_handles.firework_firing
