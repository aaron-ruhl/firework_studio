from scipy.signal import butter, lfilter

class AudioFilter:
    def __init__(self, sample_rate):
        self.sample_rate = sample_rate

    def lowpass(self, data, cutoff, order=5):
        """Apply a low-pass filter to the data."""
        nyq = 0.5 * self.sample_rate
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return lfilter(b, a, data)

    def highpass(self, data, cutoff, order=5):
        """Apply a high-pass filter to the data."""
        nyq = 0.5 * self.sample_rate
        normal_cutoff = cutoff / nyq #Most digital filter design functions (like those in scipy.signal) expect the cutoff frequency as a fraction of the Nyquist frequency, not in Hz.
        b, a = butter(order, normal_cutoff, btype='high', analog=False) #  This normalization ensures the cutoff is in the correct range (0 to 1)
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
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")