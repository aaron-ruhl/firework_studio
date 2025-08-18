import os
import librosa
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QTimer

import numpy as np
from toaster import ToastDialog
from PyQt6.QtCore import QThread, pyqtSignal

from analysis import AudioAnalysis
from filters import AudioFilter


class AudioLoaderThread(QThread):
    finished = pyqtSignal(object, object, list, float, list, list)  # audio_data, sr, audio_datas, duration, paths, segment_times

    def __init__(self, paths, sr=None):
        super().__init__()
        self.paths = paths
        self.sr = sr
        self.audio_datas = []
        self.audio_data = None
        self.duration = 0.0
        self.padding = 4

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
        if audio_data is not None and sr is not None:
            if isinstance(self.padding, (list, np.ndarray)):
                pad_samples_list = [int(p * sr) for p in self.padding[:len(audio_datas)]]
                # If fewer paddings than audio_datas, pad with zeros
                while len(pad_samples_list) < len(audio_datas):
                    pad_samples_list.append(0)
                audio_datas = [
                    np.concatenate([np.zeros(pad_samples, dtype=ad.dtype), ad])
                    for pad_samples, ad in zip(pad_samples_list, audio_datas)
                ]
            else:
                pad_samples = int(self.padding * sr)
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
        self.padding = 4  # Default padding in seconds (int)

    def set_padding(self, padding):
        self.padding = padding

    def connect_analysis_signals(self):
        # As soon as data is loaded signals for analysis are connected
        if hasattr(self.main_window, "handle_segments"):
            self.main_window.analyzer.segments_ready.connect(self.main_window.handle_segments)
        if hasattr(self.main_window, "handle_interesting_points"):
            self.main_window.analyzer.interesting_points_ready.connect(self.main_window.handle_interesting_points)
        if hasattr(self.main_window, "handle_onsets"):
            self.main_window.analyzer.onsets_ready.connect(self.main_window.handle_onsets)
        if hasattr(self.main_window, "handle_peaks"):
            self.main_window.analyzer.peaks_ready.connect(self.main_window.handle_peaks)
        #if hasattr(self.main_window, "handle_beats"):
        #    self.analyzer.beats_ready.connect(self.main_window.handle_beats)
        
    def handle_audio(self, reload=False):
        # Start thread to load audio
        if not reload:
            selected = self.select_files(self.main_window)
            if not selected:
                self.main_window.status_bar.showMessage("No audio loaded.") #type: ignore
                return
        self.thread = AudioLoaderThread(self.paths)
        if self.thread is not None:
            self.thread.set_padding(self.padding)
        # Show loading toast with spinner
        toast = ToastDialog("Loading audio...", parent=self.main_window)
        geo = self.main_window.geometry() #type: ignore
        x = geo.x() + geo.width() - toast.width() - 40
        y = geo.y() + geo.height() - toast.height() - 40
        toast.move(x, y)
        toast.show()
        self.loading_toast = toast

        # start loading audio
        self.thread.finished.connect(self.on_audio_loaded)
        self.thread.start()

    def on_audio_loaded(self, audio_data, sr, audio_datas, duration, paths):
        self.main_window.audio_data = audio_data #type: ignore
        self.main_window.sr = sr #type: ignore
        self.main_window.audio_datas = audio_datas #type: ignore
        self.main_window.duration = duration #type: ignore
        self.main_windowpaths = paths

        if audio_data is not None:
            self.main_window.clear_show() #type: ignore
            self.main_window.preview_widget.set_show_data(audio_data, sr, self.segment_times, None, duration) #type: ignore
            self.main_window.plot_waveform() #type: ignore
            self.main_window.analyzer = AudioAnalysis(audio_data,audio_datas, sr)
            self.main_window.filter = AudioFilter(sr)  # Initialize filter with sample rate

            self.connect_analysis_signals()

            basenames = [os.path.basename(p) for p in paths]
            toast = ToastDialog(f"Loaded audio: {', '.join(basenames)}", parent=self.main_window)
            geo = self.main_window.geometry() #type: ignore
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)
        else:
            self.main_window.status_bar.showMessage("No audio loaded.") #type: ignore

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

    def just_load(self, paths=None):
        if paths is None:
            paths = self.paths
        elif isinstance(paths, str):
            paths = [paths]
        elif hasattr(paths, 'path'):
            paths = [str(paths.path)]
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