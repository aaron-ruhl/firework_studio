from PyQt6.QtCore import QThread, pyqtSignal, QTimer
import numpy as np
import librosa

from toaster import ToastDialog

class AudioAnalysis(QThread):
    segments_ready = pyqtSignal(list)
    interesting_points_ready = pyqtSignal(list)
    onsets_ready = pyqtSignal(list)
    beats_ready = pyqtSignal(list)
    peaks_ready = pyqtSignal(list)

    def __init__(self, audio_data, audio_datas, sr, duration, parent=None):
        super().__init__(parent)
        self.audio_data = audio_data
        self.audio_datas = audio_datas
        self.sr = sr
        self.task = None
        self.selected_region = None  # 
        self.duration = duration

        # SEGMENT SETTINGS
        self.n_mfcc = 13
        self.min_segments = 2
        self.max_segments = 12
        self.dct_type = 2
        self.n_fft = 2048
        self.hop_length_segments = 512
        

        # INTERESTING POINTS SETTINGS
        self.min_points = 5
        self.max_points = 20
        self.pre_max = 3
        self.post_max = 3
        self.pre_avg_distance = 3
        self.post_avg_distance = 5
        self.delta = 0.5
        self.moving_avg_wait = 5

        # ONSET SETTINGS
        self.min_onsets = 5
        self.max_onsets = 20
        self.hop_length_onsets = 512
        self.backtrack = True
        self.normalize = True

        # PEAK SETTINGS
        self.min_peaks = 5
        self.max_peaks = 20
        self.scoring = "absolute"  # Options: "absolute", "relative", "sharp", "custom"
        self.custom_scoring_method = None

    def set_segment_settings(self, n_mfcc=13, min_segments=2, max_segments=12, dct_type=2, n_fft=2048, hop_length_segments=512):
        self.n_mfcc = n_mfcc
        self.min_segments = min_segments
        self.max_segments = max_segments
        self.dct_type = dct_type
        self.n_fft = n_fft
        self.hop_length_segments = hop_length_segments

    def set_interesting_points_settings(self, min_points=5, max_points=20, pre_max=3, post_max=3, pre_avg_distance=3, post_avg_distance=5, delta=0.5, moving_avg_wait=5):
        self.min_points = min_points
        self.max_points = max_points
        self.pre_max = pre_max
        self.post_max = post_max
        self.pre_avg_distance = pre_avg_distance
        self.post_avg_distance = post_avg_distance
        self.delta = delta
        self.moving_avg_wait = moving_avg_wait

    def set_onset_settings(self, min_onsets=5, max_onsets=20, hop_length_onsets=512, backtrack=True, normalize=True):
        self.min_onsets = min_onsets
        self.max_onsets = max_onsets
        self.hop_length_onsets = hop_length_onsets
        self.backtrack = backtrack
        self.normalize = normalize

    def set_peak_settings(self, min_peaks=5, max_peaks=20, scoring="absolute", custom_scoring_method=None):
        self.min_peaks = min_peaks
        self.max_peaks = max_peaks
        self.scoring = scoring
        self.custom_scoring_method = custom_scoring_method

    def set_selected_region(self, region):
        self.selected_region = region

    def reset_selected_region(self):
        self.selected_region = None

    def clear_signals(self):
        self.segments_ready.emit([])
        self.interesting_points_ready.emit([])
        self.onsets_ready.emit([])
        self.beats_ready.emit([])
        self.peaks_ready.emit([])

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
        '''Segment each audio into distinct portions and concatenate results, limited to selected_region if set'''
        
        segments = []
        if self.audio_data is None or len(self.audio_data) == 0:
            return segments

        if self.selected_region is not None and isinstance(self.selected_region, (tuple, list)) and len(self.selected_region) == 2:
            start_time, end_time = self.selected_region
            selected_duration = end_time - start_time
            start_idx = int(start_time * self.sr)
            end_idx = int(end_time * self.sr)
            audio_data_region = self.audio_data[start_idx:end_idx]
            region_offset = start_idx
        else:
            audio_data_region = self.audio_data
            region_offset = 0

        mfcc = librosa.feature.mfcc(y=audio_data_region, sr=self.sr, n_mfcc=self.n_mfcc,dct_type=self.dct_type, n_fft=self.n_fft, hop_length=self.hop_length_segments)

        similarity = np.dot(mfcc.T, mfcc)
        similarity = similarity / np.max(similarity)

        # Set duration to selected_region if available
        duration = self.duration if self.selected_region is None else selected_duration
        # Use min_segments and max_segments to decide how many segments to draw
        min_segments = self.min_segments
        max_segments = self.max_segments
        target_segments = max(min_segments, min(max_segments, int(duration // 4)))
        if target_segments < 2:
            target_segments = 2

        segment_boundaries = librosa.segment.agglomerative(similarity, k=target_segments,)
        segment_times = librosa.frames_to_time(segment_boundaries, sr=self.sr)
        # Offset times if region is used
        if region_offset > 0:
            segment_times += librosa.samples_to_time(region_offset, sr=self.sr)

        segments = [(segment_times[i], segment_times[i+1]) for i in range(len(segment_times)-1)]
        segments.extend(segments)
        return segments

    def find_interesting_points(self):
        '''Find points of interest in each audio signal and concatenate results, limited to selected_region if set'''
        
        points = []
        if self.audio_data is None or len(self.audio_data) == 0:
            return points
        
        if self.selected_region is not None and isinstance(self.selected_region, (tuple, list)) and len(self.selected_region) == 2:
            start_time, end_time = self.selected_region
            selected_duration = end_time - start_time
            start_idx = int(start_time * self.sr)
            end_idx = int(end_time * self.sr)
            audio_data_region = self.audio_data[start_idx:end_idx]
            region_offset = start_idx
        else:
            audio_data_region = self.audio_data
            region_offset = 0

        centroids = librosa.feature.spectral_centroid(y=audio_data_region, sr=self.sr)[0]
        times = librosa.times_like(centroids, sr=self.sr)

        # Offset times if region is used
        if region_offset > 0:
            times += librosa.samples_to_time(region_offset, sr=self.sr)
        peaks = librosa.util.peak_pick(centroids, pre_max=self.pre_max, post_max=self.post_max, pre_avg=self.pre_avg_distance, post_avg=self.post_avg_distance, delta=self.delta, wait=self.moving_avg_wait)
        interesting_points = [times[p] for p in peaks]


        # Set duration to selected_region if available
        duration = self.duration if self.selected_region is None else selected_duration
        # Use min_points and max_points to decide how many segments to draw
        target_points = max(self.min_points, min(self.max_points, int(duration // 3)))

        if len(peaks) > 0:
            top_indices = np.argsort(centroids[peaks])[::-1][:target_points]
            interesting_points = [times[peaks[i]] for i in top_indices]
        points.extend(interesting_points)

        return points

    def find_onsets(self):
        '''Find onsets in each audio signal and concatenate results, limited to selected_region if set'''
        onsets = []
        if self.audio_data is None or len(self.audio_data) == 0:
            return onsets
        
        if self.selected_region is not None and isinstance(self.selected_region, (tuple, list)) and len(self.selected_region) == 2:
            start_time, end_time = self.selected_region
            selected_duration = end_time - start_time
            start_idx = int(start_time * self.sr)
            end_idx = int(end_time * self.sr)
            audio_data_region = self.audio_data[start_idx:end_idx]
            region_offset = start_idx
        else:
            audio_data_region = self.audio_data
            region_offset = 0

        onset_frames = librosa.onset.onset_detect(y=audio_data_region, sr=self.sr, hop_length=self.hop_length_onsets, backtrack=self.backtrack,normalize=self.normalize,)
        onset_times = librosa.frames_to_time(onset_frames, sr=self.sr)


        # Offset times if region is used
        if region_offset > 0:
            onset_times += librosa.samples_to_time(region_offset, sr=self.sr)
        # set the duration to selected region if available
        duration = self.duration if self.selected_region is None else selected_duration
        # Set the min and max amount of onsets based on settings
        target_onsets = max(self.min_onsets, min(self.max_onsets, int(duration // 3)))
        if len(onset_times) > target_onsets:
            indices = np.linspace(0, len(onset_times) - 1, target_onsets, dtype=int)
            sampled_onsets = [onset_times[i] for i in indices]
            onsets.extend(sampled_onsets)
        else:
            onsets.extend(onset_times.tolist())
        return onsets

    def find_local_maxima(self): 
        '''Find n local maxima and minima using derivative approximation and Newton's method within selected_region'''
        peaks = []
        if self.audio_data is None or len(self.audio_data) == 0:
            return peaks

        # If selected_region is provided, convert times to indices and slice audio_data
        if self.selected_region is not None and isinstance(self.selected_region, (tuple, list)) and len(self.selected_region) == 2:
            start_time, end_time = self.selected_region
            selected_duration = end_time - start_time
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

        if self.scoring == "absolute":
            # Score extrema by the absolute value of the audio signal at zero crossing (higher value = higher score)
            scores = np.abs(audio_data_region[zero_crossings])
        elif self.scoring == "relative":
            # Score extrema by the relative value of the audio signal at zero crossing (higher value = higher score)
            scores = audio_data_region[zero_crossings] / np.max(np.abs(audio_data_region))  # Avoid division by zero
        elif self.scoring == "sharp":
            # Score extrema by the sharpness of the signal (higher value = higher score)
            scores = np.abs(np.diff(audio_data_region, 2))[zero_crossings[1:-1]]
        elif self.scoring == "custom":
            # Score extrema by a custom method (higher value = higher score)
            if self.custom_scoring_method is not None:
                scores = self.custom_scoring_method(audio_data_region, zero_crossings)
        if len(scores) == 0:
            return peaks
        
        # set the duration to selected region if available
        duration = self.duration if self.selected_region is None else selected_duration
        # Set the min and max amount of peaks based on settings
        target_peaks = max(self.min_peaks, min(self.max_peaks, int(duration // 3)))
        # Choose "target_peaks" of the top indices
        top_indices = np.argsort(scores)[::-1][:target_peaks]
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
