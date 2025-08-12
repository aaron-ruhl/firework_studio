from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QRect, Qt, QPoint
from PyQt6.QtGui import QPainter, QColor

from PyQt6.QtWidgets import QMenu, QColorDialog, QInputDialog
import sounddevice as sd
import random


from fireworks_timeline import FireworkTimelineRenderer
from handles import FiringHandles

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
        self.number_firings = 1
        self.pattern = "circle"
        self.firing_handles = []

        self.current_time = 0
        self.playhead_time = 0
        self.duration = 0
        self.audio_thread = None
        self.selected_firing = None
        self.selected_region = tuple()
        self.preview_timer = None

        self.timeline_renderer = FireworkTimelineRenderer(self)

    def set_show_data(self, audio_data, sr, segment_times, firework_times, duration):
        self.audio_data = audio_data
        self.sr = sr
        self.segment_times = segment_times
        self.firework_times = firework_times
        self.duration = duration
        self.update()

    def reset_fireworks(self):
        self.fireworks = []
        self.update()

    def get_handles(self):
        return self.fireworks

    def set_handles(self, handles):
        self.fireworks = []
        self.firework_times = []
        for i, handle in enumerate(handles):
            if hasattr(handle, "firing_color") and isinstance(handle.firing_color, QColor):
                color = handle.firing_color
            elif hasattr(handle, "firing_color") and isinstance(handle.firing_color, (tuple, list)) and len(handle.firing_color) == 3:
                color = QColor(*handle.firing_color)
            else:
                handle.firing_color = QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
            pattern = handle.pattern if hasattr(handle, "pattern") else self.pattern
            number_firings = handle.number_firings if hasattr(handle, "number_firings") else self.number_firings
            firing_time = handle.firing_time
            fw_handle = FiringHandles(
                firing_time,
                color,
                number_firings=number_firings,
                pattern=pattern,
                display_number=i + 1
            )
            self.fireworks.append(fw_handle)
            self.firework_times.append(firing_time)
        self.fireworks.sort(key=lambda h: h.firing_time)
        self.firework_times.sort()
        self.update()

    def reset_selected_region(self):
        if self.duration:
            self.selected_region = (0, self.duration)
        else:
            self.selected_region = tuple()
        self.set_show_data(self.audio_data, self.sr, self.segment_times, self.firework_times, self.duration)
        self.update()
        
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
        self.update()

    def set_number_firings(self, count):
        self.number_firings = count

    def set_pattern(self, pattern):
        self.pattern = pattern

    def add_time(self):
        if self.audio_data is None or self.sr is None:
            return
        if self.firework_times is None:
            self.firework_times = []
        elif not isinstance(self.firework_times, list):
            self.firework_times = list(self.firework_times)

        firing_time = self.current_time
        if firing_time < self.delay:
            return
        color = QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

        self.firework_times.append(firing_time)
        self.firework_times.sort()

        handle = FiringHandles(
            firing_time,
            color,
            number_firings=self.number_firings,
            pattern=self.pattern,
            display_number=0  # temporary, will set below
        )
        self.fireworks.append(handle)
        self.fireworks.sort(key=lambda h: h.firing_time)

        # Update display_number for all handles to ensure uniqueness and order
        for i, h in enumerate(self.fireworks):
            h.display_number = i + 1

        self.update()

    def advance_preview(self):
        if self.audio_data is None or self.sr is None or self.duration is None:
            return
        self.current_time += 0.016
        if self.current_time > self.duration:
            self.current_time = self.duration
        if self.current_time < 0:
            self.current_time = 0

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
            if self.current_time < 0:
                self.current_time = 0

            def play_audio():
                if self.audio_data is not None and self.current_time is not None and self.sr is not None:
                    if self.selected_region and len(self.selected_region) == 2:
                        start, end = self.selected_region
                        play_start = min(self.current_time, end)
                        start_idx = int(play_start * self.sr)
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
        self.timeline_renderer.draw(painter)

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

        if self.selected_region and len(self.selected_region) == 2 and self.duration:
            draw_start, draw_end = self.selected_region
            zoom_duration = max(draw_end - draw_start, 1e-6)
        else:
            draw_start = 0
            draw_end = self.duration
            zoom_duration = self.duration if self.duration else 1

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
                self.setCursor(Qt.CursorShape.SplitHCursor)
                self.update()
                if event.button() == Qt.MouseButton.RightButton:
                    self.show_firing_context_menu(event.globalPosition().toPoint(), idx)
                    self.dragging_firing = False
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

        if self.selected_region and len(self.selected_region) == 2 and self.duration:
            draw_start, draw_end = self.selected_region
            zoom_duration = max(draw_end - draw_start, 1e-6)
        else:
            draw_start = 0
            draw_end = self.duration
            zoom_duration = self.duration if self.duration else 1

        if hasattr(self, 'dragging_playhead') and self.dragging_playhead:
            x = event.position().x()
            x = max(left_margin, min(x, w - right_margin))
            new_time = (x - left_margin) / usable_w * zoom_duration + draw_start
            new_time = max(0, min(new_time, self.duration))
            if event.buttons() & Qt.MouseButton.LeftButton:
                self.current_time = new_time
            self.update()
            return

        if hasattr(self, 'dragging_firing') and self.dragging_firing and self.selected_firing is not None:
            x = event.position().x() - getattr(self, 'drag_offset', 0)
            x = max(left_margin, min(x, w - right_margin))
            new_time = (x - left_margin) / usable_w * zoom_duration + draw_start
            new_time = max(0, min(new_time, self.duration))
            handle = self.fireworks[self.selected_firing]
            handle.firing_time = new_time
            self.fireworks.sort(key=lambda h: h.firing_time)
            self.firework_times = [h.firing_time for h in self.fireworks]
            for i, h in enumerate(self.fireworks):
                h.display_number = i + 1
            for i, h in enumerate(self.fireworks):
                if h is handle:
                    self.selected_firing = i
                    break
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
            new_time = max(0, min(new_time, self.duration))
            self.current_time = new_time
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
                return
            return

    def show_firing_context_menu(self, global_pos, idx):
        handle = self.fireworks[idx] if 0 <= idx < len(self.fireworks) else None
        if handle is None:
            return

        menu = QMenu(self)

        # Show current values in the menu text
        change_color_action = menu.addAction(f"Change Color (Current: {handle.firing_color.name() if isinstance(handle.firing_color, QColor) else str(handle.firing_color)})")
        change_time_action = menu.addAction(f"Change Time (Current: {handle.firing_time:.3f}s)")
        change_pattern_action = menu.addAction(f"Change Pattern (Current: {handle.pattern})")
        change_number_action = menu.addAction(f"Change Number of Firings (Current: {handle.number_firings})")
        delete_action = menu.addAction("Delete Firing")

        action = menu.exec(global_pos)

        if action == change_color_action:
            initial_color = handle.firing_color
            if not isinstance(initial_color, QColor):
                try:
                    initial_color = QColor(initial_color)
                except Exception:
                    initial_color = QColor(255, 255, 255)
            color = QColorDialog.getColor(initial_color, self, "Select Firework Color")
            if color.isValid():
                handle.firing_color = color
                self.update()
        elif action == change_time_action:
            new_time, ok = QInputDialog.getDouble(self, "Change Firing Time", "Time (seconds):", handle.firing_time, 0, self.duration, 3)
            if ok:
                handle.firing_time = new_time
                self.fireworks.sort(key=lambda h: h.firing_time)
                self.firework_times = [h.firing_time for h in self.fireworks]
                for i, h in enumerate(self.fireworks):
                    h.display_number = i + 1
                self.update()
        elif action == change_pattern_action:
            patterns = [
                "circle",
                "chrysanthemum",
                "palm",
                "willow",
                "peony",
                "ring",
            ]
            current = patterns.index(handle.pattern) if handle.pattern in patterns else 0
            pattern, ok = QInputDialog.getItem(self, "Change Pattern", "Pattern:", patterns, current, False)
            if ok:
                handle.pattern = pattern
                self.update()
        elif action == change_number_action:
            num, ok = QInputDialog.getInt(self, "Change Number of Firings", "Number:", handle.number_firings, 1, 100, 1)
            if ok:
                handle.number_firings = num
                self.update()
        elif action == delete_action:
            self.selected_firing = idx
            self.remove_selected_firing()
