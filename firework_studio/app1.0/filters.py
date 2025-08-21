from scipy.signal import butter, lfilter

class AudioFilter:
    def __init__(self, sample_rate, original_audio=None):
        self.sample_rate = sample_rate
        self.original_audio = original_audio

    def reload_original(self):
        """Return the original, unfiltered audio data."""
        if self.original_audio is None:
            raise ValueError("No original audio data set.")
        return self.original_audio

    def lowpass(self, data, cutoff, order=5):
        """Apply a low-pass filter to the data."""
        nyq = 0.5 * self.sample_rate
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return lfilter(b, a, data)

    def highpass(self, data, cutoff, order=5):
        """Apply a high-pass filter to the data."""
        nyq = 0.5 * self.sample_rate
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='high', analog=False)
        return lfilter(b, a, data)

    def bandpass(self, data, lowcut, highcut, order=5):
        """Apply a band-pass filter to the data."""
        nyq = 0.5 * self.sample_rate
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(order, [low, high], btype='band')
        return lfilter(b, a, data)

    def apply(self, data, filter_type, **kwargs):
        if filter_type == 'lowpass':
            return self.lowpass(data, kwargs.get('cutoff'), kwargs.get('order', 5))
        elif filter_type == 'highpass':
            return self.highpass(data, kwargs.get('cutoff'), kwargs.get('order', 5))
        elif filter_type == 'bandpass':
            return self.bandpass(data, kwargs.get('lowcut'), kwargs.get('highcut'), kwargs.get('order', 5))
        elif filter_type == 'reload_original':
            return self.reload_original()
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")