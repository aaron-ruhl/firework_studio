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