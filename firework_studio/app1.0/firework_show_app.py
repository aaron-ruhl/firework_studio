import numpy as np
import os
# Set matplotlib backend before any other matplotlib imports to prevent window flash
import matplotlib
matplotlib.use('Qt5Agg')  # Force Qt backend, no separate windows
import matplotlib.pyplot as plt
# Disable matplotlib interactive mode to prevent any window popups
plt.ioff()  # Turn off interactive mode
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt import NavigationToolbar2QT
import librosa

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import (
    QColor, QAction, QPalette, QIcon, QShortcut, 
    QKeySequence
)
from PyQt6.QtWidgets import (
    QMenu, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QSizePolicy, 
    QStatusBar, QGroupBox, QComboBox, QMenuBar, 
    QSpinBox, QInputDialog, QTabWidget, QLineEdit, 
    QScrollArea, QApplication, QSpacerItem, QDockWidget,
    QToolBar
)

from firework_canvas_2 import FireworksCanvas
from fireworks_preview import FireworkPreviewWidget
from loader import AudioLoader
from toaster import ToastDialog
from waveform_selection import WaveformSelectionTool
from show_file_handler import ShowFileHandler
from filters import AudioFilter
from collapsible_widget import CollapsibleWidget
from filter_dialog import FilterDialog
from firework_show_helper import FireworkShowHelper
from create_tab import CreateTabHelper
from fireworks_menu import MenuBarHelper

'''THIS IS THE MAIN VIEW FOR THE FIREWORK STUDIO APPLICATION'''
class FireworkShowApp(QMainWindow):
    def clear_show(self):
        # Only clear if audio is loaded
        if self.audio_data is not None and self.sr is not None:
            self.preview_widget.set_show_data(self.audio_data, self.sr, self.segment_times, None, self.duration)
            self.preview_widget.stop_preview()
            self.preview_widget.reset_selected_region()  # Reset selected region in preview widget
            self.fireworks_canvas.update_animation()  # Reset firings displayed
            self.preview_widget.reset_fireworks()  # Reset fireworks in preview widget
            if self.analyzer is not None:
                self.analyzer.clear_signals()  # Clear any analysis signals
                # Clear the legend from the waveform plot
                ax = self.waveform_canvas.figure.axes[0]
                ax.legend_.remove() if ax.legend_ else None
                self.peaks = []
                self.segment_times = []
                self.points = []
                self.onsets = []  
            self.firework_show_helper.plot_waveform()  # Update waveform after clearing
            self.firework_show_helper.update_firework_show_info()  # Update info after clearing

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

    ############################################################
    #                                                          #
    #        Initialize the main window properties             #
    #                                                          #
    ############################################################

    def __init__(self):
        super().__init__()
        self.firework_show_helper = FireworkShowHelper(self)
        # Set window properties first to prevent flash
        self.setWindowTitle("Firework Studio")
        # Set initial geometry to full screen to prevent small window flash
        primary_screen = QApplication.primaryScreen()
        if primary_screen is not None:
            screen_geometry = primary_screen.geometry()
        else:
            # Fallback to a default geometry if no screen is available
            screen_geometry = self.geometry()
        self.setGeometry(screen_geometry)
        self.setWindowState(Qt.WindowState.WindowMaximized)
        
        # Set dark palette 
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 215, 0))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 215, 0))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor(255, 215, 0))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 215, 0))
        dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 215, 0))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(255, 215, 0))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(30, 30, 30))
        self.setPalette(dark_palette)
        self.setAutoFillBackground(True)
        
        # App Initialization
        self.generating_toast = None
        self.clear_btn = None
        self.firework_show_info = "No audio loaded. Load audio to get started. Use the arrow keys to change what firework(s) you add."
        self.audio_data = None
        self.audio_datas = []
        self.sr = None
        self.duration = None
        self.firework_firing = []
        self.start = None
        self.end = None
        self.fireworks_colors = []
        self.filtered_firings = []
        self.paths = []
        self.padding = 0

        # Audio analysis settings
        self.analyzer = None  
        self.peaks = []
        self.segment_times = []
        self.points = []
        self.onsets = []  

        # Filter settings
        self.filter = None  # Will be set to an instance of AudioFilter in loader.py
        self.filter_type = None  
        self.filter_kwargs = {}  
        self.cutoff = None  
        self.order = None  

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

        ############################################################
        #                                                          #
        #        Fireworks Display Preview                         #
        #                                                          #
        ############################################################

        # Fireworks preview widget
        self.preview_widget = FireworkPreviewWidget()
        self.preview_widget.setFixedHeight(80)
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
            # Ensure fireworks stay within the visible area by setting a reasonable minimum height
            container.setMinimumHeight(300)
            container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.fireworks_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.fireworks_canvas.set_fireworks_enabled(False)  # Disable fireworks initially since it is technically starting in a paused state
            return container

        self.fireworks_canvas_container = create_fireworks_canvas_container()
        self.fireworks_canvas.setStyleSheet("background-color: #23242b;")  # Set canvas background color

        ##############################################################
        #                                                            #
        #     Spectrogram Canvas                                     #
        #           - (Placed inside waveform canvas below)          #
        ##############################################################

        # Create a spectrogram canvas for plot_spectrogram
        self.spectrogram_canvas = FigureCanvas(Figure(figsize=(8, 4)))
        self.spectrogram_canvas.setFixedHeight(80)
        self.spectrogram_ax = self.spectrogram_canvas.figure.subplots()
        # Set the background color to black for the spectrogram axes and figure
        self.spectrogram_ax.set_facecolor("#000000")
        self.spectrogram_canvas.figure.set_facecolor("#000000")
        # Show a default message (no plot) until audio is loaded
        self.spectrogram_ax.axis("off")
        self.spectrogram_ax.text(
            0.5, 0.5, "Load audio to get started.",
            color="#ffd700", fontsize=13, ha="center", va="center", transform=self.spectrogram_ax.transAxes,
            bbox=dict(facecolor="#33353c", edgecolor="none", boxstyle="round,pad=0.5")
        )
        self.spectrogram_canvas.draw_idle()
        
        ###########################################################
        #                                                         #
        #           Waveform Canvas                               #
        #                                                         #
        ###########################################################

        # Create a canvas for displaying the waveform needed here for loading audio
        def create_waveform_canvas():
            canvas = FigureCanvas(Figure(figsize=(7, 1)))
            ax = canvas.figure.subplots()
            ax.set_facecolor('black')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            # Remove left/right margin workaround
            canvas.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
            return canvas
        self.waveform_canvas = create_waveform_canvas()
        self.waveform_canvas.setFixedHeight(80)
        self.waveform_canvas.setContentsMargins(0, 0, 0, 0)  # No margin

        # Add NavigationToolbar for zoom/pan (does not disrupt custom selection tool)
        self.waveform_toolbar = NavigationToolbar2QT(self.waveform_canvas, self)

        # Hide the left/right arrow buttons on the waveform toolbar
        for action in self.waveform_toolbar.actions():
            if hasattr(action, "icon") and action.icon():
                icon_name = action.icon().name() if hasattr(action.icon(), "name") else ""
                # Hide actions with standard left/right arrow icons
                if icon_name in ["matplotlib.toolbar_prev", "matplotlib.toolbar_next"]:
                    action.setVisible(False)
                # Alternatively, check by text if icon name is unavailable
                if hasattr(action, "text") and action.text() in ["Back", "Forward"]:
                    action.setVisible(False)

        # Add custom Undo and Redo buttons for marking actions
        self.undo_btn = QPushButton()
        self.undo_btn.setIcon(QIcon(os.path.join("icons", "undo.png")))
        self.undo_btn.setStyleSheet(button_style)
        self.undo_btn.setToolTip("Undo last marking")
        self.undo_btn.clicked.connect(self.firework_show_helper.undo_last_marking)

        self.redo_btn = QPushButton()
        self.redo_btn.setIcon(QIcon(os.path.join("icons", "redo.png")))
        self.redo_btn.setStyleSheet(button_style)
        self.redo_btn.setToolTip("Redo last marking")
        self.redo_btn.clicked.connect(self.firework_show_helper.redo_last_marking)

        # Add these buttons to the waveform toolbar
        self.waveform_toolbar.addSeparator()
        self.waveform_toolbar.addWidget(self.undo_btn)
        self.waveform_toolbar.addWidget(self.redo_btn)
                    
        # Ensure "Home" button always resets the waveform view, even after selection
        def reset_waveform_view():
            # Also clear selection tool region if needed
            if hasattr(self.waveform_selector, "clear_selection"):
                self.waveform_selector.clear_selection(redraw=False)
            legend = self.waveform_canvas.figure.axes[0].get_legend()
            self.firework_show_helper.plot_waveform(current_legend=legend)
            self.firework_show_helper.plot_spectrogram()

        # Patch the NavigationToolbar "home" button to call our reset
        for action in self.waveform_toolbar.actions():
            if hasattr(action, "text") and action.text() == "Home":
                action.triggered.disconnect()
                action.triggered.connect(reset_waveform_view)
                break

        # Style the waveform toolbar for better responsiveness and appearance
        self.waveform_toolbar.setStyleSheet("""
            QToolBar {
            background: #23242b;
            border: none;
            min-height: 36px;
            max-height: 36px;
            padding: 0px;
            margin: 0px;
            }
            QToolButton {
            background: #31323a;
            color: #8fb9bd;  /* Use gray-blue for text to match arrow color */
            border: 1px solid #444657;
            border-radius: 4px;
            font-size: 13px;
            min-width: 32px;
            min-height: 28px;
            margin: 2px;
            padding: 2px 8px;
            }
            QToolButton:hover {
            background: #49505a;
            color: #ffd700;
            border: 1.2px solid #ffd700;
            }
            QToolButton:pressed {
            background: rgba(255, 215, 0, 0.7); /* Light gold, slightly opaque */
            color: #23242b;
            border: 1.2px solid #ffd700;
            }
            QToolButton:checked {
            background: rgba(255, 215, 0, 0.7); /* Light gold, slightly opaque */
            color: #23242b;
            border: 1.2px solid #ffd700;
            }
        """)
        self.waveform_toolbar.setMovable(False)
        self.waveform_toolbar.setIconSize(QSize(22, 22))

        # Add mouse hover event to show time label at cursor 
        self.waveform_time_label = QLabel(self.waveform_canvas)
        self.waveform_time_label.setStyleSheet(
            "background: #23242b; color: #ffd700; border: 1px solid #ffd700; border-radius: 4px; padding: 2px 6px; font-size: 13px;"
        )
        self.waveform_time_label.setVisible(False)

        # Add a waveform panning/selection tool using matplotlib's SpanSelector
        self.waveform_selector = WaveformSelectionTool(self.waveform_canvas, main_window=self)

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

        # Patch the NavigationToolbar "zoom" button to call our zoom_to_selection
        for action in self.waveform_toolbar.actions():
            if hasattr(action, "text") and action.text() == "Zoom":
                action.triggered.disconnect()
                def zoom_and_keep_toggled():
                    self.waveform_selector.zoom_to_selection()
                    action.setChecked(False)  # Keep the button toggled off
                action.triggered.connect(zoom_and_keep_toggled)
                break

        self.waveform_canvas.mpl_connect("figure_leave_event", on_waveform_leave)
        self.waveform_canvas.leaveEvent = lambda event: self.waveform_time_label.setVisible(False)

        ############################################################
        #                                                          #
        #                   Create Tab Widget                      #
        #                                                          #
        ############################################################

        # Instantiate the helper and get the widget for the tab
        self.create_tab_helper = CreateTabHelper(self)
        create_tab_widget = self.create_tab_helper.create_tab_widget

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
                self.firework_show_helper.update_firework_show_info()
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
                self.firework_show_helper.update_firework_show_info()
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
                self.firework_show_helper.update_firework_show_info()
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
                self.firework_show_helper.update_firework_show_info()
            spinner.valueChanged.connect(on_count_changed)
            layout.addWidget(spinner)
            group_box.setVisible(False)  # Hide the group box initially
            return group_box

        self.firework_count_spinner_group = create_firework_count_spinner()


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
        #                                                          #
        #                       Status Bar                         #
        #                                                          #
        ############################################################
        # Add info label to display audio loading status
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(self.firework_show_info)
        self.status_bar.repaint()  # Force repaint to ensure visibility

        # Ensure status bar stays visible in fullscreen by raising it above other widgets
        self.status_bar.raise_()
        # Optionally, set a custom style for the status bar (without z-index, which is unsupported in Qt)
        self.status_bar.setStyleSheet("QStatusBar { background: #23242b; color: #ffd700; }")

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
        self.load_btn.clicked.connect(self.firework_show_helper.update_firework_show_info)

        ############################################################
        #                                                          #
        #       Menu Bar                                           #
        #                                                          #
        ############################################################

        # Instantiate the menu helper
        self.menu_helper = MenuBarHelper(self, button_style, menu_style)

        ############################################################
        #                                                          #
        #       Toolbar with all buttons                           #
        #                                                          #
        ############################################################
        # Create a toolbar and add all main buttons in a professional layout
        toolbar = QToolBar("Main Controls")
        toolbar.setMovable(True)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setStyleSheet("""
            QToolBar {
            background: #23242b;
            border-top: 1px solid #444657;
            border-bottom: none;
            spacing: 8px;
            padding: 8px 16px;
            min-height: 48px;
            }
            QToolButton {
            background: #31323a;
            color: #ffd700;
            border: 1px solid #444657;
            border-radius: 6px;
            font-size: 14px;
            min-width: 40px;
            min-height: 36px;
            margin: 4px;
            padding: 4px 12px;
            }
            QToolButton:hover {
            background: #49505a;
            color: #ffd700;
            border: 1.2px solid #ffd700;
            }
            QToolButton:pressed {
            background: #353a40;
            color: #ffd700;
            border: 1.2px solid #ffd700;
            }
            QToolButton:checked {
            background: #23242b;
            color: #ffd700;
            border: 1.2px solid #ffd700;
            }
        """)

        # Add buttons to toolbar in logical order with spacers
        toolbar.addWidget(self.load_btn)
        toolbar.addSeparator()
        toolbar.addWidget(self.save_btn)
        toolbar.addWidget(self.load_show_btn)
        toolbar.addSeparator()
        toolbar.addWidget(self.play_pause_btn)
        toolbar.addWidget(self.stop_btn)
        toolbar.addSeparator()
        toolbar.addWidget(self.add_firing_btn)
        toolbar.addWidget(self.delete_firing_btn)
        toolbar.addWidget(self.clear_btn)
        toolbar.addSeparator()
        toolbar.addWidget(self.pattern_selector)
        toolbar.addWidget(self.firework_count_spinner_group)

        # Add a stretch to push right-aligned controls (if needed)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        # Make sure the toolbar is added to the window
        # Change from BottomToolBarArea to TopToolBarArea for visibility
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, toolbar)

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

        #############################################################
        #                                                          #
        #        Overall UI Elements layout                        #
        #                                                          #
        #############################################################
        # Delay showing the collapsible waveform until after the window is shown to avoid flash
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Use a simple vertical layout without scroll area
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        waveform_container = QWidget()
        waveform_container.setStyleSheet("""
            background-color: #181a20;
            color: #8fb9bd;
        """)
        # Set maximum size policy for height so collapsible widget works properly
        waveform_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        waveform_layout = QVBoxLayout(waveform_container)

        waveform_layout.setContentsMargins(40, 0, 40, 0)
        waveform_layout.setSpacing(0)
        waveform_container.setStyleSheet("""
            background-color: #000000;
            color: #8fb9bd;
        """)
        waveform_layout.addWidget(self.waveform_toolbar)
        waveform_layout.addWidget(self.waveform_canvas)

        self.spectrogram_canvas.setContentsMargins(0, 0, 0, 0)
        self.spectrogram_canvas.setFixedHeight(80)
        self.spectrogram_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        waveform_layout.addWidget(self.spectrogram_canvas)

        # Create but do not show collapsible_waveform yet
        self.collapsible_waveform = CollapsibleWidget("Waveform & Spectrogram", waveform_container)
        # Add with stretch=0 so it only takes needed space
        layout.addWidget(self.collapsible_waveform, stretch=0)

        # Add preview timeline widget after collapsible widget with stretch=0 so it stays fixed size
        layout.addWidget(self.preview_widget, stretch=0)

        # Add tab widget after preview widget with stretch=1 so it expands/contracts
        tab_widget = QTabWidget()
        tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444657; background: #23242b; }
            QTabBar::tab { background: #31323a; color: #ffd700; border: 1px solid #444657; border-radius: 4px; min-width: 120px; min-height: 32px; font-size: 13px; }
            QTabBar::tab:selected { background: #23242b; color: #ffd700; border: 1.2px solid #ffd700; }
            QTabBar::tab:hover { background: #49505a; color: #ffd700; }
        """)

        tab_widget.addTab(self.fireworks_canvas_container, "Preview")
        tab_widget.addTab(create_tab_widget, "Create")
        
        # Add to main layout with stretch=1 so it takes remaining space and grows/shrinks
        layout.addWidget(tab_widget, stretch=1)

    def reset_filter_to_original(self):
        """Reset audio filter and restore original audio data."""
        if self.filter and self.filter.original_audio is not None:
            self.audio_data = self.filter.original_audio.copy()
            # Replot the waveform to show the original audio
            if hasattr(self, 'firework_show_helper') and self.firework_show_helper:
                self.firework_show_helper.plot_waveform()
                self.firework_show_helper.plot_spectrogram()
            return True
        return False

    def showEvent(self, event):
        super().showEvent(event)
