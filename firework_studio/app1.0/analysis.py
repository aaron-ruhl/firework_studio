from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import librosa
from PyQt6.QtWidgets import QMessageBox

class AudioAnalysis(QThread):
    segments_ready = pyqtSignal(list)
    interesting_points_ready = pyqtSignal(list)
    onsets_ready = pyqtSignal(list)
    beats_ready = pyqtSignal(list)
    peaks_ready = pyqtSignal(list)

    def __init__(self, audio_data, audio_datas, sr, parent=None):
        super().__init__(parent)
        self.audio_data = audio_data
        self.audio_datas = audio_datas
        self.sr = sr
        self.task = None
        self.selected_region = None  # For local extrema analysis
        self.n = 100

    def set_n(self, n):
        self.n = n

    def set_selected_region(self, region):
        self.selected_region = region

    def reset_selected_region(self):
        self.selected_region = None

    def run(self):
        # Run the selected analysis task in the thread
        if self.task == "segments":
            segments = self.find_segments()
            self.segments_ready.emit(segments)
        elif self.task == "interesting_points":
            points = self.find_interesting_points()
            self.interesting_points_ready.emit(points)
        elif self.task == "onsets":
            onsets = self.find_onsets()
            self.onsets_ready.emit(onsets)
        elif self.task == "beats":
            beats = self.find_beats()
            self.beats_ready.emit(beats)
        elif self.task == "maxima":
            peaks = self.find_local_maxima()
            self.peaks_ready.emit(peaks)

    def analyze_segments(self):
        self.task = "segments"
        self.start()

    def analyze_interesting_points(self):
        self.task = "interesting_points"
        self.start()

    def analyze_onsets(self):
        self.task = "onsets"
        self.start()

    def analyze_beats(self):
        self.task = "beats"
        self.start()

    def analyze_maxima(self):
        self.task = "maxima"
        self.start()

    def find_segments(self):
        '''Segment each audio into distinct portions and concatenate results'''
        results = []
        audio_datas = getattr(self, "audio_datas", [self.audio_datas])
        for audio_data in audio_datas:
            if audio_data is None or len(audio_data) == 0:
                print("No audio data available for segment analysis.")
                continue
            # To avoid blocking, process in smaller chunks if possible
            try:
                mfcc = librosa.feature.mfcc(y=audio_data, sr=self.sr, n_mfcc=13)
                similarity = np.dot(mfcc.T, mfcc)
                similarity = similarity / np.max(similarity)
                segment_boundaries = librosa.segment.agglomerative(similarity, k=6)
                segment_times = librosa.frames_to_time(segment_boundaries, sr=self.sr)
                segments = [(segment_times[i], segment_times[i+1]) for i in range(len(segment_times)-1)]
                results.extend(segments)
            except Exception as e:
                print(f"Error in segment analysis: {e}")
        return results

    def find_interesting_points(self):
        '''Find points of interest in each audio signal and concatenate results'''
        results = []
        for audio_data in getattr(self, "audio_datas", [self.audio_datas]):
            if audio_data is None or len(audio_data) == 0:
                print("No audio data available for interesting points analysis.")
                continue
            centroids = librosa.feature.spectral_centroid(y=audio_data, sr=self.sr)[0]
            times = librosa.times_like(centroids, sr=self.sr)
            peaks = librosa.util.peak_pick(centroids, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.5, wait=5)
            interesting_points = [times[p] for p in peaks]
            N = 10
            if len(peaks) > 0:
                top_indices = np.argsort(centroids[peaks])[::-1][:N]
                interesting_points = [times[peaks[i]] for i in top_indices]
            print(f"Found {len(interesting_points)} interesting points")
            results.extend(interesting_points)
        return results

    def find_onsets(self):
        '''Find onsets in each audio signal and concatenate results'''
        results = []
        for audio_data in getattr(self, "audio_datas", [self.audio_datas]):
            if audio_data is None or len(audio_data) == 0:
                print("No audio data available for onset analysis.")
                continue
            onset_frames = librosa.onset.onset_detect(y=audio_data, sr=self.sr)
            onset_times = librosa.frames_to_time(onset_frames, sr=self.sr)
            max_onsets = 20
            if len(onset_times) > max_onsets:
                indices = np.linspace(0, len(onset_times) - 1, max_onsets, dtype=int)
                sampled_onsets = [onset_times[i] for i in indices]
                results.extend(sampled_onsets)
            else:
                print(f"Found {len(onset_times)} onsets")
                results.extend(onset_times.tolist())
        return results
    
    def find_local_maxima(self): 
        '''Find n local maxima and minima using derivative approximation and Newton's method within selected_region'''
        peaks = []
        if self.audio_data is None or len(self.audio_data) == 0:
            return peaks

        # If selected_region is provided, convert times to indices and slice audio_data
        if self.selected_region is not None and isinstance(self.selected_region, (tuple, list)) and len(self.selected_region) == 2:
            start_time, end_time = self.selected_region # type: ignore
            start_idx = int(start_time * self.sr)
            end_idx = int(end_time * self.sr)
            audio_data_region = self.audio_data[start_idx:end_idx]
            offset = start_idx
        else:
            audio_data_region = self.audio_data
            offset = 0

        # Check if audio_data_region is long enough for gradient calculation
        if len(audio_data_region) < 2:
            return peaks

        # First derivative approximation
        first_deriv = np.gradient(audio_data_region)

        # Find zero crossings in first derivative (potential extrema)
        zero_crossings = np.where(np.diff(np.sign(first_deriv)))[0]

        # Score extrema by the absolute value of the audio signal at zero crossing (higher value = higher score)
        scores = np.abs(audio_data_region[zero_crossings])  
        if len(scores) == 0:
            return peaks
        # Choose "N" of the top indices
        top_indices = np.argsort(scores)[::-1][:self.n]
        extrema_indices = zero_crossings[top_indices]

        # Round and deduplicate
        rounded_indices = np.unique(np.round(extrema_indices).astype(int))

        # Refine using Newton's method
        refined_indices = []
        for idx in rounded_indices:
            x = idx
            for _ in range(5):  # 5 iterations of Newton's method
                if x <= 0 or x >= len(audio_data_region) - 1:
                    break
                f_prime = (audio_data_region[x+1] - audio_data_region[x-1]) / 2
                f_double_prime = audio_data_region[x+1] - 2*audio_data_region[x] + audio_data_region[x-1]
                if f_double_prime == 0:
                    break
                # Newton's method step
                x_new = x - f_prime / f_double_prime
                if abs(x_new - x) < 1e-3:
                    break
                x = int(np.clip(x_new, 1, len(audio_data_region)-2))
            refined_indices.append(x + offset)

        # Remove duplicates after refinement
        times = librosa.samples_to_time(refined_indices, sr=self.sr)
        times = np.unique(np.round(times, 1))
        peaks.extend(times.tolist())
        return peaks
    
    def find_beats(self):
        '''Sample Beats, potentially for use in a naive firework show generator that is not implemented yet'''
        _, beat_frames = librosa.beat.beat_track(y=self.audio_data, sr=self.sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=self.sr)
        return beat_times.tolist()
