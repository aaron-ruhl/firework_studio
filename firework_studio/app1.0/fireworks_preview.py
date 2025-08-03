from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QRect, Qt
from PyQt6.QtGui import QPainter, QColor
import librosa
import sounddevice as sd
import random

'''THIS IS THE BAR CLASS FOR ALONG THE BOTTOM TWO PLOTS'''
class FireworkPreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(200)
        self.audio_data = None
        self.sr = None
        self.segment_times = None
        self.firework_firing = None
        self.preview_timer = None
        self.current_time = 0
        self.duration = 0
        self.resume=False
        self.fireworks_colors = []

    def set_show_data(self, audio_data, sr, segment_times, firework_firing):
        self.audio_data = audio_data
        self.sr = sr
        self.segment_times = segment_times
        self.firework_firing = firework_firing
        self.duration = librosa.get_duration(y=audio_data, sr=sr)
        self.update()

    def start_preview(self):
        if self.audio_data is not None and self.sr is not None:
            sd.stop()
            # Start playback from current_time, not from 0
            sd.play(self.audio_data[int(self.current_time * self.sr):], self.sr, blocking=False)
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
            self.pause_preview()
        else:
            self.start_preview()

    def pause_preview(self):
        if self.preview_timer and self.preview_timer.isActive():
            self.preview_timer.stop()
            self.resume = True
        if sd.get_stream() is not None:
            sd.stop(ignore_errors=True)

    def stop_preview(self):
        if self.preview_timer and self.preview_timer.isActive():
            self.preview_timer.stop()
        self.current_time = 0
        if sd.get_stream() is not None:
            sd.stop(ignore_errors=True)
        self.update()

    def add_time(self, seconds):
        if self.firework_firing is None:
            self.firework_firing = []
        elif not isinstance(self.firework_firing, list):
            self.firework_firing = list(self.firework_firing)
        self.firework_firing.append(self.current_time)
        self.update()

    def advance_preview(self):
        self.current_time += 0.05
        if self.current_time > self.duration:
            if self.preview_timer is not None:
                self.preview_timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(30, 30, 40))
        
        # Remove all padding: draw from edge to edge
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
        if self.segment_times is not None:
            for t in self.segment_times:
                x = left_margin + usable_w * t / self.duration
                painter.setPen(QColor(255, 165, 0))
                painter.drawLine(int(x), timeline_y - 100, int(x), timeline_y + 100)

        # Draw firework firings
        if self.firework_firing is not None:
            if not hasattr(self, 'firework_colors') or len(self.firework_colors) != len(self.firework_firing):
                # Generate and store a random color for each firing
                self.firework_colors = [
                    QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
                    for _ in self.firework_firing
                ]
            for idx, ft in enumerate(self.firework_firing):
                x = left_margin + usable_w * ft / self.duration
                color = self.firework_colors[idx]
                if abs(ft - self.current_time) < 0.1:
                    painter.setBrush(color)
                    painter.setPen(QColor(255, 255, 0))
                    painter.drawEllipse(int(x) - 15, timeline_y - 35, 30, 30)
                else:
                    painter.setBrush(color)
                    painter.setPen(color)
                    painter.drawEllipse(int(x) - 5, timeline_y - 10, 10, 10)

        # Draw playhead
        if self.duration and self.duration > 0:
            playhead_x = left_margin + usable_w * self.current_time / self.duration
            painter.setPen(QColor(0, 255, 0))
            painter.drawLine(int(playhead_x), timeline_y - 40, int(playhead_x), timeline_y + 40)
        w = self.width()
