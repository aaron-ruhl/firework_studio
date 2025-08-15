import os
import librosa
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QTimer

import numpy as np
from toaster import ToastDialog
from PyQt6.QtCore import QThread, pyqtSignal


class AudioLoaderThread(QThread):
    finished = pyqtSignal(object, object, list, float, list, list)  # audio_data, sr, audio_datas, duration, paths, segment_times

    def __init__(self, paths, sr=None):
        super().__init__()
        self.paths = paths
        self.sr = sr
        self.audio_datas = []
        self.audio_data = None
        self.duration = 0.0
        self.padding = 10

    def set_padding(self, padding):
        self.padding = padding

    def run(self):
        audio_datas = []
        sr = self.sr
        for path in self.paths:
            try:
                path_str = str(path)
                if path_str.lower().endswith('.npy'):
                    audio_data = np.load(path_str)
                    if sr is None:
                        sr = 16000
                else:
                    if sr is None:
                        sr = 16000
                    audio_data, _ = librosa.load(path_str, sr=sr, mono=True)
                audio_datas.append(audio_data)
            except Exception as e:
                print(f"Error loading audio file {path}: {e}")
                continue
        # Concatenate all audio data
        if self.padding and self.padding > 0 and audio_data is not None and sr is not None:
            pad_samples = int(self.padding * sr)
            # Add silence at the beginning of each audio segment
            audio_datas = [np.concatenate([np.zeros(pad_samples, dtype=ad.dtype), ad]) for ad in audio_datas]
            audio_data = np.concatenate(audio_datas) if audio_datas else None
        else:
            audio_data = np.concatenate(audio_datas) if audio_datas else None
        duration = librosa.get_duration(y=audio_data, sr=sr) if audio_data is not None and sr is not None else 0.0
        self.finished.emit(audio_data, sr, audio_datas, duration, self.paths, [])

class AudioLoader():
    def __init__(self, main_window=None):
        self.paths = []
        self.audio_datas = []
        self.sr = None
        self.audio_data = None
        self.duration = 0.0
        self.main_window = main_window
        self.segment_times = []
        self.thread = None
        self.padding = 10  # Default padding in seconds (int)

    def set_padding(self, padding):
        self.padding = padding

    def handle_audio(self):
        # Start thread to load audio
        selected = self.select_files(self.main_window)
        if not selected:
            self.main_window.status_bar.showMessage("No audio loaded.")
            return

        self.thread = AudioLoaderThread(self.paths)
        if self.thread is not None:
            self.thread.set_padding(self.padding)
        # Show loading toast with spinner
        toast = ToastDialog("Loading audio...", parent=self.main_window)
        geo = self.main_window.geometry()
        x = geo.x() + geo.width() - toast.width() - 40
        y = geo.y() + geo.height() - toast.height() - 40
        toast.move(x, y)
        toast.show()
        self.loading_toast = toast
        self.thread.finished.connect(self.on_audio_loaded)
        self.thread.start()

    def on_audio_loaded(self, audio_data, sr, audio_datas, duration, paths, segment_times):
        self.main_window.audio_data = audio_data
        self.main_window.sr = sr
        self.main_window.audio_datas = audio_datas
        self.main_window.duration = duration
        self.main_windowpaths = paths
        self.segment_times = segment_times

        if audio_data is not None:
            self.main_window.clear_show()
            self.main_window.preview_widget.set_show_data(audio_data, sr, segment_times, None, duration)
            self.main_window.plot_waveform()
            basenames = [os.path.basename(p) for p in paths]
            toast = ToastDialog(f"Loaded audio: {', '.join(basenames)}", parent=self.main_window)
            geo = self.main_window.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)
        else:
            self.main_window.status_bar.showMessage("No audio loaded.")

    def select_files(self, parent=None):
        files, _ = QFileDialog.getOpenFileNames(
            parent,
            "Select Audio Files",
            "",
            "Audio Files (*.wav *.mp3 *.flac *.npy)"
        )
        if files:
            self.paths = files
            return True
        else:
            return False

    def just_load(self, paths):
        if isinstance(paths, str):
            self.paths = [paths]
        elif isinstance(paths, list):
            self.paths = []
            for path in paths:
                if isinstance(path, str):
                    self.paths.append(path)
                elif hasattr(path, 'path'):
                    self.paths.append(str(path.path))
                else:
                    print(f"Skipping invalid path: {path} (type: {type(path)})")
        else:
            self.paths = [str(paths)]
        self.audio_datas = []
        self.sr = None
        if not self.paths:
            print("No valid paths found for audio loading")
            return None, None, [], 0.0

        # Synchronous load for non-UI usage
        audio_datas = []
        sr = self.sr
        for path in self.paths:
            try:
                path_str = str(path)
                if path_str.lower().endswith('.npy'):
                    audio_data = np.load(path_str)
                    if sr is None:
                        sr = 16000
                else:
                    if sr is None:
                        sr = 16000
                    audio_data, _ = librosa.load(path_str, sr=sr, mono=True)
                audio_datas.append(audio_data)
            except Exception as e:
                print(f"Error loading audio file {path}: {e}")
                continue
        audio_data = np.concatenate(audio_datas) if audio_datas else None
        duration = librosa.get_duration(y=audio_data, sr=sr) if audio_data is not None and sr is not None else 0.0
        return audio_data, sr, audio_datas, duration