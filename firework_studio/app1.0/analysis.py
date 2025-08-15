from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import librosa
from PyQt6.QtWidgets import QMessageBox

class AudioAnalysis(QThread):
    segments_ready = pyqtSignal(list)
    interesting_points_ready = pyqtSignal(list)
    onsets_ready = pyqtSignal(list)
    beats_ready = pyqtSignal(list)

    def __init__(self, audio_datas, sr, parent=None):
        super().__init__(parent)
        self.audio_datas = audio_datas
        self.sr = sr
        self.task = None

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

    def find_segments(self):
        '''Segment each audio into distinct portions and concatenate results'''
        results = []
        for audio_data in getattr(self, "audio_datas", [self.audio_datas]):
            if audio_data is None or len(audio_data) == 0:
                print("No audio data available for segment analysis.")
                continue
            mfcc = librosa.feature.mfcc(y=audio_data, sr=self.sr, n_mfcc=13)
            similarity = np.dot(mfcc.T, mfcc)
            similarity = similarity / np.max(similarity)
            segment_boundaries = librosa.segment.agglomerative(similarity, k=6)
            segment_times = librosa.frames_to_time(segment_boundaries, sr=self.sr)
            segments = [(segment_times[i], segment_times[i+1]) for i in range(len(segment_times)-1)]
            results.extend(segments)
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

    def find_beats(self):
        '''Sample Beats for use in a naive firework show generator'''
        _, beat_frames = librosa.beat.beat_track(y=self.audio_data, sr=self.sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=self.sr)
        return beat_times.tolist()
