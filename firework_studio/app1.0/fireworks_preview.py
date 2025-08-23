from PyQt6.QtWidgets import QWidget, QMenu, QColorDialog, QInputDialog
from PyQt6.QtCore import QTimer, QRect, Qt, QElapsedTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QIcon, QPixmap, QAction

import sounddevice as sd
import random
import threading

import copy

from fireworks_timeline import FireworkTimelineRenderer
from handles import FiringHandles

class HandlesStack:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []

    def push(self, handles):
        # Store a deep copy to avoid mutation issues
        self.undo_stack.append(copy.deepcopy(handles))
        self.redo_stack.clear()

    def undo(self, current_handles):
        if self.undo_stack:
            self.redo_stack.append(copy.deepcopy(current_handles))
            previous = self.undo_stack.pop()
            return copy.deepcopy(previous)
        return None

    def redo(self, current_handles):
        if self.redo_stack:
            self.undo_stack.append(copy.deepcopy(current_handles))
            next_state = self.redo_stack.pop()
            return copy.deepcopy(next_state)
        return None

    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()

    def top(self):
        if self.undo_stack:
            return copy.deepcopy(self.undo_stack[-1])
        return None

class FireworkPreviewWidget(QWidget):
    handles_changed = pyqtSignal(list)

    def __init__(self):
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
        self.dragging_playhead = False
        self.dragging_firing = False
        self.timeline_renderer = FireworkTimelineRenderer(self)
        self._elapsed_timer = QElapsedTimer()
        self.handles_stack = HandlesStack()
        self.undo_stack = self.handles_stack.undo_stack
        self.redo_stack = self.handles_stack.redo_stack

    def set_show_data(self, audio_data, sr, segment_times, firework_times, duration):
        self.audio_data = audio_data
        self.sr = sr
        self.segment_times = segment_times
        self.firework_times = firework_times
        self.duration = duration
        self.update()

    def reset_fireworks(self):
        self.fireworks = []
        self.handles_stack.clear()  # Clear undo/redo history
        self.update()
        # Emit signal to notify that handles have changed
        self.handles_changed.emit(self.fireworks)

    def get_handles(self):
        return self.fireworks

    def clear_undo_history(self):
        """Clear the undo/redo history. Should be called when loading a new file."""
        self.handles_stack.clear()

    def redo(self):
        new_handles = self.handles_stack.redo(self.fireworks)
        if new_handles is not None:
            # Store the exact handles without any processing to avoid color changes
            self.fireworks = new_handles  # These are already deep copied from the stack
            # Rebuild firework_times from the restored handles
            self.firework_times = [h.firing_time for h in self.fireworks]
            # Only call update to refresh the visual
            self.update()
            # Emit signal to notify that handles have changed
            self.handles_changed.emit(self.fireworks)

    def undo(self):
        new_handles = self.handles_stack.undo(self.fireworks)
        if new_handles is not None:
            # Store the exact handles without any processing to avoid color changes  
            self.fireworks = new_handles  # These are already deep copied from the stack
            # Rebuild firework_times from the restored handles
            self.firework_times = [h.firing_time for h in self.fireworks]
            # Only call update to refresh the visual
            self.update()
            # Emit signal to notify that handles have changed
            self.handles_changed.emit(self.fireworks)
            
    def set_handles(self, handles, emit_signal=True):
        fireworks = []
        firework_times = []
        pattern_default = self.pattern
        number_firings_default = self.number_firings

        for i, handle in enumerate(handles):
            color = getattr(handle, "handle_color", None)
            if isinstance(color, QColor):
                pass
            elif isinstance(color, (tuple, list)) and len(color) >= 3:
                color = QColor(color[0], color[1], color[2])
            else:
                # Assign a color from the palette if no valid color exists
                color_index = i % len(self.timeline_renderer.handle_colors)
                palette_color = self.timeline_renderer.handle_colors[color_index]
                color = QColor(palette_color.red(), palette_color.green(), palette_color.blue())

            pattern = getattr(handle, "pattern", pattern_default)
            number_firings = getattr(handle, "number_firings", number_firings_default)
            firing_time = float(getattr(handle, "firing_time", 0))

            fw_handle = FiringHandles(
                firing_time,
                color,
                number_firings=int(number_firings),
                pattern=str(pattern),
                display_number=i + 1
            )
            fireworks.append(fw_handle)
            firework_times.append(firing_time)

        # Sort once, in-place, for both lists
        fireworks.sort(key=lambda h: h.firing_time)
        firework_times.sort()

        self.fireworks = fireworks
        self.firework_times = firework_times
        self.update()
        
        # Emit signal to notify that handles have changed (unless explicitly disabled)
        if emit_signal:
            self.handles_changed.emit(self.fireworks)

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

    def add_time(self, specific_handle=None):
        if self.audio_data is None or self.sr is None:
            return
        if self.firework_times is None:
            self.firework_times = []
        elif not isinstance(self.firework_times, list):
            self.firework_times = list(self.firework_times)

        firing_time = self.current_time
        if firing_time < self.delay:
            return
        
        # Save current state before adding new firework
        self.handles_stack.push(self.fireworks)
        
        # Assign color from palette based on current number of fireworks
        next_index = len(self.fireworks)
        color_index = next_index % len(self.timeline_renderer.handle_colors)
        palette_color = self.timeline_renderer.handle_colors[color_index]
        color = QColor(palette_color.red(), palette_color.green(), palette_color.blue())

        self.firework_times.append(firing_time)
        self.firework_times.sort()

        if specific_handle is None:
            handle = FiringHandles(
            firing_time,
            color,
            number_firings=self.number_firings,
            pattern=self.pattern,
            display_number=0  # temporary, will set below
            )
        else:
            handle = FiringHandles.from_list(specific_handle)
            
        self.fireworks.append(handle)
        self.fireworks.sort(key=lambda h: h.firing_time)

        # Update display_number for all handles to ensure uniqueness and order
        for i, h in enumerate(self.fireworks):
            h.display_number = i + 1

        self.update()
        
        # Emit signal to notify that handles have changed
        self.handles_changed.emit(self.fireworks)

    def advance_preview(self):
        if self.audio_data is None or self.sr is None or self.duration is None:
            return
        # Use QElapsedTimer to track actual elapsed time
        if not hasattr(self, '_last_preview_time'):
            self._elapsed_timer = QElapsedTimer()
            self._elapsed_timer.start()
            self._last_preview_time = self._elapsed_timer.elapsed()
        now = self._elapsed_timer.elapsed()
        if self._last_preview_time is not None:
            elapsed_ms = now - self._last_preview_time
        else:
            elapsed_ms = 0
        self._last_preview_time = now
        elapsed_sec = elapsed_ms / 1000.0
        self.current_time += elapsed_sec
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
            # Reset timer tracking
            self._last_preview_time = None
        self.update()

    def remove_selected_firing(self):
        if hasattr(self, 'selected_firing') and self.selected_firing is not None:
            # Save current state before removing firework
            self.handles_stack.push(self.fireworks)
            
            idx = self.selected_firing
            if self.firework_times is not None and 0 <= idx < len(self.firework_times):
                if not isinstance(self.firework_times, list):
                    self.firework_times = list(self.firework_times)
                del self.firework_times[idx]
                if self.fireworks is not None and len(self.fireworks) > idx:
                    del self.fireworks[idx]
            self.selected_firing = None
            self.update()
            
            # Emit signal to notify that handles have changed
            self.handles_changed.emit(self.fireworks)
        return self.firework_times
    
    def start_preview(self):
        if self.audio_data is not None and self.sr is not None:
            try:
                sd.stop(ignore_errors=True)
            except Exception:
                pass
            if self.current_time < 0:
                self.current_time = 0
            # Convert current_time to an index to play the audio from that index which is current_time
            def play_audio():
                if self.audio_data is not None and self.current_time is not None and self.sr is not None:
                    play_start = max(0, min(self.current_time, self.duration if self.duration else 0))
                    start_idx = int(play_start * self.sr)
                    sd.play(self.audio_data[start_idx:], self.sr, blocking=False)

            if self.audio_thread is not None and self.audio_thread.is_alive():
                self.audio_thread.join(timeout=1)
            self.audio_thread = threading.Thread(target=play_audio, daemon=True)
            self.audio_thread.start()
        if self.preview_timer:
            self.preview_timer.stop()
        # Reset elapsed timer for accurate playhead movement
        if hasattr(self, '_last_preview_time'):
            del self._last_preview_time
        self._elapsed_timer.start()
        self._last_preview_time = self._elapsed_timer.elapsed()
        self.preview_timer = QTimer(self)
        self.preview_timer.timeout.connect(self.advance_preview)
        self.preview_timer.start(1)  # 1 ms interval for smooth playhead

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
        try:
            if sd.get_stream() is not None:
                sd.stop(ignore_errors=True)
        except RuntimeError:
            pass
        if self.audio_thread is not None and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1)
            self.audio_thread = None
        self.current_time = 0  # Reset playhead to start
        self.audio_thread = None
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
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

        if self.selected_region and len(self.selected_region) == 2 and self.duration:
            draw_start, draw_end = self.selected_region
            zoom_duration = max(draw_end - draw_start, 1e-6)
        else:
            draw_start = 0
            draw_end = self.duration
            zoom_duration = self.duration if self.duration else 1

        playhead_time = min(max(self.current_time, 0), self.duration)
        playhead_x = left_margin + usable_w * (playhead_time - draw_start) / zoom_duration if self.duration else left_margin
        playhead_x = max(left_margin, min(playhead_x, w - right_margin))  # Ensure playhead stays within timeline
        playhead_rect = QRect(int(playhead_x) - 8, timeline_y - 40, 16, 80)

        # Only start dragging playhead if mouse is inside playhead rect and left button is pressed
        if playhead_rect.contains(event.position().toPoint()) and event.button() == Qt.MouseButton.LeftButton:
            self.dragging_playhead = True
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            return

        if not hasattr(self, 'firing_handles'):
            return

        self.selected_firing = None
        self.dragging_firing = False

        handle_clicked = False
        for rect, idx in self.firing_handles:
            if rect.contains(event.position().toPoint()):
                self.selected_firing = idx
                if event.button() == Qt.MouseButton.LeftButton:
                    # Don't save state here - wait until drag actually completes
                    # Store the original time to compare if meaningful change occurred
                    self.drag_start_time = self.fireworks[idx].firing_time if idx < len(self.fireworks) else 0
                    self.dragging_firing = True
                    self.drag_offset = event.position().x() - rect.center().x()
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.update()
                if event.button() == Qt.MouseButton.RightButton:
                    self.show_firing_context_menu(event.globalPosition().toPoint(), idx)
                    self.dragging_firing = False
                handle_clicked = True
        # If right click and not on a handle, move playhead to clicked position
        if event.button() == Qt.MouseButton.RightButton and not handle_clicked:
            x = event.position().x()
            x = max(left_margin, min(x, w - right_margin))
            new_time = (x - left_margin) / usable_w * zoom_duration + draw_start
            new_time = max(0, min(new_time, self.duration))
            self.current_time = new_time
            self.dragging_playhead = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
            # Only stop preview if it was running
            if self.preview_timer and self.preview_timer.isActive():
                try:
                    if sd.get_stream() is not None:
                        sd.stop(ignore_errors=True)
                except RuntimeError:
                    pass
                self.preview_timer.stop()
                self.preview_timer.stop()
            self.update()

    def mouseDoubleClickEvent(self, event):
        # Add firing at double-clicked position
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
        saved_time = self.current_time
        self.current_time = new_time
        self.add_time()
        self.current_time = saved_time
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

        for rect, _ in self.firing_handles:
            if rect.contains(event.position().toPoint()):
                self.setCursor(Qt.CursorShape.OpenHandCursor)
                self.setCursor(Qt.CursorShape.OpenHandCursor)
        playhead_time = min(max(self.current_time, 0), self.duration)
        playhead_x = left_margin + usable_w * (playhead_time - draw_start) / zoom_duration if self.duration else left_margin
        playhead_x = max(left_margin, min(playhead_x, w - right_margin))
        playhead_rect = QRect(int(playhead_x) - 8, timeline_y - 40, 16, 80)
        if playhead_rect.contains(event.position().toPoint()):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            return

        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        # Only handle releasing drag actions
        if hasattr(self, 'dragging_firing') and self.dragging_firing:
            self.dragging_firing = False
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            
            # Only save to undo stack if the drag resulted in a meaningful change
            if (hasattr(self, 'drag_start_time') and self.selected_firing is not None 
                and self.selected_firing < len(self.fireworks)):
                current_time = self.fireworks[self.selected_firing].firing_time
                # Only save if the time changed by more than 0.01 seconds (meaningful change)
                if abs(current_time - self.drag_start_time) > 0.01:
                    # Save the state with the original time, then update
                    temp_fireworks = copy.deepcopy(self.fireworks)
                    temp_fireworks[self.selected_firing].firing_time = self.drag_start_time
                    self.handles_stack.push(temp_fireworks)
                    
            self.update()
            # Emit signal to notify that handles have changed
            self.handles_changed.emit(self.fireworks)
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
            # Only stop preview if it was running
            if self.preview_timer and self.preview_timer.isActive():
                try:
                    if sd.get_stream() is not None:
                        sd.stop(ignore_errors=True)
                except RuntimeError:
                    pass
                self.preview_timer.stop()
            return
       
    def show_firing_context_menu(self, global_pos, idx):
        handle = self.fireworks[idx] if 0 <= idx < len(self.fireworks) else None
        if handle is None:
            return

        menu = QMenu(self)

        # Display the firing number at the top as a disabled, bold action
        display_number_text = f"🔥 -- Firing #{handle.display_number} -- 🔥"
        display_number_action = QAction(display_number_text, self)
        font = display_number_action.font()
        font.setBold(True)
        display_number_action.setFont(font)
        display_number_action.setEnabled(False)
        menu.addAction(display_number_action)
        menu.addSeparator()

        # Show color sample as a colored square in the menu
        color = handle.explosion_color if isinstance(handle.explosion_color, QColor) else QColor(handle.explosion_color)
        pixmap = QPixmap(16, 16)
        pixmap.fill(color)
        icon = QIcon(pixmap)
        change_color_action = menu.addAction(icon, f"Change Color (Current: {color.name()})")
        change_time_action = menu.addAction(f"Change Time (Current: {handle.firing_time:.3f}s)")
        change_pattern_action = menu.addAction(f"Change Pattern (Current: {handle.pattern})")
        change_number_action = menu.addAction(f"Change Number of Firings (Current: {handle.number_firings})")
        delete_action = menu.addAction("Delete Firing")

        action = menu.exec(global_pos)

        if action == change_color_action:
            initial_color = handle.explosion_color
            if not isinstance(initial_color, QColor):
                try:
                    initial_color = QColor(*initial_color) if isinstance(initial_color, (tuple, list)) else QColor(initial_color)
                except Exception:
                    initial_color = QColor(255, 255, 255)
            color = QColorDialog.getColor(initial_color, self, "Select Firework Color")
            if color.isValid():
                # Save current state before changing color
                self.handles_stack.push(self.fireworks)
                # Store as tuple for serialization
                handle.explosion_color = (color.red(), color.green(), color.blue())
                self.update()
                # Emit signal to notify that handles have changed
                self.handles_changed.emit(self.fireworks)

        elif action == change_time_action:
            new_time, ok = QInputDialog.getDouble(self, "Change Firing Time", "Time (seconds):", handle.firing_time, 0, self.duration, 3)
            if ok:
                # Save current state before changing time
                self.handles_stack.push(self.fireworks)
                handle.firing_time = float(new_time)  # Ensure it's a Python float
                self.fireworks.sort(key=lambda h: h.firing_time)
                self.firework_times = [h.firing_time for h in self.fireworks]
                for i, h in enumerate(self.fireworks):
                    h.display_number = i + 1
                self.update()
                # Emit signal to notify that handles have changed
                self.handles_changed.emit(self.fireworks)
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
                # Save current state before changing pattern
                self.handles_stack.push(self.fireworks)
                handle.pattern = str(pattern)  # Ensure it's a Python string
                self.update()
                # Emit signal to notify that handles have changed
                self.handles_changed.emit(self.fireworks)
        elif action == change_number_action:
            num, ok = QInputDialog.getInt(self, "Change Number of Firings", "Number:", handle.number_firings, 1, 100, 1)
            if ok:
                # Save current state before changing number of firings
                self.handles_stack.push(self.fireworks)
                handle.number_firings = int(num)  # Ensure it's a Python int
                self.update()
                # Emit signal to notify that handles have changed
                self.handles_changed.emit(self.fireworks)
        elif action == delete_action:
            self.selected_firing = idx
            self.remove_selected_firing()