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
        files, _ = QFileDialog.getOpenFileNames(
            parent,
            "Select Audio Files",
            "",
            "Audio Files (*.wav *.mp3 *.flac *.npy)"
        )
        if files:
            self.paths = files

    def load(self):
        for path in self.paths:
            try:
                # Ensure path is a string
                path_str = str(path)
                if path_str.lower().endswith('.npy'):
                    audio_data = np.load(path_str)
                    # If .npy file contains sample rate info, handle here (not standard)
                    if self.sr is None:
                        self.sr = 16000  # Default sample rate if not specified
                else:
                    if self.sr is None:
                        self.sr = 16000  # Default sample rate if not specified
                    audio_data, _ = librosa.load(path_str, sr=self.sr, mono=True)
                self.audio_datas.append(audio_data)
            except Exception as e:
                print(f"Error loading audio file {path}: {e}")
                continue
        # Update self.audio_data after loading
        self.audio_data = np.concatenate(self.audio_datas) if self.audio_datas else None
        if self.audio_data is not None and self.sr is not None:
            self.duration = librosa.get_duration(y=self.audio_data, sr=self.sr)
        else:
            self.duration = 0.0

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

    def just_load(self, paths):
        # Handle different input types
        if isinstance(paths, str):
            self.paths = [paths]
        elif isinstance(paths, list):
            # Ensure all elements are strings (paths)
            self.paths = []
            for path in paths:
                if isinstance(path, str):
                    self.paths.append(path)
                elif hasattr(path, 'path'):  # Handle audio data objects with path attribute
                    self.paths.append(str(path.path))
                else:
                    # Skip non-string, non-path objects
                    print(f"Skipping invalid path: {path} (type: {type(path)})")
        else:
            self.paths = [str(paths)]  # Convert to string as fallback
        
        # Clear previous data
        self.audio_datas = []
        self.sr = None
        
        if not self.paths:
            print("No valid paths found for audio loading")
            return None, None, [], 0.0
            
        self.load()
        return self.audio_data, self.sr, self.audio_datas, self.duration