import sys
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import librosa

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QComboBox, QFileDialog, QColorDialog
)
import librosa.display

from fireworks_canvas import FireworksCanvas
from fireworks_preview import FireworkPreviewWidget

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
        
        ''' Load Audio Button '''
        self.load_btn = QPushButton("Load Audio")
        self.load_btn.clicked.connect(self.load_audio)
        layout.addWidget(self.load_btn)
        self.info_label = QLabel("No audio loaded.")
        layout.addWidget(self.info_label)

        ''' Fireworks show generator button'''
        self.generate_btn = QPushButton("Generate Fireworks Show")
        self.info_label.setText("Click to generate fireworks show based on audio.")
        def on_generate_clicked():
            self.generate_btn.setText("Generating show...")
            QApplication.processEvents()
            self.update_preview_widget()
            self.generate_btn.setText("Generate Fireworks Show")
        self.generate_btn.clicked.connect(on_generate_clicked)
        layout.addWidget(self.generate_btn)

        ''' Fireworks Show Preview Screen'''
        fireworks_canvas_container = QWidget()
        fireworks_canvas_layout = QVBoxLayout(fireworks_canvas_container)
        fireworks_canvas_container.setMinimumHeight(425)  # Make the window/canvas taller
        fireworks_canvas_layout.setContentsMargins(0, 0, 0, 0)
        fireworks_canvas_layout.setSpacing(0)
        self.fireworks_canvas = FireworksCanvas()
        fireworks_canvas_layout.addWidget(self.fireworks_canvas)
        layout.addWidget(fireworks_canvas_container, stretch=5, )

        # Create controls
        controls_layout = QHBoxLayout()
        # Color picker button
        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.choose_color)
        controls_layout.addWidget(self.color_button)
        # Pattern selector
        pattern_label = QLabel("Pattern:")
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems(["Random", "Circle", "Heart", "Text"])
        self.pattern_combo.currentTextChanged.connect(self.update_pattern)
        controls_layout.addWidget(pattern_label)
        controls_layout.addWidget(self.pattern_combo)
        # Background selector
        background_label = QLabel("Background:")
        self.background_combo = QComboBox()
        self.background_combo.addItems(["Night Sky", "Cityscape", "Mountains"])
        self.background_combo.currentTextChanged.connect(self.update_background)
        controls_layout.addWidget(background_label)
        controls_layout.addWidget(self.background_combo)
        layout.addLayout(controls_layout)
        
        # Define these here because it is used in the media playback controls
        self.preview_widget = FireworkPreviewWidget()
        self.preview_widget.setMinimumHeight(150)  # Make the preview widget taller

        ''' Preview firework show button (needs to be updated with media playback controls) '''
        # Media playback controls layout
        media_controls_layout = QHBoxLayout()
        button_style = """
            QPushButton {
            background-color: #1976d2;
            color: #fff;
            border: none;
            border-radius: 8px;
            padding: 8px 18px;
            font-size: 16px;
            font-weight: bold;
            margin: 0 6px;
            min-width: 90px;
            min-height: 36px;
            }
            QPushButton:hover {
            background-color: #1565c0;
            }
            QPushButton:pressed {
            background-color: #0d47a1;
            }
        """

        # Play/Pause button with icon toggle
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setFixedSize(40, 40)
        self.play_pause_btn.setCheckable(True)
        self.play_pause_btn.setText("▶️")
        # Use a blue color that matches the icon style in setText (e.g., #1976d2)
        self.play_pause_btn.setStyleSheet(
            """
            font-size: 20px;
            border-radius: 20px;
            background-color: #2196f3;
            color: white;
            """
        )
        
        def toggle_icon(checked):
            self.play_pause_btn.setText("⏸️" if checked else "▶️")
            self.preview_widget.toggle_play_pause()
        self.play_pause_btn.toggled.connect(toggle_icon)
        media_controls_layout.addWidget(self.play_pause_btn)

        self.stop_btn = QPushButton("⏹️")
        self.stop_btn.setFixedSize(40, 40)
        self.stop_btn.setStyleSheet(
            """
            font-size: 20px;
            border-radius: 20px;
            background-color: #2196f3;
            color: white;
            """
        )
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
        layout.addWidget(self.waveform_canvas)

        layout.addWidget(self.preview_widget)

    def load_audio(self):
        file_dialog = QFileDialog()
        path, _ = file_dialog.getOpenFileName(self, "Open Audio File", "", "Audio Files (*.wav *.mp3 *.ogg)")
        if path:
            self.info_label.setText(f"Loading audio from: {path}")
            self.audio_path = path

            # Load audio in a way that allows UI to update
            QApplication.processEvents()
            self.audio_data, self.sr = librosa.load(path)
            self.plot_waveform()  # Draw waveform as soon as audio is loaded

            self.info_label.setText(
                f"Loaded: {path}\nSample Rate: {self.sr} Hz, Duration: {librosa.get_duration(y=self.audio_data, sr=self.sr):.2f} seconds"
            )
            self.waveform_canvas.figure.patch.set_facecolor('black')
            ax = self.waveform_canvas.figure.axes[0]
            ax.set_facecolor('black')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, self.firework_firing)

    def update_preview_widget(self):
        self.periods_info, self.segment_times = self.make_segments(self.audio_path)
        self.firework_firing = self.simple_beatsample(self.audio_data, self.sr, self.segment_times)
        self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, self.firework_firing)
        self.info_label.setText(
            f"Show generated!\nSegments: {len(self.segment_times)-1}, Firework firings: {len(self.firework_firing)}"
        )

    def plot_waveform(self):
        self.waveform_canvas.setFixedHeight(150)  # Increase height for better visibility
        ax = self.waveform_canvas.figure.subplots()
        ax.clear()
        # Remove all spines and ticks for a seamless look
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_frame_on(False)
        # Make axes occupy the full canvas area, removing all padding/margins
        ax.set_position((0.0, 0.0, 1.0, 1.0))
        if self.audio_data is not None:
            sr = self.sr if self.sr is not None else 22050  # Default librosa sample rate
            librosa.display.waveshow(self.audio_data, sr=sr, ax=ax, alpha=0.5)
        # Ensure all spines are invisible (removes white edge)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.tick_params(axis='x', colors='white', length=0)
        ax.tick_params(axis='y', colors='white', length=0)
        ax.title.set_color('white')
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

    def make_segments(self, path):
        # Use librosa to detect similar periods (repeating patterns) in the song
        y, sr = librosa.load(path)
        # Compute self-similarity matrix using chroma features
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        recurrence = librosa.segment.recurrence_matrix(chroma, mode='affinity', sym=True)

        # Segment the song using agglomerative clustering
        segments = librosa.segment.agglomerative(recurrence, k=8)  # k is the number of segments, adjust as needed

        # Get segment boundaries in time
        segment_times = librosa.frames_to_time(segments, sr=sr)

        # Organize information in a dictionary
        periods_info = []
        for i in range(len(segment_times) - 1):
            start_min, start_sec = divmod(int(segment_times[i]), 60)
            end_min, end_sec = divmod(int(segment_times[i+1]), 60)
            periods_info.append({
                'start': f"{start_min:02d}:{start_sec:02d}",
                'end': f"{end_min:02d}:{end_sec:02d}",
                'segment_id': i
            })

        # periods_info now contains all detected similar periods with start/end times
        return periods_info, segment_times
    
    def update_particle_count(self, value):
        self.fireworks_canvas.particle_count = value

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.fireworks_canvas.firework_color = color

    def update_pattern(self, pattern):
        self.fireworks_canvas.pattern = pattern
        # Pattern implementation will be added later

    def update_background(self, background):
        self.fireworks_canvas.background = background
        # Background implementation will be added later
    
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
