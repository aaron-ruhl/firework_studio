from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import librosa

class AudioAnalysis(QThread):
    segments_found = pyqtSignal(list)
    interesting_points_found = pyqtSignal(list)
    onset_points_found = pyqtSignal(list)
    beat_points_found = pyqtSignal(list)

    def __init__(self, audio_data, sr, parent=None):
        super().__init__(parent)
        self.audio_data = audio_data
        self.sr = sr

    def find_segments(self, audio_data, sr):
        # Use librosa's feature extraction and similarity to segment the audio
        # Compute MFCCs as features
        mfcc = librosa.feature.mfcc(y=audio_data, sr=sr, n_mfcc=13)
        # Compute self-similarity matrix
        similarity = np.dot(mfcc.T, mfcc)
        # Normalize similarity matrix
        similarity = similarity / np.max(similarity)
        # Use librosa's agglomerative segmentation
        segment_boundaries = librosa.segment.agglomerative(similarity, k=6)  # k = number of segments (can be tuned)
        # Convert boundaries to times
        segment_times = librosa.frames_to_time(segment_boundaries, sr=sr)
        # Pair up start/end times
        segments = [(segment_times[i], segment_times[i+1]) for i in range(len(segment_times)-1)]
        print(f"Found segments: {segments}")
        return segments
    
    def find_interesting_points(self, audio_data, sr):
        # Use spectral centroid as an example of "interesting" points
        centroids = librosa.feature.spectral_centroid(y=audio_data, sr=sr)[0]
        times = librosa.times_like(centroids, sr=sr)
        # Pick local maxima as interesting points
        peaks = librosa.util.peak_pick(centroids, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=0.5, wait=5)
        interesting_points = [times[p] for p in peaks]
        # Select only the top N most prominent points (e.g., 10)
        N = 10
        if len(peaks) > 0:
            # Sort peaks by centroid value (descending), pick top N
            top_indices = np.argsort(centroids[peaks])[::-1][:N]
            interesting_points = [times[peaks[i]] for i in top_indices]
        return interesting_points
    
    def find_onsets(self, audio_data, sr):
        # Use librosa.onset.onset_detect to find onset events
        onset_frames = librosa.onset.onset_detect(y=audio_data, sr=sr)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)
        # Sample a subset of onsets (e.g., evenly spaced, max 20)
        max_onsets = 20
        if len(onset_times) > max_onsets:
            indices = np.linspace(0, len(onset_times) - 1, max_onsets, dtype=int)
            sampled_onsets = [onset_times[i] for i in indices]
            return sampled_onsets
        return onset_times.tolist()

    def find_beats(self, audio_data, sr):
        # Use librosa.beat.beat_track to find beat positions
        tempo, beat_frames = librosa.beat.beat_track(y=audio_data, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        return beat_times.tolist()