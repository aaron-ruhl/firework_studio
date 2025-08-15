from PyQt6.QtCore import QRect, QPoint, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QVector2D
import numpy as np

class FireworkTimelineRenderer:
    def __init__(self, widget):
        self.widget = widget
        self.handle_colors = [
            QColor(40, 40, 60),      # Deep blue-gray
            QColor(60, 30, 60),      # Muted purple
            QColor(30, 30, 30),      # Charcoal
            QColor(70, 0, 70),       # Deep plum
            QColor(50, 0, 40),       # Eggplant
            QColor(0, 0, 0),         # Black
            QColor(30, 20, 40),      # Muted indigo
            QColor(80, 20, 60),      # Dusty rose
            QColor(55, 0, 40),       # Dark magenta
            QColor(25, 25, 50),      # Navy blue
            QColor(45, 45, 70),      # Slate blue
            QColor(35, 25, 55),      # Grape
            QColor(20, 20, 35),      # Midnight
            QColor(65, 35, 55),      # Mauve
            QColor(15, 10, 25),      # Very dark purple
            QColor(50, 20, 50),      # Heather
            QColor(60, 10, 40),      # Burgundy
            QColor(30, 10, 30),      # Raisin
            QColor(20, 0, 20),       # Black plum
            QColor(70, 10, 50),      # Deep rose
        ]

    def _next_handle_color(self):
        if not hasattr(self, '_handle_color_stack') or not self._handle_color_stack:
            self._handle_color_stack = list(self.handle_colors)
        return self._handle_color_stack.pop()

    def draw(self, painter):
        w, h = self.widget.width(), self.widget.height()
        left_margin = 40
        right_margin = 40
        top_margin = 30
        bottom_margin = 40
        usable_w = w - left_margin - right_margin
        usable_h = h - top_margin - bottom_margin
        timeline_y = top_margin + usable_h // 2

        # Draw selected region and playhead label
        self._draw_selected_region(painter, left_margin, usable_w, timeline_y)
        # Draw timeline bar and ticks
        self._draw_timeline_bar(painter, left_margin, usable_w, timeline_y)
        # Draw firing handles
        self._draw_firing_handles(painter, left_margin, usable_w, timeline_y)
        # Draw playhead
        self._draw_playhead(painter, left_margin, usable_w, timeline_y)
        # Draw border
        painter.setPen(QColor(80, 80, 100, 180))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRect(left_margin, top_margin, usable_w, usable_h), 12, 12)
        painter.setClipping(False)

    def _get_draw_region(self):
        widget = self.widget
        if widget.selected_region and len(widget.selected_region) == 2 and widget.duration:
            draw_start, draw_end = widget.selected_region
            zoom_duration = max(draw_end - draw_start, 1e-9)
        else:
            draw_start = 0
            draw_end = widget.duration if widget.duration is not None else 1.0
            zoom_duration = draw_end if draw_end > 0 else 1.0
        return draw_start, draw_end, zoom_duration

    def _time_to_x(self, time, left_margin, usable_w, draw_start, zoom_duration):
        # This function ensures that any time value is mapped to the correct pixel position
        # regardless of zoom level or selected_region
        rel = (time - draw_start) / zoom_duration
        rel = min(max(rel, 0.0), 1.0)
        return left_margin + rel * usable_w

    def _x_to_time(self, x, left_margin, usable_w, draw_start, zoom_duration):
        # Inverse of _time_to_x, for accurate handle movement
        rel = (x - left_margin) / usable_w
        rel = min(max(rel, 0.0), 1.0)
        return draw_start + rel * zoom_duration

    def _draw_selected_region(self, painter, left_margin, usable_w, timeline_y):
        widget = self.widget
        draw_start, draw_end, zoom_duration = self._get_draw_region()
        if widget.selected_region and len(widget.selected_region) == 2 and widget.duration:
            def format_time(t):
                mins = int(t // 60)
                secs = int(t % 60)
                ms = int((t - int(t)) * 1000)
                return f"{mins:02d}:{secs:02d}:{ms:03d}"
            gap = 1.41
            if widget.playhead_time < draw_start - gap or widget.playhead_time > draw_end + gap:
                label = format_time(widget.playhead_time)
                orig_font = painter.font()
                label_font = orig_font
                label_font = label_font.__class__(label_font)  # Make a copy
                label_font.setBold(True)
                label_font.setPointSizeF(orig_font.pointSizeF() * 1.1)
                painter.setFont(label_font)
                label_width = painter.fontMetrics().horizontalAdvance(label) + 12
                label_height = painter.fontMetrics().height() + 6
                arrow_y = timeline_y - 48 + 12 + label_height // 2

                if widget.playhead_time < draw_start:
                    arrow_x = 10
                    points = [
                        QVector2D(arrow_x + 8, arrow_y - 18),
                        QVector2D(arrow_x + 8, arrow_y + 18),
                        QVector2D(arrow_x, arrow_y)
                    ]
                    painter.setBrush(QColor(0, 255, 120, 180))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawPolygon(*[QPoint(int(p.x()), int(p.y())) for p in points])
                    painter.setBrush(QColor(25, 28, 40, 230))
                    painter.drawRoundedRect(arrow_x + 16, arrow_y - label_height // 2, label_width, label_height, 7, 7)
                    painter.setPen(QColor(0, 255, 120))
                    painter.drawText(arrow_x + 16, arrow_y - label_height // 2, label_width, label_height, Qt.AlignmentFlag.AlignCenter, label)
                else:
                    arrow_x = widget.width() - 10
                    points = [
                        QVector2D(arrow_x - 8, arrow_y - 18),
                        QVector2D(arrow_x - 8, arrow_y + 18),
                        QVector2D(arrow_x, arrow_y)
                    ]
                    painter.setBrush(QColor(0, 255, 120, 180))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawPolygon(*[QPoint(int(p.x()), int(p.y())) for p in points])
                    painter.setBrush(QColor(25, 28, 40, 230))
                    painter.drawRoundedRect(arrow_x - 16 - label_width, arrow_y - label_height // 2, label_width, label_height, 7, 7)
                    painter.setPen(QColor(0, 255, 120))
                    painter.drawText(arrow_x - 16 - label_width, arrow_y - label_height // 2, label_width, label_height, Qt.AlignmentFlag.AlignCenter, label)
                painter.setFont(orig_font)

    def _draw_timeline_bar(self, painter, left_margin, usable_w, timeline_y):
        widget = self.widget
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
        draw_start, draw_end, span = self._get_draw_region()
        step = nice_step(span, approx_ticks)
        first_tick = ((draw_start // step) + 1) * step if draw_start % step != 0 else draw_start
        orig_font = painter.font()
        label_font = orig_font
        label_font = label_font.__class__(label_font)  # Make a copy
        label_font.setPointSizeF(orig_font.pointSizeF() * 0.9)
        painter.setFont(label_font)
        tick_times = np.arange(first_tick, draw_end + 1e-6, step)
        for t in tick_times:
            x = self._time_to_x(t, left_margin, usable_w, draw_start, span)
            painter.drawLine(int(round(x)), timeline_y + 10, int(round(x)), timeline_y + 18)
            if widget.duration:
                minutes = int(t // 60)
                seconds = int(t % 60)
                label = f"{minutes}:{seconds:02d}"
                painter.setPen(QColor(200, 200, 220))
                painter.drawText(int(round(x)) - 12, timeline_y + 22, 24, 14, Qt.AlignmentFlag.AlignCenter, label)
                painter.setPen(QColor(150, 150, 170))
        painter.setFont(orig_font)
        
    def _draw_firing_handles(self, painter, left_margin, usable_w, timeline_y):
        widget = self.widget
        widget.firing_handles = []
        handle_width = 14
        handle_height = 15
        draw_start, draw_end, zoom_duration = self._get_draw_region()
        if widget.fireworks is not None and widget.duration:
            orig_font = painter.font()
            indices = [i for i, fw in enumerate(widget.fireworks) if draw_start <= fw.firing_time <= draw_end]
            for idx in indices:
                fw = widget.fireworks[idx]
                is_selected = hasattr(widget, 'selected_firing') and widget.selected_firing == idx
                color = self.handle_colors[idx % len(self.handle_colors)]
                # Always use fw.firing_time for handle position, so it stays accurate regardless of zoom
                x = self._time_to_x(fw.firing_time, left_margin, usable_w, draw_start, zoom_duration)
                painter.setBrush(color)
                painter.setPen(QColor(255, 255, 0) if is_selected else QColor(220, 220, 220, 180))
                if is_selected:
                    center_x = int(round(x))
                    painter.setPen(QColor(255, 255, 0))
                    painter.drawLine(center_x, timeline_y - handle_height, center_x, timeline_y + handle_height)
                rect_x = int(round(x)) - handle_width // 2
                rect_y = timeline_y - handle_height // 2
                painter.drawRoundedRect(rect_x, rect_y, handle_width, handle_height, 5, 5)
                painter.setPen(QColor(0, 255, 255))
                number_font = orig_font
                number_font = number_font.__class__(number_font)  # Make a copy
                number_font.setBold(True)
                number_font.setPointSizeF(orig_font.pointSizeF() * 1.1)
                painter.setFont(number_font)
                painter.drawText(
                    rect_x,
                    rect_y,
                    handle_width,
                    handle_height,
                    Qt.AlignmentFlag.AlignCenter,
                    str(fw.number_firings)
                )
                # Store handle rect and index for hit-testing, always based on fw.firing_time
                widget.firing_handles.append((QRect(rect_x, rect_y, handle_width, handle_height), idx))
            painter.setFont(orig_font)

    def _draw_playhead(self, painter, left_margin, usable_w, timeline_y):
        widget = self.widget
        draw_start, draw_end, zoom_duration = self._get_draw_region()
        widget.playhead_time = min(max(widget.current_time, 0), widget.duration)
        playhead_x = self._time_to_x(widget.playhead_time, left_margin, usable_w, draw_start, zoom_duration)
        playhead_x = max(-2_147_483_648, min(playhead_x, 2_147_483_647))
        fade = False
        if widget.playhead_time < draw_start or widget.playhead_time > draw_end:
            fade = True
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 40) if fade else QColor(0, 0, 0, 100))
        painter.drawRect(int(round(playhead_x)) - 2, timeline_y - 44, 4, 88)
        painter.setPen(QColor(0, 255, 120, 80) if fade else QColor(0, 255, 120))
        painter.drawLine(int(round(playhead_x)), timeline_y - 40, int(round(playhead_x)), timeline_y + 40)
        painter.setBrush(QColor(0, 255, 120, 80) if fade else QColor(0, 255, 120))
        points = [
            QVector2D(int(round(playhead_x)) - 8, timeline_y - 48),
            QVector2D(int(round(playhead_x)) + 8, timeline_y - 48),
            QVector2D(int(round(playhead_x)), timeline_y - 36)
        ]
        painter.drawPolygon(*[QPoint(int(p.x()), int(p.y())) for p in points])

        minutes = int(widget.playhead_time // 60)
        seconds = int(widget.playhead_time % 60)
        milliseconds = int((widget.playhead_time - int(widget.playhead_time)) * 1000)
        time_label = f"{minutes:02d}:{seconds:02d}:{milliseconds:03d}"

        orig_font = painter.font()
        label_font = orig_font
        label_font = label_font.__class__(label_font)  # Make a copy
        label_font.setBold(True)
        label_font.setPointSizeF(orig_font.pointSizeF() * 1.15)
        painter.setFont(label_font)
        label_width = painter.fontMetrics().horizontalAdvance(time_label) + 12
        label_height = painter.fontMetrics().height() + 4
        label_x = int(round(playhead_x)) - label_width // 2
        label_y = timeline_y - 48 + 12
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(25, 28, 40, 230))
        painter.drawRoundedRect(label_x, label_y, label_width, label_height, 7, 7)
        painter.setPen(QColor(0, 255, 120) if not fade else QColor(0, 255, 120, 120))
        painter.drawText(label_x, label_y, label_width, label_height, Qt.AlignmentFlag.AlignCenter, time_label)
        painter.setFont(orig_font)
