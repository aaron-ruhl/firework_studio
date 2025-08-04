from PyQt6.QtCore import QThread, pyqtSignal
import librosa


class AudioLoaderThread(QThread):
    audio_loaded = pyqtSignal(list, int)

    def __init__(self, paths):
        super().__init__()
        self.paths = paths

    def run(self):
        audio_datas = []
        sr = None
        for path in self.paths:
            y, s = librosa.load(path, sr=None)
            if sr is None:
                sr = s
            elif sr != s:
                y = librosa.resample(y, orig_sr=s, target_sr=sr)
            audio_datas.append(y)
        self.audio_loaded.emit(audio_datas, sr)