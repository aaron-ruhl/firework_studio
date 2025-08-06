from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import librosa


class SimpleBeatSampleThread(QThread):
        finished = pyqtSignal(object)

        def __init__(self, audio_data, sr, segment_times):
            super().__init__()
            self.audio_data = audio_data
            self.sr = sr
            self.segment_times = segment_times

        def run(self):
            _, beats = librosa.beat.beat_track(y=self.audio_data, sr=self.sr)
            beat_times = librosa.frames_to_time(beats, sr=self.sr)

            beat_interval = 5  # target seconds between sampled beats
            cluster_window = 2 # seconds for clustering

            firework_firing = []
            for i in range(len(self.segment_times) - 1):
                seg_start = self.segment_times[i]
                seg_end = self.segment_times[i + 1]
                beats_in_seg = beat_times[(beat_times >= seg_start) & (beat_times < seg_end)]
                if len(beats_in_seg) > 0:
                    last_time = seg_start
                    for bt in beats_in_seg:
                        if bt - last_time >= beat_interval or len(firework_firing) == 0:
                            firework_firing.append(bt)
                            last_time = bt
                    seg_center = (seg_start + seg_end) / 2
                    clustered = beats_in_seg[(np.abs(beats_in_seg - seg_center) < cluster_window)]
                    for bt in clustered:
                        if bt not in firework_firing:
                            firework_firing.append(bt)
            firework_firing = np.sort(np.array(firework_firing))
            self.finished.emit(firework_firing)

class SegmenterThread(QThread):
    segments_ready = pyqtSignal(list, object)

    def __init__(self, audio_datas, sr):
        super().__init__()
        self.audio_datas = audio_datas
        self.sr = sr

    def run(self):
        all_periods_info = []
        all_segment_times = []
        offset = 0.0
        for idx, y in enumerate(self.audio_datas):
            duration = librosa.get_duration(y=y, sr=self.sr)
            # Set number of segments: 1 per 10 seconds, min 2, max 20
            k = max(2, min(20, int(duration // 10) + 1))
            chroma = librosa.feature.chroma_cqt(y=y, sr=self.sr)
            recurrence = librosa.segment.recurrence_matrix(chroma, mode='affinity', sym=True)
            segments = librosa.segment.agglomerative(recurrence, k=k)
            segment_times = librosa.frames_to_time(segments, sr=self.sr)
            segment_times_offset = segment_times + offset
            for i in range(len(segment_times_offset) - 1):
                start_min, start_sec = divmod(int(segment_times_offset[i]), 60)
                end_min, end_sec = divmod(int(segment_times_offset[i+1]), 60)
                all_periods_info.append({
                    'start': f"{start_min:02d}:{start_sec:02d}",
                    'end': f"{end_min:02d}:{end_sec:02d}",
                    'segment_id': len(all_periods_info)
                })
            if idx == 0:
                all_segment_times.extend(segment_times_offset)
            else:
                all_segment_times.extend(segment_times_offset[1:])
            offset += duration
        self.segments_ready.emit(all_periods_info, np.array(all_segment_times))

class AudioAnalyzer:
    def __init__(self, audio_datas, sr):
        self.audio_datas = audio_datas
        self.sr = sr

    def analyze_firework_firings(self):
        firework_firings = []
        offset = 0.0
        for audio_file in self.audio_datas:
            # Segment audio and get segment times
            periods_info, segment_times = AudioAnalyzer([audio_file], self.sr).segment_audio()
            # Get beat times
            beat_times, _ = AudioAnalyzer([audio_file], self.sr).beat_sample()
            # Cluster beats near segment centers and sample at intervals
            beat_interval = 5  # seconds between sampled beats
            cluster_window = 2 # seconds for clustering
            firing = []
            for i in range(len(segment_times) - 1):
                seg_start = segment_times[i]
                seg_end = segment_times[i + 1]
                beats_in_seg = beat_times[(beat_times >= seg_start) & (beat_times < seg_end)]
                if len(beats_in_seg) > 0:
                    last_time = seg_start
                    for bt in beats_in_seg:
                        if bt - last_time >= beat_interval or len(firing) == 0:
                            firing.append(bt)
                            last_time = bt
                    seg_center = (seg_start + seg_end) / 2
                    clustered = beats_in_seg[(np.abs(beats_in_seg - seg_center) < cluster_window)]
                    for bt in clustered:
                        if bt not in firing:
                            firing.append(bt)
            firing = np.sort(np.array(firing)) + offset
            firework_firings.extend(firing)
            offset += librosa.get_duration(y=y, sr=self.sr)
        return np.sort(np.array(firework_firings))
    
    def segment_audio(self):
        # Example segmentation using librosa onset detection
        audio = np.concatenate(self.audio_datas)
        onset_env = librosa.onset.onset_strength(y=audio, sr=self.sr)
        segments = librosa.onset.onset_detect(onset_envelope=onset_env, sr=self.sr)
        segment_times = librosa.frames_to_time(segments, sr=self.sr)
        periods_info = {"onsets": segment_times}
        return periods_info, segment_times

    def beat_sample(self):
        audio = np.concatenate(self.audio_datas)
        tempo, beats = librosa.beat.beat_track(y=audio, sr=self.sr)
        beat_times = librosa.frames_to_time(beats, sr=self.sr)
        return beat_times, tempo
