# firework_show_app.py
# This is the main application file for the Firework Studio, which includes the main window and
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QSizePolicy, QDialog, QStatusBar
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

from analysis import AudioAnalyzer
from loader import AudioLoader
from toaster import ToastDialog
import json


class FireworkShowManager:
    """
    Handles saving and loading of firework show data (firings, segments, etc.)
    """

    @staticmethod
    def save_show(filepath, audio_data, firings, segment_times=None, sr=None, duration=None):
        """
        Save the firework show data to a file (JSON format).
        """
        show_data = {
            "firings": firings,
            "segment_times": segment_times if segment_times is not None else [],
            "sample_rate": sr,
            "duration": duration,
            "audio_data": audio_data  # Placeholder for audio data if needed
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(show_data, f, indent=2)

    @staticmethod
    def load_show(filepath):
        """
        Load the firework show data from a file (JSON format).
        Returns: firings, segment_times, sr, duration
        """
        with open(filepath, "r", encoding="utf-8") as f:
            show_data = json.load(f)
        firings = show_data.get("firings", [])
        segment_times = show_data.get("segment_times", [])
        sr = show_data.get("sample_rate", None)
        duration = show_data.get("duration", None)
        audio_data = show_data.get("audio_data", None)
        if audio_data is not None:
            # Convert audio data from list to numpy array if needed
            audio_data = np.array(audio_data)
        return firings, segment_times, sr, duration, audio_data


            
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
        # Start maximized but not fullscreen (windowed)
        self.showMaximized()
        self.generating_toast = None
        self.clear_btn = None
        self.audio_data = None
        self.audio_datas = []
        self.sr = None
        self.duration = None
        self.segment_times = None
        self.firework_firing = []
        self.fireworks_canvas = None  # Declare attribute before assignment
        self.firework_show_info = "No audio loaded. Load audio to get started."

        #############################################################
        #                                                          #
        #        Style for play and stop buttons                   #
        #                                                          #
        #############################################################

        button_style = """
            QPushButton {
            background-color: #49505a;
            color: #f0f0f0;
            border: none;
            border-radius: 7px;
            font-size: 14px;
            font-weight: bold;
            min-width: 60px;
            min-height: 28px;
            padding: 4px 8px;
            }
            QPushButton:hover {
            background-color: #606874;
            }
            QPushButton:pressed {
            background-color: #353a40;
            }
        """
        #############################################################
        #                                                          #
        #        Overall UI Elements layout                         #
        #                                                          #
        #############################################################
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        #############################################################
        #                                                          #
        #        Fireworks Show Preview Screen                     #
        #                                                          #
        #############################################################

        # Create the fireworks canvas
        self.fireworks_canvas = FireworksCanvas()
        # Create a container for the fireworks canvas
        def create_fireworks_canvas_container():
            container = QWidget()
            layout = QVBoxLayout(container)
            container.setMinimumHeight(435)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.fireworks_canvas)
            return container

        self.fireworks_canvas_container = create_fireworks_canvas_container()
        

        ############################################################
        #                                                          #
        #        Fireworks Preview Widget                          #
        #                                                          #
        ############################################################

        # Fireworks preview widget
        self.preview_widget = FireworkPreviewWidget()
        self.preview_widget.setMinimumHeight(150)  # Make the preview widget taller
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
                if checked:
                    self.fireworks_canvas.set_fireworks_enabled(True)
                else:
                    self.fireworks_canvas.set_fireworks_enabled(False)
                self.preview_widget.toggle_play_pause()
            btn.toggled.connect(toggle_icon)
            # Remove unsupported 'transition' property from button_style
            return btn
        
        self.play_pause_btn = create_play_pause_btn()
        self.play_pause_btn.clicked.connect(self.fireworks_canvas.reset_firings) # type: ignore
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
            btn.clicked.connect(lambda: self.fireworks_canvas.set_fireworks_enabled(True))  # Enable fireworks on stop to update screen
            btn.clicked.connect(self.fireworks_canvas.update_animation)  # Reset firings on stop
            btn.clicked.connect(lambda: self.fireworks_canvas.set_fireworks_enabled(False))  # Disable fireworks on stop
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
                self.firework_firing = self.preview_widget.add_time()
                self.update_firework_show_info()
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
            btn.setStyleSheet(button_style)
            def remove_firing_and_update_info():
                self.firework_firing = self.preview_widget.remove_selected_firing()
                self.update_firework_show_info()
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
                self.segment_times = None
                self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, None, self.duration)
                self.preview_widget.stop_preview()
                # Always reset play/pause button state and icon so playback can start again
                self.play_pause_btn.blockSignals(True)
                self.play_pause_btn.setChecked(False)
                self.play_pause_btn.setText("▶️")
                self.play_pause_btn.blockSignals(False)

            btn.clicked.connect(clear_show)
            btn.clicked.connect(lambda: self.fireworks_canvas.set_fireworks_enabled(True))  # Enable fireworks on stop to update screen
            btn.clicked.connect(self.fireworks_canvas.update_animation)  # Reset firings on stop
            btn.clicked.connect(lambda: self.fireworks_canvas.set_fireworks_enabled(False))  # Disable fireworks on stop

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

        # Add info label to display audio loading status
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(self.firework_show_info)

        ###########################################################
        #                                                         #
        #              Load Audio Button                          #
        #                                                         #
        ###########################################################

        # Create a button to load audio files
        self.load_btn = QPushButton("Load Audio")
        self.audio_loader = AudioLoader()
        self.load_btn.setStyleSheet(button_style)
        self.load_btn.setFixedHeight(40)

        def handle_audio():
            # Load audio data
            self.audio_data, self.sr, self.audio_datas, self.duration = self.audio_loader.select_and_load()
            # Plot waveform
            self.plot_waveform()
            # setup the preview widget with loaded audio data becuase play button works by playing preview_widget
            # otherwise pressing play will not play anything because the show data is not set in preview_widget
            self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, None, self.duration)
            # If audio data is loaded, enable the generate button
            if self.audio_data is not None:
                self.generate_btn.setEnabled(True)
                self.generate_btn.setVisible(True)  
                # Show when audio is loaded
                self.status_bar.showMessage("Generate fireworks show from scratch or use generate show button to get help.")
                # Show a toast notification with loaded audio file names
                basenames = [os.path.basename(p) for p in self.audio_loader.paths]
                toast = ToastDialog(f"Loaded audio: {', '.join(basenames)}", parent=self)
                self.update_firework_show_info()
                geo = self.geometry()
                x = geo.x() + geo.width() - toast.width() - 40
                y = geo.y() + geo.height() - toast.height() - 40
                toast.move(x, y)
                toast.show()
                QTimer.singleShot(2500, toast.close)
            elif self.audio_data is None:
                self.generate_btn.setVisible(False)  # Hide if no audio

        # Connect the load_btn to open file dialog and load audio

        self.load_btn.clicked.connect(lambda: handle_audio())
        media_controls_layout.addWidget(self.load_btn)

        ###########################################################
        #                                                         #
        #              Fireworks show generator button            #
        #                                                         #
        ###########################################################

        # Create a button to generate fireworks show
        def create_generate_btn():
            btn = QPushButton("Generate Show")
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)            
            ai_button_style = """
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ff5252, 
                        stop:0.2 #ffeb3b, 
                        stop:0.4 #4caf50, 
                        stop:0.6 #2196f3, 
                        stop:0.8 #8e24aa, 
                        stop:1 #e040fb
                    );
                    border: 2px solid #8e24aa;
                    letter-spacing: 1px;
                    min-width: 180px;
                    min-height: 40px;
                    max-width: 180px;
                    max-height: 40px;
                
            """
            btn.setStyleSheet(ai_button_style)
            btn.setFixedHeight(40)
            btn.setMinimumWidth(60)
            btn.setCheckable(False)  # Prevent checked/pressed state
            btn.setAutoDefault(False)

            def generate_and_reset():
                self.preview_widget.stop_preview()
                self.play_pause_btn.blockSignals(True)
                self.play_pause_btn.setChecked(False)
                self.play_pause_btn.setText("▶️")
                self.play_pause_btn.blockSignals(False)
                QApplication.processEvents()
            btn.clicked.connect(generate_and_reset)
            return btn
        
        self.generate_btn = create_generate_btn()
        media_controls_layout.addWidget(self.generate_btn)
        self.generate_btn.setVisible(False)  # Hide initially

        ###########################################################
        #                                                         #
        # Canvas for waveform display and firework firing display #
        #                                                         #
        ###########################################################
        
        # Create a canvas for displaying the waveform needed here for loading audio
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
        
        #################################################################
        #                                                               # 
        #        Set up the main layout for the application window      #
        #                                                               #
        #################################################################

        layout = QVBoxLayout(central_widget)
        # Add Save and Load buttons for firework show
        save_load_layout = QHBoxLayout()
        save_load_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        save_load_layout.setSpacing(10)

        def create_save_btn():
            btn = QPushButton("Save Show")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1976d2;
                    color: #fff;
                    border: none;
                    border-radius: 7px;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 80px;
                    min-height: 28px;
                    padding: 4px 12px;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
                QPushButton:pressed {
                    background-color: #0d47a1;
                }
            """)
            def save_show():
                options = QFileDialog.Option(0)
                file_path, _ = QFileDialog.getSaveFileName(self, "Save Firework Show", "", "Firework Show (*.json);;All Files (*)", options=options)
                if file_path:
                    FireworkShowManager.save_show(
                        file_path,
                        self.audio_data.tolist() if self.audio_data is not None else None,
                        self.firework_firing,
                        self.segment_times,
                        self.sr,
                        self.duration
                    )
                    toast = ToastDialog("Show saved!", parent=self)
                    geo = self.geometry()
                    x = geo.x() + geo.width() - toast.width() - 40
                    y = geo.y() + geo.height() - toast.height() - 40
                    toast.move(x, y)
                    toast.show()
                    QTimer.singleShot(2000, toast.close)
            btn.clicked.connect(save_show)
            return btn

        def create_load_show_btn():
            btn = QPushButton("Load Show")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #388e3c;
                    color: #fff;
                    border: none;
                    border-radius: 7px;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 80px;
                    min-height: 28px;
                    padding: 4px 12px;
                }
                QPushButton:hover {
                    background-color: #2e7031;
                }
                QPushButton:pressed {
                    background-color: #1b5e20;
                }
            """)
            def load_show():
                options = QFileDialog.Option(0)
                file_path, _ = QFileDialog.getOpenFileName(self, "Load Firework Show", "", "Firework Show (*.json);;All Files (*)", options=options)
                if file_path:
                    firings, segment_times, sr, duration, audio_data = FireworkShowManager.load_show(file_path)
                    self.firework_firing = firings
                    self.segment_times = segment_times
                    self.sr = sr
                    self.duration = duration
                    if audio_data is not None:
                        self.audio_data = audio_data
                    self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, self.firework_firing, self.duration)
                    self.plot_waveform()
                    self.update_firework_show_info()
                    toast = ToastDialog("Show loaded!", parent=self)
                    geo = self.geometry()
                    x = geo.x() + geo.width() - toast.width() - 40
                    y = geo.y() + geo.height() - toast.height() - 40
                    toast.move(x, y)
                    toast.show()
                    QTimer.singleShot(2000, toast.close)
            btn.clicked.connect(load_show)
            return btn

        self.save_btn = create_save_btn()
        self.load_show_btn = create_load_show_btn()
        save_load_layout.addWidget(self.save_btn)
        save_load_layout.addWidget(self.load_show_btn)
        layout.addLayout(save_load_layout)
        layout.addWidget(self.fireworks_canvas_container, stretch=5)
        layout.addLayout(media_controls_layout)
        layout.addWidget(self.preview_widget, stretch=0, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.waveform_canvas)

        ###########################################################
        #                                                         #
        #        Set dark theme palette and styles for the app    #
        #                                                         #
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
    def plot_waveform(self):
        # Enable interactive zooming/panning for the waveform canvas
        self.waveform_canvas.figure.clear()
        self.waveform_canvas.figure.set_facecolor('#181818')  # Set figure background to dark
        self.waveform_canvas.figure.subplots()
        self.waveform_canvas.figure.tight_layout()
        self.waveform_canvas.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.waveform_canvas.setFocus()

        # Enable matplotlib's built-in navigation toolbar for zoom/pan
        # Add a compact, dark-themed navigation toolbar above the waveform
        if not hasattr(self.waveform_canvas, 'waveform_toolbar'):
            self.waveform_canvas.waveform_toolbar = NavigationToolbar2QT(self.waveform_canvas, self.waveform_canvas)
            self.waveform_canvas.waveform_toolbar.setStyleSheet("""
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
            self.waveform_canvas.waveform_toolbar.setIconSize(self.waveform_canvas.waveform_toolbar.iconSize().scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio))
            # Add the toolbar above the waveform_canvas in the parent layout
            parent_layout = self.waveform_canvas.parentWidget().layout() if self.waveform_canvas.parentWidget() else None
            if parent_layout is not None:
                idx = parent_layout.indexOf(self.waveform_canvas)
                parent_layout.insertWidget(idx, self.waveform_canvas.waveform_toolbar)
        # Always get the axes after subplots() is called
        ax = self.waveform_canvas.figure.axes[0]
        ax.clear()
        ax.set_facecolor('#181818')  # Set axes background to dark
        ax.set_frame_on(False)
        # Make axes occupy the full canvas area, removing all padding/margins
        ax.set_position((0.0, 0.0, 1.0, 1.0))
        if self.audio_data is not None:
            sr = self.sr if self.sr is not None else 22050  # Default librosa sample rate
            librosa.display.waveshow(self.audio_data, sr=sr, ax=ax, alpha=0.5, color='white')
            ax.set_facecolor('#181818')
            ax.set_xticks([])
        # Ensure all spines are invisible (removes white edge)
        for spine in ax.spines.values():
            spine.set_visible(False)
        # Plot segments
        if self.segment_times is not None:
            for i, t in enumerate(self.segment_times):
                ax.axvline(t, color='orange', linestyle='--', alpha=0.7)
        ax.set_title("Waveform with Segments", color='white')  # Set title color to white
        ax.title.set_color('white')
        # Fit x-axis to audio duration
        if self.audio_data is not None and self.duration is not None:
            ax.set_xlim((0, self.duration))
        if self.audio_data is not None and self.duration is not None:
            ax.set_xlim((0, self.duration))


    def update_firework_show_info(self):
        # Format duration as mm:ss if available
        if self.duration is not None:
            mins, secs = divmod(int(self.duration), 60)
            duration_str = f"{mins:02d}:{secs:02d}"
        else:
            duration_str = "N/A"
        self.firework_show_info = (
            f"Sample Rate: {self.sr if self.sr is not None else 'N/A'} | "
            f"Duration: {duration_str} | "
            f"Segments: {len(self.segment_times) if self.segment_times is not None else 0} | "
            f"Firework Firings: {len(self.firework_firing) if self.firework_firing is not None else 0}"
        )
        if hasattr(self, "status_bar"):
            self.status_bar.showMessage(self.firework_show_info)