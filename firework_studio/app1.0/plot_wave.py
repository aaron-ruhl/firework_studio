from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt import NavigationToolbar2QT
import librosa

import librosa.display

def plot_waveform(self,audio,sr=None, segment_times=None):
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
    ax.clear()
    ax.set_frame_on(False)
    # Make axes occupy the full canvas area, removing all padding/margins
    ax.set_position((0.0, 0.0, 1.0, 1.0))
    if audio is not None:
        sr = sr if sr is not None else 22050  # Default librosa sample rate
        librosa.display.waveshow(audio, sr=sr, ax=ax, alpha=0.5)
        ax.set_facecolor('black')
        ax.set_xticks([])
        ax.set_yticks([])
    # Ensure all spines are invisible (removes white edge)
    for spine in ax.spines.values():
        spine.set_visible(False)
    # Plot segments
    if segment_times is not None:
        for i, t in enumerate(segment_times):
            ax.axvline(t, color='orange', linestyle='--', alpha=0.7)
    ax.set_title("Waveform with Segments")
    # Fit x-axis to audio duration
    sr = float(sr) if sr is not None else 22050.0  # Default librosa sample rate as float
    duration = librosa.get_duration(y=audio, sr=sr)
    ax.set_xlim((0, duration))
    self.waveform_canvas.draw()

