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
from PyQt6.QtWidgets import QGroupBox, QRadioButton, QButtonGroup
from matplotlib.widgets import SpanSelector
from fireworks_preview import WaveformSelectionTool
import soundfile as sf
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtCore import QEvent

class FireworkShowManager:
    """
    Handles saving and loading of firework show data (firings, segments, etc.)
    """

    @staticmethod
    def save_show(filepath, audio_data, firings, segment_times=None, sr=None, duration=None, background=None, background_path=None, fireworks_colors=None):
        """
        Save the firework show data to a file (JSON format).
        """
        # Convert numpy array to list for JSON serialization
        audio_data_serializable = audio_data.tolist() if isinstance(audio_data, np.ndarray) else audio_data
        show_data = {
            "firings": firings,
            "segment_times": segment_times if segment_times is not None else [],
            "sample_rate": sr,
            "duration": duration,
            "audio_data": audio_data_serializable,  # Now serializable
            "background": background,
            "background_path": background_path,
            "fireworks_colors": fireworks_colors
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(show_data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def load_show(filepath):
        """
        Load the firework show data from a file (JSON format).
        Returns: firings, segment_times, sr, duration, audio_data, background, background_path, fireworks_colors
        """
        with open(filepath, "r", encoding="utf-8") as f:
            show_data = json.load(f)
        firings = show_data.get("firings", [])
        segment_times = show_data.get("segment_times", [])
        sr = show_data.get("sample_rate", None)
        duration = show_data.get("duration", None)
        audio_data = show_data.get("audio_data", None)
        background = show_data.get("background", None)
        background_path = show_data.get("background_path", None)
        fireworks_colors = show_data.get("fireworks_colors", None)
        if audio_data is not None:
            # Convert audio data from list to numpy array if needed
            audio_data = np.array(audio_data)
        return firings, segment_times, sr, duration, audio_data, background, background_path, fireworks_colors

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
        self.setMinimumSize(1600, 900)  # Ensure enough room for all widgets
        # Start maximized but not fullscreen (windowed)
        self.showMaximized()
        self.show()  # Ensure the window is shown and maximized
        self.generating_toast = None
        self.clear_btn = None
        self.audio_data = None
        self.audio_datas = []
        self.sr = None
        self.duration = None
        self.segment_times = []
        self.firework_firing = []
        self.firework_show_info = "No audio loaded. Load audio to get started."
        self.start = None
        self.end = None


        #############################################################
        #                                                          #
        #        Style buttons                                      #
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
            QComboBox {
                color: #e0e0e0;
                background: #23242b;
                font-size: 15px;
                border: 1px solid #444657;
                border-radius: 6px;
                padding: 6px 24px 6px 12px;
                min-width: 120px;
            }
            QComboBox:hover, QComboBox:focus {
                background: #31323a;
                border: 1.5px solid #ffd700;
                color: #ffd700;
            }
            QComboBox:!hover:!focus {
                border: 1px solid #444657;
                color: #e0e0e0;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid #444657;
                background: #23242b;
            }
            QComboBox::down-arrow {
                image: url(:/qt-project.org/styles/commonstyle/images/arrowdown-16.png);
                width: 16px;
                height: 16px;
            }
            QComboBox QAbstractItemView {
                background: #23242b;
                color: #e0e0e0;
                selection-background-color: #31323a;
                selection-color: #ffd700;
                border: 1px solid #444657;
                outline: none;
            }
            """

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
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.fireworks_canvas)
            # Ensure fireworks stay within the visible area by setting a minimum height
            container.setMinimumHeight(700)
            container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.fireworks_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            return container

        self.fireworks_canvas_container = create_fireworks_canvas_container()
        

        ############################################################
        #                                                          #
        #        Fireworks Preview Widget                          #
        #                                                          #
        ############################################################

        # Fireworks preview widget
        self.preview_widget = FireworkPreviewWidget()
        self.preview_widget.setMinimumHeight(90)
        # Enable mouse press tracking for the preview widget
        self.preview_widget.setMouseTracking(True)
        self.preview_widget.installEventFilter(self)


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
            btn.setText("Play")
            btn.setStyleSheet(button_style)
            def toggle_icon(checked, btn=btn):
                btn.setText("Pause" if checked else "Play")
                if checked:
                    self.fireworks_canvas.set_fireworks_enabled(True)  # Enable fireworks while playing
                else:
                    self.fireworks_canvas.set_fireworks_enabled(False)  # Disable fireworks while paused
                self.preview_widget.toggle_play_pause()
            btn.toggled.connect(toggle_icon)
            return btn
        
        self.play_pause_btn = create_play_pause_btn()

        ###########################################
        #                                         #
        #        Stop button                      #
        #                                         #
        ###########################################

        # Create a stop button to stop the preview and reset fireworks
        def create_stop_btn():
            btn = QPushButton("Stop")
            btn.setFixedSize(40, 40)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(self.preview_widget.stop_preview)
            btn.clicked.connect(self.fireworks_canvas.reset_fireworks) # type: ignore
            def reset_play_pause():
                btn_parent = self.play_pause_btn
                btn_parent.blockSignals(True)
                if btn_parent.isChecked():
                    btn_parent.setChecked(False)
                btn_parent.setText("Play")
                btn_parent.blockSignals(False)
            btn.clicked.connect(reset_play_pause)
            return btn

        self.stop_btn = create_stop_btn()

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
                if self.audio_data is None:
                    return
                self.firework_firing = self.preview_widget.add_time()
                self.update_firework_show_info()
            btn.clicked.connect(add_firing_and_update_info)
            return btn

        self.add_firing_btn = create_add_firing_btn()

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
                if self.audio_data is None:
                    return
                self.firework_firing = self.preview_widget.remove_selected_firing()
                self.update_firework_show_info()
            btn.clicked.connect(remove_firing_and_update_info)
            return btn

        self.delete_firing_btn = create_delete_firing_btn()
        ###########################################################
        #                                                         #
        #      Firework Pattern Selector (Change Pattern)         #
        #                                                         #
        ###########################################################

        def create_pattern_selector():
            group_box = QGroupBox("Explosion Pattern")
            group_box.setStyleSheet("QGroupBox { color: #e0e0e0; font-weight: bold; }")
            layout = QHBoxLayout()
            group_box.setLayout(layout)
            patterns = [
            ("Circle", "circle"),
            ("Chrysanthemum", "chrysanthemum"),
            ("Palm", "palm"),
            ("Willow", "willow"),
            ("Peony", "peony"),
            ("Ring", "ring"),
            ]
            combo = QComboBox()
            combo.setStyleSheet(
            button_style
            )
            for label, pattern in patterns:
                combo.addItem(label, pattern)
            # Set default pattern
            combo.setCurrentIndex(0)
            self.fireworks_canvas.choose_firework_pattern(patterns[0][1])
            def on_pattern_changed(index):
                pattern = combo.itemData(index)
                self.fireworks_canvas.choose_firework_pattern(pattern)
            combo.currentIndexChanged.connect(on_pattern_changed)
            layout.addWidget(combo)
            return group_box

        self.pattern_selector = create_pattern_selector()
        ###########################################################
        #                                                         #
        #              Load Audio Button                          #
        #                                                         #
        ###########################################################

        # Create a button to load audio files
        self.load_btn = QPushButton("Load Audio")
        self.audio_loader = AudioLoader()
        self.load_btn.setStyleSheet(button_style)

        def handle_audio():
            # Load audio data
            self.audio_data, self.sr, self.audio_datas, self.duration = self.audio_loader.select_and_load()
            # setup the preview widget with loaded audio data becuase play button works by playing preview_widget
            # otherwise pressing play will not play anything because the show data is not set in preview_widget
            self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, None, self.duration)
            # Plot the waveform
            self.plot_waveform()
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

        ###########################################################
        #                                                         #
        #    Clear show button (styled to match Add Firing)       #
        #                                                         #
        ###########################################################

        # Create a button to clear the show
        def create_clear_btn():
            btn = QPushButton("Clear Show")
            btn.setStyleSheet(button_style)
            # Also pause the show if playing
            def clear_show():
            # Only clear if audio is loaded
                if self.audio_data is not None and self.sr is not None:
                    self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, None, self.duration)
                    self.preview_widget.stop_preview()
                    self.preview_widget.reset_selected_region()  # Reset selected region in preview widget
                    self.fireworks_canvas.update_animation()  # Reset firings displayed
                    setattr(self, "firework_firing", [])  # Clear firings
                    self.plot_waveform()  # Update waveform after clearing
                    self.update_firework_show_info()  # Update info after clearing
                    
                    def show_cleared_toast():
                        toast = ToastDialog("Show cleared!", parent=self)
                        geo = self.geometry()
                        x = geo.x() + geo.width() - toast.width() - 40
                        y = geo.y() + geo.height() - toast.height() - 40
                        toast.move(x, y)
                        toast.show()
                        QTimer.singleShot(2500, toast.close)
                    show_cleared_toast()
                else:
                    return
                # Always reset play/pause button state and icon so playback can start again
                self.play_pause_btn.blockSignals(True)
                self.play_pause_btn.setChecked(False)
                self.play_pause_btn.setText("Play")
                self.play_pause_btn.blockSignals(False)
                

            btn.clicked.connect(clear_show)

            return btn

        self.clear_btn = create_clear_btn()
    
        ############################################################
        #                                                         #
        #              Add info status bar                        #
        #                                                         #
        ############################################################

        # Add info label to display audio loading status
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(self.firework_show_info)

        ###########################################################
        #                                                         #
        #    Create a reset button to reset the selected region   #
        #                                                         #
        ###########################################################
        def create_reset_btn():
            btn = QPushButton("Reset")
            btn.setStyleSheet(button_style)
            btn.clicked.connect(self.preview_widget.reset_selected_region)
            btn.setToolTip("Reset the selected region in the preview widget")
            btn.clicked.connect(lambda: self.status_bar.showMessage(self.firework_show_info))
            return btn

        self.reset_btn = create_reset_btn()

        ###########################################################
        #                                                         #
        #              Current time display label                 #
        #                                                         #
        ###########################################################

        def create_current_time_label():
            label = QLabel("00:00:000")
            label.setStyleSheet(
            button_style +
            """
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #e0e0e0;
                background: #23232b;
                border: none;
            }
            """
            )
            label.setFixedWidth(140)
            # Update current_time_label whenever playback time changes
            def update_time_label():
                if hasattr(self.preview_widget, "current_time"):
                    t = self.preview_widget.current_time
                    mins = int(t // 60)
                    secs = int(t % 60)
                    ms = int((t - int(t)) * 1000)
                    self.current_time_label.setText(f"{mins:02d}:{secs:02d}:{ms:03d}")
                else:
                    self.current_time_label.setText("00:00:000")

            # Timer to update the label during playback
            self.time_update_timer = QTimer(self) # type: ignore
            self.time_update_timer.setInterval(1)  # type: ignore # update every 0.5 seconds for better ms accuracy
            self.time_update_timer.timeout.connect(update_time_label) # type: ignore

            def on_play_pause(checked):
                update_time_label()
                if checked:
                    self.time_update_timer.start() # type: ignore
                else:
                    self.time_update_timer.stop() # type: ignore

            self.play_pause_btn.toggled.connect(on_play_pause)
            self.stop_btn.clicked.connect(lambda: (self.current_time_label.setText("00:00:000"), self.time_update_timer.stop())) # type: ignore
            return label
        self.current_time_label = create_current_time_label()

         #################################################################
        #                                                               # 
        #        Save and Load Show buttons                            #
        #                                                               #
        #################################################################
        # Create a button to save and load firework shows
        def create_save_btn():
            btn = QPushButton("Save Show")
            btn.setStyleSheet(button_style)
            def save_show():
                options = QFileDialog.Option(0)
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Save Firework Show", "", "Firework Show (*.json);;All Files (*)", options=options
                )
                if file_path:
                    # Get current background and path
                    bg = getattr(self.fireworks_canvas, "current_background", None)
                    bg_path = getattr(self.fireworks_canvas, "custom_background_path", None)
                    fireworks_colors = getattr(self, "fireworks_colors", None)
                    # Ensure all data is serializable and no extra artifacts are added
                    audio_data_to_save = (
                        self.audio_data.tolist() if isinstance(self.audio_data, np.ndarray) else self.audio_data
                    )
                    firings_to_save = (
                        [float(t) for t in getattr(self.preview_widget, "firework_firing", [])] if hasattr(self.preview_widget, "firework_firing") else []
                    )
                    segment_times_to_save = (
                        [float(t) for t in self.segment_times] if self.segment_times is not None else []
                    )
                    FireworkShowManager.save_show(
                        file_path,
                        audio_data_to_save,
                        firings_to_save,
                        segment_times_to_save,
                        self.sr,
                        self.duration,
                        background=bg,
                        background_path=bg_path,
                        fireworks_colors=fireworks_colors
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
            btn.setStyleSheet(button_style)
            def load_show():
                options = QFileDialog.Option(0)
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Load Firework Show", "", "Firework Show (*.json);;All Files (*)", options=options
                )
                if file_path:
                    firings, segment_times, sr, duration, audio_data_loaded, background, background_path, fireworks_colors = FireworkShowManager.load_show(file_path)
                    # Carefully restore all fields, converting types as needed
                    self.firework_firing = [float(t) for t in firings] if firings is not None else []
                    self.segment_times = [float(t) for t in segment_times] if segment_times is not None else []
                    self.sr = int(sr) if sr is not None else None
                    self.duration = float(duration) if duration is not None else None
                    if isinstance(audio_data_loaded, list):
                        self.audio_data = np.array(audio_data_loaded, dtype=np.float32)
                    elif isinstance(audio_data_loaded, np.ndarray):
                        self.audio_data = audio_data_loaded.astype(np.float32)
                    else:
                        self.audio_data = None
                    self.plot_waveform()
                    self.preview_widget.set_fireworks_colors(fireworks_colors)
                    self.preview_widget.set_show_data(
                        self.audio_data, self.sr, self.segment_times, self.firework_firing, self.duration
                    )
                    # Restore background selection
                    if background:
                        if background == "custom" and background_path:
                            self.fireworks_canvas.set_background("custom", background_path)
                            for btn_radio in self.background_btn.findChildren(QRadioButton):
                                if btn_radio.text().lower() == "custom":
                                    btn_radio.setChecked(True)
                                    break
                        else:
                            self.fireworks_canvas.set_background(background)
                            for btn_radio in self.background_btn.findChildren(QRadioButton):
                                if btn_radio.text().replace(" ", "").lower() == background.replace(" ", "").lower():
                                    btn_radio.setChecked(True)
                                    break
                    # Ensure firings are displayed after loading
                    self.preview_widget.set_show_data(
                        self.audio_data, self.sr, self.segment_times, self.firework_firing, self.duration
                    )
                    self.fireworks_canvas.update_animation()
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
        # Add a spacer after save/load buttons for better layout

        ###########################################################
        #                                                         #
        #              Background selection                       #
        #                                                         #
        ###########################################################
        # Create a button to select background
        def create_background_btn():
            group_box = QGroupBox("Background")
            group_box.setStyleSheet("QGroupBox { color: #e0e0e0; font-weight: bold; }")
            bg_layout = QHBoxLayout()
            group_box.setLayout(bg_layout)

            backgrounds = [
                ("Night Sky", "night"),
                ("Sunset", "sunset"),
                ("City", "city"),
                ("Mountains", "mountains"),
                ("Custom", "custom"),
            ]
            # Create radio buttons for each background option
            button_group = QButtonGroup(self)
            for label, bg_name in backgrounds:
                radio = QRadioButton(label)
                radio.setStyleSheet("color: #e0e0e0;")
                bg_layout.addWidget(radio)
                button_group.addButton(radio)
                radio.toggled.connect(lambda checked, bg=bg_name: self.fireworks_canvas.set_background(bg) if checked and bg != "custom" else None)
                if bg_name == "custom":
                    def on_custom_bg_selected(checked, radio=radio):
                        if checked:
                            file_dialog = QFileDialog(self)
                            file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif)")
                            if file_dialog.exec():
                                selected_files = file_dialog.selectedFiles()
                                if selected_files:
                                    image_path = selected_files[0]
                                    self.fireworks_canvas.set_background("custom", image_path)
                    radio.toggled.connect(lambda checked, r=radio: on_custom_bg_selected(checked, r))
            # Set default selection
            button_group.buttons()[0].setChecked(True)
            self.fireworks_canvas.set_background(backgrounds[0][1])


            return group_box
        self.background_btn = create_background_btn()

        ###########################################################
        #                                                         #
        #              Fireworks show generator button            #
        #                                                         #
        ###########################################################

        # Create a button to generate fireworks show
        def create_generate_btn():
            btn = QPushButton("Generate Show")
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)            
            ai_button_style = button_style + """
                QPushButton {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #ff5252, 
                        stop:0.2 #ffeb3b, 
                        stop:0.4 #4caf50, 
                        stop:0.6 #2196f3, 
                        stop:0.8 #8e24aa, 
                        stop:1 #e040fb
                    );
                }
            """
            btn.setStyleSheet(ai_button_style)
            btn.setCheckable(False)  # Prevent checked/pressed state
            btn.setAutoDefault(False)

            def generate_and_reset():
                self.preview_widget.stop_preview()
                self.play_pause_btn.blockSignals(True)
                self.play_pause_btn.setChecked(False)
                self.play_pause_btn.setText("Play")
                self.play_pause_btn.blockSignals(False)
                QApplication.processEvents()
            btn.clicked.connect(generate_and_reset)
            return btn
        
        self.generate_btn = create_generate_btn()
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
            canvas.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
            return canvas
        self.waveform_canvas = create_waveform_canvas()

        # Add a waveform panning/selection tool using matplotlib's SpanSelector
        self.waveform_selector = WaveformSelectionTool(self.waveform_canvas, main_window=self)

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

        media_controls_layout.insertWidget(0, self.play_pause_btn, alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        media_controls_layout.insertWidget(1, self.stop_btn, alignment=Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        media_controls_layout.addWidget(self.add_firing_btn)
        media_controls_layout.addWidget(self.delete_firing_btn)
        media_controls_layout.addWidget(self.load_btn)
        media_controls_layout.addStretch()
        media_controls_layout.addWidget(self.clear_btn)
        media_controls_layout.addWidget(self.reset_btn)
        media_controls_layout.insertWidget(2, self.current_time_label, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        media_controls_layout.addWidget(self.save_btn)
        media_controls_layout.addWidget(self.load_show_btn)
        media_controls_layout.addWidget(self.pattern_selector)
        media_controls_layout.addWidget(self.background_btn)
        media_controls_layout.addWidget(self.generate_btn)

        # Wrap the media_controls_layout in a QWidget so it can be added to the main layout
        self.media_controls_widget = QWidget()
        self.media_controls_widget.setLayout(media_controls_layout)
        
        #############################################################
        #                                                          #
        #        Overall UI Elements layout                         #
        #                                                          #
        #############################################################
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        # Use a QStackedLayout-like approach to overlay media_controls_widget on top of the fireworks_canvas_container
        # Create a container widget with a QVBoxLayout for stacking
        overlay_container = QWidget()
        overlay_layout = QVBoxLayout(overlay_container)
        overlay_layout.setContentsMargins(0, 0, 0, 0)
        overlay_layout.setSpacing(0)
        # Add the fireworks canvas (main content)
        overlay_layout.addWidget(self.fireworks_canvas_container)
        # Place the media controls widget with negative top margin to overlap the bottom of the canvas
        self.media_controls_widget.setParent(overlay_container)
        overlay_layout.addWidget(self.media_controls_widget, alignment=Qt.AlignmentFlag.AlignBottom)
        overlay_layout.setStretch(0, 1)
        overlay_layout.setStretch(1, 0)
        # Add the overlay container to the main layout
        layout.addWidget(overlay_container)
        layout.addWidget(self.media_controls_widget)  # Use the widget, not the layout
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
        # Adjust current_time_label to fit time tightly (remove extra width)
        self.current_time_label.setFixedWidth(self.current_time_label.fontMetrics().horizontalAdvance("00:00:000") + 18)
        self.current_time_label.setContentsMargins(0, 0, 0, 0)
       
        

    ###############################################################
    #                                                             #
    #  HELPER FUNCTIONS for loading audio and segmenting it       #
    #                                                             #
    ###############################################################
    def plot_waveform(self):
        """
        Plot the waveform and highlight segment times and firework firings.
        Uses a black background and white waveform for a professional look, with grid lines.
        """
        ax = self.waveform_canvas.figure.axes[0]
        ax.clear()
        if self.audio_data is not None and self.sr is not None:
            # Draw waveform in white for a clean, professional look
            librosa.display.waveshow(self.audio_data, sr=self.sr, ax=ax, color="#ffffff")
            ax.set_facecolor('black')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            ax.set_title("Waveform with Segments", color='white')
            # Plot segment times in subtle gray
            if self.segment_times is not None and isinstance(self.segment_times, (list, tuple, np.ndarray)):
                for t in self.segment_times:
                    if t is not None and np.isfinite(t):
                        ax.axvline(x=t, color="#bbbbbb", linestyle="--", linewidth=1.2, alpha=0.7)
            if self.duration is not None and self.sr is not None:
                ax.set_xlim(0, self.duration)
            elif self.audio_data is not None and self.sr is not None:
                ax.set_xlim(0, len(self.audio_data) / self.sr)
            else:
                ax.set_xlim(0, 1)
            ax.set_xlabel("Time (s)", color='white')
            ax.set_ylabel("Amplitude", color='white')
            # Add grid lines in white, with some transparency for subtlety
            ax.grid(True, color="#888888", alpha=0.3, linestyle="--", linewidth=0.8)
        else:
            ax.set_title("No audio loaded", color='white')
            ax.set_xticks([])
            ax.set_yticks([])
        self.waveform_canvas.draw_idle()

    def update_firework_show_info(self):
        #Updates the variable called firework_show_info, not the actual show.
        # This is just for diplaying information as it changes
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