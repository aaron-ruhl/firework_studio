import numpy as np
import os
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QAction, QPalette
from PyQt6.QtWidgets import (
    QMenu, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QSizePolicy, QStatusBar,
    QGroupBox, QComboBox, QMenuBar
)

from fireworks_canvas import FireworksCanvas
from fireworks_preview import FireworkPreviewWidget
from analysis import AudioAnalyzer
from loader import AudioLoader
from toaster import ToastDialog
from waveform_selection import WaveformSelectionTool
from PyQt6.QtWidgets import QToolBar, QWidgetAction
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QSpinBox, QGroupBox
from PyQt6.QtWidgets import QWidgetAction


import numpy as np
from PyQt6.QtWidgets import QPushButton, QFileDialog, QRadioButton
from PyQt6.QtGui import QColor
from toaster import ToastDialog
from show_file_handler import ShowFileHandler
from PyQt6.QtGui import QShortcut, QKeySequence
from PyQt6.QtWidgets import QInputDialog

'''THIS IS THE MAIN WINDOW CLASS FOR THE FIREWORK STUDIO APPLICATION'''
class FireworkShowApp(QMainWindow):
    def clear_show(self):
            # Only clear if audio is loaded
            if self.audio_data is not None and self.sr is not None:
                self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, None, self.duration)
                self.preview_widget.stop_preview()
                self.preview_widget.reset_selected_region()  # Reset selected region in preview widget
                self.fireworks_canvas.update_animation()  # Reset firings displayed
                self.preview_widget.reset_fireworks()  # Reset fireworks in preview widget
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
                pass
                return
            # Always reset play/pause button state and icon so playback can start again
            self.play_pause_btn.blockSignals(True)
            self.play_pause_btn.setChecked(False)
            self.play_pause_btn.setIcon(QIcon(os.path.join("icons", "play.png")))
            self.play_pause_btn.blockSignals(False)

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
        self.firework_show_info = "No audio loaded. Load audio to get started. Use the arrow keys to change what firework(s) you add."
        self.start = None
        self.end = None
        self.fireworks_colors = []
        self.filtered_firings = []
        self.paths = []
        self.padding = 0

        #############################################################
        #                                                          #
        #        Style buttons                                      #
        #                                                          #
        #############################################################
        button_style = """
            QPushButton {
            background-color: #49505a;
            color: #ffd700;
            border: 1px solid #444657;
            border-radius: 5px;
            font-size: 12px;
            font-weight: 500;
            min-width: 36px;
            min-height: 28px;
            max-width: 80px;
            max-height: 28px;
            padding: 2px 6px;
            margin: 0px;
            }
            QPushButton:hover {
            background-color: #606874;
            color: #ffd700;
            border: 1.2px solid #ffd700;
            }
            QPushButton:pressed {
            background-color: #353a40;
            color: #ffd700;
            border: 1.2px solid #ffd700;
            }
            QPushButton:checked {
            background-color: #23242b;
            color: #ffd700;
            border: 1.2px solid #ffd700;
            }
            QComboBox {
            background: #23242b;
            color: #ffd700;
            border: 1px solid #444657;
            font-size: 12px;
            border-radius: 4px;
            padding: 3px 16px 3px 6px;
            min-width: 40px;
            max-width: 100px;
            margin: 0px;
            }
            QComboBox:hover, QComboBox:focus {
            background: #31323a;
            color: #ffd700;
            border: 1.2px solid #ffd700;
            }
            QComboBox::drop-down {
            background: #23242b;
            border-left: 1px solid #444657;
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 16px;
            }
            QComboBox::down-arrow {
            width: 10px;
            height: 10px;
            }
            QComboBox QAbstractItemView {
            background: #23242b;
            border: 1px solid #444657;
            color: #ffd700;
            selection-background-color: #31323a;
            selection-color: #ffd700;
            outline: ;
            }
            QToolBar {
            background: #23242b;
            border: none;
            spacing: 0px;
            padding: 0px;
            margin: 0px;
            min-height: 36px;
            max-height: 36px;
            }
            QGroupBox {
            background-color: #23242b;
            border: 1px solid #444657;
            border-radius: 6px;
            color: #ffd700;
            font-size: 13px;
            font-weight: bold;
            }
            QGroupBox:title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 4px;
            color: #ffd700;
            font-size: 13px;
            font-weight: bold;
            }
            QSpinBox {
            background-color: #23242b;
            color: #ffd700;
            border: 1px solid #444657;
            border-radius: 4px;
            font-size: 13px;
            font-weight: bold;
            min-width: 40px;
            max-width: 60px;
            padding: 2px 8px;
            margin: 0px;
            qproperty-alignment: AlignCenter;
            }
            QSpinBox::up-button, QSpinBox::down-button {
            background: #31323a;
            border: 1px solid #444657;
            border-radius: 2px;
            width: 16px;
            height: 14px;
            }
            QSpinBox::up-arrow, QSpinBox::down-arrow {
            width: 10px;
            height: 10px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background: #ffd700;
            border: 1.2px solid #ffd700;
            }
            QSpinBox:focus {
            border: 1.2px solid #ffd700;
            color: #ffd700;
            }
        """

        menu_style = """
            QMenu {
            background-color: #23242b;
            color: #ffd700;
            border: 1px solid #444657;
            border-radius: 6px;
            font-size: 13px;
            padding: 4px 0px;
            min-width: 160px;
            }
            QMenu::item {
            background-color: transparent;
            color: #ffd700;
            padding: 6px 24px 6px 24px;
            border-radius: 4px;
            font-size: 13px;
            }
            QMenu::item:selected {
            background-color: #31323a;
            color: #ffd700;
            }
            QMenu::separator {
            height: 1px;
            background: #444657;
            margin: 4px 12px 4px 12px;
            }
            QMenu::icon {
            margin-left: 8px;
            margin-right: 12px;
            }
            QMenuBar {
            background-color: #23242b;
            color: #ffd700;
            border: none;
            font-size: 14px;
            font-weight: bold;
            padding: 0px 8px;
            min-height: 28px;
            }
            QMenuBar::item {
            background: transparent;
            color: #ffd700;
            padding: 4px 16px;
            border-radius: 4px;
            }
            QMenuBar::item:selected {
            background: #31323a;
            color: #ffd700;
            }
            QMenuBar::item:pressed {
            background: #353a40;
            color: #ffd700;
            }
        """

        #############################################################
        #                                                          #
        #        Fireworks Display Screen                          #
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
            self.fireworks_canvas.set_fireworks_enabled(False)  # Disable fireworks initially since it is technically starting in a paused state
            return container

        self.fireworks_canvas_container = create_fireworks_canvas_container()
        self.fireworks_canvas.setStyleSheet("background-color: #23242b;")  # Set canvas background color

        ############################################################
        #                                                          #
        #        Fireworks Display Preview                         #
        #                                                          #
        ############################################################

        # Fireworks preview widget
        self.preview_widget = FireworkPreviewWidget()
        self.preview_widget.setFixedHeight(90)
        # Enable mouse press tracking for the preview widget
        self.preview_widget.setMouseTracking(True)

        # If the user is dragging the playhead, set play_pause_btn to "Play"
        def on_dragging_playhead(event_type):
            if event_type == "dragging_playhead":
                self.play_pause_btn.blockSignals(True)
                self.play_pause_btn.setChecked(False)
                self.play_pause_btn.setIcon(QIcon(os.path.join("icons", "play.png")))
                self.play_pause_btn.blockSignals(False)

        # Override the preview_widget's mouseMoveEvent to call on_dragging_playhead
        original_mouse_release_event = self.preview_widget.mouseReleaseEvent
        def custom_mouse_release_event(event):
            if self.preview_widget.dragging_playhead:
                on_dragging_playhead("dragging_playhead")
            original_mouse_release_event(event)
        self.preview_widget.mouseReleaseEvent = custom_mouse_release_event

        ###########################################################
        #                                                         #
        #           Canvas for waveform display                   #
        #                                                         #
        ###########################################################
        # Create a canvas for displaying the waveform needed here for loading audio
        def create_waveform_canvas():
            canvas = FigureCanvas(Figure(figsize=(7, 1)))
            ax = canvas.figure.subplots()
            ax.set_facecolor('black')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            canvas.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
            return canvas
        self.waveform_canvas = create_waveform_canvas()

        # Add a waveform panning/selection tool using matplotlib's SpanSelector
        self.waveform_selector = WaveformSelectionTool(self.waveform_canvas, main_window=self)

        # --- Add mouse hover event to show time label at cursor ---

        self.waveform_time_label = QLabel(self.waveform_canvas)
        self.waveform_time_label.setStyleSheet(
            "background: #23242b; color: #ffd700; border: 1px solid #ffd700; border-radius: 4px; padding: 2px 6px; font-size: 13px;"
        )
        self.waveform_time_label.setVisible(False)

        def on_waveform_motion(event):
            if event.inaxes and self.audio_data is not None and self.sr is not None:
                x = event.xdata
                if x is not None and 0 <= x <= (self.duration if self.duration else len(self.audio_data)/self.sr):
                    mins = int(x // 60)
                    secs = int(x % 60)
                    ms = int((x - int(x)) * 1000)
                    self.waveform_time_label.setText(f"{mins:02d}:{secs:02d}:{ms:03d}")
                    # Convert axes coords to widget coords
                    canvas = self.waveform_canvas
                    ax = event.inaxes
                    # Get pixel position of mouse in widget
                    x_disp, y_disp = canvas.figure.transFigure.inverted().transform(
                        canvas.figure.transFigure.transform((event.x, event.y))
                    )
                    # Use event.x, event.y (pixels) relative to canvas widget
                    label_width = self.waveform_time_label.sizeHint().width()
                    label_height = self.waveform_time_label.sizeHint().height()
                    # Offset label above cursor, keep inside widget
                    x_widget = int(event.x) - label_width // 2
                    y_widget = int(event.y) - label_height - 8
                    x_widget = max(0, min(x_widget, canvas.width() - label_width))
                    y_widget = max(0, y_widget)
                    self.waveform_time_label.move(x_widget, y_widget)
                    self.waveform_time_label.setVisible(True)
                else:
                    self.waveform_time_label.setVisible(False)
            else:
                self.waveform_time_label.setVisible(False)

        self.waveform_canvas.mpl_connect("motion_notify_event", on_waveform_motion)

        # Hide the label when the mouse leaves the waveform_canvas widget
        def on_waveform_leave(event):
            self.waveform_time_label.setVisible(False)

        self.waveform_canvas.mpl_connect("figure_leave_event", on_waveform_leave)
        self.waveform_canvas.leaveEvent = lambda event: self.waveform_time_label.setVisible(False)

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
            btn.setIcon(QIcon(os.path.join("icons", "play.png")))
            btn.setStyleSheet(button_style)
            return btn

        def toggle_icon(checked):
            if checked:
                if self.audio_data is None:
                    self.play_pause_btn.setChecked(False)
                    return
                self.play_pause_btn.setIcon(QIcon(os.path.join("icons", "pause.png")))
                self.fireworks_canvas.set_fireworks_enabled(True)
                self.fireworks_canvas.reset_firings()  # Reset firings to ensure they are displayed correctly
                if hasattr(self.fireworks_canvas, "fireworks"):
                    for firework in self.fireworks_canvas.fireworks:
                        firework.resume_explode()
            else:
                self.play_pause_btn.setIcon(QIcon(os.path.join("icons", "play.png")))
                self.fireworks_canvas.set_fireworks_enabled(False)
                if hasattr(self.fireworks_canvas, "fireworks"):
                    for firework in self.fireworks_canvas.fireworks:
                        firework.pause_explode()
            self.preview_widget.toggle_play_pause()

        self.play_pause_btn = create_play_pause_btn()
        self.play_pause_btn.toggled.connect(toggle_icon)

        ###########################################
        #                                         #
        #        Stop button                      #
        #                                         #
        ###########################################

        # Create a stop button to stop the preview and reset fireworks
        def create_stop_btn():
            btn = QPushButton()
            btn.setIcon(QIcon(os.path.join("icons", "stop.png")))
            btn.setFixedSize(40, 40)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(self.preview_widget.stop_preview)
            btn.clicked.connect(self.fireworks_canvas.reset_fireworks) # type: ignore
            def reset_play_pause():
                btn_parent = self.play_pause_btn
                btn_parent.blockSignals(True)
                if btn_parent.isChecked():
                    btn_parent.setChecked(False)
                btn_parent.setIcon(QIcon(os.path.join("icons", "play.png")))
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
            btn = QPushButton()
            btn.setIcon(QIcon(os.path.join("icons", "plus.png")))
            btn.setStyleSheet(button_style)
            def add_firing_and_update_info():
                if self.audio_data is None:
                    return
                self.firework_firing = self.preview_widget.add_time()
                self.update_firework_show_info()
                # Immediately update the status bar to reflect the new firing count
                if hasattr(self, "status_bar") and self.status_bar is not None:
                    self.status_bar.showMessage(self.firework_show_info)
                    self.status_bar.repaint()
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
            btn = QPushButton()
            btn.setIcon(QIcon(os.path.join("icons", "delete.png")))
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
            group_box = QGroupBox()
            group_box.setStyleSheet(button_style)
            layout = QHBoxLayout()
            group_box.setLayout(layout)
            patterns = [
                ("Circle", "circle"),
                ("Chrys", "chrysanthemum"),
                ("Palm", "palm"),
                ("Willow", "willow"),
                ("Peony", "peony"),
                ("Ring", "ring"),
            ]
            combo = QComboBox()
            combo.setStyleSheet(button_style)
            for label, pattern in patterns:
                combo.addItem(label, pattern)
            # Set default pattern
            combo.setCurrentIndex(0)
            def on_pattern_changed(index):
                pattern = combo.itemData(index)
                self.preview_widget.set_pattern(pattern)
                self.update_firework_show_info()
            combo.currentIndexChanged.connect(on_pattern_changed)
            layout.addWidget(combo)
            group_box.setVisible(False)
            return group_box

        self.pattern_selector = create_pattern_selector()

        ###########################################################
        #                                                         #
        #        Number Wheel for Firework Count                  #
        #                                                         #
        ###########################################################

        def create_firework_count_spinner():
            group_box = QGroupBox("Firework Count")
            group_box.setStyleSheet(button_style)
            layout = QHBoxLayout()
            group_box.setLayout(layout)
            spinner = QSpinBox()
            spinner.setMinimum(1)
            spinner.setMaximum(20)
            spinner.setValue(1)
            spinner.setStyleSheet(button_style)
            # Set default firework count
            def on_count_changed(value):
                self.preview_widget.set_number_firings(value)
                self.update_firework_show_info()
            spinner.valueChanged.connect(on_count_changed)
            layout.addWidget(spinner)
            group_box.setVisible(False)  # Hide the group box initially
            return group_box

        self.firework_count_spinner_group = create_firework_count_spinner()

        ###########################################################
        #                                                         #
        #              Load Audio Button                          #
        #                                                         #
        ###########################################################

        # Create a button to load audio files
        self.load_btn = QPushButton()
        self.load_btn.setIcon(QIcon(os.path.join("icons", "upload.png")))
        self.audio_loader = AudioLoader(self)
        self.load_btn.setStyleSheet(button_style)

        self.load_btn.clicked.connect(lambda: self.audio_loader.handle_audio())
        self.load_btn.clicked.connect(self.update_firework_show_info)

        ###########################################################
        #                                                         #
        #    Clear show button (styled to match Add Firing)       #
        #                                                         #
        ###########################################################

        # Create a button to clear the show
        def create_clear_btn():
            btn = QPushButton()
            btn.setIcon(QIcon(os.path.join("icons", "clear-show.png")))
            btn.setStyleSheet(button_style)
            # Also pause the show if playing
            btn.clicked.connect(self.clear_show)
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
        self.status_bar.repaint()  # Force repaint to ensure visibility

        #################################################################
        #                                                               # 
        #        Save and Load Show buttons                             #
        #                                                               #
        #################################################################

        def create_save_btn():
            btn = QPushButton()
            btn.setStyleSheet(button_style)
            btn.clicked.connect(self.show_file_handler.save_show)
            return btn

        def create_load_show_btn():
            btn = QPushButton()
            btn.setStyleSheet(button_style)
            btn.clicked.connect(self.show_file_handler.load_show)
            return btn
        
        # Instantiate and use the handler
        self.show_file_handler = ShowFileHandler(self, button_style)
        self.save_btn = create_save_btn()
        self.save_btn.setIcon(QIcon(os.path.join("icons", "save.png")))
        self.load_show_btn = create_load_show_btn()
        self.load_show_btn.setIcon(QIcon(os.path.join("icons", "load.png")))
        # Add a spacer after save/load buttons for better layout

        ############################################################
        #                                                          #
        #                         File menu                        #
        #                                                          #
        ###########################################################

        # Ensure the menu bar exists before adding the File menu
        if self.menuBar() is None:
            self.setMenuBar(QMenuBar(self))
        file_menu = self.menuBar().addMenu("&File") #type: ignore

        if file_menu is not None:
            # Only set stylesheet for the menu bar
            self.menuBar().setStyleSheet(menu_style) #type: ignore

            # Save Show action
            save_action = QAction(QIcon(os.path.join("icons", "save.png")), "Save...", self)
            save_action.setShortcut("Ctrl+S")
            save_action.triggered.connect(self.save_btn.click)
            file_menu.addAction(save_action)

            # Load Show action
            load_action = QAction(QIcon(os.path.join("icons", "load.png")), "Open...", self)
            load_action.setShortcut("Ctrl+O")
            load_action.triggered.connect(self.load_show_btn.click)
            file_menu.addAction(load_action)

            # Clear Show action
            clear_action = QAction(QIcon(os.path.join("icons", "clear-show.png")), "Clear Show", self)
            clear_action.setShortcut("C")
            clear_action.triggered.connect(self.clear_btn.click)
            file_menu.addAction(clear_action)

            # Exit action
            exit_action = QAction(QIcon(os.path.join("icons", "exit.png")), "Exit", self)
            exit_action.setShortcut("Ctrl+Q")
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)

        ############################################################
        #                                                          #
        #                         Edit menu                        #
        #                                                          #
        ############################################################

        # Ensure the menu bar exists before adding the Edit menu
        if self.menuBar() is None:
            self.setMenuBar(QMenuBar(self))
        edit_menu = self.menuBar().addMenu("&Edit") #type: ignore
        # Set a dark style for the Edit menu to match the rest of the app
        if edit_menu is not None:
            # Play/Pause action (styled and with shortcut)
            play_pause_action = QAction(QIcon(os.path.join("icons", "play.png")), "Play/Pause", self)
            play_pause_action.setShortcut("Space")
            play_pause_action.triggered.connect(lambda: self.play_pause_btn.toggle())
            edit_menu.addAction(play_pause_action)

            # Stop action (styled and with shortcut)
            stop_action = QAction(QIcon(os.path.join("icons", "stop.png")), "Stop", self)
            stop_action.setShortcut("S")
            stop_action.triggered.connect(self.stop_btn.click)
            edit_menu.addAction(stop_action)

            # Load Audio action
            load_audio_action = QAction(QIcon(os.path.join("icons", "upload.png")), "Load Audio...", self)
            load_audio_action.setShortcut("Ctrl+L")
            load_audio_action.triggered.connect(self.load_btn.click)
            edit_menu.addAction(load_audio_action)

            # Add separator
            edit_menu.addSeparator()

            # Add Firing action
            add_firing_action = QAction(QIcon(os.path.join("icons", "plus.png")), "Add Firing", self)
            add_firing_action.setShortcut("A")
            add_firing_action.triggered.connect(self.add_firing_btn.click)
            edit_menu.addAction(add_firing_action)

            # Delete Firing action
            delete_firing_action = QAction(QIcon(os.path.join("icons", "delete.png")), "Delete Firing", self)
            delete_firing_action.setShortcut("D")
            delete_firing_action.triggered.connect(self.delete_firing_btn.click)
            edit_menu.addAction(delete_firing_action)

            # Separator
            edit_menu.addSeparator()
            # Add a submenu for background selection under Edit menu
            background_menu = QMenu("Background", self)
            backgrounds = [
            ("Night Sky", "night"),
            ("Sunset", "sunset"),
            ("City", "city"),
            ("Mountains", "mountains"),
            ("Desert", "desert"),
            ("Custom...", "custom"),
            ]
            for label, bg_name in backgrounds:
                bg_action = QAction(label, self)
                if bg_name != "custom":
                    def make_bg_handler(bg=bg_name):
                        return lambda: self.fireworks_canvas.set_background(bg)
                    bg_action.triggered.connect(make_bg_handler())
                else:
                    def custom_bg_handler():
                        file_dialog = QFileDialog(self)
                        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif)")
                        if file_dialog.exec():
                            selected_files = file_dialog.selectedFiles()
                            if selected_files:
                                image_path = selected_files[0]
                                self.fireworks_canvas.set_background("custom", image_path)
                        bg_action.triggered.connect(custom_bg_handler)
            background_menu.addAction(bg_action)
            edit_menu.addMenu(background_menu)

            # --- Add Padding submenu ---
            padding_menu = QMenu("Padding", self)
            # Store actions so we can update their checked state
            self.padding_actions = []
            for pad_value in [5, 10, 15, 20, 25, 30]:
                pad_action = QAction(f"{pad_value} seconds", self)
                pad_action.setCheckable(True)
                pad_action.setChecked(self.padding == pad_value)
                self.padding_actions.append(pad_action)
                def make_pad_handler(value=pad_value, action=pad_action):
                    def handler(checked=False):
                        self.padding = value  # Ensure self.padding is set
                        self.audio_loader.set_padding(value)  # Pass to audio_loader
                        # Uncheck all others, check only this one
                        for a in self.padding_actions:
                            a.setChecked(a is action)
                    return handler
                pad_action.triggered.connect(make_pad_handler())
                padding_menu.addAction(pad_action)
            # Optionally, add a custom padding dialog
            custom_pad_action = QAction("Custom...", self)
            def custom_pad_handler():
                value, ok = QInputDialog.getInt(self, "Set Custom Padding", "Padding (seconds):", value=self.padding, min=0, max=500)
                if ok:
                    self.padding = value  # Ensure self.padding is set
                    self.audio_loader.set_padding(value)  # Pass to audio_loader
                    # Uncheck all preset actions
                    for a in self.padding_actions:
                        a.setChecked(False)
            custom_pad_action.triggered.connect(custom_pad_handler)
            padding_menu.addAction(custom_pad_action)
            edit_menu.addMenu(padding_menu)
        ############################################################
        #                                                          #
        #                         Help menu                        #
        #                                                          #
        ############################################################

        # Add Help menu only once
        menu_bar = self.menuBar()
        if menu_bar is None:
            menu_bar = QMenuBar(self)
            self.setMenuBar(menu_bar)
        if not any(menu.title() == "&Help" for menu in menu_bar.findChildren(QMenu)):
            help_menu = menu_bar.addMenu("&Help")
            if help_menu is not None:
                help_action = QAction("How to Use Firework Studio", self)
                help_action.setShortcut("F1")
                def show_help_dialog():
                    help_text = (
                        "<b>How to Load Multiple Audio Files:</b><br>"
                        "Click the <b>Load Audio</b> button or use <b>Ctrl+L</b> to select and load audio files.<br>"
                        "You can load more than one file, and it concatenates them in the same order they are displayed in the file dialog window.<br><br>"
                        "<b>Changing Number of Firings and Pattern:</b><br>"
                        "Use the <b>Up/Down arrow keys</b> to change the number of fireworks fired at each time.<br>"
                        "Use the <b>Left/Right arrow keys</b> to change the firework pattern.<br><br>"
                        "<b>Saving and Loading a Show:</b><br>"
                        "Click the <b>Save</b> button or use <b>Ctrl+S</b> to save your show.<br>"
                        "Click the <b>Load</b> button or use <b>Ctrl+O</b> to load a previously saved show.<br><br>"
                        "<b>Preview Widget:</b><br>"
                        "The preview widget lets you select a region of the audio by clicking and dragging.<br>"
                        "Right-click on the preview widget to access context menu options for firings.<br>"
                    )
                    dialog = ToastDialog(help_text, parent=self)
                    dialog.setWindowTitle("Firework Studio Help")
                    dialog.setMinimumWidth(500)
                    dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
                    # Fade out after 4s unless mouse is inside
                    dialog.fade_active = False  # Track if fade is running #type: ignore

                    def fade_step(opacity):
                        if not dialog.fade_active: #type: ignore
                            return  # Stop fading if fade is cancelled
                        if opacity > 0:
                            dialog.setWindowOpacity(opacity)
                            QTimer.singleShot(50, lambda: fade_step(opacity - 0.04))
                        else:
                            dialog.close()
                            dialog.setWindowOpacity(1.0)

                    def cancel_fade(_event=None):
                        dialog.fade_active = False #type: ignore
                        dialog.setWindowOpacity(1.0)

                    def start_fade():
                        dialog.fade_active = True #type: ignore
                        fade_step(1.0)

                    # Properly override event handlers
                    def on_enter(event):
                        cancel_fade(event)
                    def on_leave(event):
                        QTimer.singleShot(4000, start_fade)

                    QTimer.singleShot(400, start_fade)  # Increased from 2500ms to 4000ms
                    dialog.enterEvent = on_enter
                    dialog.leaveEvent = on_leave #type: ignore
                    dialog.show()
                help_action.triggered.connect(show_help_dialog)
                help_menu.addAction(help_action)

        ############################################################
        #                                                          #
        #        Shortcuts                                          #
        #                                                          #
        ############################################################

        # Add global hotkeys using QShortcut so they work when the app is focused
        QShortcut(QKeySequence("Up"), self, activated=lambda: self.firework_count_spinner_group.findChild(QSpinBox).stepUp())  # type: ignore
        QShortcut(QKeySequence("Down"), self, activated=lambda: self.firework_count_spinner_group.findChild(QSpinBox).stepDown())  # type: ignore
        QShortcut(QKeySequence("Left"), self, activated=lambda: self.pattern_selector.findChild(QComboBox).setCurrentIndex(
            max(0, self.pattern_selector.findChild(QComboBox).currentIndex() - 1)
        ))  # type: ignore
        QShortcut(QKeySequence("Right"), self, activated=lambda: self.pattern_selector.findChild(QComboBox).setCurrentIndex(
            min(self.pattern_selector.findChild(QComboBox).count() - 1, self.pattern_selector.findChild(QComboBox).currentIndex() + 1)
        ))  # type: ignore

        # Shortcut to cycle backgrounds (excluding "custom") using the Home key
        def cycle_background():
            backgrounds = ["night", "sunset", "city", "mountains", "desert"]
            current_bg = getattr(self.fireworks_canvas, "current_background", "night")
            idx = backgrounds.index(current_bg) if current_bg in backgrounds else 0
            next_idx = (idx + 1) % len(backgrounds)
            self.fireworks_canvas.set_background(backgrounds[next_idx])
            self.fireworks_canvas.current_background = backgrounds[next_idx] #type: ignore
        QShortcut(QKeySequence("Home"), self, activated=cycle_background)  # type: ignore

        #############################################################
        #                                                          #
        #        Overall UI Elements layout                        #
        #                                                          #
        #############################################################
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        # Add the preview widget and waveform canvas below
        layout.addWidget(self.preview_widget, stretch=0, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.waveform_canvas)
        layout.addWidget(self.fireworks_canvas_container)
        # Add the preview widget and waveform canvas below
        layout.addWidget(self.preview_widget, stretch=0, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(self.waveform_canvas)
        
        ###########################################################
        #                                                         #
        #        Set dark theme palette and styles for the app    #
        #                                                         #
        ###########################################################

        dark_palette = self.palette()
        dark_palette.setColor(self.backgroundRole(), QColor(30, 30, 30))
        dark_palette.setColor(self.foregroundRole(), QColor(255, 215, 0))     # Light gold text
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        self.setPalette(dark_palette)

    ###############################################################
    #                                                             #
    #  HELPER FUNCTIONS for loading audio and segmenting it       #
    #                                                             #
    ###############################################################
    def update_time_label(self):
        """Update current_time_label to always reflect the playhead position."""
        if hasattr(self.preview_widget, "playhead"):
            t = self.preview_widget.playhead.current_time  # type: ignore
            mins = int(t // 60)
            secs = int(t % 60)
            ms = int((t - int(t)) * 1000)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}:{ms:03d}")  # type: ignore
        else:
            self.current_time_label.setText("00:00:000")  # type: ignore
            
    def plot_waveform(self):
        ax = self.waveform_canvas.figure.axes[0]  
        ax.clear()
        if self.audio_data is not None:
            # Create time axis in seconds
            times = np.linspace(0, len(self.audio_data) / self.sr, num=len(self.audio_data))  # type: ignore
            # Downsample for dense signals to avoid smudging
            max_points = 2000  # Adjust for performance/detail
            if len(self.audio_data) > max_points:
                factor = len(self.audio_data) // max_points
                # Use min/max envelope for better visibility
                audio_data_reshaped = self.audio_data[:factor * max_points].reshape(-1, factor)
                envelope_min = audio_data_reshaped.min(axis=1)
                envelope_max = audio_data_reshaped.max(axis=1)
                times_ds = times[:factor * max_points].reshape(-1, factor)
                times_ds = times_ds.mean(axis=1)
                ax.fill_between(times_ds, envelope_min, envelope_max, color="#8fb9bd", alpha=0.7, linewidth=0)
                ax.plot(times_ds, envelope_max, color="#5fd7e6", linewidth=0.7, alpha=0.9)
                ax.plot(times_ds, envelope_min, color="#5fd7e6", linewidth=0.7, alpha=0.9)
            else:
                ax.plot(times, self.audio_data, color="#8fb9bd", linewidth=1.2, alpha=0.95, antialiased=True)
            ax.set_facecolor('#181a20')
            ax.tick_params(axis='y', colors='white')
            ax.set_title("Waveform with Segments", color='white')
            # Plot segment times in subtle gray
            if self.segment_times is not None and isinstance(self.segment_times, (list, tuple, np.ndarray)):
                for t in self.segment_times:
                    if t is not None and np.isfinite(t):
                        ax.axvline(x=t, color="#e3bd13", linestyle="--", linewidth=1.2, alpha=0.7)
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
        # Updates the variable called firework_show_info, not the actual show.
        # This is just for displaying information as it changes
        # Format duration as mm:ss if available
        if self.duration is not None:
            mins, secs = divmod(int(self.duration), 60)
            duration_str = f"{mins:02d}:{secs:02d}"
        else:
            duration_str = "N/A"
        # Always get the latest firings from the preview widget if possible
        if hasattr(self, "preview_widget") and hasattr(self.preview_widget, "firework_times"):
            firing_count = len(self.preview_widget.firework_times) if self.preview_widget.firework_times is not None else 0

        # Get current pattern from pattern_selector
        pattern = "N/A"
        if hasattr(self, "pattern_selector"):
            combo = self.pattern_selector.findChild(QComboBox)
            if combo is not None:
                pattern = combo.currentText()

        # Get number of firings from firework_count_spinner_group
        number_firings = "N/A"
        if hasattr(self, "firework_count_spinner_group"):
            spinner = self.firework_count_spinner_group.findChild(QSpinBox)
            if spinner is not None:
                number_firings = spinner.value()
        # Build info string for status bar (single line, spaced, with separators)
        self.firework_show_info = (
            f"🎆 Pattern: {pattern} | "
            f"Amount: {number_firings} | "
            f"Firings: {firing_count} 🎆"
            f"   🎵 SR: {self.sr if self.sr is not None else 'N/A'} | "
            f"Duration: {duration_str} | "
            f"Segments: {len(self.segment_times) if self.segment_times is not None else 0} "
            f"🎵"
        )
        if hasattr(self, "status_bar") and self.status_bar is not None:
            self.status_bar.showMessage(self.firework_show_info)
            self.status_bar.repaint()  # Force repaint to ensure update

    # Helper to add widgets to toolbar using QWidgetAction
    def add_toolbar_widget(self, widget, toolbar):
        action = QWidgetAction(self)
        action.setDefaultWidget(widget)
        toolbar.addAction(action)