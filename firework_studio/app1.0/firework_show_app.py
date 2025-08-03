import sys
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import librosa
from PyQt6.QtCore import QTimer
from matplotlib.backends.backend_qt import NavigationToolbar2QT
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QComboBox, QFileDialog, QColorDialog
)
import librosa.display

from fireworks_canvas import FireworksCanvas
from fireworks_preview import FireworkPreviewWidget
from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPolygonItem
from PyQt6.QtGui import QBrush, QPen, QColor, QPolygonF
from PyQt6.QtCore import QPointF
import random
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QLinearGradient, QBrush
from PyQt6.QtGui import QPolygonF
from PyQt6.QtWidgets import QSizePolicy
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtCore import QTimer

class ToastDialog(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""
            QDialog {
            background-color: rgba(40, 40, 40, 220);
            border-radius: 10px;
            }
            QLabel {
            color: #fff;
            padding: 12px 24px;
            font-size: 16px;
            }
        """)
        layout = QVBoxLayout(self)
        label = QLabel(message)
        layout.addWidget(label)
        self.adjustSize()

'''THIS IS THE MAIN WINDOW CLASS FOR THE FIREWORK STUDIO APPLICATION'''
class FireworkShowApp(QMainWindow):

    def __init__(self):
        super().__init__()
        # Set dark theme palette for the entire application
        dark_palette = self.palette()
        dark_palette.setColor(self.backgroundRole(), QColor(30, 30, 30))
        dark_palette.setColor(self.foregroundRole(), QColor(220, 220, 220))
        self.setPalette(dark_palette)
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #222;
                color: #fff;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:checked {
                background-color: #444;
            }
            QComboBox, QSlider, QLabel {
                background-color: #222;
                color: #e0e0e0;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView {
                background-color: #222;
                color: #e0e0e0;
            }
            QSlider::groove:horizontal {
                background: #444;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #888;
                border: 1px solid #222;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)
        self.setWindowTitle("Firework Studio")
        self.setGeometry(100, 100, 1800, 1000)

        self.audio_path = None
        self.audio_data = None
        self.sr = None
        self.segment_times = None
        self.periods_info = None
        self.firework_firing = None
        
        ''' Overall UI Elements layout'''
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        ''' Fireworks Show Preview Screen'''
        # Fireworks Show Preview Screen with background support
        fireworks_canvas_container = QWidget()
        # Set a default background color (night sky) for the container
        fireworks_canvas_container.setStyleSheet("background-color: #10101e; border-radius: 8px;")
        fireworks_canvas_layout = QVBoxLayout(fireworks_canvas_container)
        fireworks_canvas_container.setMinimumHeight(435)  # Make the window/canvas taller
        fireworks_canvas_layout.setContentsMargins(0, 0, 0, 0)
        fireworks_canvas_layout.setSpacing(0)
        self.fireworks_canvas = FireworksCanvas()
        fireworks_canvas_layout.addWidget(self.fireworks_canvas)
        layout.addWidget(fireworks_canvas_container, stretch=5)

        # Define these here because it is used in the media playback controls
        self.preview_widget = FireworkPreviewWidget()
        self.preview_widget.setMinimumHeight(150)  # Make the preview widget taller

        ''' Preview firework show button with media playback controls '''
        # Media playback controls layout
        media_controls_layout = QHBoxLayout()
        # Align the media controls layout vertically centered
        media_controls_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        button_style = """
            QPushButton {
            background-color: #2196f3;
            color: #fff;
            border: none;
            border-radius: 7px;
            font-size: 14px;
            font-weight: bold;
            min-width: 60px;
            min-height: 28px;
            padding: 4px 8px;
            }
            QPushButton:hover {
            background-color: #1e88e5;
            }
            QPushButton:pressed {
            background-color: #1565c0;
            }
        """
        # Ensure all three buttons are aligned properly in the media_controls_layout
        media_controls_layout.setSpacing(12)
        media_controls_layout.setContentsMargins(0, 0, 0, 0)
        media_controls_layout.addStretch()
        # Play/Pause button with icon toggle
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setFixedSize(40, 40)
        self.play_pause_btn.setCheckable(True)
        self.play_pause_btn.setText("▶️")
        # Use a blue color that matches the icon style in setText (e.g., #1976d2)
        self.play_pause_btn.setStyleSheet(button_style)
        
        def toggle_icon(checked):
            self.play_pause_btn.setText("⏸️" if checked else "▶️")
            self.preview_widget.toggle_play_pause()
        self.play_pause_btn.toggled.connect(toggle_icon)
        media_controls_layout.addWidget(self.play_pause_btn)

        self.stop_btn = QPushButton("⏹️")
        self.stop_btn.setFixedSize(40, 40)
        self.stop_btn.setStyleSheet(button_style)
        self.stop_btn.clicked.connect(self.preview_widget.stop_preview)
        self.stop_btn.clicked.connect(self.fireworks_canvas.reset_fireworks)
        def reset_play_pause():
            # Only update the button state and icon, do not trigger play
            self.play_pause_btn.blockSignals(True)
            if self.play_pause_btn.isChecked():
                self.play_pause_btn.setChecked(False)
            self.play_pause_btn.setText("▶️")
            self.play_pause_btn.blockSignals(False)
        self.stop_btn.clicked.connect(reset_play_pause)
        media_controls_layout.addWidget(self.stop_btn)

        self.add_firing_btn = QPushButton("Add Firing")
        self.add_firing_btn.setStyleSheet(button_style)
        self.add_firing_btn.clicked.connect(lambda: self.preview_widget.add_time(1))
        media_controls_layout.addWidget(self.add_firing_btn)

        # Clear show button (styled to match Add Firing)
        # Also pause the show if playing
        def clear_show():
            self.fireworks_canvas.reset_fireworks()
            self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, None)
            self.preview_widget.stop_preview()
            # Always reset play/pause button state and icon so playback can start again
            self.play_pause_btn.blockSignals(True)
            self.play_pause_btn.setChecked(False)
            self.play_pause_btn.setText("▶️")
            self.play_pause_btn.blockSignals(False)
        self.clear_btn = QPushButton("Clear Show")
        self.clear_btn.setStyleSheet(button_style)
        self.clear_btn.clicked.connect(clear_show)
        def show_cleared_toast():
            toast = ToastDialog("Show cleared!", parent=self)
            geo = self.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)
        self.clear_btn.clicked.connect(show_cleared_toast)
        media_controls_layout.addWidget(self.clear_btn)

        # Ensure all media control buttons are perfectly aligned horizontally
        # by setting a fixed height for all buttons and aligning them to the center
        button_height = 40
    
        self.play_pause_btn.setFixedSize(40, button_height)
        self.stop_btn.setFixedSize(40, button_height)
        self.add_firing_btn.setFixedHeight(button_height)
        self.clear_btn.setFixedHeight(button_height)
        # Set the size policy to ensure vertical alignment
        for btn in [self.play_pause_btn, self.stop_btn, self.add_firing_btn, self.clear_btn]:
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # Current time display label

        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 18px;
                font-weight: bold;
                min-width: 60px;
                qproperty-alignment: 'AlignVCenter | AlignLeft';
            }
        """)
        self.current_time_label.setFixedWidth(70)

        # Place the label at the left of the media controls
        media_controls_layout.insertWidget(0, self.current_time_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Update current_time_label whenever playback time changes

        def update_time_label():
            if hasattr(self.preview_widget, "current_time"):
                t = int(self.preview_widget.current_time)
                mins, secs = divmod(t, 60)
                self.current_time_label.setText(f"{mins:02d}:{secs:02d}")
            else:
                self.current_time_label.setText("00:00")

        # Timer to update the label during playback
        self.time_update_timer = QTimer(self)
        self.time_update_timer.setInterval(200)  # update every 200 ms
        self.time_update_timer.timeout.connect(update_time_label)

        def on_play_pause(checked):
            update_time_label()
            if checked:
                self.time_update_timer.start()
            else:
                self.time_update_timer.stop()

        self.play_pause_btn.toggled.connect(on_play_pause)
        self.stop_btn.clicked.connect(lambda: (self.current_time_label.setText("00:00"), self.time_update_timer.stop()))
        ''' Load Audio Button '''
        self.load_btn = QPushButton("Load Audio")
        self.load_btn.clicked.connect(self.load_audio)
        media_controls_layout.addWidget(self.load_btn)
        self.info_label = QLabel("No audio loaded.")
        layout.addWidget(self.info_label)

        ''' Fireworks show generator button'''
        # This button also resets the show (like stop_btn) before generating
        def generate_and_reset():
            self.fireworks_canvas.reset_fireworks()
            self.preview_widget.stop_preview()
            # Always reset play/pause button state and icon so playback can start again
            self.play_pause_btn.blockSignals(True)
            self.play_pause_btn.setChecked(False)
            self.play_pause_btn.setText("▶️")
            self.play_pause_btn.blockSignals(False)
            self.generate_btn.setText("Generating show...")
            QApplication.processEvents()
            self.update_preview_widget()
            self.generate_btn.setText("Generate Fireworks Show")

        self.generate_btn = QPushButton("Generate Fireworks Show")
        self.info_label.setText("Load audio to generate fireworks show.")
        self.generate_btn.clicked.connect(generate_and_reset)
        media_controls_layout.addWidget(self.generate_btn)
        layout.addLayout(media_controls_layout)

        ''' Canvas for waveform display and firework firing display '''
        self.waveform_canvas = FigureCanvas(Figure(figsize=(20, 1)))
        ax = self.waveform_canvas.figure.subplots()
        ax.set_facecolor('black')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        ax.set_title("Waveform with Segments", color='white')
        self.waveform_canvas.setFixedHeight(150)
        self.waveform_canvas.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
        layout.addWidget(self.waveform_canvas)

        layout.addWidget(self.preview_widget)

    def load_audio(self):
        """Load one or more audio files, concatenate, and update waveform display."""
        # Reset segments and firework firings when loading new audio
        self.segment_times = None
        self.firework_firing = None
        self.fireworks_canvas.reset_fireworks()
        file_dialog = QFileDialog()
        paths, _ = file_dialog.getOpenFileNames(self, "Open Audio File(s)", "", "Audio Files (*.wav *.mp3 *.ogg)")
        if paths:
            self.info_label.setText(f"Loading audio from: {', '.join(paths)}")
            QApplication.processEvents()
            self.audio_datas = []
            sr = None
            for path in paths:
                y, s = librosa.load(path, sr=None)
                if sr is None:
                    sr = s
                elif sr != s:
                    # Resample to first file's sample rate
                    y = librosa.resample(y, orig_sr=s, target_sr=sr)
                self.audio_datas.append(y)
            self.audio_data = np.concatenate(self.audio_datas)
            self.sr = sr
            self.audio_path = paths[0] if len(paths) == 1 else None  # Only keep path if single file

            self.plot_waveform()  # Draw waveform as soon as audio is loaded

            duration = librosa.get_duration(y=self.audio_data, sr=self.sr)
            self.info_label.setText("")
            toast = ToastDialog(
                f"Loaded: {len(paths)} file(s)\nSample Rate: {self.sr} Hz, Duration: {duration:.2f} seconds",
                parent=self
            )
            # Position at bottom right of main window
            geo = self.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(7500, toast.close)
            self.waveform_canvas.figure.patch.set_facecolor('black')
            ax = self.waveform_canvas.figure.axes[0]
            ax.set_facecolor('black')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, self.firework_firing)

    def update_preview_widget(self):
        self.periods_info, self.segment_times = self.make_segments(self.sr)
        self.firework_firing = self.simple_beatsample(self.audio_data, self.sr, self.segment_times)
        self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, self.firework_firing)
        # Show a small dialog box at the bottom right that pops up then goes away

        toast = ToastDialog(
            f"Show generated!\nSegments: {len(self.segment_times)-1}, Firework firings: {len(self.firework_firing)}",
            parent=self
        )
        # Position at bottom right of main window
        geo = self.geometry()
        x = geo.x() + geo.width() - toast.width() - 40
        y = geo.y() + geo.height() - toast.height() - 40
        toast.move(x, y)
        toast.show()
        QTimer.singleShot(7500, toast.close)

    def plot_waveform(self):
        # Enable interactive zooming/panning for the waveform canvas
        self.waveform_canvas.figure.clear()
        self.waveform_canvas.figure.subplots()
        self.waveform_canvas.figure.tight_layout()
        self.waveform_canvas.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.waveform_canvas.setFocus()

        # Enable matplotlib's built-in navigation toolbar for zoom/pan
        # Add a compact, dark-themed navigation toolbar above the waveform
        if not hasattr(self, 'waveform_toolbar'):
            self.waveform_toolbar = NavigationToolbar2QT(self.waveform_canvas, self)
            self.waveform_toolbar.setStyleSheet("""
            QToolBar {
                background: #181818;
                border: none;
                spacing: 2px;
                padding: 2px 4px;
                min-height: 28px;
                max-height: 28px;
            }
            QToolButton {
                background: transparent;
                color: #e0e0e0;
                border: none;
                margin: 0 2px;
                padding: 2px;
                min-width: 22px;
                min-height: 22px;
            }
            QToolButton:checked, QToolButton:pressed {
                background: #222;
            }
            """)
            self.waveform_toolbar.setIconSize(self.waveform_toolbar.iconSize().scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio))
            parent_layout = self.centralWidget().layout()
            idx = parent_layout.indexOf(self.waveform_canvas)
            parent_layout.insertWidget(idx, self.waveform_toolbar)
            ax = self.waveform_canvas.figure.axes[0]
            ax.set_xticks([])
            ax.set_yticks([])
        self.waveform_canvas.setFixedHeight(150)  # Increase height for better visibility
        ax = self.waveform_canvas.figure.subplots()
        ax.clear()
        ax.set_frame_on(False)
        # Make axes occupy the full canvas area, removing all padding/margins
        ax.set_position((0.0, 0.0, 1.0, 1.0))
        if self.audio_data is not None:
            sr = self.sr if self.sr is not None else 22050  # Default librosa sample rate
            librosa.display.waveshow(self.audio_data, sr=sr, ax=ax, alpha=0.5)
            ax.set_facecolor('black')
            ax.set_xticks([])
            ax.set_yticks([])
        # Ensure all spines are invisible (removes white edge)
        for spine in ax.spines.values():
            spine.set_visible(False)
        # Plot segments
        if self.segment_times is not None:
            for i, t in enumerate(self.segment_times):
                ax.axvline(t, color='orange', linestyle='--', alpha=0.7)
        ax.set_title("Waveform with Segments")
        # Fit x-axis to audio duration
        sr = float(self.sr) if self.sr is not None else 22050.0  # Default librosa sample rate as float
        duration = librosa.get_duration(y=self.audio_data, sr=sr)
        ax.set_xlim((0, duration))
        self.waveform_canvas.draw()

    def preview_show(self):
        if self.audio_data is not None and self.firework_firing is not None:
            self.preview_widget.start_preview()

    def make_segments(self,sr):
        # Make segments for each entry in self.audio_datas, then concatenate
        all_periods_info = []
        all_segment_times = []
        offset = 0.0
        for idx, y in enumerate(self.audio_datas):
            # Compute self-similarity matrix using chroma features
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            recurrence = librosa.segment.recurrence_matrix(chroma, mode='affinity', sym=True)
            # Segment the song using agglomerative clustering
            segments = librosa.segment.agglomerative(recurrence, k=8)
            segment_times = librosa.frames_to_time(segments, sr=sr)
            # Offset segment times by the current offset (total duration so far)
            segment_times_offset = segment_times + offset
            # Organize information in a dictionary
            for i in range(len(segment_times_offset) - 1):
                start_min, start_sec = divmod(int(segment_times_offset[i]), 60)
                end_min, end_sec = divmod(int(segment_times_offset[i+1]), 60)
                all_periods_info.append({
                    'start': f"{start_min:02d}:{start_sec:02d}",
                    'end': f"{end_min:02d}:{end_sec:02d}",
                    'segment_id': len(all_periods_info)
                })
            # Add segment times (except last, to avoid duplicate at joins)
            if idx == 0:
                all_segment_times.extend(segment_times_offset)
            else:
                all_segment_times.extend(segment_times_offset[1:])
            # Update offset for next song
            offset += librosa.get_duration(y=y, sr=sr)
        # periods_info now contains all detected similar periods with start/end times
        return all_periods_info, np.array(all_segment_times)

    def simple_beatsample(self, audio_data, sr, segment_times):
        # Calculate beat times in seconds
        _, beats = librosa.beat.beat_track(y=audio_data, sr=sr)
        beat_times = librosa.frames_to_time(beats, sr=sr)

        beat_interval = 5  # target seconds between sampled beats
        cluster_window = 2 # seconds for clustering

        # Sample beats: start with first beat in each segment, then add clustered beats within cluster_window
        firework_firing = []
        for i in range(len(segment_times) - 1):
            seg_start = segment_times[i]
            seg_end = segment_times[i + 1]
            beats_in_seg = beat_times[(beat_times >= seg_start) & (beat_times < seg_end)]
            if len(beats_in_seg) > 0:
                # Sample every ~beat_interval seconds
                last_time = seg_start
                for bt in beats_in_seg:
                    if bt - last_time >= beat_interval or len(firework_firing) == 0:
                        firework_firing.append(bt)
                        last_time = bt
                # Add clustered beats within cluster_window near segment center
                seg_center = (seg_start + seg_end) / 2
                clustered = beats_in_seg[(np.abs(beats_in_seg - seg_center) < cluster_window)]
                for bt in clustered:
                    if bt not in firework_firing:
                        firework_firing.append(bt)
        firework_firing = np.sort(np.array(firework_firing))
        return firework_firing
