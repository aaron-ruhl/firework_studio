from PyQt6.QtCore import QRect, QPoint, Qt
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QVector2D, QVector3D, QVector4D
import numpy as np

class FireworkTimelineRenderer:
    def __init__(self, widget):
        self.widget = widget

    def draw(self, painter):
        w, h = self.widget.width(), self.widget.height()
        left_margin = 40
        right_margin = 40
        top_margin = 30
        bottom_margin = 40
        usable_w = w - left_margin - right_margin
        usable_h = h - top_margin - bottom_margin
        timeline_y = top_margin + usable_h // 2

        grad = QColor(25, 28, 40)
        painter.fillRect(self.widget.rect(), grad)

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
            draw_end = widget.duration
            zoom_duration = widget.duration if widget.duration else 1
        return draw_start, draw_end, zoom_duration

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
        t = first_tick
        orig_font = painter.font()
        label_font = orig_font
        label_font = label_font.__class__(label_font)  # Make a copy
        label_font.setPointSizeF(orig_font.pointSizeF() * 0.9)
        painter.setFont(label_font)
        # Use vectorized tick calculation
        tick_times = np.arange(first_tick, draw_end + 1e-6, step)
        for t in tick_times:
            x = left_margin + int((t - draw_start) / span * usable_w)
            painter.drawLine(x, timeline_y + 10, x, timeline_y + 18)
            if widget.duration:
                minutes = int(t // 60)
                seconds = int(t % 60)
                label = f"{minutes}:{seconds:02d}"
                painter.setPen(QColor(200, 200, 220))
                painter.drawText(x - 12, timeline_y + 22, 24, 14, Qt.AlignmentFlag.AlignCenter, label)
                painter.setPen(QColor(150, 150, 170))
        painter.setFont(orig_font)

    def _draw_firing_handles(self, painter, left_margin, usable_w, timeline_y):
        widget = self.widget
        widget.firing_handles = []
        handle_radius = 12
        draw_start, draw_end, zoom_duration = self._get_draw_region()
        if widget.fireworks is not None and widget.duration:
            orig_font = painter.font()
            # Use list comprehensions and vector math for handle positions
            indices = [i for i, fw in enumerate(widget.fireworks) if draw_start <= fw.firing_time <= draw_end]
            xs = [
                left_margin + ((widget.fireworks[i].firing_time - draw_start) / zoom_duration) * usable_w
                for i in indices
            ]
            for idx, x in zip(indices, xs):
                fw = widget.fireworks[idx]
                is_selected = hasattr(widget, 'selected_firing') and widget.selected_firing == idx
                painter.setBrush(fw.firing_color)
                painter.setPen(QColor(255, 255, 0) if is_selected else QColor(220, 220, 220, 180))
                r = int(handle_radius * (1.3 if is_selected else 1))
                painter.drawRoundedRect(int(round(x)) - r, timeline_y - r, 2 * r, 2 * r, 7, 7)
                painter.setPen(QColor(255, 255, 255))
                number_font = orig_font
                number_font = number_font.__class__(number_font)  # Make a copy
                number_font.setBold(True)
                number_font.setPointSizeF(orig_font.pointSizeF() * 1.1)
                painter.setFont(number_font)
                painter.drawText(
                    int(round(x)) - handle_radius,
                    timeline_y - handle_radius + 3,
                    2 * handle_radius,
                    2 * handle_radius,
                    Qt.AlignmentFlag.AlignCenter,
                    str(fw.display_number)
                )
                widget.firing_handles.append((QRect(int(round(x)) - handle_radius, timeline_y - handle_radius + 3, 2 * handle_radius, 2 * handle_radius), idx))
            painter.setFont(orig_font)

    def _draw_playhead(self, painter, left_margin, usable_w, timeline_y):
        widget = self.widget
        draw_start, draw_end, zoom_duration = self._get_draw_region()
        widget.playhead_time = min(max(widget.current_time, 0), widget.duration)
        playhead_x = left_margin + ((widget.playhead_time - draw_start) / zoom_duration) * usable_w
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
