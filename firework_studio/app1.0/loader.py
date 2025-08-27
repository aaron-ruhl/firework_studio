import os
import librosa
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QTimer

import numpy as np
from toaster import ToastDialog
from PyQt6.QtCore import QThread, pyqtSignal

from analysis import AudioAnalysis
from filters import AudioFilter
from settings import SettingsManager


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
                    sr = self.sr if self.sr is not None else 16000
                else:
                    sr = self.sr if self.sr is not None else 16000
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
        if hasattr(self.main_window, "analyzer") and self.main_window.analyzer is not None: # type: ignore
            if hasattr(self.main_window, "firework_show_helper"):
                try:
                    # Disconnect existing connections to avoid duplicates
                    self.main_window.analyzer.segments_ready.disconnect() # type: ignore
                    self.main_window.analyzer.interesting_points_ready.disconnect() # type: ignore
                    self.main_window.analyzer.onsets_ready.disconnect() # type: ignore
                    self.main_window.analyzer.peaks_ready.disconnect() # type: ignore
                except:
                    pass  # Ignore if no connections exist
                
                # Connect the signals
                self.main_window.analyzer.segments_ready.connect(self.main_window.firework_show_helper.handle_segments) # type: ignore
                self.main_window.analyzer.interesting_points_ready.connect(self.main_window.firework_show_helper.handle_interesting_points) # type: ignore
                self.main_window.analyzer.onsets_ready.connect(self.main_window.firework_show_helper.handle_onsets) # type: ignore
                self.main_window.analyzer.peaks_ready.connect(self.main_window.firework_show_helper.handle_peaks) # type: ignore
                self.main_window.connect_analysis_buttons() # type: ignore

    def apply_initial_settings(self):
        """Apply current settings to the analyzer for consistency"""
        if hasattr(self.main_window, "analyzer") and self.main_window.analyzer is not None: # type: ignore
            # Use the SettingsManager to get current settings
            settings_manager = SettingsManager()
            settings_manager.apply_settings_to_analyzer(self.main_window.analyzer) # type: ignore

            # if create_tab_helper exists and has settings, use those as well just in case it is needed later
            if hasattr(self.main_window, "create_tab_helper"):
                helper = self.main_window.create_tab_helper # type: ignore
                
                # Apply segment settings if the helper has them
                if hasattr(helper, 'n_mfcc_spin'):
                    self.main_window.analyzer.set_segment_settings( # type: ignore
                        n_mfcc=helper.n_mfcc_spin.value(),
                        min_segments=helper.min_segments_spin.value(),
                        max_segments=helper.max_segments_spin.value(),
                        dct_type=helper.dct_type_spin.value(),
                        n_fft=helper.n_fft_spin.value(),
                        hop_length_segments=helper.hop_length_segments_spin.value()
                    )
                
                # Apply onset settings if the helper has them
                if hasattr(helper, 'min_onsets_spin'):
                    self.main_window.analyzer.set_onset_settings(
                        min_onsets=helper.min_onsets_spin.value(),
                        max_onsets=helper.max_onsets_spin.value(),
                        hop_length_onsets=helper.hop_length_onsets_spin.value(),
                        backtrack=helper.backtrack_box.currentText() == "True",
                        normalize=helper.normalize_box.currentText() == "True"
                    )
                
                # Apply interesting points settings if the helper has them
                if hasattr(helper, 'min_points_spin'):
                    self.main_window.analyzer.set_interesting_points_settings( # type: ignore
                        min_points=helper.min_points_spin.value(),
                        max_points=helper.max_points_spin.value(),
                        pre_max=helper.pre_max_spin.value(),
                        post_max=helper.post_max_spin.value(),
                        pre_avg_distance=helper.pre_avg_distance_spin.value(),
                        post_avg_distance=helper.post_avg_distance_spin.value(),
                        delta=helper.delta_spin.value() * 0.1,
                        moving_avg_wait=helper.moving_avg_wait_spin.value()
                    )
                
                # Apply peak settings if the helper has them
                if hasattr(helper, 'min_peaks_spin'):
                    custom_func = None
                    if hasattr(helper, 'custom_function_edit'):
                        text = helper.custom_function_edit.text().strip()
                        if text:
                            try:
                                if text.startswith("lambda"):
                                    custom_func = eval(text, {"__builtins__": {}}, {})
                            except Exception:
                                custom_func = None
                    
                    self.main_window.analyzer.set_peak_settings( # type: ignore
                        min_peaks=helper.min_peaks_spin.value(),
                        max_peaks=helper.max_peaks_spin.value(),
                        scoring=helper.scoring_box.currentText(),
                        custom_scoring_method=custom_func
                    )
        
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
            self.main_window.firework_show_helper.plot_waveform() #type: ignore
            self.main_window.firework_show_helper.plot_spectrogram() #type: ignore
            
            # Clean up existing analyzer thread if it exists
            if hasattr(self.main_window, 'analyzer') and self.main_window.analyzer is not None: # type: ignore
                if self.main_window.analyzer.isRunning(): # type: ignore
                    self.main_window.analyzer.quit() # type: ignore
                    self.main_window.analyzer.wait() # type: ignore
            
            self.main_window.analyzer = AudioAnalysis(audio_data,audio_datas, sr, duration) # type: ignore
            self.main_window.filter = AudioFilter(sr, audio_data) # type: ignore # Initialize filter with sample rate and audio data

            # Apply current create tab settings to the newly created analyzer
            self.apply_initial_settings()
            self.connect_analysis_signals()

            # Activate the analyze segments button so it will show messages
            if hasattr(self.main_window, "segment_btn"):
                self.main_window.segment_btn.click()

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
                if sr is None:
                    sr = 41000
                path_str = str(path)
                if path_str.lower().endswith('.npy'):
                    audio_data = np.load(path_str)
                else:
                    audio_data, _ = librosa.load(path_str, sr=sr, mono=True)
                audio_datas.append(audio_data)
            except Exception as e:
                print(f"Error loading audio file {path}: {e}")
                continue
        audio_data = np.concatenate(audio_datas) if audio_datas else None
        duration = librosa.get_duration(y=audio_data, sr=sr) if audio_data is not None and sr is not None else 0.0
        return audio_data, sr, audio_datas, duration