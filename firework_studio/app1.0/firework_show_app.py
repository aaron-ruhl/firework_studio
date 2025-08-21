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
import librosa.display

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import (
    QColor, QAction, QPalette, QIcon, QShortcut, 
    QKeySequence
)
from PyQt6.QtWidgets import (
    QMenu, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLabel, QFileDialog, 
    QSizePolicy, QStatusBar, QGroupBox, QComboBox,
    QMenuBar, QWidgetAction, QSpinBox, QInputDialog,
    QTabWidget, QLineEdit, QScrollArea, QDoubleSpinBox,
    QDialog
)

from firework_canvas_2 import FireworksCanvas
from fireworks_preview import FireworkPreviewWidget
from loader import AudioLoader
from toaster import ToastDialog
from waveform_selection import WaveformSelectionTool
from show_file_handler import ShowFileHandler
from filters import AudioFilter
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QToolButton
class CollapsibleWidget(QWidget):
    def __init__(self, title, child_widget, parent=None):
        super().__init__(parent)
        self.toggle_btn = QToolButton(text=title)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(True)
        self.toggle_btn.setArrowType(Qt.ArrowType.DownArrow)
        self.toggle_btn.setStyleSheet("""
            QToolButton {
            background: #23242b;
            color: #ffd700;
            border: 1px solid #444657;
            border-radius: 4px;
            font-size: 13px;
            min-height: 28px;
            padding: 2px 8px;
            }
            QToolButton:checked {
            background: #31323a;
            color: #ffd700;
            }
        """)
        # Set maximum size policy so widget can shrink properly
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.child_widget = child_widget
        self.child_widget.setVisible(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toggle_btn)
        layout.addWidget(self.child_widget)
        self.toggle_btn.toggled.connect(self.toggle_child)
        self.toggle_btn.toggled.connect(self.update_arrow)
        self.update_arrow(self.toggle_btn.isChecked())

    def toggle_child(self, checked):
        self.child_widget.setVisible(checked)
        # Immediately update geometry to trigger layout recalculation
        self.updateGeometry()
        
        # If we have a reference to the scroll area, adjust its height dynamically
        main_window = self.window()
        if main_window and hasattr(main_window, 'scroll_area'):
            if checked:
                # Expanded: Allow scroll area to grow
                # toolbar (36px) + waveform (80px) + spectrogram (80px) + preview (80px) + padding (60px)
                expanded_height = 36 + 80 + 80 + 80 + 60  # 336px
                main_window.scroll_area.setMinimumHeight(expanded_height)
                main_window.scroll_area.setMaximumHeight(600)
            else:
                # Collapsed: Shrink scroll area to just preview widget + button height
                # preview (80px) + button (28px) + padding (20px)
                collapsed_height = 80 + 28 + 20  # 128px
                main_window.scroll_area.setMinimumHeight(collapsed_height)
                main_window.scroll_area.setMaximumHeight(collapsed_height)
        
        # Force the main window to adjust its layout
        if main_window:
            main_window.updateGeometry()
            # Force layout update on the central widget
            central_widget = main_window.centralWidget()
            if central_widget:
                central_widget.layout().invalidate()
                central_widget.layout().activate()

    def update_arrow(self, checked):
        self.toggle_btn.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)
    
    def sizeHint(self) -> QSize:
        if self.child_widget.isVisible():
            return super().sizeHint()
        else:
            # When collapsed, only account for the button height
            button_height = self.toggle_btn.sizeHint().height()
            return QSize(super().sizeHint().width(), button_height)
    
    def minimumSizeHint(self) -> QSize:
        # When collapsed, minimum size is just the button
        if not self.child_widget.isVisible():
            return self.toggle_btn.minimumSizeHint()
        return super().minimumSizeHint()
    
    def hasHeightForWidth(self) -> bool:
        return False
    
    def heightForWidth(self, width: int) -> int:
        if self.child_widget.isVisible():
            return super().sizeHint().height()
        else:
            return self.toggle_btn.sizeHint().height()
        # Expanded: include child_widget size
        if self.toggle_btn.isChecked() and self.child_widget.isVisible():
            btn_hint = self.toggle_btn.sizeHint()
            child_hint = self.child_widget.sizeHint()
            return QSize(
                max(btn_hint.width(), child_hint.width()),
                btn_hint.height() + child_hint.height()
            )
        else:
            # Collapsed: only show button
            btn_hint = self.toggle_btn.sizeHint()
            return QSize(btn_hint.width(), btn_hint.height())

    def minimumSizeHint(self) -> QSize:
        # Expanded: include child_widget minimum size
        if self.toggle_btn.isChecked() and self.child_widget.isVisible():
            btn_min = self.toggle_btn.minimumSizeHint()
            child_min = self.child_widget.minimumSizeHint()
            return QSize(
                max(btn_min.width(), child_min.width()),
                btn_min.height() + child_min.height()
            )
        else:
            # Collapsed: only show button
            btn_min = self.toggle_btn.minimumSizeHint()
            return QSize(btn_min.width(), btn_min.height())


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

    ############################################################
    #                                                          #
    #        Initialize the main window properties             #
    #                                                          #
    ############################################################

    def __init__(self):
        super().__init__()
        
        # Set window properties first to prevent flash
        self.setWindowTitle("Firework Studio")
        # Set initial geometry to full screen to prevent small window flash
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.setWindowState(Qt.WindowState.WindowMaximized)
        
        # Set dark palette immediately
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
            # Ensure fireworks stay within the visible area by setting a minimum height
            container.setMinimumHeight(700)
            container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.fireworks_canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.fireworks_canvas.set_fireworks_enabled(False)  # Disable fireworks initially since it is technically starting in a paused state
            return container

        self.fireworks_canvas_container = create_fireworks_canvas_container()
        self.fireworks_canvas.setStyleSheet("background-color: #23242b;")  # Set canvas background color

        #######################################################################
        #                                                                     #
        #                           Spectrogram Display                       #
        #                                                                     #
        #######################################################################


        # Create a spectrogram canvas for later use in plot_spectrogram
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

        # Add a label to show current frequency (y-axis) in kHz at mouse location
        self.spectrogram_freq_label = QLabel(self.spectrogram_canvas)
        self.spectrogram_freq_label.setStyleSheet(
            "background: #23242b; color: #ffd700; border: 1px solid #ffd700; border-radius: 4px; padding: 2px 6px; font-size: 13px;"
        )
        self.spectrogram_freq_label.setVisible(False)

        def on_spectrogram_motion(event):
            if event.inaxes == self.spectrogram_ax and event.xdata is not None and event.ydata is not None:
                freq_khz = event.ydata / 1000.0
                # Get dB value at mouse location
                x, y = event.xdata, event.ydata
                # Find nearest pixel in spectrogram data
                S = librosa.stft(self.audio_data, n_fft=2048, hop_length=512)
                S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)
                # Convert axes coords to spectrogram array indices
                times = librosa.frames_to_time(np.arange(S_db.shape[1]), sr=self.sr, hop_length=512)
                freqs = librosa.fft_frequencies(sr=self.sr, n_fft=2048)
                # Find closest indices
                time_idx = np.argmin(np.abs(times - x))
                freq_idx = np.argmin(np.abs(freqs - y))
                db_val = S_db[freq_idx, time_idx] if 0 <= freq_idx < S_db.shape[0] and 0 <= time_idx < S_db.shape[1] else None
                if db_val is not None:
                    self.spectrogram_freq_label.setText(f"{db_val:.1f} dB @ {freq_khz:.2f} kHz")
                else:
                    self.spectrogram_freq_label.setText(f"{freq_khz:.2f} kHz")
                # Position label near mouse, keep inside widget
                label_width = self.spectrogram_freq_label.sizeHint().width()
                label_height = self.spectrogram_freq_label.sizeHint().height()
                x_widget = int(event.x) - label_width // 2
                y_widget = int(event.y) - label_height - 8
                x_widget = max(0, min(x_widget, self.spectrogram_canvas.width() - label_width))
                y_widget = max(0, y_widget)
                self.spectrogram_freq_label.move(x_widget, y_widget)
                self.spectrogram_freq_label.setVisible(True)
            else:
                self.spectrogram_freq_label.setVisible(False)

        def on_spectrogram_leave(event):
            self.spectrogram_freq_label.setVisible(False)

        self.spectrogram_canvas.mpl_connect("motion_notify_event", on_spectrogram_motion)
        self.spectrogram_canvas.mpl_connect("figure_leave_event", on_spectrogram_leave)
        self.spectrogram_canvas.leaveEvent = lambda event: self.spectrogram_freq_label.setVisible(False)
        
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
            # Remove left/right margin workaround
            canvas.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
            return canvas
        self.waveform_canvas = create_waveform_canvas()
        self.waveform_canvas.setFixedHeight(80)
        self.waveform_canvas.setContentsMargins(0, 0, 0, 0)  # No margin

        # Add NavigationToolbar for zoom/pan (does not disrupt custom selection tool)
        self.waveform_toolbar = NavigationToolbar2QT(self.waveform_canvas, self)

        # Ensure "Home" button always resets the waveform view, even after selection
        def reset_waveform_view():
            # Also clear selection tool region if needed
            if hasattr(self.waveform_selector, "clear_selection"):
                self.waveform_selector.clear_selection(redraw=False)
            legend = self.waveform_canvas.figure.axes[0].get_legend()
            self.plot_waveform(current_legend=legend)
            self.plot_spectrogram()

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

        # This will be the "Create" tab content

        create_tab_widget = QWidget()

        # Create a scroll area for the tab content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QWidget {
            background-color: #23242b;
            color: #ffd700;
            font-size: 15px;
            font-family: 'Segoe UI', 'Arial', sans-serif;
            }
            QGroupBox {
            background-color: #181a20;
            border: 2px solid #ffd700;
            border-radius: 8px;
            color: #ffd700;
            font-size: 16px;
            font-weight: bold;
            margin-top: 12px;
            margin-bottom: 12px;
            padding: 8px 12px;
            }
            QGroupBox:title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: #ffd700;
            font-size: 16px;
            font-weight: bold;
            }
            QLabel {
            color: #ffd700;
            font-size: 15px;
            font-weight: 500;
            padding: 4px 0;
            }
            QComboBox, QSpinBox {
            background-color: #23242b;
            color: #ffd700;
            border: 2px solid #ffd700;
            border-radius: 6px;
            font-size: 15px;
            font-weight: bold;
            min-width: 60px;
            min-height: 32px;
            padding: 4px 12px;
            margin: 4px 0;
            }
            QPushButton {
            background-color: #ffd700;
            color: #23242b;
            border: 2px solid #ffd700;
            border-radius: 6px;
            font-size: 15px;
            font-weight: bold;
            min-width: 80px;
            min-height: 32px;
            margin: 6px 0;
            }
            QPushButton:hover {
            background-color: #fffbe6;
            color: #23242b;
            border: 2px solid #ffd700;
            }
            QMenu {
            background-color: #23242b;
            color: #ffd700;
            border: 2px solid #ffd700;
            border-radius: 8px;
            font-size: 15px;
            padding: 8px 0px;
            }
            QTabWidget::pane {
            border: 2px solid #ffd700;
            background: #23242b;
            }
            QTabBar::tab {
            background: #181a20;
            color: #ffd700;
            border: 2px solid #ffd700;
            border-radius: 6px;
            min-width: 140px;
            min-height: 36px;
            font-size: 15px;
            font-weight: bold;
            margin: 4px;
            }
            QTabBar::tab:selected {
            background: #ffd700;
            color: #23242b;
            border: 2px solid #ffd700;
            }
            QTabBar::tab:hover {
            background-color: #fffbe6;
            color: #23242b;
            }
        """)

        # Create the actual content widget and layout
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Remove left/right margins
        content_widget.setContentsMargins(0, 0, 0, 0)  # Remove left/right margins

        # Placeholder for additional vertical sections
        main_layout.addWidget(QLabel("Lay down firing..."))

        # Add a professional label for "Analysis Settings"
        analysis_label = QLabel("Analysis Settings")
        analysis_label.setStyleSheet("""
            QLabel {
                color: #ffd700;
                font-size: 20px;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 8px 0 12px 0;
                border-bottom: 2px solid #ffd700;
                margin-bottom: 12px;
                background: transparent;
            }
        """)
        analysis_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        main_layout.addWidget(analysis_label)
        # Responsive horizontal layout for analysis section
        analysis_section = QHBoxLayout()
        analysis_section.setSpacing(12)
        analysis_section.setContentsMargins(0, 0, 0, 0)
        
        # --- Segment Settings ---
        segment_group = QGroupBox("Segment Settings")
        segment_layout = QVBoxLayout()
        min_segments_spin = QSpinBox()
        min_segments_spin.setRange(1, 50)
        min_segments_spin.setValue(2)
        min_segments_spin.setPrefix("Min: ")
        min_segments_spin.setStyleSheet("font-size: 10px;")
        segment_layout.addWidget(min_segments_spin)
        max_segments_spin = QSpinBox()
        max_segments_spin.setRange(2, 50)
        max_segments_spin.setValue(19)
        max_segments_spin.setPrefix("Max: ")
        max_segments_spin.setStyleSheet("font-size: 10px;")
        segment_layout.addWidget(max_segments_spin)
        n_mfcc_spin = QSpinBox()
        n_mfcc_spin.setRange(1, 40)
        n_mfcc_spin.setValue(13)
        n_mfcc_spin.setPrefix("MFCC: ")
        n_mfcc_spin.setStyleSheet("font-size: 10px;")
        segment_layout.addWidget(n_mfcc_spin)
        dct_type_spin = QSpinBox()
        dct_type_spin.setRange(1, 4)
        dct_type_spin.setValue(2)
        dct_type_spin.setPrefix("DCT: ")
        dct_type_spin.setStyleSheet("font-size: 10px;")
        segment_layout.addWidget(dct_type_spin)
        n_fft_spin = QSpinBox()
        n_fft_spin.setRange(256, 8192)
        n_fft_spin.setValue(2048)
        n_fft_spin.setPrefix("FFT: ")
        n_fft_spin.setStyleSheet("font-size: 10px;")
        segment_layout.addWidget(n_fft_spin)
        hop_length_segments_spin = QSpinBox()
        hop_length_segments_spin.setRange(64, 4096)
        hop_length_segments_spin.setValue(512)
        hop_length_segments_spin.setPrefix("Hop: ")
        hop_length_segments_spin.setStyleSheet("font-size: 10px;")
        segment_layout.addWidget(hop_length_segments_spin)
        segment_group.setLayout(segment_layout)
        segment_group.setMinimumWidth(220)
        segment_group.setMaximumWidth(260)
        analysis_section.addWidget(segment_group)

        # --- Onset Settings ---
        onset_group = QGroupBox("Onset Settings")
        onset_layout = QVBoxLayout()
        min_onsets_spin = QSpinBox()
        min_onsets_spin.setRange(1, 100)
        min_onsets_spin.setValue(5)
        min_onsets_spin.setPrefix("Min: ")
        min_onsets_spin.setStyleSheet("font-size: 10px;")
        onset_layout.addWidget(min_onsets_spin)
        max_onsets_spin = QSpinBox()
        max_onsets_spin.setRange(1, 100)
        max_onsets_spin.setValue(20)
        max_onsets_spin.setPrefix("Max: ")
        max_onsets_spin.setStyleSheet("font-size: 10px;")
        onset_layout.addWidget(max_onsets_spin)
        hop_length_onsets_spin = QSpinBox()
        hop_length_onsets_spin.setRange(64, 4096)
        hop_length_onsets_spin.setValue(512)
        hop_length_onsets_spin.setPrefix("Hop: ")
        hop_length_onsets_spin.setStyleSheet("font-size: 10px;")
        onset_layout.addWidget(hop_length_onsets_spin)
        backtrack_box = QComboBox()
        backtrack_box.addItems(["True", "False"])
        backtrack_box.setCurrentIndex(0)
        backtrack_box.setEditable(False)
        backtrack_box.setMinimumWidth(80)
        backtrack_box.setMaximumWidth(120)
        backtrack_box.setStyleSheet("font-size: 10px;")
        backtrack_label = QLabel(
            "<b>Backtrack:</b><br>"
            "This is primarily useful when using onsets as slice points for segmentation.<br>"
            "If enabled, detected onsets are shifted to the nearest preceding peak in the signal."
        )
        backtrack_label.setWordWrap(True)
        backtrack_label.setStyleSheet("font-size: 11px; color: #ffd700; padding: 2px 0;")
        backtrack_label.setMinimumHeight(9)
        onset_layout.addWidget(backtrack_label)
        onset_layout.addWidget(backtrack_box)
        normalize_box = QComboBox()
        normalize_box.addItems(["True", "False"])
        normalize_box.setCurrentIndex(1)
        normalize_box.setEditable(False)
        normalize_box.setMinimumWidth(80)
        normalize_box.setMaximumWidth(120)
        normalize_box.setStyleSheet("font-size: 10px;")
        onset_layout.addWidget(QLabel("Normalize:"))
        onset_layout.addWidget(normalize_box)
        onset_group.setLayout(onset_layout)
        onset_group.setMinimumWidth(220)
        onset_group.setMaximumWidth(260)
        analysis_section.addWidget(onset_group)

        # --- Interesting Points Settings ---
        points_group = QGroupBox("Interesting Points Settings")
        points_layout = QVBoxLayout()
        min_points_spin = QSpinBox()
        min_points_spin.setRange(1, 100)
        min_points_spin.setValue(5)
        min_points_spin.setPrefix("Min: ")
        min_points_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(min_points_spin)
        max_points_spin = QSpinBox()
        max_points_spin.setRange(1, 100)
        max_points_spin.setValue(20)
        max_points_spin.setPrefix("Max: ")
        max_points_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(max_points_spin)
        pre_max_spin = QSpinBox()
        pre_max_spin.setRange(0, 20)
        pre_max_spin.setValue(3)
        pre_max_spin.setPrefix("PreMax: ")
        pre_max_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(pre_max_spin)
        post_max_spin = QSpinBox()
        post_max_spin.setRange(0, 20)
        post_max_spin.setValue(3)
        post_max_spin.setPrefix("PostMax: ")
        post_max_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(post_max_spin)
        pre_avg_distance_spin = QSpinBox()
        pre_avg_distance_spin.setRange(0, 20)
        pre_avg_distance_spin.setValue(3)
        pre_avg_distance_spin.setPrefix("PreAvgDist: ")
        pre_avg_distance_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(pre_avg_distance_spin)
        post_avg_distance_spin = QSpinBox()
        post_avg_distance_spin.setRange(0, 20)
        post_avg_distance_spin.setValue(5)
        post_avg_distance_spin.setPrefix("PostAvgDist: ")
        post_avg_distance_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(post_avg_distance_spin)
        delta_spin = QSpinBox()
        delta_spin.setRange(0, 100)
        delta_spin.setValue(5)
        delta_spin.setPrefix("Delta x0.1: ")
        delta_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(delta_spin)
        moving_avg_wait_spin = QSpinBox()
        moving_avg_wait_spin.setRange(0, 20)
        moving_avg_wait_spin.setValue(5)
        moving_avg_wait_spin.setPrefix("MA Wait: ")
        moving_avg_wait_spin.setStyleSheet("font-size: 10px;")
        points_layout.addWidget(moving_avg_wait_spin)
        points_group.setLayout(points_layout)
        points_group.setMinimumWidth(220)
        points_group.setMaximumWidth(260)
        analysis_section.addWidget(points_group)

        # --- Peak Settings ---
        peak_group = QGroupBox("Peak Settings")
        peak_layout = QVBoxLayout()
        min_peaks_spin = QSpinBox()
        min_peaks_spin.setRange(1, 100)
        min_peaks_spin.setValue(10)
        min_peaks_spin.setPrefix("Min: ")
        min_peaks_spin.setStyleSheet("font-size: 10px;")
        peak_layout.addWidget(min_peaks_spin)
        max_peaks_spin = QSpinBox()
        max_peaks_spin.setRange(1, 100)
        max_peaks_spin.setValue(30)
        max_peaks_spin.setPrefix("Max: ")
        max_peaks_spin.setStyleSheet("font-size: 10px;")
        peak_layout.addWidget(max_peaks_spin)
        scoring_box = QComboBox()
        scoring_box.addItems(["squared", "absolute", "relative", "sharp", "custom"])
        scoring_box.setCurrentIndex(0)
        scoring_box.setMinimumWidth(100)
        scoring_box.setMaximumWidth(140)
        scoring_box.setStyleSheet("font-size: 10px;")
        label = QLabel(
            "<b>Scoring:</b><br>"
            "This enables the user to set the scoring method used to determine which peaks to keep.<br>"
            "<b>Current options:</b> <code>absolute</code>, <code>relative</code>, <code>sharp</code>, <code>custom</code>."
        )
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 11px; color: #ffd700; padding: 2px 0;")
        label.setMinimumHeight(9)
        peak_layout.addWidget(label)
        peak_layout.addWidget(scoring_box)
        custom_function_edit = QLineEdit()
        custom_function_edit.setPlaceholderText("custom_scoring_method(audio_data_region, zero_crossings)")
        custom_function_edit.setStyleSheet("font-size: 10px;")
        label = QLabel(
            "<b>Custom Function:</b><br>"
            "Define a lambda function for custom peak scoring.<br>"
            "Example: <br><code>lambda audio_data_region, zero_crossings: np.abs(audio_data_region[zero_crossings])</code><br>"
            "<b>Arguments:</b>"
            "<ul>"
            "<li><b>audio_data_region</b>: The audio currently selected by the user.</li>"
            "<li><b>zero_crossings</b>: Locations of detected zero crossings (all found peaks).</li>"
            "</ul>"
        )
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 11px; color: #ffd700; padding: 2px 0;")
        label.setMinimumHeight(9)
        peak_layout.addWidget(label)
        peak_layout.addWidget(custom_function_edit)
        peak_group.setLayout(peak_layout)
        peak_group.setMinimumWidth(280)
        peak_group.setMaximumWidth(400)
        analysis_section.addWidget(peak_group, stretch=2)

        # --- Connect fields to analyzer setters ---
        def update_segment_settings():
            if self.analyzer is not None:
                self.analyzer.set_segment_settings(
                n_mfcc=n_mfcc_spin.value(),
                min_segments=min_segments_spin.value(),
                max_segments=max_segments_spin.value(),
                dct_type=dct_type_spin.value(),
                n_fft=n_fft_spin.value(),
                hop_length_segments=hop_length_segments_spin.value()
                )
        for spin in [n_mfcc_spin, min_segments_spin, dct_type_spin, n_fft_spin, hop_length_segments_spin]:
            spin.valueChanged.connect(update_segment_settings)
        min_segments_spin.valueChanged.connect(update_segment_settings)
        max_segments_spin.valueChanged.connect(update_segment_settings)

        def update_onset_settings():
            if self.analyzer is not None:
                self.analyzer.set_onset_settings(
                min_onsets=min_onsets_spin.value(),
                max_onsets=max_onsets_spin.value(),
                hop_length_onsets=hop_length_onsets_spin.value(),
                backtrack=backtrack_box.currentText() == "True",
                normalize=normalize_box.currentText() == "True"
                )
        for spin in [min_onsets_spin, max_onsets_spin, hop_length_onsets_spin]:
            spin.valueChanged.connect(update_onset_settings)
        backtrack_box.currentIndexChanged.connect(update_onset_settings)
        normalize_box.currentIndexChanged.connect(update_onset_settings)

        def update_points_settings():
            if self.analyzer is not None:
                self.analyzer.set_interesting_points_settings(
                    min_points=min_points_spin.value(),
                    max_points=max_points_spin.value(),
                    pre_max=pre_max_spin.value(),
                    post_max=post_max_spin.value(),
                    pre_avg_distance=pre_avg_distance_spin.value(),
                    post_avg_distance=post_avg_distance_spin.value(),
                    delta=delta_spin.value() * 0.1,
                    moving_avg_wait=moving_avg_wait_spin.value()
                )
        for spin in [min_points_spin, max_points_spin, pre_max_spin, post_max_spin, pre_avg_distance_spin, post_avg_distance_spin, delta_spin, moving_avg_wait_spin]:
            spin.valueChanged.connect(update_points_settings)

        def update_peak_settings():
            custom_func = None
            text = custom_function_edit.text().strip()
            if text:
                try:
                    # Only allow lambda expressions for safety
                    if text.startswith("lambda"):
                        custom_func = eval(text, {"__builtins__": {}}, {})
                except Exception:
                    custom_func = None
            if self.analyzer is not None:
                self.analyzer.set_peak_settings(
                    min_peaks=min_peaks_spin.value(),
                    max_peaks=max_peaks_spin.value(),
                    scoring=scoring_box.currentText(),
                    custom_scoring_method=custom_func
                )
        for spin in [min_peaks_spin, max_peaks_spin]:
            spin.valueChanged.connect(update_peak_settings)
        scoring_box.currentIndexChanged.connect(update_peak_settings)
        custom_function_edit.textChanged.connect(update_peak_settings)

        # Add the horizontal analysis section to the main vertical layout
        main_layout.addLayout(analysis_section)

        content_widget.setLayout(main_layout)
        scroll_area.setWidget(content_widget)
        scroll_area.setContentsMargins(0, 0, 0, 0)
        # Set the scroll area as the only child of the tab widget
        create_tab_widget_layout = QVBoxLayout(create_tab_widget)
        create_tab_widget_layout.setContentsMargins(0, 8, 0, 8)
        create_tab_widget_layout.addWidget(scroll_area)
        create_tab_widget.setLayout(create_tab_widget_layout)
        create_tab_widget.setContentsMargins(0, 0, 0, 0)

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
        #                         Analysis menu                    #
        #                                                          #
        ############################################################

        # Ensure the menu bar exists before adding the Analysis menu
        menu_bar = self.menuBar()
        if menu_bar is None:
            menu_bar = QMenuBar(self)
            self.setMenuBar(menu_bar)
        analysis_menu = None
        # Find existing Analysis menu or create it
        for menu in menu_bar.findChildren(QMenu):
            if menu.title() == "&Analysis":
                analysis_menu = menu
                break
        if analysis_menu is None:
            analysis_menu = menu_bar.addMenu("&Analysis")
        
        # Segment Audio action
        segment_action = QAction("Segment Audio", self)
        segment_action.setShortcut("Ctrl+M")
        def segment_audio():
            if self.analyzer is not None:
                # Only show toast the first time segments are found
                self.analyzer.analyze_segments()
                self._segments_toast_shown = False

            # Display a toast/loading dialog while processing segments
            toast = ToastDialog("Analyzing segments...")
            geo = self.geometry() #type: ignore
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()

            # clear the loading toast and let user know it is not doing anything because no audio is loaded
            if self.audio_data is None or len(self.audio_data) == 0:
                def show_no_audio_toast():
                    toast = ToastDialog("No audio data available for analysis.", parent=self)
                    geo = self.geometry()
                    x = geo.x() + geo.width() - toast.width() - 40
                    y = geo.y() + geo.height() - toast.height() - 40
                    toast.move(x, y)
                    toast.show()
                    QTimer.singleShot(2500, toast.close)
                show_no_audio_toast()

        segment_action.triggered.connect(segment_audio)
        if analysis_menu is not None:
            analysis_menu.addAction(segment_action)

        # Interesting Points action
        interesting_points_action = QAction("Find Interesting Points", self)
        interesting_points_action.setShortcut("Ctrl+I")
        def find_interesting_points():
            # Only show toast the first time interesting points are found
            if self.analyzer is not None:
                self.analyzer.analyze_interesting_points()
                self._interesting_points_toast_shown = False

            # Display a toast/loading dialog while processing interesting points
            toast = ToastDialog("Analyzing interesting points...")
            geo = self.geometry() #type: ignore
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()

            # clear the loading toast and let user know it is not doing anything because no audio is loaded
            if self.audio_data is None or len(self.audio_data) == 0:
                def show_no_audio_toast():
                    toast = ToastDialog("No audio data available for analysis.", parent=self)
                    geo = self.geometry()
                    x = geo.x() + geo.width() - toast.width() - 40
                    y = geo.y() + geo.height() - toast.height() - 40
                    toast.move(x, y)
                    toast.show()
                    QTimer.singleShot(2500, toast.close)
                show_no_audio_toast()
                    
        interesting_points_action.triggered.connect(find_interesting_points)
        if analysis_menu is not None:
            analysis_menu.addAction(interesting_points_action)

        # Onsets action
        onsets_action = QAction("Find Onsets", self)
        onsets_action.setShortcut("Ctrl+N")
        def find_onsets():
            # Only show toast the first time onsets are found
            if self.analyzer is not None:
                self.analyzer.analyze_onsets()
                self._onsets_toast_shown = False

            # Display a toast/loading dialog while processing onsets
            toast = ToastDialog("Analyzing onsets...")
            geo = self.geometry() #type: ignore
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()

            # clear the loading toast and let user know it is not doing anything because no audio is loaded
            if self.audio_data is None or len(self.audio_data) == 0:
                def show_no_audio_toast():
                    toast = ToastDialog("No audio data available for analysis.", parent=self)
                    geo = self.geometry()
                    x = geo.x() + geo.width() - toast.width() - 40
                    y = geo.y() + geo.height() - toast.height() - 40
                    toast.move(x, y)
                    toast.show()
                    QTimer.singleShot(2500, toast.close)
                show_no_audio_toast()

        onsets_action.triggered.connect(find_onsets)

        if analysis_menu is not None:
            analysis_menu.addAction(onsets_action)

        # Local Maxima action
        maxima_action = QAction("Find Local Maxima", self)
        maxima_action.setShortcut("Ctrl+X")
        def find_local_maxima():
            # Only show toast the first time local maxima are found
            if self.analyzer is not None:
                self.analyzer.analyze_maxima()
                self._peaks_toast_shown = False

            # Display a toast/loading dialog while processing maxima
            toast = ToastDialog("Analyzing local maxima...")
            geo = self.geometry() #type: ignore
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()

            # clear the loading toast and let user know it is not doing anything because no audio is loaded
            if self.audio_data is None or len(self.audio_data) == 0:
                def show_no_audio_toast():
                    toast = ToastDialog("No audio data available for analysis.", parent=self)
                    geo = self.geometry()
                    x = geo.x() + geo.width() - toast.width() - 40
                    y = geo.y() + geo.height() - toast.height() - 40
                    toast.move(x, y)
                    toast.show()
                    QTimer.singleShot(2500, toast.close)
                show_no_audio_toast()

        maxima_action.triggered.connect(find_local_maxima)

        if analysis_menu is not None:
            analysis_menu.addAction(maxima_action)

        # Add "Apply Filter" action to Analysis menu
        apply_filter_action = QAction("Apply Filter...", self)
        apply_filter_action.setShortcut("Ctrl+F")

        def open_filter_dialog():

            class FilterDialog(QDialog):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("Apply Audio Filter")
                    self.setMinimumWidth(320)
                    layout = QVBoxLayout(self)

                    # Filter type
                    layout.addWidget(QLabel("Filter Type:"))
                    self.type_box = QComboBox()
                    self.type_box.addItems(["lowpass", "highpass", "bandpass"])
                    layout.addWidget(self.type_box)

                    # Order
                    layout.addWidget(QLabel("Order:"))
                    self.order_spin = QSpinBox()
                    self.order_spin.setRange(1, 12)
                    self.order_spin.setValue(4)
                    layout.addWidget(self.order_spin)

                    # Cutoff(s)
                    self.cutoff_layout = QHBoxLayout()
                    self.cutoff_label = QLabel("Cutoff Frequency (Hz):")
                    self.cutoff_layout.addWidget(self.cutoff_label)
                    self.cutoff_spin = QDoubleSpinBox()
                    self.cutoff_spin.setRange(20, 20000)
                    self.cutoff_spin.setValue(1000)
                    self.cutoff_spin.setDecimals(1)
                    self.cutoff_layout.addWidget(self.cutoff_spin)
                    # For bandpass, add second cutoff
                    self.cutoff_spin2 = QDoubleSpinBox()
                    self.cutoff_spin2.setRange(20, 20000)
                    self.cutoff_spin2.setValue(5000)
                    self.cutoff_spin2.setDecimals(1)
                    self.cutoff_spin2.setVisible(False)
                    self.cutoff_layout.addWidget(self.cutoff_spin2)
                    layout.addLayout(self.cutoff_layout)

                    def update_cutoff_fields():
                        filter_type = self.type_box.currentText()
                        if filter_type == "bandpass":
                            self.cutoff_label.setText("Cutoff Range (Hz):")
                            self.cutoff_spin2.setVisible(True)
                        else:
                            self.cutoff_label.setText("Cutoff Frequency (Hz):")
                            self.cutoff_spin2.setVisible(False)
                    self.type_box.currentIndexChanged.connect(lambda _: update_cutoff_fields())

                    # Buttons
                    btn_layout = QHBoxLayout()
                    ok_btn = QPushButton("Apply")
                    cancel_btn = QPushButton("Cancel")
                    btn_layout.addWidget(ok_btn)
                    btn_layout.addWidget(cancel_btn)
                    layout.addLayout(btn_layout)

                    ok_btn.clicked.connect(self.accept)
                    cancel_btn.clicked.connect(self.reject)

                def get_values(self):
                    filter_type = self.type_box.currentText()
                    order = self.order_spin.value()
                    if filter_type == "bandpass":
                        lowcut = self.cutoff_spin.value()
                        highcut = self.cutoff_spin2.value()
                        # Ensure both are valid floats and lowcut < highcut
                        if lowcut is None or highcut is None or not isinstance(lowcut, float) or not isinstance(highcut, float):
                            cutoff = (1000.0, 5000.0)
                        else:
                            cutoff = (min(lowcut, highcut), max(lowcut, highcut))
                    else:
                        cutoff = self.cutoff_spin.value()
                    return filter_type, order, cutoff

            dialog = FilterDialog(self)
            if dialog.exec():
                filter_type, order, cutoff = dialog.get_values()
                # Save filter settings to self
                self.filter_type = filter_type
                self.order = order
                self.cutoff = cutoff
                self.filter_kwargs = {"order": order, "cutoff": cutoff}
                # Apply filter to audio_data and replot
                if self.audio_data is not None and self.sr is not None:
                    try:
                        # Ensure self.filter is an instance of AudioFilter
                        if self.filter is None or not hasattr(self.filter, "apply"):
                            self.filter = AudioFilter(self.sr)  # Initialize filter with sample rate
                        # Use lowercase for filter type comparison
                        if filter_type.lower() in ["lowpass", "highpass", "bandpass"]:
                            kwargs = {"sr": self.sr, "order": order}
                            if filter_type.lower() == "bandpass":
                                # cutoff is a tuple (lowcut, highcut)
                                lowcut, highcut = cutoff if isinstance(cutoff, (tuple, list)) and len(cutoff) == 2 else (1000.0, 5000.0)
                                kwargs["lowcut"] = lowcut
                                kwargs["highcut"] = highcut
                            else:
                                kwargs["cutoff"] = cutoff
                            filtered = self.filter.apply(self.audio_data, filter_type.lower(), **kwargs)
                            self.audio_data = filtered
                            self.plot_waveform()
                            toast = ToastDialog(f"Applied {filter_type} filter!", parent=self)
                            geo = self.geometry()
                            x = geo.x() + geo.width() - toast.width() - 40
                            y = geo.y() + geo.height() - toast.height() - 40
                            toast.move(x, y)
                            toast.show()
                            QTimer.singleShot(2000, toast.close)
                        else:
                            toast = ToastDialog(f"Filter type '{filter_type}' is not supported.", parent=self)
                            toast.show()
                            QTimer.singleShot(2500, toast.close)
                    except Exception as e:
                        toast = ToastDialog(f"Filter error: {e}", parent=self)
                        toast.show()
                        QTimer.singleShot(2500, toast.close)
                        

        apply_filter_action.triggered.connect(open_filter_dialog)
        if analysis_menu is not None:
            analysis_menu.addAction(apply_filter_action)
            
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
            '''
            self.background_actions = []
            for label, bg_name in backgrounds:
                bg_action = QAction(label, self)
                bg_action.setCheckable(bg_name != "custom")
                # Set checked if current background matches
                if bg_name != "custom":
                    bg_action.setChecked(getattr(self.fireworks_canvas, "current_background", "night") == bg_name)
                    self.background_actions.append(bg_action)
                    def make_bg_handler(bg=bg_name, action=bg_action):
                        def handler():
                            self.fireworks_canvas.set_background(bg)
                            self.fireworks_canvas.current_background = bg
                            # Uncheck all others, check only this one
                            for a in self.background_actions:
                                a.setChecked(a is action)
                        return handler
                    bg_action.triggered.connect(make_bg_handler())
                else:
                    def custom_bg_handler(action=bg_action):
                        file_dialog = QFileDialog(self)
                        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp *.gif)")
                        if file_dialog.exec():
                            selected_files = file_dialog.selectedFiles()
                            if selected_files:
                                image_path = selected_files[0]
                                self.fireworks_canvas.set_background("custom", image_path)
                                self.fireworks_canvas.current_background = "custom"
                                # Uncheck all preset actions
                                for a in self.background_actions:
                                    a.setChecked(False)
                        # Custom is not checkable
                    bg_action.triggered.connect(lambda: custom_bg_handler())
                background_menu.addAction(bg_action)
            edit_menu.addMenu(background_menu)
            '''
            # --- Add Padding submenu ---
            padding_menu = QMenu("Padding", self)
            # Store actions so we can update their checked state
            self.padding_actions = []
            for pad_value in [5, 10, 15, 20, 25, 50]:
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
                        # reload or load audio data to add padding if changed
                        custom_check = self.audio_data is not None
                        self.audio_loader.handle_audio(reload=custom_check)
                    return handler
                pad_action.triggered.connect(make_pad_handler())
                padding_menu.addAction(pad_action)
            # Optionally, add a custom padding dialog
            custom_pad_action = QAction("Custom...", self)
            def custom_pad_handler():
                # Ask user for a comma-separated list of paddings
                text, ok = QInputDialog.getText(
                    self,
                    "Set Custom Padding Vector",
                    "Enter padding (seconds) before each audio file, separated by commas:\n"
                    "Example: 5,10,5 for 5s before first, 10s before second, 5s before third, etc.",
                text=",".join(str(v) for v in getattr(self.audio_loader, "padding_vector", [self.padding]))
                )
                if ok:
                    try:
                        if "[" in text or "]" in text:
                            text = text.replace("[", "").replace("]", "")
                        # Parse the input into a list of floats/ints
                        padding_vector = [float(v.strip()) for v in text.split(",") if v.strip() != ""]
                        self.audio_loader.set_padding(padding_vector)
                        self.padding = padding_vector  # Save as a list
                        # Uncheck all preset actions
                        for a in self.padding_actions:
                            a.setChecked(False)
                        # reload or load audio data to add padding if changed
                        custom_check = self.audio_data is not None
                        self.audio_loader.handle_audio(reload=custom_check)
                    except Exception as e:
                        toast = ToastDialog(f"Invalid input for padding vector: {e}", parent=self)
                        toast.show()
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

        #############################################################
        #                                                          #
        #        Overall UI Elements layout                        #
        #                                                          #
        #############################################################
        # Delay showing the collapsible waveform until after the window is shown to avoid flash
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Use a main layout that will contain everything
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create a scroll area for the upper content (waveform + preview)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameStyle(0)  # Remove frame
        scroll_area.setStyleSheet("""
            QScrollArea { 
                background-color: #000000; 
                border: none; 
            }
            QScrollArea > QWidget > QWidget { 
                background-color: #000000; 
            }
            QScrollBar:vertical {
                background-color: #23242b;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #ffd700;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #fffbe6;
            }
        """)
        
        # Content widget for the scroll area
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #000000;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)

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
        scroll_layout.addWidget(self.collapsible_waveform)

        scroll_layout.addWidget(self.preview_widget, stretch=0, alignment=Qt.AlignmentFlag.AlignBottom)
        
        # Set the scroll content and add to scroll area
        scroll_area.setWidget(scroll_content)
        
        # Store reference to scroll area for dynamic height adjustment
        self.scroll_area = scroll_area
        
        # Set initial height for scroll area - start expanded (since collapsible widget starts checked/expanded)
        # Expanded height: toolbar (36px) + waveform (80px) + spectrogram (80px) + preview (80px) + padding
        expanded_height = 36 + 80 + 80 + 80 + 60  # 336px total with padding
        collapsed_height = 80 + 28 + 20  # 128px when collapsed
        
        scroll_area.setMinimumHeight(expanded_height)
        scroll_area.setMaximumHeight(600)  # Allow room to grow if needed

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
        
        # Add to main layout with proper stretch factors
        main_layout.addWidget(scroll_area, stretch=0)  # Fixed size upper area
        main_layout.addWidget(tab_widget, stretch=1)   # Expandable lower area
    
        # Show the window - it's already set to maximized state
        self.show()

    ###############################################################
    #                                                             #
    #                     HELPER FUNCTIONS                        #
    #                                                             #
    ###############################################################

    def plot_spectrogram(self):
        if self.audio_data is not None and self.sr is not None:
            self.spectrogram_ax.clear()
            # Compute the spectrogram using librosa
            S = librosa.stft(self.audio_data, n_fft=2048, hop_length=512)
            S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)
            img = librosa.display.specshow(
                S_db, ax=self.spectrogram_ax, sr=self.sr, hop_length=512,
                x_axis='time', y_axis='linear', cmap='magma'
            )
            self.spectrogram_ax.grid(False)

            # Remove all margins/padding so plot fills the canvas
            self.spectrogram_canvas.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)

            self.spectrogram_ax.set_xlabel("")
            self.spectrogram_ax.set_ylabel("")
            self.spectrogram_ax.set_xticks([])
            self.spectrogram_ax.set_yticks([])

            self.spectrogram_canvas.draw_idle()
        else:
            self.spectrogram_ax.clear()
            self.spectrogram_canvas.draw_idle()

    def plot_waveform(self, current_legend=None):
        audio_to_plot = self.audio_data

        ax = self.waveform_canvas.figure.axes[0]
        ax.clear()  # Clear the previous plot
        if audio_to_plot is not None:
            '''            # If a filter is applied, use it to process audio (currently not functional)
            if hasattr(self, "filter") and self.filter is not None:
                # Apply the filter to the audio data
                audio_to_plot = self.filter["instance"].apply(audio_to_plot, self.filter["type"], **self.filter["kwargs"])
            '''
            # Create time axis in seconds
            times = np.linspace(0, len(audio_to_plot) / self.sr, num=len(audio_to_plot))  # type: ignore
            # Downsample for dense signals to avoid smudging
            max_points = 2000  # Adjust for performance/detail
            if len(audio_to_plot) > max_points:
                factor = len(audio_to_plot) // max_points
                # Use min/max envelope for better visibility
                audio_data_reshaped = audio_to_plot[:factor * max_points].reshape(-1, factor)
                envelope_min = audio_data_reshaped.min(axis=1)
                envelope_max = audio_data_reshaped.max(axis=1)
                times_ds = times[:factor * max_points].reshape(-1, factor)
                times_ds = times_ds.mean(axis=1)
                ax.fill_between(times_ds, envelope_min, envelope_max, color="#8fb9bd", alpha=0.7, linewidth=0)
                ax.plot(times_ds, envelope_max, color="#5fd7e6", linewidth=0.7, alpha=0.9)
                ax.plot(times_ds, envelope_min, color="#5fd7e6", linewidth=0.7, alpha=0.9)
            else:
                ax.plot(times, audio_to_plot, color="#8fb9bd", linewidth=1.2, alpha=0.95, antialiased=True)
            ax.set_facecolor("#000000")
            ax.tick_params(axis='y', colors='white')
            # Plot segment times in gold
            if self.segment_times is not None and isinstance(self.segment_times, (list, tuple)):
                for t in self.segment_times:
                    if t is not None and isinstance(t, (int, float)) and np.isfinite(t):
                        ax.axvline(x=t, color="#ffd700", linestyle="--", linewidth=1.2, alpha=0.9)
            self.waveform_canvas.draw_idle()  # Ensure segment lines are drawn
            # Update the waveform selector's original limits after redraw
            if hasattr(self, 'waveform_selector'):
                self.waveform_selector.update_original_limits()
            if self.duration is not None and self.sr is not None:
                ax.set_xlim(0, self.duration)
            elif audio_to_plot is not None and self.sr is not None:
                ax.set_xlim(0, len(audio_to_plot) / self.sr)
            else:
                ax.set_xlim(0, 1)
            
            # Update the waveform selector's original limits to match the new axis limits
            if hasattr(self, 'waveform_selector') and hasattr(self.waveform_selector, 'update_original_limits'):
                self.waveform_selector.update_original_limits()
                
            ax.set_xlabel("Time (s)", color='white')
            ax.set_ylabel("Amplitude", color='white')
            # Add grid lines in white, with some transparency for subtlety
            ax.grid(True, color="#888888", alpha=0.3, linestyle="--", linewidth=0.8)
        else:
            ax.set_title("No audio loaded", color='white')
            ax.set_xticks([])
            ax.set_yticks([])
        
        # Check for analysis and replot if it was there
        if current_legend is not None:
            if self.segment_times is not None and isinstance(self.segment_times, (list, tuple)):
                self.handle_segments(self.segment_times)  # Reapply segments if needed
            if self.points is not None and isinstance(self.points, (list, tuple)):
                self.handle_interesting_points(self.points)  # Reapply points if needed
            if self.onsets is not None and isinstance(self.onsets, (list, tuple)):
                self.handle_onsets(self.onsets)  # Reapply onsets if needed
            if self.peaks is not None and isinstance(self.peaks, (list, tuple)):
                self.handle_peaks(self.peaks)  # Reapply peaks if needed

        self.waveform_canvas.draw_idle()
        # Update the waveform selector's original limits after redraw
        if hasattr(self, 'waveform_selector'):
            self.waveform_selector.update_original_limits()
        
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
        return

    def handle_segments(self, segment_times): 
        # Always update self.segments with the new segments
        if self.segment_times is None or self.segment_times == []:
            self.segment_times = list(segment_times)
            new_segments = list(segment_times)
        else:
            # Only add segments not already present
            new_segments = [s for s in segment_times if s not in self.segment_times]
            self.segment_times.extend(new_segments)

        ax = self.waveform_canvas.figure.axes[0]
        # Remove previous segment lines (by clearing and replotting)
        # Only plot one legend entry for all segments
        if self.segment_times is not None:
            for t in self.segment_times:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#ffd700", linestyle="--", linewidth=1.2, alpha=0.9, label=None)
                elif isinstance(t, (np.ndarray, list, tuple)):
                    for tt in np.atleast_1d(t):
                        if isinstance(tt, (int, float)) and np.isscalar(tt) and not isinstance(tt, complex):
                            ax.axvline(x=float(tt), color="#ffd700", linestyle="--", linewidth=1.2, alpha=0.9, label=None)
            # Add a single legend entry if not present
            legend = ax.get_legend()
            labels = [l.get_text() for l in legend.get_texts()] if legend else []
            if "Segment" not in labels:
                ax.axvline(x=0, color="#ffd700", linestyle="--", linewidth=1.2, alpha=0.9, label="Segment")
                leg = ax.legend(
                    loc="upper right",
                    framealpha=0.3,
                    fontsize=7,  # Make legend font small
                    markerscale=0.7,
                    handlelength=1.2,
                    borderpad=0.3,
                    labelspacing=0.2,
                    handletextpad=0.3,
                    borderaxespad=0.2,
                )
                if leg:
                    leg.get_frame().set_alpha(0.3)
        
        def show_segments_toast():
            toast = ToastDialog(f"Found {len(new_segments)//2 + 1} segments!", parent=self) # segments are between two lines so divided by 2
            geo = self.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)
        if hasattr(self, "_segments_toast_shown") and not self._segments_toast_shown:
            show_segments_toast()
            self._segments_toast_shown = True

        self.update_firework_show_info()  # Update info with new segment count
        self.waveform_canvas.draw_idle()
        # Update the waveform selector's original limits after redraw
        if hasattr(self, 'waveform_selector'):
            self.waveform_selector.update_original_limits()

    def handle_interesting_points(self, points):
        # Always update self.points with the new points
        # Append new points to self.points, avoiding duplicates
        if self.points is None or self.points == []:
            self.points = list(points)
            new_points = list(points)
        else:
            # Only add points not already present
            new_points = [p for p in points if p not in self.points]
            self.points.extend(new_points)

        ax = self.waveform_canvas.figure.axes[0]
        # Only plot one legend entry for all interesting points
        if self.points is not None and isinstance(self.points, (list, tuple, np.ndarray)):
            for t in self.points:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#ff6f00", linestyle=":", linewidth=1.5, alpha=0.8, label=None)
            legend = ax.get_legend()
            labels = [l.get_text() for l in legend.get_texts()] if legend else []
            if "Interesting Point" not in labels:
                ax.axvline(x=0, color="#ff6f00", linestyle=":", linewidth=1.5, alpha=0.8, label="Interesting Point")
                leg = ax.legend(
                    loc="upper right",
                    framealpha=0.3,
                    fontsize=7,
                    markerscale=0.7,
                    handlelength=1.2,
                    borderpad=0.3,
                    labelspacing=0.2,
                    handletextpad=0.3,
                    borderaxespad=0.2,
                )
                if leg:
                    leg.get_frame().set_alpha(0.3)
        
        def show_interesting_toast():
                toast = ToastDialog(f"Found {len(new_points)} interesting points!", parent=self)
                geo = self.geometry()
                x = geo.x() + geo.width() - toast.width() - 40
                y = geo.y() + geo.height() - toast.height() - 40
                toast.move(x, y)
                toast.show()
                QTimer.singleShot(2500, toast.close)
        if hasattr(self, "_interesting_points_toast_shown") and not self._interesting_points_toast_shown:
            show_interesting_toast()
            self._interesting_points_toast_shown = True
        self.waveform_canvas.draw_idle()
        # Update the waveform selector's original limits after redraw
        if hasattr(self, 'waveform_selector'):
            self.waveform_selector.update_original_limits()

    def handle_onsets(self, onsets):
        # Always update self.onsets with the new onsets
        # Append new onsets to self.onsets, avoiding duplicates
        if self.onsets is None or self.onsets == []:
            self.onsets = list(onsets)
            new_onsets = list(onsets)
        else:
            # Only add onsets not already present
            new_onsets = [o for o in onsets if o not in self.onsets]
            self.onsets.extend(new_onsets)

        ax = self.waveform_canvas.figure.axes[0]
        # Only plot one legend entry for all onsets
        if self.onsets is not None and isinstance(self.onsets, (list, tuple, np.ndarray)):
            for t in self.onsets:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#00ff6f", linestyle="-.", linewidth=1.5, alpha=0.8, label=None)
            legend = ax.get_legend()
            labels = [l.get_text() for l in legend.get_texts()] if legend else []
            if "Onset" not in labels:
                ax.axvline(x=0, color="#00ff6f", linestyle="-.", linewidth=1.5, alpha=0.8, label="Onset")
                leg = ax.legend(
                    loc="upper right",
                    framealpha=0.3,
                    fontsize=7,
                    markerscale=0.7,
                    handlelength=1.2,
                    borderpad=0.3,
                    labelspacing=0.2,
                    handletextpad=0.3,
                    borderaxespad=0.2,
                )
                if leg:
                    leg.get_frame().set_alpha(0.3)
        
        def show_onset_toast():
            toast = ToastDialog(f"Found {len(new_onsets)} onsets!", parent=self)
            geo = self.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)

        if hasattr(self, "_onsets_toast_shown") and not self._onsets_toast_shown:
            show_onset_toast()
            self._onsets_toast_shown = True

        self.waveform_canvas.draw_idle()
        # Update the waveform selector's original limits after redraw
        if hasattr(self, 'waveform_selector'):
            self.waveform_selector.update_original_limits()

    def handle_peaks(self, peaks):
        # Always update self.peaks with the new peaks
        # Append new peaks to self.peaks, avoiding duplicates
        if self.peaks is None or self.peaks == []:
            self.peaks = list(peaks)
            new_peaks = list(peaks)
        else:
            # Only add peaks not already present
            new_peaks = [p for p in peaks if p not in self.peaks]
            self.peaks.extend(new_peaks)

        ax = self.waveform_canvas.figure.axes[0]
        # Only plot one legend entry for all peaks
        if self.peaks is not None and isinstance(self.peaks, (list, tuple, np.ndarray)):
            for t in self.peaks:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#ff00ff", linestyle="--", linewidth=1.5, alpha=0.8, label=None)
            legend = ax.get_legend()
            labels = [l.get_text() for l in legend.get_texts()] if legend else []
            if "Peak" not in labels:
                ax.axvline(x=0, color="#ff00ff", linestyle="--", linewidth=1.5, alpha=0.8, label="Peak")
                leg = ax.legend(
                    loc="upper right",
                    framealpha=0.3,
                    fontsize=7,
                    markerscale=0.7,
                    handlelength=1.2,
                    borderpad=0.3,
                    labelspacing=0.2,
                    handletextpad=0.3,
                    borderaxespad=0.2,
                )
                if leg:
                    leg.get_frame().set_alpha(0.3)

        def show_peaks_toast():
            toast = ToastDialog(f"Found {len(new_peaks)} peaks!", parent=self)
            geo = self.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)

        if not hasattr(self, "_peaks_toast_shown") or not self._peaks_toast_shown:
            show_peaks_toast()
            self._peaks_toast_shown = True

        self.waveform_canvas.draw_idle()
        # Update the waveform selector's original limits after redraw
        if hasattr(self, 'waveform_selector'):
            self.waveform_selector.update_original_limits()
