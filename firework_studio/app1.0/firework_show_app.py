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

from beat_thread import SimpleBeatSampleThread
from segment_thread import SegmenterThread
from load_thread import AudioLoaderThread
from toaster import ToastDialog
from plot_wave import plot_waveform


            
'''THIS IS THE MAIN WINDOW CLASS FOR THE FIREWORK STUDIO APPLICATION'''
class FireworkShowApp(QMainWindow):
    def __init__(self):
        super().__init__()

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
        self.fireworks_canvas = None
        self.audio_datas = []
        self._running_threads = []
        self.generating_toast = None
        self.clear_btn = None
        self.duration = None

        #############################################################
        #                                                          #
        #        Style for play and stop buttons                   #
        #                                                          #
        #############################################################

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

        # Create a container for the fireworks canvas
        def create_fireworks_canvas_container():
            container = QWidget()
            layout = QVBoxLayout(container)
            container.setMinimumHeight(435)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            self.fireworks_canvas = FireworksCanvas()
            layout.addWidget(self.fireworks_canvas)
            return container

        self.fireworks_canvas_container = create_fireworks_canvas_container()
        fireworks_canvas_container = self.fireworks_canvas_container
        layout.addWidget(fireworks_canvas_container, stretch=5)

        ############################################################
        #                                                          #
        #        Fireworks Preview Widget                          #
        #                                                          #
        ############################################################

        # Fireworks preview widget
        self.preview_widget = FireworkPreviewWidget()
        self.preview_widget.setMinimumHeight(150)  # Make the preview widget taller
        layout.addWidget(self.preview_widget, stretch=0, alignment=Qt.AlignmentFlag.AlignBottom)
        # Enable mouse press tracking for the preview widget
        self.preview_widget.setMouseTracking(True)
        self.preview_widget.installEventFilter(self)

        ############################################################
        #                                                          #
        #        Media playback controls                           #
        #                                                          #                                                        
        ############################################################

        # Create a horizontal layout for media controls
        media_controls_layout = QHBoxLayout()
        media_controls_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        # Ensure all three buttons are aligned properly in the media_controls_layout
        media_controls_layout.setSpacing(12)
        media_controls_layout.setContentsMargins(0, 0, 0, 0)
        media_controls_layout.addStretch()

        ###############################################
        #                                             #
        #        Play/Pause button                    #
        #                                             #
        ###############################################

        # Create a play/pause button to control the preview playback
        def create_play_pause_btn():
            btn = QPushButton()
            btn.setFixedSize(40, 40)
            btn.setCheckable(True)
            btn.setText("▶️")
            btn.setStyleSheet(button_style)
            def toggle_icon(checked):
                btn.setText("⏸️" if checked else "▶️")
                self.preview_widget.toggle_play_pause()
            btn.toggled.connect(toggle_icon)
            return btn
        
        self.play_pause_btn = create_play_pause_btn()
        media_controls_layout.addWidget(self.play_pause_btn)

        ###########################################
        #                                         #
        #        Stop button                      #
        #                                         #
        ###########################################

        # Create a stop button to stop the preview and reset fireworks
        def create_stop_btn():
            btn = QPushButton("⏹️")
            btn.setFixedSize(40, 40)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(self.preview_widget.stop_preview)
            btn.clicked.connect(self.fireworks_canvas.reset_fireworks) # type: ignore
            def reset_play_pause():
                btn_parent = self.play_pause_btn
                btn_parent.blockSignals(True)
                if btn_parent.isChecked():
                    btn_parent.setChecked(False)
                btn_parent.setText("▶️")
                btn_parent.blockSignals(False)
            btn.clicked.connect(reset_play_pause)
            return btn

        self.stop_btn = create_stop_btn()
        media_controls_layout.addWidget(self.stop_btn)

        ###############################################
        #                                             #
        #        Add Firing button                    #
        #                                             #
        ###############################################

        # Create a button to add a new firework firing time
        def create_add_firing_btn():
            btn = QPushButton("Add Firing")
            btn.setStyleSheet(button_style)
            def add_firing_and_update_info():
                self.preview_widget.add_time(1)
                self.info_label.setText(f"Firework firings: {len(self.preview_widget.firework_firing)}")
            btn.clicked.connect(add_firing_and_update_info)
            return btn

        self.add_firing_btn = create_add_firing_btn()
        media_controls_layout.addWidget(self.add_firing_btn)

        ###############################################################
        #                                                             #
        #        Delete Firing button                                 #
        #                                                             #
        ###############################################################

        # Create a button to delete the selected firing
        def create_delete_firing_btn():
            btn = QPushButton("Delete Firing")
            btn.setStyleSheet("""
                QPushButton {
                background-color: #e53935;
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
                background-color: #c62828;
                }
                QPushButton:pressed {
                background-color: #8e2420;
                }
            """)
            def remove_firing_and_update_info():
                self.preview_widget.remove_selected_firing()
                self.info_label.setText(f"Firework firings: {len(self.preview_widget.firework_firing)}")
            btn.clicked.connect(remove_firing_and_update_info)
            return btn

        self.delete_firing_btn = create_delete_firing_btn()
        media_controls_layout.addWidget(self.delete_firing_btn)

        ###########################################################
        #                                                         #
        #    Clear show button (styled to match Add Firing)       #
        #                                                         #
        ###########################################################

        # Create a button to clear the show
        def create_clear_btn():
            btn = QPushButton("Clear Show")
            btn.setStyleSheet("""
                QPushButton {
                background-color: #43a047;
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
                background-color: #388e3c;
                }
                QPushButton:pressed {
                background-color: #2e7031;
                }
            """)
            # Also pause the show if playing
            def clear_show():
                self.fireworks_canvas.reset_fireworks()
                self.segment_times = None
                self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, None, self.duration)
                self.preview_widget.stop_preview()
                # Always reset play/pause button state and icon so playback can start again
                self.play_pause_btn.blockSignals(True)
                self.play_pause_btn.setChecked(False)
                self.play_pause_btn.setText("▶️")
                self.play_pause_btn.blockSignals(False)
                self.info_label.setText("Show cleared. Load audio to generate a new show.")
                
            btn.clicked.connect(clear_show)
            def show_cleared_toast():
                toast = ToastDialog("Show cleared!", parent=self)
                geo = self.geometry()
                x = geo.x() + geo.width() - toast.width() - 40
                y = geo.y() + geo.height() - toast.height() - 40
                toast.move(x, y)
                toast.show()
                QTimer.singleShot(2500, toast.close)
            btn.clicked.connect(show_cleared_toast)
            return btn

        self.clear_btn = create_clear_btn()
        media_controls_layout.addWidget(self.clear_btn)

        ###########################################################
        #                                                         #
        #              Current time display label                 #
        #                                                         #
        ###########################################################

        # Create a label to display the current playback time
        def create_current_time_label():
            label = QLabel("00:00")
            label.setStyleSheet("""
                QLabel {
                    color: #e0e0e0;
                    font-size: 18px;
                    font-weight: bold;
                    min-width: 60px;
                    qproperty-alignment: 'AlignVCenter | AlignLeft';
                }
            """)
            label.setFixedWidth(70)
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
            return label
        self.current_time_label = create_current_time_label()
        media_controls_layout.insertWidget(0, self.current_time_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        ############################################################
        #                                                         #
        #              Add info label to the media controls       #
        #                                                         #
        ############################################################
        
        # Add a vertical line to separate the time label from the buttons
        def create_vline():
            vline = QFrame()
            vline.setFrameShape(QFrame.Shape.VLine)
            vline.setFrameShadow(QFrame.Shadow.Sunken)
            vline.setStyleSheet("color: #444; background: #444; min-width: 2px;")
            return vline
        self.vline = create_vline()
        media_controls_layout.insertWidget(1, self.vline, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Add info label to display audio loading status
        self.info_label = QLabel("No audio loaded.")
        self.info_label.setStyleSheet("color: #b0b0b0; font-size: 15px; padding-left: 12px;")
        media_controls_layout.insertWidget(2, self.info_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        ###########################################################
        #                                                         #
        #              Load Audio Button                          #
        #                                                         #
        ###########################################################

        # Create a button to load audio files
        self.load_btn = QPushButton("Load Audio")
        self.load_btn.clicked.connect(self.load_audio)
        media_controls_layout.addWidget(self.load_btn)

        ###########################################################
        #                                                         #
        #              Fireworks show generator button            #
        #                                                         #
        ###########################################################

        # Create a button to generate fireworks show
        def create_generate_btn():
            btn = QPushButton("Generate Fireworks Show")
            self.info_label.setText("Load audio to generate fireworks show.")
            def generate_and_reset():
                self.fireworks_canvas.reset_fireworks()
                self.preview_widget.stop_preview()
                self.play_pause_btn.blockSignals(True)
                self.play_pause_btn.setChecked(False)
                self.play_pause_btn.setText("▶️")
                self.play_pause_btn.blockSignals(False)
                self.info_label.setText("Generating fireworks show...")
                QApplication.processEvents()
                self.update_preview_widget()
                btn.setText("Generate Fireworks Show")
            btn.clicked.connect(generate_and_reset)
            return btn

        self.generate_btn = create_generate_btn()
        media_controls_layout.addWidget(self.generate_btn)
        layout.addLayout(media_controls_layout)

        ###########################################################
        #                                                         #
        # Canvas for waveform display and firework firing display #
        #                                                         #
        ###########################################################

        # Create a canvas for displaying the waveform
        def create_waveform_canvas():
            canvas = FigureCanvas(Figure(figsize=(20, 1)))
            ax = canvas.figure.subplots()
            ax.set_facecolor('black')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            ax.set_title("Waveform with Segments", color='white')
            canvas.setFixedHeight(150)
            canvas.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
            return canvas
        self.waveform_canvas = create_waveform_canvas()
        layout.addWidget(self.waveform_canvas)

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
        plot_waveform(self,self.audio_data, self.sr, self.segment_times)
        self.duration = librosa.get_duration(y=self.audio_data, sr=self.sr)
        self.info_label.setText("")
        filenames = [os.path.basename(p) for p in getattr(self.audio_loader_thread, 'paths', [])]
        toast = ToastDialog(
            f"Loaded: {', '.join(filenames)}\nSample Rate: {self.sr} Hz, Duration: {self.duration:.2f} seconds",
            parent=self
        )
        # Ensure the waveform plot has a dark background
        if self.waveform_canvas is not None:
            ax = self.waveform_canvas.figure.axes[0]
            ax.set_facecolor('black')
            self.waveform_canvas.figure.set_facecolor('black')
            self.waveform_canvas.draw()
        geo = self.geometry()
        x = geo.x() + geo.width() - toast.width() - 40
        y = geo.y() + geo.height() - toast.height() - 40
        toast.move(x, y)
        toast.show()
        QTimer.singleShot(4000, toast.close)
        self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, self.firework_firing, self.duration)

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
                self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, self.firework_firing, self.duration)
                num_segments = len(self.segment_times) - 1 if self.segment_times is not None else 0
                num_firings = len(self.firework_firing) if self.firework_firing is not None else 0
                self.info_label.setText(f"Firework firings: {num_firings}")
                toast = ToastDialog(
                    f"Show generated!\nSegments: {num_segments}, Firework firings: {num_firings}",
                    parent=self
                )
                geo = self.geometry()
                x = geo.x() + geo.width() - toast.width() - 40
                y = geo.y() + geo.height() - toast.height() - 40
                toast.move(x, y)
                toast.show()
                QTimer.singleShot(4000, toast.close)
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
