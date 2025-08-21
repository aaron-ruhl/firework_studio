import numpy as np
import librosa
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QComboBox, QSpinBox
from toaster import ToastDialog

import librosa.display

class FireworkShowHelper:
    def __init__(self, main_window):
        self.main_window = main_window

    def plot_spectrogram(self):
        mw = self.main_window
        if mw.audio_data is not None and mw.sr is not None:
            mw.spectrogram_ax.clear()
            S = librosa.stft(mw.audio_data, n_fft=2048, hop_length=512)
            S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)
            img = librosa.display.specshow(
                S_db, ax=mw.spectrogram_ax, sr=mw.sr, hop_length=512,
                x_axis='time', y_axis='linear', cmap='magma'
            )
            mw.spectrogram_ax.grid(False)
            mw.spectrogram_canvas.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
            mw.spectrogram_ax.set_xlabel("")
            mw.spectrogram_ax.set_ylabel("")
            mw.spectrogram_ax.set_xticks([])
            mw.spectrogram_ax.set_yticks([])
            mw.spectrogram_canvas.draw_idle()
        else:
            mw.spectrogram_ax.clear()
            mw.spectrogram_canvas.draw_idle()

    def plot_waveform(self, current_legend=None):
        mw = self.main_window
        audio_to_plot = mw.audio_data
        ax = mw.waveform_canvas.figure.axes[0]
        ax.clear()
        if audio_to_plot is not None:
            times = np.linspace(0, len(audio_to_plot) / mw.sr, num=len(audio_to_plot))
            max_points = 2000
            if len(audio_to_plot) > max_points:
                factor = len(audio_to_plot) // max_points
                audio_data_reshaped = audio_to_plot[:factor * max_points].reshape(-1, factor)
                envelope_min = audio_data_reshaped.min(axis=1)
                envelope_max = audio_data_reshaped.max(axis=1)
                times_ds = times[:factor * max_points].reshape(-1, factor)
                times_ds = times_ds.mean(axis=1)
                ax.fill_between(times_ds, envelope_min, envelope_max, color="#8fb9bd", alpha=0.7, linewidth=0)
                ax.plot(times_ds, envelope_max, color="#5fd7e6", linewidth=0.7, alpha=0.9)
                ax.plot(times_ds, envelope_min, color="#5fd7e6", linewidth=0.7, alpha=0.9)
            else:
                ax.plot(times, audio_to_plot, color="#8fb9bd", linewidth=1.2, alpha=0.95, antialiased=True)
            ax.set_facecolor("#000000")
            ax.tick_params(axis='y', colors='white')
            if mw.segment_times is not None and isinstance(mw.segment_times, (list, tuple)):
                for t in mw.segment_times:
                    if t is not None and isinstance(t, (int, float)) and np.isfinite(t):
                        ax.axvline(x=t, color="#ffd700", linestyle="--", linewidth=1.2, alpha=0.9)
            mw.waveform_canvas.draw_idle()
            if hasattr(mw, 'waveform_selector'):
                mw.waveform_selector.update_original_limits()
            if mw.duration is not None and mw.sr is not None:
                ax.set_xlim(0, mw.duration)
            elif audio_to_plot is not None and mw.sr is not None:
                ax.set_xlim(0, len(audio_to_plot) / mw.sr)
            else:
                ax.set_xlim(0, 1)
            if hasattr(mw, 'waveform_selector') and hasattr(mw.waveform_selector, 'update_original_limits'):
                mw.waveform_selector.update_original_limits()
            ax.set_xlabel("Time (s)", color='white')
            ax.set_ylabel("Amplitude", color='white')
            ax.grid(True, color="#888888", alpha=0.3, linestyle="--", linewidth=0.8)
        else:
            ax.set_title("No audio loaded", color='white')
            ax.set_xticks([])
            ax.set_yticks([])
        if current_legend is not None:
            if mw.segment_times is not None and isinstance(mw.segment_times, (list, tuple)):
                self.handle_segments(mw.segment_times)
            if mw.points is not None and isinstance(mw.points, (list, tuple)):
                self.handle_interesting_points(mw.points)
            if mw.onsets is not None and isinstance(mw.onsets, (list, tuple)):
                self.handle_onsets(mw.onsets)
            if mw.peaks is not None and isinstance(mw.peaks, (list, tuple)):
                self.handle_peaks(mw.peaks)
        mw.waveform_canvas.draw_idle()
        if hasattr(mw, 'waveform_selector'):
            mw.waveform_selector.update_original_limits()

    def update_firework_show_info(self):
        mw = self.main_window
        if mw.duration is not None:
            mins, secs = divmod(int(mw.duration), 60)
            duration_str = f"{mins:02d}:{secs:02d}"
        else:
            duration_str = "N/A"
        firing_count = len(mw.preview_widget.firework_times) if hasattr(mw, "preview_widget") and hasattr(mw.preview_widget, "firework_times") and mw.preview_widget.firework_times is not None else 0
        pattern = "N/A"
        if hasattr(mw, "pattern_selector"):
            combo = mw.pattern_selector.findChild(QComboBox)
            if combo is not None:
                pattern = combo.currentText()
        number_firings = "N/A"
        if hasattr(mw, "firework_count_spinner_group"):
            spinner = mw.firework_count_spinner_group.findChild(QSpinBox)
            if spinner is not None:
                number_firings = spinner.value()
        mw.firework_show_info = (
            f"🎆 Pattern: {pattern} | "
            f"Amount: {number_firings} | "
            f"Firings: {firing_count} 🎆"
            f"   🎵 SR: {mw.sr if mw.sr is not None else 'N/A'} | "
            f"Duration: {duration_str} | "
            f"Segments: {len(mw.segment_times) if mw.segment_times is not None else 0} "
            f"🎵"
        )
        if hasattr(mw, "status_bar") and mw.status_bar is not None:
            mw.status_bar.showMessage(mw.firework_show_info)
            mw.status_bar.repaint()
        return

    def handle_segments(self, segment_times):
        mw = self.main_window
        if mw.segment_times is None or mw.segment_times == []:
            mw.segment_times = list(segment_times)
            new_segments = list(segment_times)
        else:
            new_segments = [s for s in segment_times if s not in mw.segment_times]
            mw.segment_times.extend(new_segments)
        ax = mw.waveform_canvas.figure.axes[0]
        if mw.segment_times is not None:
            for t in mw.segment_times:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#ffd700", linestyle="--", linewidth=1.2, alpha=0.9, label=None)
                elif isinstance(t, (np.ndarray, list, tuple)):
                    for tt in np.atleast_1d(t):
                        if isinstance(tt, (int, float)) and np.isscalar(tt) and not isinstance(tt, complex):
                            ax.axvline(x=float(tt), color="#ffd700", linestyle="--", linewidth=1.2, alpha=0.9, label=None)
            legend = ax.get_legend()
            labels = [l.get_text() for l in legend.get_texts()] if legend else []
            if "Segment" not in labels:
                ax.axvline(x=0, color="#ffd700", linestyle="--", linewidth=1.2, alpha=0.9, label="Segment")
                leg = ax.legend(
                    loc="upper right",
                    framealpha=0.3,
                    fontsize=7,
                    markerscale=0.7,
                    handlelength=1.2,
                    borderpad=0.3,
                    labelspacing=0.2,
                    handletextpad=0.3,
                    borderaxespad=0.2,
                )
                if leg:
                    leg.get_frame().set_alpha(0.3)
        def show_segments_toast():
            toast = ToastDialog(f"Found {len(new_segments)//2 + 1} segments!", parent=mw)
            geo = mw.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)
        if hasattr(mw, "_segments_toast_shown") and not mw._segments_toast_shown:
            show_segments_toast()
            mw._segments_toast_shown = True
        self.update_firework_show_info()
        mw.waveform_canvas.draw_idle()
        if hasattr(mw, 'waveform_selector'):
            mw.waveform_selector.update_original_limits()

    def handle_interesting_points(self, points):
        mw = self.main_window
        if mw.points is None or mw.points == []:
            mw.points = list(points)
            new_points = list(points)
        else:
            new_points = [p for p in points if p not in mw.points]
            mw.points.extend(new_points)
        ax = mw.waveform_canvas.figure.axes[0]
        if mw.points is not None and isinstance(mw.points, (list, tuple, np.ndarray)):
            for t in mw.points:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#ff6f00", linestyle=":", linewidth=1.5, alpha=0.8, label=None)
            legend = ax.get_legend()
            labels = [l.get_text() for l in legend.get_texts()] if legend else []
            if "Interesting Point" not in labels:
                ax.axvline(x=0, color="#ff6f00", linestyle=":", linewidth=1.5, alpha=0.8, label="Interesting Point")
                leg = ax.legend(
                    loc="upper right",
                    framealpha=0.3,
                    fontsize=7,
                    markerscale=0.7,
                    handlelength=1.2,
                    borderpad=0.3,
                    labelspacing=0.2,
                    handletextpad=0.3,
                    borderaxespad=0.2,
                )
                if leg:
                    leg.get_frame().set_alpha(0.3)
        def show_interesting_toast():
            toast = ToastDialog(f"Found {len(new_points)} interesting points!", parent=mw)
            geo = mw.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)
        if hasattr(mw, "_interesting_points_toast_shown") and not mw._interesting_points_toast_shown:
            show_interesting_toast()
            mw._interesting_points_toast_shown = True
        mw.waveform_canvas.draw_idle()
        if hasattr(mw, 'waveform_selector'):
            mw.waveform_selector.update_original_limits()

    def handle_onsets(self, onsets):
        mw = self.main_window
        if mw.onsets is None or mw.onsets == []:
            mw.onsets = list(onsets)
            new_onsets = list(onsets)
        else:
            new_onsets = [o for o in onsets if o not in mw.onsets]
            mw.onsets.extend(new_onsets)
        ax = mw.waveform_canvas.figure.axes[0]
        if mw.onsets is not None and isinstance(mw.onsets, (list, tuple, np.ndarray)):
            for t in mw.onsets:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#00ff6f", linestyle="-.", linewidth=1.5, alpha=0.8, label=None)
            legend = ax.get_legend()
            labels = [l.get_text() for l in legend.get_texts()] if legend else []
            if "Onset" not in labels:
                ax.axvline(x=0, color="#00ff6f", linestyle="-.", linewidth=1.5, alpha=0.8, label="Onset")
                leg = ax.legend(
                    loc="upper right",
                    framealpha=0.3,
                    fontsize=7,
                    markerscale=0.7,
                    handlelength=1.2,
                    borderpad=0.3,
                    labelspacing=0.2,
                    handletextpad=0.3,
                    borderaxespad=0.2,
                )
                if leg:
                    leg.get_frame().set_alpha(0.3)
        def show_onset_toast():
            toast = ToastDialog(f"Found {len(new_onsets)} onsets!", parent=mw)
            geo = mw.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)
        if hasattr(mw, "_onsets_toast_shown") and not mw._onsets_toast_shown:
            show_onset_toast()
            mw._onsets_toast_shown = True
        mw.waveform_canvas.draw_idle()
        if hasattr(mw, 'waveform_selector'):
            mw.waveform_selector.update_original_limits()

    def handle_peaks(self, peaks):
        mw = self.main_window
        if mw.peaks is None or mw.peaks == []:
            mw.peaks = list(peaks)
            new_peaks = list(peaks)
        else:
            new_peaks = [p for p in peaks if p not in mw.peaks]
            mw.peaks.extend(new_peaks)
        ax = mw.waveform_canvas.figure.axes[0]
        if mw.peaks is not None and isinstance(mw.peaks, (list, tuple, np.ndarray)):
            for t in mw.peaks:
                if isinstance(t, (int, float)) and np.isscalar(t) and not isinstance(t, complex):
                    ax.axvline(x=float(t), color="#ff00ff", linestyle="--", linewidth=1.5, alpha=0.8, label=None)
            legend = ax.get_legend()
            labels = [l.get_text() for l in legend.get_texts()] if legend else []
            if "Peak" not in labels:
                ax.axvline(x=0, color="#ff00ff", linestyle="--", linewidth=1.5, alpha=0.8, label="Peak")
                leg = ax.legend(
                    loc="upper right",
                    framealpha=0.3,
                    fontsize=7,
                    markerscale=0.7,
                    handlelength=1.2,
                    borderpad=0.3,
                    labelspacing=0.2,
                    handletextpad=0.3,
                    borderaxespad=0.2,
                )
                if leg:
                    leg.get_frame().set_alpha(0.3)
        def show_peaks_toast():
            toast = ToastDialog(f"Found {len(new_peaks)} peaks!", parent=mw)
            geo = mw.geometry()
            x = geo.x() + geo.width() - toast.width() - 40
            y = geo.y() + geo.height() - toast.height() - 40
            toast.move(x, y)
            toast.show()
            QTimer.singleShot(2500, toast.close)
        if not hasattr(mw, "_peaks_toast_shown") or not mw._peaks_toast_shown:
            show_peaks_toast()
            mw._peaks_toast_shown = True
        mw.waveform_canvas.draw_idle()
        if hasattr(mw, 'waveform_selector'):
            mw.waveform_selector.update_original_limits()
