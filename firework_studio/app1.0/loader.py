import librosa
from PyQt6.QtWidgets import QFileDialog
from matplotlib.backends.backend_qt import NavigationToolbar2QT
import numpy as np

class AudioLoader():
    
    def __init__(self):
        self.paths = []
        self.audio_datas = []
        self.sr = None
        self.audio_data = None
        self.duration = 0.0

    def select_files(self, parent=None):
        files, _ = QFileDialog.getOpenFileNames(parent, "Select Audio Files", "", "Audio Files (*.wav *.mp3 *.flac)")
        if files:
            self.paths = files

    def load(self):
        for path in self.paths:
            if self.sr is None:
                self.sr = 16000  # Default sample rate if not specified
            audio_data, _ = librosa.load(path, sr=self.sr, mono=True)
            self.audio_datas.append(audio_data)
        # Update self.audio_data after loading
        self.audio_data = np.concatenate(self.audio_datas) if self.audio_datas else None
        self.duration = librosa.get_duration(y=self.audio_data, sr=self.sr) if self.audio_data is not None else 0.0

    def select_and_load(self, parent=None, figure_canvas=None):
        # Ensure parent is either None or a QWidget, not a bool
        if isinstance(parent, bool):
            parent = None
        self.select_files(parent)
        # Store the figure_canvas for plotting
        self.figure_canvas = figure_canvas
        # Clear previous audio data and sample rate before loading new files
        self.audio_datas = []
        self.sr = None
        self.load()

        return self.audio_data, self.sr, self.audio_datas, self.duration