# firework_show_app.py
# This is the main application file for the Firework Studio, which includes the main window and
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QSizePolicy, QDialog
)

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt import NavigationToolbar2QT
import librosa
import librosa.display

from fireworks_canvas import FireworksCanvas
from fireworks_preview import FireworkPreviewWidget
from PyQt6.QtWidgets import QFrame
import os
from PyQt6.QtCore import QPropertyAnimation

class SimpleBeatSampleThread(QThread):
        finished = pyqtSignal(object)

        def __init__(self, audio_data, sr, segment_times):
            super().__init__()
            self.audio_data = audio_data
            self.sr = sr
            self.segment_times = segment_times

        def run(self):
            _, beats = librosa.beat.beat_track(y=self.audio_data, sr=self.sr)
            beat_times = librosa.frames_to_time(beats, sr=self.sr)

            beat_interval = 5  # target seconds between sampled beats
            cluster_window = 2 # seconds for clustering

            firework_firing = []
            for i in range(len(self.segment_times) - 1):
                seg_start = self.segment_times[i]
                seg_end = self.segment_times[i + 1]
                beats_in_seg = beat_times[(beat_times >= seg_start) & (beat_times < seg_end)]
                if len(beats_in_seg) > 0:
                    last_time = seg_start
                    for bt in beats_in_seg:
                        if bt - last_time >= beat_interval or len(firework_firing) == 0:
                            firework_firing.append(bt)
                            last_time = bt
                    seg_center = (seg_start + seg_end) / 2
                    clustered = beats_in_seg[(np.abs(beats_in_seg - seg_center) < cluster_window)]
                    for bt in clustered:
                        if bt not in firework_firing:
                            firework_firing.append(bt)
            firework_firing = np.sort(np.array(firework_firing))
            self.finished.emit(firework_firing)
            
class ToastDialog(QDialog):
    # ToastDialog: A frameless, styled dialog for displaying temporary toast notifications.
    """
    ToastDialog is a custom QDialog subclass that displays a temporary, styled notification ("toast") 
    in a PyQt application. Toasts are stacked vertically in the bottom-right corner of the parent window 
    and automatically manage their position to avoid overlap.
    Attributes:
        _active_toasts (list): Class-level list tracking currently active ToastDialog instances.
    Args:
        message (str): The message to display in the toast.
        parent (QWidget, optional): The parent widget for the dialog.
    Methods:
        show():
            Displays the toast dialog, stacking it with other visible toasts in the bottom-right 
            corner of the parent window.
        closeEvent(event):
            Handles the dialog close event and removes the toast from the active toasts list.
    """
    _active_toasts = []

    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setStyleSheet("""
            QDialog {
            background-color: rgb(40, 40, 40);
            border-radius: 14px;
            min-width: 320px;
            min-height: 80px;
            }
            QLabel {
            color: #fff;
            padding: 18px 32px;
            font-size: 20px;
            }
        """)
        layout = QVBoxLayout(self)
        label = QLabel(message)
        layout.addWidget(label)
        self.adjustSize()
        ToastDialog._active_toasts.append(self)

    def show(self):
        # Stack toasts vertically so they don't overlap
        parent = self.parentWidget()
        if parent:
            geo = parent.geometry()
            margin = 40
            spacing = 12
            width = self.width()
            height = self.height()
            # Only consider visible toasts
            visible_toasts = [t for t in ToastDialog._active_toasts if t.isVisible()]
            idx = len(visible_toasts)
            x = geo.x() + geo.width() - width - margin
            y = geo.y() + geo.height() - height - margin - (idx * (height + spacing))
            self.move(x, y)
            # Fade out the previous toast if any
            if visible_toasts:
                prev_toast = visible_toasts[-1]
                if prev_toast is not self:
                    # Use QPropertyAnimation for fade out
                    prev_toast.setWindowOpacity(1.0)
                    anim = QPropertyAnimation(prev_toast, b"windowOpacity")
                    anim.setDuration(350)
                    anim.setStartValue(1.0)
                    anim.setEndValue(0.0)
                    # Ensure the toast closes after fade
                    def close_prev():
                        prev_toast.close()
                        anim.deleteLater()
                    anim.finished.connect(close_prev)
                    anim.start()
                    prev_toast._fade_anim = anim  # Prevent garbage collection
        super().show()

    def closeEvent(self, event):
        if self in ToastDialog._active_toasts:
            ToastDialog._active_toasts.remove(self)
        super().closeEvent(event)

class AudioLoaderThread(QThread):
    audio_loaded = pyqtSignal(list, int)

    def __init__(self, paths):
        super().__init__()
        self.paths = paths

    def run(self):
        audio_datas = []
        sr = None
        for path in self.paths:
            y, s = librosa.load(path, sr=None)
            if sr is None:
                sr = s
            elif sr != s:
                y = librosa.resample(y, orig_sr=s, target_sr=sr)
            audio_datas.append(y)
        self.audio_loaded.emit(audio_datas, sr)

class SegmenterThread(QThread):
    segments_ready = pyqtSignal(list, object)

    def __init__(self, audio_datas, sr):
        super().__init__()
        self.audio_datas = audio_datas
        self.sr = sr

    def run(self):
        all_periods_info = []
        all_segment_times = []
        offset = 0.0
        for idx, y in enumerate(self.audio_datas):
            chroma = librosa.feature.chroma_cqt(y=y, sr=self.sr)
            recurrence = librosa.segment.recurrence_matrix(chroma, mode='affinity', sym=True)
            segments = librosa.segment.agglomerative(recurrence, k=8)
            segment_times = librosa.frames_to_time(segments, sr=self.sr)
            segment_times_offset = segment_times + offset
            for i in range(len(segment_times_offset) - 1):
                start_min, start_sec = divmod(int(segment_times_offset[i]), 60)
                end_min, end_sec = divmod(int(segment_times_offset[i+1]), 60)
                all_periods_info.append({
                    'start': f"{start_min:02d}:{start_sec:02d}",
                    'end': f"{end_min:02d}:{end_sec:02d}",
                    'segment_id': len(all_periods_info)
                })
            if idx == 0:
                all_segment_times.extend(segment_times_offset)
            else:
                all_segment_times.extend(segment_times_offset[1:])
            offset += librosa.get_duration(y=y, sr=self.sr)
        self.segments_ready.emit(all_periods_info, np.array(all_segment_times))

'''THIS IS THE MAIN WINDOW CLASS FOR THE FIREWORK STUDIO APPLICATION'''
class FireworkShowApp(QMainWindow):
    def __init__(self):
        super().__init__()
        ###########################################################
        #                                                          #
        #        Set dark theme palette and styles for the app     #
        #                                                          #
        ###########################################################
        dark_palette = self.palette()
        dark_palette.setColor(self.backgroundRole(), QColor(30, 30, 30))
        dark_palette.setColor(self.foregroundRole(), QColor(220, 220, 220))
        self.setPalette(dark_palette)
        self.setStyleSheet("""
            QMainWindow, QWidget {
            background: #23232b;
            color: #e0e0e0;
            }
            QPushButton {
            background: #2a2a38;
            color: #fff;
            border-radius: 6px;
            padding: 6px 12px;
            }
            QPushButton:checked {
            background: #3a3a4a;
            }
            QLabel {
            color: #e0e0e0;
            background: transparent;
            }
        """)

        ############################################################
        #                                                          #
        #        Initialize the main window properties             #
        #                                                          #
        ############################################################
        self.setWindowTitle("Firework Studio")
        self.setGeometry(100, 100, 1800, 1000)
        self.audio_path = None
        self.audio_data = None
        self.sr = None
        self.segment_times = None
        self.periods_info = None
        self.firework_firing = None
        
        #############################################################
        #                                                          #
        #        Overall UI Elements layout                         #
        #                                                          #
        #############################################################
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        #############################################################
        #                                                          #
        #        Fireworks Show Preview Screen                     #
        #                                                          #
        #############################################################
        fireworks_canvas_container = QWidget()
        fireworks_canvas_layout = QVBoxLayout(fireworks_canvas_container)
        fireworks_canvas_container.setMinimumHeight(435)  # Make the window/canvas taller
        fireworks_canvas_layout.setContentsMargins(0, 0, 0, 0)
        fireworks_canvas_layout.setSpacing(0)
        self.fireworks_canvas = FireworksCanvas()
        fireworks_canvas_layout.addWidget(self.fireworks_canvas)
        layout.addWidget(fireworks_canvas_container, stretch=5)

        # Define these here because it is used in the media playback controls
        # but these are used in the FireworkPreviewWidget
        self.preview_widget = FireworkPreviewWidget()
        self.preview_widget.setMinimumHeight(150)  # Make the preview widget taller

        ############################################################
        #                                                          #
        #        Media playback controls                           #
        #                                                          #                                                        
        ############################################################
        media_controls_layout = QHBoxLayout()
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

        ###############################################
        #                                             #
        #        Play/Pause button                    #
        #                                             #
        ###############################################
        self.play_pause_btn.setStyleSheet(button_style)
        def toggle_icon(checked):
            # Use a more standard pause icon (two vertical bars)
            self.play_pause_btn.setText("⏸️" if checked else "▶️")
            self.preview_widget.toggle_play_pause()
        self.play_pause_btn.toggled.connect(toggle_icon)
        media_controls_layout.addWidget(self.play_pause_btn)

        ###########################################
        #                                         #
        #        Stop button                      #
        #                                         #
        ###########################################
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

        ###############################################
        #                                             #
        #        Add Firing button                    #
        #                                             #
        ###############################################
        self.add_firing_btn = QPushButton("Add Firing")
        self.add_firing_btn.setStyleSheet(button_style)
        self.add_firing_btn.clicked.connect(lambda: self.preview_widget.add_time(1))
        media_controls_layout.addWidget(self.add_firing_btn)

        ###########################################################
        #                                                         #
        #    Clear show button (styled to match Add Firing)       #
        #                                                         #
        ###########################################################
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

        ###########################################################
        #                                                         #
        #             Media control buttons alignment             #
        #                                                         #
        ###########################################################
        # setting a fixed height for all buttons and aligning them to the center
        button_height = 40
        self.play_pause_btn.setFixedSize(40, button_height)
        self.stop_btn.setFixedSize(40, button_height)
        self.add_firing_btn.setFixedHeight(button_height)
        self.clear_btn.setFixedHeight(button_height)
        # Set the size policy to ensure vertical alignment
        for btn in [self.play_pause_btn, self.stop_btn, self.add_firing_btn, self.clear_btn]:
            btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        ###########################################################
        #                                                         #
        #              Current time display label                 #
        #                                                         #
        ###########################################################
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

        # Add info label to the right of the current_time_label, separated by a vertical line
        vline = QFrame()
        vline.setFrameShape(QFrame.Shape.VLine)
        vline.setFrameShadow(QFrame.Shadow.Sunken)
        vline.setStyleSheet("color: #444; background: #444; min-width: 2px;")
        media_controls_layout.insertWidget(1, vline, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.info_label = QLabel("No audio loaded.")
        self.info_label.setStyleSheet("color: #b0b0b0; font-size: 15px; padding-left: 12px;")
        media_controls_layout.insertWidget(2, self.info_label, alignment=Qt.AlignmentFlag.AlignVCenter)
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

        ###########################################################
        #                                                         #
        #              Load Audio Button                          #
        #                                                         #
        ###########################################################
        self.load_btn = QPushButton("Load Audio")
        self.load_btn.clicked.connect(self.load_audio)
        media_controls_layout.addWidget(self.load_btn)

        ###########################################################
        #                                                         #
        #              Fireworks show generator button            #
        #                                                         #
        ###########################################################
        # This button also resets the (like thestop_btn) before generating
        def generate_and_reset():
            self.fireworks_canvas.reset_fireworks()
            self.preview_widget.stop_preview()
            # Always reset play/pause button state and icon so playback can start again
            self.play_pause_btn.blockSignals(True)
            self.play_pause_btn.setChecked(False)
            self.play_pause_btn.setText("▶️")
            self.play_pause_btn.blockSignals(False)
            # Show "Generating show..." toast persistently until generation is done
            self.generating_toast = ToastDialog("Generating show...", parent=self) # type: ignore
            geo = self.geometry()
            x = geo.x() + geo.width() - self.generating_toast.width() - 40 # type: ignore
            y = geo.y() + geo.height() - self.generating_toast.height() - 40 # type: ignore
            self.generating_toast.move(x, y) # type: ignore
            self.generating_toast.show() # type: ignore
            QApplication.processEvents()
            self.update_preview_widget()
            self.generate_btn.setText("Generate Fireworks Show")

        self.generate_btn = QPushButton("Generate Fireworks Show")
        self.info_label.setText("Load audio to generate fireworks show.")
        self.generate_btn.clicked.connect(generate_and_reset)
        media_controls_layout.addWidget(self.generate_btn)
        layout.addLayout(media_controls_layout)

        ###########################################################
        #                                                         #
        # Canvas for waveform display and firework firing display #
        #                                                         #
        ###########################################################
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
        
    ###############################################################
    #                                                             #
    #  HELPER FUNCTIONS for loading audio and segmenting it       #
    #                                                             #
    ###############################################################
    # Use a worker thread for loading audio and segmenting to keep UI responsive
    def load_audio(self):
        self.segment_times = None
        self.firework_firing = None
        self.fireworks_canvas.reset_fireworks()
        file_dialog = QFileDialog()
        paths, _ = file_dialog.getOpenFileNames(self, "Open Audio File(s)", "", "Audio Files (*.wav *.mp3 *.ogg)")
        if paths:
            filenames = [os.path.basename(p) for p in paths]
            self.info_label.setText(f"Loading audio from: {', '.join(filenames)}")
            QApplication.processEvents()
            self.audio_loader_thread = AudioLoaderThread(paths)
            self.audio_loader_thread.audio_loaded.connect(self.on_audio_loaded)
            self.audio_loader_thread.start()
    
    def on_audio_loaded(self, audio_datas, sr):
        self.audio_datas = audio_datas
        self.audio_data = np.concatenate(self.audio_datas)
        self.sr = sr
        self.audio_path = None if len(self.audio_datas) > 1 else None
        self.plot_waveform()
        duration = librosa.get_duration(y=self.audio_data, sr=self.sr)
        self.info_label.setText("")
        filenames = [os.path.basename(p) for p in getattr(self.audio_loader_thread, 'paths', [])]
        toast = ToastDialog(
            f"Loaded: {', '.join(filenames)}\nSample Rate: {self.sr} Hz, Duration: {duration:.2f} seconds",
            parent=self
        )
        geo = self.geometry()
        x = geo.x() + geo.width() - toast.width() - 40
        y = geo.y() + geo.height() - toast.height() - 40
        toast.move(x, y)
        toast.show()
        QTimer.singleShot(7500, toast.close)
        self.waveform_canvas.figure.patch.set_facecolor('black')
        ax = self.waveform_canvas.figure.axes[0]
        ax.set_facecolor('black')
        self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, self.firework_firing)

    # Override make_segments to use the worker thread
    def make_segments(self, sr):
        # Start segmenter thread and return after segments_ready signal
        self.segmenter_thread = SegmenterThread(self.audio_datas, sr)
        result = {}

        def on_segments_ready(periods_info, segment_times):
            result['periods_info'] = periods_info
            result['segment_times'] = segment_times

        self.segmenter_thread.segments_ready.connect(on_segments_ready)
        self.segmenter_thread.start()
        self.segmenter_thread.wait()
        return result.get('periods_info', []), result.get('segment_times', None)
   
    def update_preview_widget(self):
        # Run segmentation and beat sampling in background threads to keep UI responsive
        def on_segments_ready(periods_info, segment_times):
            self.periods_info = periods_info
            self.segment_times = segment_times

            def on_beats_ready(firework_firing):
                self.firework_firing = firework_firing
                self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, self.firework_firing)
                num_segments = len(self.segment_times) - 1 if self.segment_times is not None else 0
                num_firings = len(self.firework_firing) if self.firework_firing is not None else 0
                toast = ToastDialog(
                    f"Show generated!\nSegments: {num_segments}, Firework firings: {num_firings}",
                    parent=self
                )
                geo = self.geometry()
                x = geo.x() + geo.width() - toast.width() - 40
                y = geo.y() + geo.height() - toast.height() - 40
                toast.move(x, y)
                toast.show()
                QTimer.singleShot(7500, toast.close)
                # Remove reference to thread after finished
                if hasattr(self, "_running_threads"):
                    self._running_threads.remove(thread) # type: ignore

            # Start beat sampling in background
            if not hasattr(self, "_running_threads"):
                self._running_threads = [] # type: ignore
            thread = SimpleBeatSampleThread(self.audio_data, self.sr, self.segment_times)
            thread.finished.connect(on_beats_ready)
            self._running_threads.append(thread) # type: ignore
            thread.start()

        # Start segmentation in background
        self.segmenter_thread = SegmenterThread(self.audio_datas, self.sr)
        self.segmenter_thread.segments_ready.connect(on_segments_ready)
        self.segmenter_thread.start()

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
            central_widget = self.centralWidget()
            if central_widget is not None:
                parent_layout = central_widget.layout()
                if parent_layout is not None:
                    idx = parent_layout.indexOf(self.waveform_canvas)
                    parent_layout.insertWidget(idx, self.waveform_toolbar) # type: ignore
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

    def simple_beatsample(self, audio_data, sr, segment_times, callback=None):
        # Run beat sampling in a worker thread to keep UI responsive
        if audio_data is None or sr is None or segment_times is None:
            return None
        def on_finished(firework_firing):
            self.firework_firing = firework_firing
            if callback:
                callback(firework_firing)
        thread = SimpleBeatSampleThread(audio_data, sr, segment_times)
        thread.finished.connect(on_finished)
        thread.start()
        # Do not call thread.wait() here; let it run asynchronously
        return None
