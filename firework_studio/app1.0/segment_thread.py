from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
import librosa



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
            chroma = librosa.feature.chroma_cqt(y=y, sr=self.sr)
            recurrence = librosa.segment.recurrence_matrix(chroma, mode='affinity', sym=True)
            segments = librosa.segment.agglomerative(recurrence, k=8)
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
            offset += librosa.get_duration(y=y, sr=self.sr)
        self.segments_ready.emit(all_periods_info, np.array(all_segment_times))
